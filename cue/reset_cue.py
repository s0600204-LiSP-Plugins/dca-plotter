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

# pylint: disable=missing-docstring, invalid-name, too-few-public-methods

# pylint: disable=no-name-in-module
from PyQt5.QtCore import QT_TRANSLATE_NOOP
from PyQt5.QtWidgets import QFormLayout, QLabel, QLineEdit

# pylint: disable=import-error
from lisp.core.has_properties import Property
from lisp.ui.settings.cue_settings import CueSettingsRegistry
from lisp.ui.settings.pages import SettingsPage

# pylint: disable=relative-beyond-top-level
from .dca_cue import DcaCue

class DcaResetCue(DcaCue):
    Name = QT_TRANSLATE_NOOP('CueName', 'DCA/VCA Reset Cue')

    new_dca_name = Property('-')

class DcaResetCueSettings(SettingsPage):
    Name = QT_TRANSLATE_NOOP('SettingsPageName', 'DCA/VCA Reset Settings')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setLayout(QFormLayout())

        self.textLabel = QLabel(self)
        self.textLabel.setText('Set DCA Names to:')
        self.textInput = QLineEdit(self)
        self.layout().addRow(self.textLabel, self.textInput)

    def getSettings(self):
        return {'new_dca_name': self.textInput.text()}

    def loadSettings(self, settings):
        self.textInput.setText(settings.get('new_dca_name', '-'))

CueSettingsRegistry().add(DcaResetCueSettings, DcaResetCue)
