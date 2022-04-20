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

# pylint: disable=missing-docstring, invalid-name

import enum

# pylint: disable=no-name-in-module
from PyQt5.QtCore import Qt, QAbstractItemModel, QModelIndex
from PyQt5.QtGui import QBrush, QFont
from PyQt5.QtWidgets import QApplication

# pylint: disable=import-error
from lisp.plugins import get_plugin

from .ui import BASE_TEXT_BRUSH
from .utilities import get_blank_dca_name, get_channel_assignment_name

class AssignStateEnum(enum.Enum):
    ASSIGN = enum.auto()
    UNASSIGN = enum.auto()
    NONE = enum.auto()

### ABSTRACTS
class ModelsNode():
    '''Abstract parent class'''
    def __init__(self, parent=None):
        self.parent = parent
        self._flags = Qt.ItemFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

    def data(self, role=Qt.DisplayRole):
        # pylint: disable=no-self-use, unused-argument
        return None

    def index(self):
        return self.model().createIndex(self.rownum(), 0, self)

    def flags(self):
        return self._flags

    def model(self):
        return self.parent.model()

    def next_sibling(self):
        if self.rownum() < len(self.parent) - 1:
            return self.parent.children[self.rownum() + 1]
        return None

    def prev_sibling(self):
        if self.rownum():
            return self.parent.children[self.rownum() - 1]
        return None

    def rownum(self):
        if self.parent and self in self.parent.children:
            return self.parent.children.index(self)
        return -1

    def setData(self, value, role):
        # pylint: disable=unused-argument, no-self-use
        return False

class ModelsBranchNode(ModelsNode):
    '''Branch parent class'''
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.children = []

    def addChild(self, child):
        self.children.append(child)

    def child(self, child_num):
        return self.children[child_num]

    def childCount(self):
        return len(self.children)

    def getChildValues(self):
        indexes = []
        for child in self.children:
            indexes.append(child.value())
        return indexes

    def getInsertPoint(self, new_value):
        curr_values = self.getChildValues()
        curr_values.append(new_value)
        curr_values.sort()
        return curr_values.index(new_value)

    def removeChild(self, row):
        return self.children.pop(row)

    def value(self):
        if self.rownum() > -1:
            return self.rownum()
        return self.parent.childCount()

class ModelsLeafNode(ModelsNode):
    '''Leaf parent class'''
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._flags |= Qt.ItemNeverHasChildren

    def childCount(self):
        # pylint: disable=no-self-use
        return 0

### BRANCHES
class ModelsRootNode(ModelsBranchNode):
    '''Root class'''
    def __init__(self, model, **kwargs):
        super().__init__(**kwargs)
        self._model = model

    def model(self):
        return self._model

