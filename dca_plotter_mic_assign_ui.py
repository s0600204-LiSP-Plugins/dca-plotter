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

# pylint: disable=no-name-in-module
from PyQt5.QtWidgets import QFormLayout, QGroupBox, QSpinBox, QVBoxLayout, QWidget

from lisp.plugins import get_plugin
from lisp.plugins.dca_plotter.utilities import build_default_mic_name
from lisp.ui.qdelegates import LabelDelegate, LineEditDelegate, SpinBoxDelegate
from lisp.ui.qviews import SimpleTableView
from lisp.ui.qmodels import SimpleTableModel
from lisp.ui.settings.pages import ConfigurationPage
from lisp.ui.ui_utils import translate

class DcaPlotterMicAssignUi(ConfigurationPage):
    '''Mic Assign UI'''
    Name = "Mic Assignments"

    def __init__(self, config, **kwargs):
        super().__init__(config, **kwargs)
        self.setLayout(QVBoxLayout())

        self.widgetGroup = QGroupBox(self)
        self.widgetGroup.setTitle(translate("DcaPlotter", "Mic Assignments"))
        self.widgetGroup.setLayout(QVBoxLayout())
        self.layout().addWidget(self.widgetGroup)

        # Options at top
        self.optionsGroup = QWidget(self)
        self.optionsGroup.setLayout(QFormLayout())
        self.widgetGroup.layout().addWidget(self.optionsGroup)

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
        self.widgetGroup.layout().addWidget(self.inputList)

        self.loadConfiguration()

    def applySettings(self):
        model = self.inputList.model()
        self.config['inputs'] = []
        for row_idx in range(model.rowCount()):
            self.config['inputs'].append({
                'name': model.data(model.createIndex(row_idx, 2)),
                'in': model.data(model.createIndex(row_idx, 1))
            })
        get_plugin('DcaPlotter').WriteSessionConfig(self.config)

    def loadConfiguration(self):
        plugin_config = get_plugin('DcaPlotter').Config

        if 'inputs' in self.config and len(self.config['inputs']):
            self.inputCount.setValue(len(self.config['inputs']))
            for row_idx, row in enumerate(self.config['inputs']):
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
