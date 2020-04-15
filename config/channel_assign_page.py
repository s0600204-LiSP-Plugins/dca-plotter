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

# pylint: disable=missing-docstring, invalid-name

# pylint: disable=no-name-in-module
from PyQt5.QtWidgets import QFormLayout, QSpinBox, QVBoxLayout, QWidget

# pylint: disable=import-error
from lisp.plugins import get_plugin
from lisp.ui.qmodels import SimpleTableModel
from lisp.ui.settings.pages import SettingsPage

from midi_fixture_control.ui import SimpleTableView

from ..utilities import build_default_channel_name

class AssignUi(SettingsPage):
    '''Assign UI'''

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setLayout(QVBoxLayout())

        # Options at top
        self.optionsGroup = QWidget(self)
        self.optionsGroup.setLayout(QFormLayout())
        self.layout().addWidget(self.optionsGroup)

        self.entryCount = QSpinBox(self)
        self.entryCount.setRange(1, self.EntryLimit['num'])
        self.entryCount.editingFinished.connect(self._entryCount_editingFinished)
        self.optionsGroup.layout().addRow(self.EntryLimit['caption'], self.entryCount)

        # Table
        model = SimpleTableModel(self.TableHeadings)
        self.entryList = SimpleTableView(model, self.TableColumns, parent=self)
        self.layout().addWidget(self.entryList)

    def getSettings(self):
        model = self.entryList.model()
        conf = {}
        for row_idx in range(model.rowCount()):
            conf.setdefault(self.SessionConfigKey, []).append({
                'name': model.data(model.createIndex(row_idx, 2)),
                'in': model.data(model.createIndex(row_idx, 1))
            })
        return conf

    def loadSettings(self, settings):
        plugin_config = get_plugin('DcaPlotter').Config

        if self.SessionConfigKey in settings and settings[self.SessionConfigKey]:
            self.entryCount.setValue(len(settings[self.SessionConfigKey]))
            for row_idx, row in enumerate(settings[self.SessionConfigKey]):
                self.entryList.model().appendRow(row_idx + 1, row['in'], row['name'])
        else:
            self.entryCount.setValue(plugin_config[self.EntryLimit['key']])
            self.entryCount.editingFinished.emit()

    def _entryCount_editingFinished(self):
        entryCount = self.entryList.model().rowCount()
        value = self.entryCount.value()
        while entryCount is not value:
            if entryCount < value:
                num = entryCount + 1
                self.entryList.model().appendRow(num, num, build_default_channel_name((self.SessionConfigKey, num)))
            else:
                self.entryList.model().removeRow(entryCount - 1)
            entryCount = self.entryList.model().rowCount()
