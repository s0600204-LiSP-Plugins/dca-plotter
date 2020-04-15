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
from lisp.plugins import get_plugin
from lisp.ui.ui_utils import translate

from ..utilities import get_channel_assignment_name

class BaseRow:
    def __init__(self, parent=None):
        self._parent = parent

    def data(self, col, role):
        # pylint: disable=missing-docstring, no-self-use, unused-argument
        return None

    def flags(self, col):
        # pylint: disable=missing-docstring, no-self-use, unused-argument
        return Qt.NoItemFlags

    def model(self):
        # pylint: disable=missing-docstring
        return self._parent.model()

    def parent(self):
        return self._parent

    def rowNum(self):
        # pylint: disable=invalid-name, missing-docstring
        if not self._parent:
            return -1
        return self._parent.children().index(self)


class ParentRow(BaseRow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._rows = []

    def addChild(self, child):
        # pylint: disable=invalid-name, missing-docstring
        self._rows.append(child)

    def child(self, child_num):
        # pylint: disable=missing-docstring
        return self._rows[child_num]

    def childCount(self):
        # pylint: disable=invalid-name, missing-docstring
        return len(self._rows)

    def children(self):
        return self._rows

    def removeChild(self, child):
        # pylint: disable=invalid-name, missing-docstring
        return self._rows.pop(child)


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

    def removeChild(self, child):
        child = super().removeChild(child)
        if child.data(1, Qt.CheckStateRole) == Qt.Checked and self.childCount():
            self.child(0).setData(1, Qt.Checked, Qt.CheckStateRole)

    def setData(self, col, data, role):
        # pylint: disable=invalid-name, missing-docstring
        if col == 0 and role == Qt.EditRole:
            self._name = data


class AssignRow(BaseRow):
    def __init__(self, channel_tuple, **kwargs):
        super().__init__(**kwargs)
        self._channel = channel_tuple
        self._is_default = self._parent.childCount() == 0

    def data(self, col, role=Qt.DisplayRole):
        # pylint: disable=missing-docstring
        if col == 0 and role == Qt.DisplayRole:
            return get_channel_assignment_name(self._channel)

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
        if col == 1 and role == Qt.CheckStateRole:
            self._is_default = data == Qt.Checked
            if data == Qt.Unchecked:
                return

            for sibling in self._parent.children():
                if sibling == self:
                    continue
                sibling.setData(col, Qt.Unchecked, role)

            model = self._parent.model()
            model.dataChanged.emit(
                model.createIndex(0, 1, self),
                model.createIndex(self._parent.childCount(), 1, self),
                [Qt.CheckStateRole])

    def value(self):
        return (self._channel, self._is_default)


class RolesTreeModel(QAbstractItemModel):
    def __init__(self):
        super().__init__()
        self._root = RootRow(self)
        self._role_count = 0
        self._columns = [{
            'id': 'role_name',
            'label': translate('DcaPlotterSettings', 'Role Name & Assignments'),
        }, {
            'id': 'default_indicator',
            'label': translate('DcaPlotterSettings', 'Default'),
        }]

    def addAssign(self, role_index, channel_tuple):
        role_row = role_index.internalPointer()

        new_assign = AssignRow(channel_tuple, parent=role_row)
        position = role_row.childCount()

        self.beginInsertRows(role_index, position, position)
        self._root.child(role_index.row()).addChild(new_assign)
        self.endInsertRows()

    def addRole(self, name):
        # pylint: disable=invalid-name, missing-docstring
        uid = 'role#{0}'.format(self._role_count)
        new_role = RoleRow(uid, name, parent=self._root)
        row = self._root.childCount()

        self.beginInsertRows(QModelIndex(), row, row)
        self._root.addChild(new_role)
        self.endInsertRows()

        self._role_count += 1
        return self.createIndex(row, 0, new_role)

    def columnCount(self, _):
        # pylint: disable=invalid-name, missing-docstring
        return len(self._columns)

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

    def get_assignable_selection_choice(self, role_index):
        channel_tuples = []
        if not role_index.isValid():
            return channel_tuples

        role_row = role_index.internalPointer()
        if role_row.parent() != self._root:
            return channel_tuples

        already_assigned = []
        for child in role_row.children():
            already_assigned.append(child.value()[0])

        for assignable, count in get_plugin('DcaPlotter').get_assignable_count().items():
            for num in range(count):
                new_tuple = (assignable, num + 1)
                if new_tuple not in already_assigned:
                    channel_tuples.append(new_tuple)

        return channel_tuples

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        # pylint: disable=invalid-name, missing-docstring
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self._columns[section]['label']

        return None

    def index(self, row_num, col_num, parent_idx):
        # pylint: disable=missing-docstring
        if not self.hasIndex(row_num, col_num, parent_idx):
            return QModelIndex()

        parent_node = parent_idx.internalPointer() if parent_idx.isValid() else self._root
        child_node = parent_node.child(row_num)

        if child_node:
            return self.createIndex(row_num, col_num, child_node)
        return QModelIndex()

    def parent(self, index):
        # pylint: disable=missing-docstring
        if not index.isValid():
            return QModelIndex()

        parent = index.internalPointer().parent()
        if parent == self._root:
            return QModelIndex()

        return self.createIndex(parent.rowNum(), 0, parent)

    def removeRow(self, index):
        # pylint: disable=invalid-name, missing-docstring
        if not index.isValid():
            return

        parent = index.internalPointer().parent()
        parent_index = self.parent(index)
        if parent != self._root and not parent_index.isValid():
            return

        row_num = index.internalPointer().rowNum()
        self.beginRemoveRows(parent_index, row_num, row_num)
        if parent == self._root:
            self._root.removeChild(row_num)
        else:
            parent.removeChild(row_num)
        self.endRemoveRows()

    def root(self):
        return self._root

    def rowCount(self, index):
        # pylint: disable=invalid-name, missing-docstring
        node = index.internalPointer() if index.isValid() else self._root
        return node.childCount()

    def setData(self, index, data, role=Qt.DisplayRole):
        # pylint: disable=invalid-name, missing-docstring, no-self-use
        if not index.isValid():
            return
        index.internalPointer().setData(index.column(), data, role)
