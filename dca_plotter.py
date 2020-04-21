# This file is a derivation of work on - and as such shares the same
# licence as - Linux Show Player
#
# Linux Show Player:
#   Copyright 2012-2020 Francesco Ceruti <ceppofrancy@gmail.com>
#
# This file:
#   Copyright 2020 s0600204
#
# Linux Show Player is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Linux Show Player is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Linux Show Player.  If not, see <http://www.gnu.org/licenses/>.

# pylint: disable=missing-docstring

# pylint: disable=no-name-in-module
from PyQt5.QtCore import QT_TRANSLATE_NOOP
from PyQt5.QtWidgets import QAction

# pylint: disable=import-error
from lisp.core.plugin import Plugin
from lisp.core.signal import Signal
from lisp.cues.cue_factory import CueFactory
from lisp.plugins.list_layout.layout import ListLayout
from lisp.ui.settings.app_configuration import AppConfigurationDialog
from lisp.ui.settings.session_configuration import SessionConfigurationDialog

from dca_plotter.config.channel_assign import ChannelAssignConfig
from dca_plotter.cue.change_cue import DcaChangeCue
from dca_plotter.cue.reset_cue import DcaResetCue
from dca_plotter.dca_plotter_settings import DcaPlotterSettings
from dca_plotter.mapper.dialog import DcaMappingDialog
from dca_plotter.mapper.model import DcaMappingModel
from dca_plotter.tracker.model import DcaTrackingModel
from dca_plotter.tracker.view import DcaTrackingView

class DcaPlotter(Plugin):
    """Provides the ability to plot DCA/VCA assignments"""

    Name = 'DCA/VCA Plotter'
    Authors = ('s0600204',)
    Depends = ('Midi', 'MidiFixtureControl')
    Description = 'Provides the ability to plot DCA/VCA assignments'
    CueCategory = QT_TRANSLATE_NOOP("CueCategory", "DCA/VCA Manipulation")

    _mapping_menu_action = None
    _mapping_dialog = None
    _mapping_model = None
    _tracking_model = None
    _tracker_view = None

    _cue_types = (DcaChangeCue, DcaResetCue)

    initialised = Signal()

    def __init__(self, app):
        super().__init__(app)

        # Register the settings widget
        AppConfigurationDialog.registerSettingsPage(
            'plugins.dca_plotter', DcaPlotterSettings, DcaPlotter.Config)

        # Register the session-level configuration of inputs
        SessionConfigurationDialog.registerSettingsPage(
            'channel_assign', ChannelAssignConfig, self)

        # Register our cue types
        for cue_type in self._cue_types:
            CueFactory.register_factory(cue_type.__name__, cue_type)
            app.window.registerSimpleCueMenu(cue_type, self.CueCategory)

    def _open_mapper_dialog(self):
        if not self.mapper_enabled():
            return
        if not self._mapping_dialog:
            self._mapping_dialog = DcaMappingDialog(self._mapping_model)
        self._mapping_dialog.open()

    def _pre_session_deinitialisation(self, _):
        '''Called when session is being de-init'd.'''
        layout = self.app.layout
        if isinstance(layout, ListLayout):
            layout.model.item_added.disconnect(self._on_cue_added)
            layout.model.item_moved.disconnect(self._on_cue_moved)
            layout.model.item_removed.disconnect(self._on_cue_removed)
            layout.view.listView.currentItemChanged.disconnect(self._on_cue_selected)
        if self._tracker_view:
            self._tracker_view.deinitialise()
            self._tracker_view = None

    def finalize(self):
        '''Called when application is closing'''
        super().finalize()
        self._tracker_view = None

    def _on_session_initialised(self, _):
        """Post-session-initialisation init.

        Called after the plugin session-configuration have been set, but before cues have
        been restored (in the case of loading from file).
        """
        layout = self.app.layout

        # Create the session's dca-tracking model
        # This model does not contain cues.
        # Instead it tracks which mics are muted and are currently assigned where
        self._tracking_model = DcaTrackingModel(self.mapper_enabled())

        # If the mapper is not to be used we don't need to have it or its menu option in existence
        if not self.mapper_enabled():
            if self._mapping_menu_action:
                self.app.window.menuTools.removeAction(self._mapping_menu_action)
            self._mapping_menu_action = None
            self._mapping_model = None
            if self._mapping_dialog:
                self._mapping_dialog.close()
            self.initialised.emit()
            return

        # Draw the tracker
        self._tracker_view = DcaTrackingView(parent=layout.view.parent())
        layout.view.layout().addWidget(self._tracker_view)

        # Create the mapping model.
        # This model *does* contain cues - or references to them - and with the
        # aid of the listeners below gets updated when certain cues are updated.
        self._mapping_model = DcaMappingModel()
        if self._mapping_dialog:
            self._mapping_dialog.setModel(self._mapping_model)

        # Create an entry in the "Tools" menu
        if not self._mapping_menu_action:
            self._mapping_menu_action = QAction('DCA Mapper', self.app.window)
            self._mapping_menu_action.triggered.connect(self._open_mapper_dialog)
            self.app.window.menuTools.addAction(self._mapping_menu_action)

        # Listeners for cue actions
        layout.model.item_added.connect(self._on_cue_added)
        layout.model.item_moved.connect(self._on_cue_moved)
        layout.model.item_removed.connect(self._on_cue_removed)
        layout.view.listView.currentItemChanged.connect(self._on_cue_selected)

        self.initialised.emit()

    def _on_cue_selected(self, current, _):
        """Action to take when a cue is selected.

        This function only gets called if the session is in the "List" layout.
        With the "Cart" layout, selecting a cue calls the cue.
        (And there are no other layouts currently.)
        """
        if current and self._mapping_model:
            if self._is_supported_cuetype(current.cue.type):
                self._tracking_model.select_cue(current.cue)
            else:
                self._tracking_model.clear_current_diff()

    def _on_cue_added(self, cue):
        """Action to take when a cue is added to the List Layout."""
        if self._is_supported_cuetype(cue.type):
            self._mapping_model.append_cuerow(cue)
            cue.property_changed.connect(self._tracking_model.on_cue_update)

    def _on_cue_moved(self, _, new_index):
        """Action to take when a cue is moved in the List Layout."""
        cue = self.app.layout.model.item(new_index)
        if self._is_supported_cuetype(cue.type):
            self._mapping_model.move_cuerow(cue, new_index)

    def _on_cue_removed(self, cue):
        """Action to take when a cue is removed from the List Layout."""
        if self._is_supported_cuetype(cue.type):
            self._mapping_model.remove_cuerow(cue)
            cue.property_changed.disconnect(self._tracking_model.on_cue_update)

    def get_assignable_count(self):
        counts = {}
        for assignable in ['input', 'fx']:
            count = len(self.SessionConfig['assigns'][assignable])
            counts[assignable] = count if count > 0 else self.Config[assignable + '_channel_count']
        return counts

    def mapper_enabled(self):
        return isinstance(self.app.layout, ListLayout)

    def mapper(self):
        return self._mapping_model

    def tracker(self):
        return self._tracking_model

    def _is_supported_cuetype(self, cue_type):
        return cue_type in [ct.__name__ for ct in self._cue_types]
