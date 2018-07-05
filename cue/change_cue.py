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

from PyQt5.QtCore import Qt, QT_TRANSLATE_NOOP
from PyQt5.QtWidgets import QFormLayout

from lisp.core.has_properties import Property
from lisp.cues.cue import Cue
from lisp.plugins import get_plugin
from lisp.ui.settings.cue_settings import CueSettingsRegistry
from lisp.ui.settings.pages import SettingsPage
from lisp.ui.ui_utils import translate

class DcaChangeCue(Cue):
    Name = QT_TRANSLATE_NOOP('CueName', 'DCA/VCA Change Cue')

    dca_change = Property()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = translate('CueName', self.Name)

    def __start__(self, fade=False):
        return False

class DcaChangeCueSettings(SettingsPage):
    Name = QT_TRANSLATE_NOOP('SettingsPageName', 'DCA/VCA Change Settings')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setLayout(QFormLayout())

    def getSettings(self):
        return {'dca_change': {}}

    def loadSettings(self, settings):
        conf = settings.get('dca_change', {})

CueSettingsRegistry().add(DcaChangeCueSettings, DcaChangeCue)
