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

from PyQt5.QtWidgets import QAction#, QDialog

from lisp.application import Application
from lisp.core.plugin import Plugin
from lisp.plugins.dca_plotter.cue.change_cue import DcaChangeCue
from lisp.plugins.dca_plotter.dca_plotter_mic_assign_ui import DcaPlotterMicAssignUi
from lisp.plugins.dca_plotter.dca_plotter_settings import DcaPlotterSettings
from lisp.plugins.dca_plotter.mapper.dialog import DcaMappingDialog
from lisp.plugins.dca_plotter.mapper.model import DcaMappingModel
from lisp.plugins.dca_plotter.tracker.model import DcaTrackingModel
from lisp.plugins.list_layout.layout import ListLayout
from lisp.ui.settings.app_configuration import AppConfigurationDialog
from lisp.ui.settings.session_configuration import SessionConfigurationDialog
from lisp.ui.ui_utils import translate

class DcaPlotter(Plugin):
    """Provides the ability to plot DCA/VCA assignments"""

    Name = 'DCA/VCA Plotter'
    Authors = ('s0600204',)
    Depends = ('Midi', 'MidiFixtureControl')
    Description = 'Provides the ability to plot DCA/VCA assignments'

    _mapper_enabled = False
    _mapping_menu_action = None
    _mapping_model = None
    _tracking_model = None

    def __init__(self, app):
        super().__init__(app)

        # Register the settings widget
        AppConfigurationDialog.registerSettingsPage(
            'plugins.dca_plotter', DcaPlotterSettings, DcaPlotter.Config)

        # Register the session-level mic assign ui
        SessionConfigurationDialog.registerSettingsPage(
            'mic_assign', DcaPlotterMicAssignUi, self)

        # Register our cue types
        app.register_cue_type(DcaChangeCue, translate("CueCategory", "DCA/VCA Manipulation"))

        # Register a listener for when a session has been created.
        Application().session_created.connect(self._on_session_init)

    def _open_mapper_dialog(self):
        if self._mapper_enabled:
            dca_mapper = DcaMappingDialog()
            dca_mapper.exec_()

    def _on_session_init(self):
        """Post-session-creation init"""

        # Create the session's dca-tracking model
        # This model does not contain cues.
        # Instead it tracks which mics are muted and are currently assigned where
        self._tracking_model = DcaTrackingModel()

        layout = Application().layout
        self._mapper_enabled = isinstance(layout, ListLayout)
        if not self._mapper_enabled:
            if self._mapping_menu_action:
                self.app.window.menuTools.removeAction(self._mapping_menu_action)
            self._mapping_menu_action = None
            self._mapping_model = None
            return

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

    def _on_cue_selected(self, prev, curr):
        """Action to take when a cue is selected.

        This function only gets called if the session is in the "List" layout.
        With the "Cart" layout, selecting a cue calls the cue, and there are no other layouts currently.
        """
        # prev and curr are both of type
        # -> lisp.plugins.list_layout.list_view.CueTreeWidgetItem
        pass

    def _on_cue_added(self, cue):
        """Action to take when a cue is added to the List Layout."""
        if isinstance(cue, DcaChangeCue):
            self._mapping_model.append_cuerow(cue)

    def _on_cue_moved(self, old_index, new_index):
        """Action to take when a cue is moved in the List Layout."""
        cue = Application().layout._list_model.item(new_index)
        if isinstance(cue, DcaChangeCue):
            self._mapping_model.move_cuerow(cue, new_index)

    def _on_cue_removed(self, cue):
        """Action to take when a cue is removed from the List Layout."""
        if isinstance(cue, DcaChangeCue):
            self._mapping_model.remove_cuerow(cue)

    def get_microphone_count(self):
        count = len(self.SessionConfig['inputs'])
        return count if count > 0 else self.Config['input_channel_count']

    def mapper_enabled(self):
        return self._mapper_enabled

    def mapper(self):
        return self._mapping_model

    def tracker(self):
        return self._tracking_model
