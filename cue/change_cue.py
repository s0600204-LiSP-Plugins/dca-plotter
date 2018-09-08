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
from PyQt5.QtWidgets import QHBoxLayout, QTreeView, QHeaderView, QScrollArea, QWidget

from lisp.core.has_properties import Property
from lisp.cues.cue import Cue
from lisp.plugins import get_plugin
from lisp.ui.settings.cue_settings import CueSettingsRegistry
from lisp.ui.settings.pages import SettingsPage
from lisp.ui.ui_utils import translate

from lisp.plugins.dca_plotter.dca_plotter_input_select_dialog import InputSelectDialog
from lisp.plugins.dca_plotter.dca_plotter_models import DcaBlockModel, DcaBlockActionDelegate

class DcaChangeCue(Cue):
    Name = QT_TRANSLATE_NOOP('CueName', 'DCA/VCA Change Cue')

    dca_changes = Property([])
    dca_names = Property([])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = translate('CueName', self.Name)
        dca_count = get_plugin('DcaPlotter').SessionConfig['dca_count']

    def __start__(self, fade=False):
        get_plugin('DcaPlotter').tracker.call_cue(self.dca_changes)
        return False

class DcaChangeCueSettings(SettingsPage):
    Name = QT_TRANSLATE_NOOP('SettingsPageName', 'DCA/VCA Change Settings')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dca_count = get_plugin('DcaPlotter').SessionConfig['dca_count']
        self.dca_blocks = []
        self.inputSelectDialog = InputSelectDialog(parent=self)

        self.setLayout(QHBoxLayout())

        self.innerWidget = QWidget(self)
        self.innerWidget.setLayout(QHBoxLayout())

        for bl in range(self.dca_count):
            m = DcaBlockModel(self.inputSelectDialog)
            v = DcaBlockView(m)
            # These two next lines shouldn't be needed
            # However, I can't seem to determine the correct sizePolicy/sizeHint/whatevers needed to make it scale correctly,
            # so after an hour+ spent on it, this is what you're getting(!)
            # (Until I rewrite this all, of course.)
            v.setMaximumWidth(210)
            v.setMinimumHeight(350)
            self.dca_blocks.append({ 'm': m, 'v': v })
            self.innerWidget.layout().addWidget(v)
        
        self.scrollArea = QScrollArea(self)
        self.scrollArea.setWidget(self.innerWidget)
        self.layout().addWidget(self.scrollArea)

    def getSettings(self):
        assigns = []
        for a in range(self.dca_count):
            assigns.append(self.dca_blocks[a]['m'].serialise())
        return {'dca_changes': assigns}

    def loadSettings(self, settings):
        plotter_plugin = get_plugin('DcaPlotter')
        if plotter_plugin.mapper_enabled():
            cuerow = plotter_plugin.mapper()._find_cuerow(settings['id'])

        assigns = settings.get('dca_changes', [])
        for a in range(len(assigns), self.dca_count):
            assigns.append({
                'add': [],
                'rem': []
            })

        for dca_num, entries in enumerate(assigns):
            inh = []
            if plotter_plugin.mapper_enabled():
                for entry in cuerow.child(dca_num).children:
                    if entry.inherited():
                        inh.append(entry.value())

            entries['inherit'] = inh
            self.dca_blocks[dca_num]['m'].deserialise(entries)

class DcaBlockView(QTreeView):

    _delegates = []

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

        # Set appropriate delegates for the action icon-buttons
        for col in range(1, 3):
            new_delegate = DcaBlockActionDelegate()
            self._delegates.append(new_delegate)
            self.setItemDelegateForColumn(col, new_delegate)
            self.header().resizeSection(col, 24)

        # Show all (can only be done after setting the model)
        self.expandAll()

        self.header().setSectionResizeMode(0, QHeaderView.Stretch)
        

CueSettingsRegistry().add(DcaChangeCueSettings, DcaChangeCue)
