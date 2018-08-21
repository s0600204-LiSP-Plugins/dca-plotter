
# pylint: disable=no-name-in-module
from PyQt5.QtCore import Qt, QAbstractItemModel, QModelIndex
from PyQt5.QtGui import QFont

from lisp.plugins import get_plugin
from lisp.plugins.dca_plotter.utilities import get_mic_assign_name

#ActionRole = Qt.UserRole + 1
ACTION_COLUMN_COUNT = 0

### ABSTRACTS
class DcaAssignNode():
    '''Abstract parent class'''
    def __init__(self, parent=None):
        self.parent = parent
        self.flags = Qt.ItemFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

    def data(self, column, role=Qt.DisplayRole):
        # pylint: disable=no-self-use, unused-argument
        return None

    def model(self):
        return self.parent.model()

    def row(self):
        return self.parent.children.index(self)

class DcaAssignBranchNode(DcaAssignNode):
    '''Branch parent class'''
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.children = []

    def addChild(self, child):
        self.children.append(child)

    def getInsertPoint(self, mic_num):
        # pylint: disable=unused-argument
        return self.rowCount()

    def removeChild(self, row):
        return self.children.pop(row)

    def rowCount(self):
        return len(self.children)

class DcaAssignLeafNode(DcaAssignNode):
    '''Leaf parent class'''
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.flags |= Qt.ItemNeverHasChildren

    def rowCount(self):
        # pylint: disable=no-self-use
        return 0

### BRANCHES
class DcaAssignRootNode(DcaAssignBranchNode):
    '''Root class'''
    def __init__(self, model, **kwargs):
        super().__init__(**kwargs)
        self._model = model

    def model(self):
        return self._model

class DcaAssignRow(DcaAssignBranchNode):
    '''Row class.'''
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cue_id = False

        # pylint: disable=unused-variable
        for dca in range(get_plugin('DcaPlotter').SessionConfig['dca_count']):
            self.addChild(DcaAssignBlock(parent=self))

    def rowCount(self):
        return 1

    def columnCount(self):
        return len(self.children)

class DcaAssignBlock(DcaAssignBranchNode):
    '''Block class'''
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = False

    def columnCount(self):
        # pylint: disable=no-self-use
        return 1

class DcaAssignCategory(DcaAssignBranchNode):
    '''Category class'''
    def __init__(self, caption, **kwargs):
        super().__init__(**kwargs)
        self.caption = caption

    def addChild(self, child):
        self.children.insert(self.getInsertPoint(child.value), child)

    def columnCount(self):
        # pylint: disable=no-self-use
        return 1 + ACTION_COLUMN_COUNT

    def data(self, column, role=Qt.DisplayRole):
        if column == 0:
            if role == Qt.DisplayRole:
                return self.caption

            if role == Qt.FontRole:
                font = QFont()
                font.setBold(True)
                return font

        return super().data(column, role)

    def getChildValues(self):
        indexes = []
        for child in self.children:
            indexes.append(child.value)
        return indexes

    def getInsertPoint(self, mic_num):
        curr_values = self.getChildValues()
        curr_values.append(mic_num)
        curr_values.sort()
        return curr_values.index(mic_num)

### LEAVES
class DcaAssignEntry(DcaAssignLeafNode):
    '''Entry class'''
    def __init__(self, value, **kwargs):
        super().__init__(**kwargs)
        self.value = value

    def data(self, column, role=Qt.DisplayRole):
        if column == 0:
            if role == Qt.DisplayRole:
                return get_mic_assign_name(self.value)
            if role == Qt.EditRole:
                return self.value

        return super().data(column, role)

    def getColumnCount(self):
        # pylint: disable=no-self-use
        return 1 + ACTION_COLUMN_COUNT

### MODEL
class DcaAssignModel(QAbstractItemModel):
    def __init__(self):
        super().__init__()
        self.root = DcaAssignRootNode(model=self)

    def columnCount(self, index):
        node = index.internalPointer() if index.isValid() else self.root
        return node.columnCount()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        parent = index.internalPointer().parent
        if parent == self.root:
            return QModelIndex()

        return self.createIndex(parent.row(), 0, parent)

    def rowCount(self, index):
        node = index.internalPointer() if index.isValid() else self.root
        return node.rowCount()

    def _add_node(self, destination, new_node):
        '''Adds a node as a child of another'''
        ## if destination is an index:
        parent_index = destination
        parent_node = parent_index.internalPointer()

        rownum = parent_node.getInsertPoint(new_node.internalPointer().value)
        self.beginInsertRows(parent_index, rownum, rownum)
        parent_node.addChild(new_node)
        self.endInsertRows()

    def _relocate_node(self, node_index, destination):
        '''Relocate a node from its parent node to another '''
        old_parent_index = node_index.parent()
        old_parent_node = old_parent_index.internalPointer()
        old_parent_rownum = node_index.row()

        ## if destination is an index:
        new_parent_index = destination
        new_parent_node = new_parent_index.internalPointer()
        ## else if destination is a node:
        #   new_parent_node = destination
        #   new_parent_index = self.createIndex(new_parent_node.row(), 0, new_parent_node)
        new_parent_rownum = new_parent_node.getInsertPoint(node_index.internalPointer().value)

        self.beginMoveRows(old_parent_index,
                           old_parent_rownum,
                           old_parent_rownum,
                           new_parent_index,
                           new_parent_rownum)
        child = old_parent_node.removeChild(node_index.row())
        child.parent_node = new_parent_node
        new_parent_node.addChild(child)
        self.endMoveRows()

    def _remove_node(self, node_index):
        '''Remove a node from its parent'''
        self.beginRemoveRows(node_index.parent(), node_index.row(), node_index.row())
        self.root_node.child(node_index.parent().row()).removeChild(node_index.row())
        self.endRemoveRows()
