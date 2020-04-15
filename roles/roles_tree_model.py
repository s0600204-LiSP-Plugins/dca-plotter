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
from PyQt5.QtCore import Qt, QAbstractItemModel, QModelIndex
from PyQt5.QtGui import QFont

# pylint: disable=import-error
from lisp.ui.ui_utils import translate

class BaseRow:
    def __init__(self, parent=None):
        self.parent = parent

    def data(self, col, role):
        # pylint: disable=missing-docstring, no-self-use, unused-argument
        return None

    def flags(self, col):
        # pylint: disable=missing-docstring, no-self-use, unused-argument
        return Qt.NoItemFlags

    def model(self):
        # pylint: disable=missing-docstring
        return self.parent.model()

    def rowNum(self):
        # pylint: disable=invalid-name, missing-docstring
        if not self.parent:
            return -1
        return self.parent.rows.index(self)


class ParentRow(BaseRow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rows = []

    def addChild(self, child):
        # pylint: disable=invalid-name, missing-docstring
        self.rows.append(child)

    def child(self, child_num):
        # pylint: disable=missing-docstring
        return self.rows[child_num]

    def childCount(self):
        # pylint: disable=invalid-name, missing-docstring
        return len(self.rows)

    def removeChild(self, child):
        # pylint: disable=invalid-name, missing-docstring
        return self.rows.pop(child)


class RootRow(ParentRow):
    def __init__(self, model, **kwargs):
        super().__init__(**kwargs)
        self._model = model

    def model(self):
        # pylint: disable=missing-docstring
        return self._model


class RoleRow(ParentRow):
    def __init__(self, role_id, name, **kwargs):
        super().__init__(**kwargs)
        self._role_id = role_id
        self._name = name

    def data(self, col, role=Qt.DisplayRole):
        # pylint: disable=missing-docstring
        if col == 0:
            if role in (Qt.DisplayRole, Qt.EditRole):
                return self._name

            if role == Qt.FontRole:
                font = QFont()
                font.setWeight(QFont.Bold)
                return font

        if col == 1 and role == Qt.EditRole:
            return -1

        return super().data(col, role)

    def flags(self, col):
        # pylint: disable=missing-docstring
        if col == 0:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable
        if col == 1:
            return Qt.ItemIsEnabled
        return super().flags(col)

    def setData(self, col, data, role):
        # pylint: disable=invalid-name, missing-docstring
        if col == 0 and role == Qt.EditRole:
            self._name = data


class AssignRow(BaseRow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._assign = None
        self._is_default = False

    def data(self, col, role=Qt.DisplayRole):
        # pylint: disable=missing-docstring
        if col == 0 and role == Qt.DisplayRole:
            return "Hey!"

        if col == 1 and role == Qt.CheckStateRole:
            return Qt.Checked if self._is_default else Qt.Unchecked

        return super().data(col, role)

    def flags(self, col):
        # pylint: disable=missing-docstring
        flags = Qt.ItemNeverHasChildren | Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if col == 0:
            return flags
        if col == 1:
            return flags | Qt.ItemIsEditable | Qt.ItemIsUserCheckable
        return super().flags(col)

    def setData(self, col, data, role):
        # pylint: disable=invalid-name, missing-docstring
        pass


class RolesTreeModel(QAbstractItemModel):
    def __init__(self):
        super().__init__()
        self.root = RootRow(self)
        self.role_count = 0
        self.columns = [{
            'id': 'role_name',
            'label': translate('DcaPlotterSettings', 'Role Name & Assignments'),
        }, {
            'id': 'default_indicator',
            'label': translate('DcaPlotterSettings', 'Default'),
        }]

    def addRole(self, name):
        # pylint: disable=invalid-name, missing-docstring
        uid = 'role#{0}'.format(self.role_count)
        new_role = RoleRow(uid, name, parent=self.root)
        row = self.root.childCount()

        self.beginInsertRows(QModelIndex(), row, row)
        self.root.addChild(new_role)
        self.endInsertRows()

        self.role_count += 1

    def columnCount(self, _):
        # pylint: disable=invalid-name, missing-docstring
        return len(self.columns)

    def data(self, index, role=Qt.DisplayRole):
        # pylint: disable=missing-docstring, no-self-use
        if not index.isValid():
            return None
        return index.internalPointer().data(index.column(), role)

    def flags(self, index):
        # pylint: disable=missing-docstring, no-self-use
        if not index.isValid():
            return Qt.NoItemFlags
        return index.internalPointer().flags(index.column())

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        # pylint: disable=invalid-name, missing-docstring
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.columns[section]['label']

        return None

    def index(self, row_num, col_num, parent_idx):
        # pylint: disable=missing-docstring
        if not self.hasIndex(row_num, col_num, parent_idx):
            return QModelIndex()

        parent_node = parent_idx.internalPointer() if parent_idx.isValid() else self.root
        child_node = parent_node.child(row_num)

        if child_node:
            return self.createIndex(row_num, col_num, child_node)
        return QModelIndex()

    def parent(self, index):
        # pylint: disable=missing-docstring
        if not index.isValid():
            return QModelIndex()

        parent = index.internalPointer().parent
        if parent == self.root:
            return QModelIndex()

        return self.createIndex(parent.rowNum(), 0, parent)

    def remRole(self, index):
        # pylint: disable=invalid-name, missing-docstring
        row = index.internalPointer().rowNum()
        self.beginRemoveRows(QModelIndex(), row, row)
        self.root.removeChild(row)
        self.endRemoveRows()

    def rowCount(self, index):
        # pylint: disable=invalid-name, missing-docstring
        node = index.internalPointer() if index.isValid() else self.root
        return node.childCount()

    def setData(self, index, data, role=Qt.DisplayRole):
        # pylint: disable=invalid-name, missing-docstring, no-self-use
        if not index.isValid():
            return
        index.internalPointer().setData(index.column(), data, role)
