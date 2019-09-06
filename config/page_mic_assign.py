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

# pylint: disable=missing-docstring, invalid-name

# pylint: disable=no-name-in-module
from PyQt5.QtWidgets import QFormLayout, QGroupBox, QSpinBox, QVBoxLayout, QWidget

# pylint: disable=import-error
from lisp.plugins import get_plugin
from lisp.ui.qdelegates import LineEditDelegate, SpinBoxDelegate
from lisp.ui.qmodels import SimpleTableModel
from lisp.ui.settings.pages import SettingsPage
from lisp.ui.ui_utils import translate

from midi_fixture_control.ui import LabelDelegate, SimpleTableView

from ..utilities import build_default_mic_name

class MicAssignUi(SettingsPage):
    '''Mic Assign UI'''
    Name = translate("DcaPlotter", "Microphone Assignments")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setLayout(QVBoxLayout())

        # Options at top
        self.optionsGroup = QWidget(self)
        self.optionsGroup.setLayout(QFormLayout())
        self.layout().layout().addWidget(self.optionsGroup)

        self.inputCount = QSpinBox(self)
        self.inputCount.setRange(1, 96)
        self.inputCount.editingFinished.connect(self._inputCount_editingFinished)
        self.optionsGroup.layout().addRow('# of Mics', self.inputCount)

        # Table of mics
        model = SimpleTableModel([
            translate('DcaPlotterSettings', 'Mic #'),
            translate('DcaPlotterSettings', 'Input #'),
            translate('DcaPlotterSettings', 'Name')
        ])
        columns = [{
            'delegate': LabelDelegate(),
            'width': 64
        }, {
            'delegate': SpinBoxDelegate(minimum=1, maximum=96),
            'width': 80
        }, {
            'delegate': LineEditDelegate(max_length=16)
        }]
        self.inputList = SimpleTableView(model, columns, parent=self)
        self.layout().layout().addWidget(self.inputList)

    def getSettings(self):
        model = self.inputList.model()
        conf = {}
        for row_idx in range(model.rowCount()):
            conf.setdefault('inputs', []).append({
                'name': model.data(model.createIndex(row_idx, 2)),
                'in': model.data(model.createIndex(row_idx, 1))
            })
        return conf

    def loadSettings(self, settings):
        plugin_config = get_plugin('DcaPlotter').Config

        if 'inputs' in settings and settings['inputs']:
            self.inputCount.setValue(len(settings['inputs']))
            for row_idx, row in enumerate(settings['inputs']):
                self.inputList.model().appendRow(row_idx + 1, row['in'], row['name'])
        else:
            self.inputCount.setValue(plugin_config['input_channel_count'])
            self.inputCount.editingFinished.emit()

    def _inputCount_editingFinished(self):
        inputCount = self.inputList.model().rowCount()
        value = self.inputCount.value()
        while inputCount is not value:
            if inputCount < value:
                num = inputCount + 1
                self.inputList.model().appendRow(num, num, build_default_mic_name(num))
            else:
                self.inputList.model().removeRow(inputCount - 1)
            inputCount = self.inputList.model().rowCount()