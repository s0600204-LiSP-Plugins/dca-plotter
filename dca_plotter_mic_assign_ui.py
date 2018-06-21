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
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QGridLayout, QFormLayout, QGroupBox, QSpinBox

from lisp.plugins import get_plugin
from lisp.plugins.dca_plotter.utilities import build_default_mic_name
from lisp.ui.qdelegates import LabelDelegate, LineEditDelegate, SpinBoxDelegate
from lisp.ui.qviews import SimpleTableView
from lisp.ui.qmodels import SimpleTableModel
from lisp.ui.ui_utils import translate

class DcaPlotterMicAssignUi(QDialog):
    '''Mic Assign UI'''

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle(translate('DcaPlotter', 'DCA/VCA Plotter :: Microphone Assignments'))
        self.setFixedWidth(800)
        self.setMinimumHeight(500)

        self.setLayout(QGridLayout())

        self.optionsGroup = QGroupBox(self)
        self.optionsGroup.setTitle(translate("DcaPlotter", "Options"))
        self.optionsGroup.setLayout(QFormLayout())
        self.optionsGroup.setFixedWidth(250)
        self.layout().addWidget(self.optionsGroup, 0, 0)

        self.inputCount = QSpinBox(self)
        self.inputCount.setRange(1, 96)
        self.inputCount.editingFinished.connect(self._inputCount_editingFinished)
        self.optionsGroup.layout().addRow('# of Mics', self.inputCount)

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
        self.layout().addWidget(self.inputList, 0, 1)

        self.buttons = QDialogButtonBox(self)
        self.buttons.addButton(QDialogButtonBox.Cancel)
        self.buttons.addButton(QDialogButtonBox.Ok)
        self.layout().addWidget(self.buttons, 1, 0, 1, 2)

        self.buttons.accepted.connect(self.applySettings)
        self.buttons.rejected.connect(self.reject)

        self.loadConfiguration()

    def applySettings(self):
        self.accept()

    def loadConfiguration(self):
        plugin_config = get_plugin('DcaPlotter').get_config()
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
