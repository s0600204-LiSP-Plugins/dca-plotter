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
from PyQt5.QtWidgets import QFormLayout, QHBoxLayout, QTreeView, QHeaderView

from lisp.core.has_properties import Property
from lisp.cues.cue import Cue
from lisp.plugins import get_plugin
from lisp.ui.settings.cue_settings import CueSettingsRegistry
from lisp.ui.settings.pages import SettingsPage
from lisp.ui.ui_utils import translate

from lisp.plugins.dca_plotter.dca_plotter_models import DcaBlockModel

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
        self.setLayout(QHBoxLayout())

        self.blockModel = DcaBlockModel()
        self.blockView = DcaBlockView(self.blockModel)
        self.layout().addWidget(self.blockView)

    def getSettings(self):
        return {'dca_change': {}}

    def loadSettings(self, settings):
        conf = settings.get('dca_change', {})

class DcaBlockView(QTreeView):

    def __init__(self, model, **kwargs):
        super().__init__(**kwargs)

        # Setup and hide the header
        self.setHeaderHidden(True)
        self.header().setSectionResizeMode(QHeaderView.Fixed)
        self.header().setStretchLastSection(False)

        # Hide decorations and prevent expansions
        self.setItemsExpandable(False)
        self.setRootIsDecorated(False)

        # Set Model
        self.setModel(model)

        # Show all (can only be done after setting the model)
        self.expandAll()

        # Set width/stretch (can only be done after setting the model)
        self.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.header().resizeSection(1, 32)

CueSettingsRegistry().add(DcaChangeCueSettings, DcaChangeCue)
