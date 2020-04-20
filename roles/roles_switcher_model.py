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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._roles = []

    def columnCount(self, index):
        # pylint: disable=invalid-name, missing-docstring
        if not index.isValid():
            return 0
        return len(self._roles[index.row()]['assigns'])

    def current(self, role_id):
        for role in self._roles:
            if role['id'] == role_id:
                return role['current']
        return None

    def data(self, index, role=Qt.DisplayRole):
        # pylint: disable=missing-docstring, no-self-use
        if not index.isValid():
            return None

        role_num = index.row()
        role_data = self._roles[role_num]
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
            return

        new_roles = []
        current_role_ids = {role['id']: idx for idx, role in enumerate(self._roles)}

        for role in plugin_config['assigns']['role']:
            new_role = {
                'id': role['id'],
                'name': role['name'],
                'current': role['default'],
                'assigns': role['assigns']
            }

            # Retain the old "current"(ly) selected option
            if role['id'] in current_role_ids:
                old_current = self._roles[current_role_ids[new_role['id']]]['current']
                if old_current in role['assigns']:
                    new_role['current'] = old_current

            new_roles.append(new_role)

        self._roles = new_roles
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
        if row < 0 or row >= len(self._roles) or col < 0 or col > len(self._roles[row]['assigns']):
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

        self._roles[row]['current'] = self._roles[row]['assigns'][col - 1]
        self.dataChanged.emit(
            self.createIndex(row, 1),
            self.createIndex(row, self.columnCount(index)),
            [Qt.CheckStateRole])
        return True
