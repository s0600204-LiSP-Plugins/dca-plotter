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

from PyQt5.QtWidgets import QVBoxLayout, QFormLayout, QSpinBox, QGroupBox

from lisp.ui.settings.pages import SettingsPage
from lisp.ui.ui_utils import translate

class DcaPlotterSettings(SettingsPage):
    Name = "DCA Plotter"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setLayout(QVBoxLayout())

        self.settingsGroup = QGroupBox(self)
        self.settingsGroup.setTitle("Plotter Defaults")
        self.settingsGroup.setLayout(QFormLayout())
        self.layout().addWidget(self.settingsGroup)

        self.inputCount = QSpinBox(self.settingsGroup)
        self.inputCount.setRange(1, 96)
        self.settingsGroup.layout().addRow('Default Microphone Count', self.inputCount)

    def getSettings(self):
        return {
            'input_channel_count': self.inputCount.value()
        }

    def loadSettings(self, settings):
        self.inputCount.setValue(settings['input_channel_count'])
