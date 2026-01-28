# This file is a derivation of work on - and as such shares the same
# licence as - Linux Show Player
#
# Linux Show Player:
#   Copyright 2012-2026 Francesco Ceruti <ceppofrancy@gmail.com>
#
# This file:
#   Copyright 2026 s0600204
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

from PyQt5.QtWidgets import (
        QFormLayout,
        QGroupBox,
        QLineEdit,
        QSpinBox,
        QVBoxLayout,
)

# pylint: disable=import-error
from lisp.ui.settings.pages import SettingsPage


class DcaPlotterSettings(SettingsPage):
    Name = "DCA Plotter"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setLayout(QVBoxLayout())

        self.settings_group = QGroupBox(self)
        self.settings_group.setTitle("Plotter Defaults")
        self.settings_group.setLayout(QFormLayout())
        self.layout().addWidget(self.settings_group)

        self.input_spinner = QSpinBox(self.settings_group)
        self.input_spinner.setRange(1, 96)
        self.settings_group.layout().addRow('Default Microphone Count', self.input_spinner)

        self.fx_spinner = QSpinBox(self.settings_group)
        self.fx_spinner.setRange(1, 16)
        self.settings_group.layout().addRow('Default Effects Unit Count', self.fx_spinner)

        self.blanking_text = QLineEdit(self)
        self.settings_group.layout().addRow('Set name of empty DCAs to', self.blanking_text)

    def getSettings(self):
        return {
            'input_channel_count': self.input_spinner.value(),
            'fx_channel_count': self.fx_spinner.value(),
            'blanking_text': self.blanking_text.text(),
        }

    def loadSettings(self, settings):
        self.input_spinner.setValue(settings['input_channel_count'])
        self.fx_spinner.setValue(settings['fx_channel_count'])
        self.blanking_text.setText(settings['blanking_text'])
