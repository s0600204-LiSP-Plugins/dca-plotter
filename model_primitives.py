
# pylint: disable=missing-docstring

import enum

# pylint: disable=no-name-in-module
from PyQt5.QtCore import Qt, QAbstractItemModel, QModelIndex
from PyQt5.QtGui import QBrush, QFont
from PyQt5.QtWidgets import QApplication

from lisp.plugins import get_plugin
from lisp.plugins.dca_plotter.utilities import build_default_dca_name, get_mic_assign_name

class AssignStateEnum(enum.Enum):
    ASSIGN = enum.auto()
    UNASSIGN = enum.auto()
    NONE = enum.auto()

### ABSTRACTS
class ModelsNode():
    '''Abstract parent class'''
    def __init__(self, parent=None):
        self.parent = parent
        self.flags = Qt.ItemFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

    def data(self, role=Qt.DisplayRole):
        # pylint: disable=no-self-use, unused-argument
        return None

    def index(self):
        return self.model().createIndex(self.rownum(), 0, self)

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
        if self in self.parent.children:
            return self.parent.children.index(self)
        return -1

    def setData(self, value, role):
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
        self.flags |= Qt.ItemNeverHasChildren

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
        self._inherited_name = build_default_dca_name(self.parent.childCount() + 1)
        self.flags |= Qt.ItemIsEditable

    def addChild(self, child):
        self.children.insert(self.getInsertPoint(child.value()), child)

    def data(self, role=Qt.DisplayRole):
        if role == Qt.DisplayRole or role == Qt.EditRole:
            return self._given_name or self._inherited_name

        if role == Qt.ForegroundRole and not self._given_name:
            return QBrush(QApplication.palette().dark().color())

        if role == Qt.TextAlignmentRole:
            return Qt.AlignHCenter | Qt.AlignBottom

        return super().data(role)

    def inherited(self):
        return self._given_name == False

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
            return get_mic_assign_name(self.value())

        if role == Qt.EditRole:
            return self.value

        if role == Qt.ForegroundRole: # Text colour:
            if self._assign_state == AssignStateEnum.ASSIGN:
                return QBrush(Qt.green)
            if self._assign_state == AssignStateEnum.UNASSIGN:
                return QBrush(Qt.red)
            if self._assign_state == AssignStateEnum.NONE and self._is_inherited:
                return QBrush(QApplication.palette().dark().color())

        if role == Qt.FontRole and self._assign_state == AssignStateEnum.UNASSIGN:
            font = QFont()
            font.setStrikeOut(True)
            return font

        return super().data(role)

    def assign_state(self):
        return self._assign_state

    def inherited(self):
        return self._is_inherited

    def setInherited(self, is_inherited):
        self._is_inherited = is_inherited

    def value(self):
        return self._value

### MODEL
class DcaModelTemplate(QAbstractItemModel):
    def __init__(self):
        super().__init__()
        self.root = ModelsRootNode(model=self)

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
        if not index.isValid():
            return False
        return index.internalPointer().setData(value, role)

    def flags(self, index):
        # pylint: disable=no-self-use
        if not index.isValid():
            return None
        return index.internalPointer().flags

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
