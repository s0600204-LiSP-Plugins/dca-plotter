# This file is a derivation of work on - and as such shares the same
# licence as - Linux Show Player
#
# Linux Show Player:
#   Copyright 2012-2021 Francesco Ceruti <ceppofrancy@gmail.com>
#
# This file:
#   Copyright 2021 s0600204
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
from PyQt5.QtCore import QAbstractItemModel, QModelIndex, Qt

from lisp.core.signal import Signal

from ..utilities import get_channel_name

# Index: (x, y), where
#     x (rows)    = Role
#     y (columns) = y0     = Role Name
#                 = y{n>0} = Assigns to that Role

class RolesSwitcherModel(QAbstractItemModel):

    dataRenewed = Signal()
    roleUpdated = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._roles = {}
        self._roles_map = []

    def columnCount(self, index):
        # pylint: disable=invalid-name, missing-docstring
        if not index.isValid():
            return 0
        idx = self._roles_map[index.row()]
        return len(self._roles[idx]['assigns'])

    def current(self, role_id):
        if role_id in self._roles:
            return self._roles[role_id]['current']
        return None

    def data(self, index, role=Qt.DisplayRole):
        # pylint: disable=missing-docstring, no-self-use
        if not index.isValid():
            return None

        idx = self._roles_map[index.row()]
        role_data = self._roles[idx]
        if index.column() == 0:
            if role == Qt.DisplayRole:
                return role_data['name']
            return None

        assign_num = index.column() - 1
        if role == Qt.DisplayRole:
            return get_channel_name(role_data['assigns'][assign_num])

        if role == Qt.CheckStateRole:
            return Qt.Checked if role_data['assigns'][assign_num] == role_data['current'] else Qt.Unchecked

        return None

    def renew(self, plugin_config):
        if 'role' not in plugin_config['assigns']:
            self._roles = {}
            self._roles_map = []
            self.dataRenewed.emit()
            return

        new_roles = {}
        for role_id, role in plugin_config['assigns']['role'].items():
            new_dict = {
                'name': role['name'],
                'current': tuple(role['default']),
                'assigns': [tuple(assign) for assign in role['assigns']],
            }

            # Retain the old "current"(ly) selected option
            if role_id in self._roles:
                old_current = self._roles[role_id]['current']
                if old_current in role['assigns']:
                    new_dict['current'] = old_current

            new_roles[role_id] = new_dict

        self._roles = new_roles
        self._roles_map = list(new_roles.keys())
        self.dataRenewed.emit()

    def flags(self, index):
        # pylint: disable=missing-docstring, no-self-use
        if not index.isValid():
            return Qt.NoItemFlags

        base_flags = Qt.ItemIsEnabled | Qt.ItemNeverHasChildren

        # Role Name
        if index.column() == 0:
            return base_flags

        # Role Assignment buttons
        return base_flags | Qt.ItemIsEditable | Qt.ItemIsUserCheckable

    def index(self, row, col):
        # pylint: disable=missing-docstring
        if row < 0 or row >= len(self._roles) or col < 0:
            return QModelIndex()

        idx = self._roles_map[row]
        if col > len(self._roles[idx]['assigns']):
            return QModelIndex()

        return self.createIndex(row, col)

    def parent(self, index):
        # pylint: disable=missing-docstring
        if not index.isValid():
            return QModelIndex()

        col = index.column()
        if col == 0:
            return QModelIndex()

        return self.index(index.column(), 0)

    def rowCount(self, index):
        # pylint: disable=invalid-name, missing-docstring
        if not index.isValid():
            return 0
        return len(self._roles)

    def setData(self, index, data, role=Qt.DisplayRole):
        # pylint: disable=invalid-name, missing-docstring, no-self-use
        if not index.isValid() or role != Qt.CheckStateRole or data != Qt.Checked:
            return False

        row = index.row()
        col = index.column()
        if row >= self.rowCount(index) or col > self.columnCount(index) or col < 1:
            return False

        idx = self._roles_map[row]
        former_current = self._roles[idx]['current']
        self._roles[idx]['current'] = self._roles[idx]['assigns'][col - 1]

        self.roleUpdated.emit(idx, former_current, self._roles[idx]['current'])
        self.dataChanged.emit(
            self.createIndex(row, 1),
            self.createIndex(row, self.columnCount(index)),
            [Qt.CheckStateRole])
        return True
