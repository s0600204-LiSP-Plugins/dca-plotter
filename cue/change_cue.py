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

from PyQt5.QtCore import QT_TRANSLATE_NOOP
from PyQt5.QtWidgets import QVBoxLayout

from lisp.core.has_properties import Property
from lisp.cues.cue import Cue
from lisp.plugins import get_plugin
from lisp.ui.settings.cue_settings import CueSettingsRegistry
from lisp.ui.settings.pages import SettingsPage
from lisp.ui.ui_utils import translate

from lisp.plugins.dca_plotter.cue.model import DcaCueModel
from lisp.plugins.dca_plotter.cue.view import DcaCueView

class DcaChangeCue(Cue):
    Name = QT_TRANSLATE_NOOP('CueName', 'DCA/VCA Change Cue')

    dca_changes = Property([])
    dca_names = Property([])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = translate('CueName', self.Name)

    def __start__(self, fade=False):
        get_plugin('DcaPlotter').tracker().call_cue(self)
        return False

class DcaChangeCueSettings(SettingsPage):
    Name = QT_TRANSLATE_NOOP('SettingsPageName', 'DCA/VCA Change Settings')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setLayout(QVBoxLayout())

        self.model = DcaCueModel()
        self.view = DcaCueView()
        self.view.setModel(self.model)
        self.layout().addWidget(self.view)

    def getSettings(self):
        return {'dca_changes': self.model.serialise()}

    def loadSettings(self, settings):
        self.model.deserialise(settings.get('dca_changes', []), settings['id'])

CueSettingsRegistry().add(DcaChangeCueSettings, DcaChangeCue)
