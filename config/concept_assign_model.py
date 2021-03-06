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
from PyQt5.QtCore import Qt, QAbstractItemModel, QModelIndex
from PyQt5.QtGui import QFont

# pylint: disable=import-error
from lisp.plugins import get_plugin

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


class GroupRow(ParentRow):
    def __init__(self, group_id, name, **kwargs):
        super().__init__(**kwargs)
        self._group_id = group_id
        self._name = name

    def data(self, col, role=Qt.DisplayRole):
        # pylint: disable=missing-docstring
        if col == -1 and role == ConceptTreeModel.AccessRole:
            return self._group_id

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
            return True
        return False


class ConceptTreeModel(QAbstractItemModel):

    AccessRole = Qt.UserRole + 1

    def __init__(self, group_id_pattern, columns, AssignRowClass, assign_categories, allow_multi):
        super().__init__()
        self._allow_multi_assign = allow_multi
        self._AssignRowClass = AssignRowClass
        self._assignable_categories = assign_categories
        self._columns = columns
        self._group_count = 0
        self._group_id_pattern = group_id_pattern
        self._root = RootRow(self)

    def addAssign(self, group_index, channel_tuple):
        group_row = group_index.internalPointer()

        new_assign = self._AssignRowClass(channel_tuple, parent=group_row)
        position = group_row.childCount()

        self.beginInsertRows(group_index, position, position)
        self._root.child(group_index.row()).addChild(new_assign)
        self.endInsertRows()

    def addGroup(self, name):
        # pylint: disable=invalid-name, missing-docstring
        uid = self._group_id_pattern.format(self._group_count)
        new_group = GroupRow(uid, name, parent=self._root)
        row = self._root.childCount()

        self.beginInsertRows(QModelIndex(), row, row)
        self._root.addChild(new_group)
        self.endInsertRows()

        self._group_count += 1
        return self.createIndex(row, 0, new_group)

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

    def get_assignable_selection_choice(self, group_index):
        if not group_index.isValid():
            return []

        group_row = group_index.internalPointer()
        if group_row.parent() != self._root:
            return []

        assignables = get_plugin('DcaPlotter').assignables(self._assignable_categories)

        if self._allow_multi_assign:
            for child in group_row.children():
                ch_tuple = child.data(-1, self.AccessRole)
                if ch_tuple in assignables:
                    assignables.remove(ch_tuple)
        else:
            for group in self._root.children():
                for child in group.children():
                    ch_tuple = child.data(-1, self.AccessRole)
                    if ch_tuple in assignables:
                        assignables.remove(ch_tuple)

        return assignables

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
            return False
        return index.internalPointer().setData(index.column(), data, role)