class ModelsResetRow(ModelsBranchNode):
    '''Reset Row class.'''
    def __init__(self, cue=None, **kwargs):
        super().__init__(**kwargs)
        self.cue = cue

    def data(self, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and self.cue:
            return "{} : {}".format(self.cue.index + 1, self.cue.name)
        return super().data(role)

    def value(self):
        if self.cue:
            return self.cue.index
        return super().value()

class ModelsAssignRow(ModelsResetRow):
    '''Assign Row class.'''
    def __init__(self, cue=None, **kwargs):
        super().__init__(cue, **kwargs)

        # pylint: disable=unused-variable
        for dca in range(get_plugin('DcaPlotter').SessionConfig['dca_count']):
            self.addChild(ModelsBlock(parent=self))

class ModelsBlock(ModelsBranchNode):
    '''Block class'''
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._given_name = False
        self._inherited_name = get_blank_dca_name()

    def addChild(self, child):
        self.children.insert(self.getInsertPoint(child.value()), child)

    def data(self, role=Qt.DisplayRole):
        if role in (Qt.DisplayRole, Qt.EditRole):
            if self.model().hideEmptyDcaNames and self.functionallyEmpty():
                return get_blank_dca_name()
            return self._given_name or self._inherited_name

        if role == Qt.ForegroundRole and not self._given_name:
            return BASE_TEXT_BRUSH

        if role == Qt.TextAlignmentRole:
            return Qt.AlignHCenter | Qt.AlignBottom

        return super().data(role)

    def flags(self):
        if self.functionallyEmpty():
            return self._flags
        return self._flags | Qt.ItemIsEditable

    # Returns True if this block is functionally empty, eg:
    # a.) It has no children, or
    # b.) All children are Unassigns.
    def functionallyEmpty(self):
        if len(self.children) == 0:
            return True

        for child in self.children:
            if child.assignState() != AssignStateEnum.UNASSIGN:
                return False
        return True

    def inherited(self):
        return self._given_name is False

    def deserialiseName(self, value):
        self.setData(value, Qt.EditRole)

    def serialiseName(self):
        return self._given_name

    def setData(self, value, role):
        if role != Qt.EditRole:
            return False

        self._given_name = value if value else False
        return True

    def setInherited(self, value):
        self._inherited_name = value


### LEAVES
class ModelsEntry(ModelsLeafNode):
    '''Entry class'''
    def __init__(self, value, state=AssignStateEnum.NONE, **kwargs):
        super().__init__(**kwargs)
        self._value = value
        self._is_inherited = False
        self._assign_state = state

    def data(self, role=Qt.DisplayRole):
        # pylint: disable=too-many-return-statements
        if role == Qt.DisplayRole:
            return get_channel_assignment_name(self.value())

        if role == Qt.ForegroundRole: # Text colour:
            if self._assign_state == AssignStateEnum.ASSIGN:
                return QBrush(Qt.green)
            if self._assign_state == AssignStateEnum.UNASSIGN:
                return QBrush(Qt.red)
            if self._assign_state == AssignStateEnum.NONE and self._is_inherited:
                return BASE_TEXT_BRUSH

        if role == Qt.FontRole and self._assign_state == AssignStateEnum.UNASSIGN:
            font = QFont()
            font.setStrikeOut(True)
            return font

        return super().data(role)

    def assignState(self):
        return self._assign_state

    def inherited(self):
        return self._is_inherited

    def setAssignState(self, new_state):
        if new_state in AssignStateEnum:
            self._assign_state = new_state

    def setInherited(self, is_inherited):
        self._is_inherited = is_inherited

    def value(self):
        return self._value

### MODEL
class DcaModelTemplate(QAbstractItemModel):

    hideEmptyDcaNames = True

    def __init__(self):
        super().__init__()
        self.root = ModelsRootNode(model=self)

    def __len__(self):
        return self.root.childCount()

    def childCount(self, index):
        node = index.internalPointer() if index.isValid() else self.root
        return node.childCount()

    def columnCount(self, index):
        # pylint: disable=no-self-use, unused-argument
        return 1

    def data(self, index, role=Qt.DisplayRole):
        # pylint: disable=no-self-use
        if not index.isValid():
            return None
        return index.internalPointer().data(role)

    def setData(self, index, value, role):
        # pylint: disable=no-self-use
        if not index.isValid():
            return False
        return index.internalPointer().setData(value, role)

    def flags(self, index):
        # pylint: disable=no-self-use
        if not index.isValid():
            return Qt.NoItemFlags
        return index.internalPointer().flags()

    def index(self, row_num, col_num, parent_idx):
        if not self.hasIndex(row_num, col_num, parent_idx):
            return QModelIndex()

        parent_node = parent_idx.internalPointer() if parent_idx.isValid() else self.root
        child_node = parent_node.child(row_num)

        if child_node:
            return self.createIndex(row_num, col_num, child_node)
        return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        parent = index.internalPointer().parent
        if parent == self.root:
            return QModelIndex()

        return self.createIndex(parent.rownum(), 0, parent)

    def rowCount(self, index):
        return self.childCount(index)

    def _add_node(self, destination, new_node):
        '''Adds a node as a child of another'''
        parent_index = destination
        parent_node = parent_index.internalPointer()

        rownum = parent_node.getInsertPoint(new_node.value())
        self.beginInsertRows(parent_index, rownum, rownum)
        parent_node.addChild(new_node)
        self.endInsertRows()

    def _clear_node(self, node_index):
        '''Clear a node of all its children'''
        node = node_index.internalPointer()
        self.beginRemoveRows(node_index, 0, node.childCount())
        while node.childCount():
            node.removeChild(0)
        self.endRemoveRows()

    def _relocate_node(self, node_index, destination):
        '''Relocate a node from its parent node to the end of another '''
        old_parent_index = node_index.parent()
        old_parent_node = old_parent_index.internalPointer()
        old_parent_rownum = node_index.rownum()

        new_parent_index = destination
        new_parent_node = new_parent_index.internalPointer()
        new_parent_rownum = new_parent_node.getInsertPoint(node_index.internalPointer().value)

        self.beginMoveRows(old_parent_index,
                           old_parent_rownum,
                           old_parent_rownum,
                           new_parent_index,
                           new_parent_rownum)
        child = old_parent_node.removeChild(node_index.rownum())
        child.parent_node = new_parent_node
        new_parent_node.addChild(child)
        self.endMoveRows()

    def _remove_node(self, node_index):
        '''Remove a node from its parent'''
        if not node_index.isValid():
            return

        self.beginRemoveRows(self.parent(node_index), node_index.row(), node_index.row())
        node_index.internalPointer().parent.removeChild(node_index.row())
        self.endRemoveRows()
