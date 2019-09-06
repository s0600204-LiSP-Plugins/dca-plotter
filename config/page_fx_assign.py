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

from ..utilities import build_default_fx_name

class FxAssignUi(SettingsPage):
    '''FX Unit Assign UI'''
    Name = translate("DcaPlotter", "Effects Assignments")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setLayout(QVBoxLayout())

        # Options at top
        self.optionsGroup = QWidget(self)
        self.optionsGroup.setLayout(QFormLayout())
        self.layout().layout().addWidget(self.optionsGroup)

        self.fxCount = QSpinBox(self)
        self.fxCount.setRange(1, 16)
        self.fxCount.editingFinished.connect(self._inputCount_editingFinished)
        self.optionsGroup.layout().addRow('# of Effects Units', self.fxCount)

        # Table of fx units
        model = SimpleTableModel([
            translate('DcaPlotterSettings', 'Effect #'),
            translate('DcaPlotterSettings', 'FX Return #'),
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
        self.fxList = SimpleTableView(model, columns, parent=self)
        self.layout().layout().addWidget(self.fxList)

    def getSettings(self):
        model = self.fxList.model()
        conf = {}
        for row_idx in range(model.rowCount()):
            conf.setdefault('fx', []).append({
                'name': model.data(model.createIndex(row_idx, 2)),
                'in': model.data(model.createIndex(row_idx, 1))
            })
        return conf

    def loadSettings(self, settings):
        plugin_config = get_plugin('DcaPlotter').Config

        if 'fx' in settings and settings['fx']:
            self.fxCount.setValue(len(settings['fx']))
            for row_idx, row in enumerate(settings['fx']):
                self.fxList.model().appendRow(row_idx + 1, row['in'], row['name'])
        else:
            self.fxCount.setValue(plugin_config['fx_channel_count'])
            self.fxCount.editingFinished.emit()

    def _inputCount_editingFinished(self):
        fxCount = self.fxList.model().rowCount()
        value = self.fxCount.value()
        while fxCount is not value:
            if fxCount < value:
                num = fxCount + 1
                self.fxList.model().appendRow(num, num, build_default_fx_name(num))
            else:
                self.fxList.model().removeRow(fxCount - 1)
            fxCount = self.fxList.model().rowCount()
