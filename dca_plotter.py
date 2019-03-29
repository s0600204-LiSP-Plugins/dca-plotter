# -*- coding: utf-8 -*-
#
# This file is part of Linux Show Player
#
# Copyright 2012-2018 Francesco Ceruti <ceppofrancy@gmail.com>
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

from lisp.core.plugin import Plugin
from lisp.core.signal import Signal
from lisp.cues.cue_factory import CueFactory
from lisp.plugins.list_layout.layout import ListLayout
from lisp.ui.settings.app_configuration import AppConfigurationDialog
from lisp.ui.settings.session_configuration import SessionConfigurationDialog
from lisp.ui.ui_utils import translate

from dca_plotter.cue.change_cue import DcaChangeCue
from dca_plotter.cue.reset_cue import DcaResetCue
from dca_plotter.dca_plotter_settings import DcaPlotterSettings
from dca_plotter.mapper.dialog import DcaMappingDialog
from dca_plotter.mapper.model import DcaMappingModel
from dca_plotter.mic_assign_ui import MicAssignUi
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
    _mapping_model = None
    _tracking_model = None
    _tracker_view = None

    initialised = Signal()

    def __init__(self, app):
        super().__init__(app)

        # Register the settings widget
        AppConfigurationDialog.registerSettingsPage(
            'plugins.dca_plotter', DcaPlotterSettings, DcaPlotter.Config)

        # Register the session-level mic assign ui
        SessionConfigurationDialog.registerSettingsPage(
            'mic_assign', MicAssignUi, self)

        # Register our cue types
        CueFactory.register_factory(DcaChangeCue.__name__, DcaChangeCue)
        app.window.registerSimpleCueMenu(DcaChangeCue, self.CueCategory)

        CueFactory.register_factory(DcaResetCue.__name__, DcaResetCue)
        app.window.registerSimpleCueMenu(DcaResetCue, self.CueCategory)

        # Register listeners for when a session has been created and pre-destruction.
        app.session_created.connect(self._on_session_init)
        app.session_before_finalize.connect(self._pre_session_deinit)

    def _open_mapper_dialog(self):
        if self.mapper_enabled():
            dca_mapper = DcaMappingDialog()
            dca_mapper.exec_()

    def _pre_session_deinit(self):
        layout = self.app.layout
        if isinstance(layout, ListLayout):
            cuelist_model = layout.list_model()
            cuelist_model.item_added.disconnect(self._on_cue_added)
            cuelist_model.item_moved.disconnect(self._on_cue_moved)
            cuelist_model.item_removed.disconnect(self._on_cue_removed)
            layout.view().listView.currentItemChanged.disconnect(self._on_cue_selected)

    def _on_session_init(self):
        """Post-session-creation init"""

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
            self.initialised.emit()
            return

        # Draw the tracker
        self._tracker_view = DcaTrackingView(parent=layout.view().parent())
        layout.view().layout().addWidget(self._tracker_view, 2, 0, 1, 3)

        # Create the mapping model.
        # This model *does* contain cues - or references to them - and with the
        # aid of the listeners below gets updated when certain cues are updated.
        self._mapping_model = DcaMappingModel()

        # Create an entry in the "Tools" menu
        if not self._mapping_menu_action:
            self._mapping_menu_action = QAction('DCA Mapper', self.app.window)
            self._mapping_menu_action.triggered.connect(self._open_mapper_dialog)
            self.app.window.menuTools.addAction(self._mapping_menu_action)

        # Listeners for cue actions
        cuelist_model = layout.list_model()
        cuelist_model.item_added.connect(self._on_cue_added)
        cuelist_model.item_moved.connect(self._on_cue_moved)
        cuelist_model.item_removed.connect(self._on_cue_removed)
        layout.view().listView.currentItemChanged.connect(self._on_cue_selected)

        self.initialised.emit()

    def _on_cue_selected(self, current, _):
        """Action to take when a cue is selected.

        This function only gets called if the session is in the "List" layout.
        With the "Cart" layout, selecting a cue calls the cue.
        (And there are no other layouts currently.)
        """
        if current:
            if _is_supported_cuetype(current.cue.type):
                self._tracking_model.select_cue(current.cue)
            else:
                self._tracking_model.clear_current_diff()

    def _on_cue_added(self, cue):
        """Action to take when a cue is added to the List Layout."""
        if _is_supported_cuetype(cue.type):
            self._mapping_model.append_cuerow(cue)
            cue.property_changed.connect(self._tracking_model.on_cue_update)

    def _on_cue_moved(self, _, new_index):
        """Action to take when a cue is moved in the List Layout."""
        cue = self.app.layout.list_model().item(new_index)
        if _is_supported_cuetype(cue.type):
            self._mapping_model.move_cuerow(cue, new_index)

    def _on_cue_removed(self, cue):
        """Action to take when a cue is removed from the List Layout."""
        if _is_supported_cuetype(cue.type):
            self._mapping_model.remove_cuerow(cue)
            cue.property_changed.disconnect(self._tracking_model.on_cue_update)

    def get_microphone_count(self):
        count = len(self.SessionConfig['inputs'])
        return count if count > 0 else self.Config['input_channel_count']

    def mapper_enabled(self):
        return isinstance(self.app.layout, ListLayout)

    def mapper(self):
        return self._mapping_model

    def tracker(self):
        return self._tracking_model

def _is_supported_cuetype(cue_type):
    return cue_type in ('DcaChangeCue', 'DcaResetCue')
