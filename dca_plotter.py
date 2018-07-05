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

from lisp.core.plugin import Plugin
from lisp.plugins.dca_plotter.cue.change_cue import DcaChangeCue
from lisp.plugins.dca_plotter.dca_plotter_mic_assign_ui import DcaPlotterMicAssignUi
from lisp.plugins.dca_plotter.dca_plotter_settings import DcaPlotterSettings
from lisp.ui.settings.app_configuration import AppConfigurationDialog
from lisp.ui.settings.session_configuration import SessionConfigurationDialog
from lisp.ui.ui_utils import translate

class DcaPlotter(Plugin):
    """Provides the ability to plot DCA/VCA assignments"""

    Name = 'DCA/VCA Plotter'
    Authors = ('s0600204',)
    Depends = ('Midi', 'MidiFixtureControl')
    Description = 'Provides the ability to plot DCA/VCA assignments'

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
