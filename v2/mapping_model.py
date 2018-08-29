
# pylint: disable=no-name-in-module
from PyQt5.QtCore import Qt, QAbstractItemModel, QModelIndex
from PyQt5.QtGui import QFont

from lisp.application import Application
from lisp.plugins import get_plugin
from lisp.plugins.dca_plotter.utilities import get_mic_assign_name

#ActionRole = Qt.UserRole + 1

### ABSTRACTS
class DcaMapNode():
    '''Abstract parent class'''
    def __init__(self, parent=None):
        self.parent = parent
        self.flags = Qt.ItemFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

    def data(self, role=Qt.DisplayRole):
        # pylint: disable=no-self-use, unused-argument
        return None

    def model(self):
        return self.parent.model()

    def rownum(self):
        return self.parent.children.index(self)

class DcaMapBranchNode(DcaMapNode):
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

class DcaMapLeafNode(DcaMapNode):
    '''Leaf parent class'''
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.flags |= Qt.ItemNeverHasChildren

    def childCount(self):
        # pylint: disable=no-self-use
        return 0

### BRANCHES
class DcaMapRootNode(DcaMapBranchNode):
    '''Root class'''
    def __init__(self, model, **kwargs):
        super().__init__(**kwargs)
        self._model = model

    def model(self):
        return self._model

class DcaMapRow(DcaMapBranchNode):
    '''Row class.'''
    def __init__(self, cue_id, **kwargs):
        super().__init__(**kwargs)
        self.cue_id = cue_id

        Application().cue_model.get(self.cue_id).property_changed.connect(self._on_property_changed)

        # pylint: disable=unused-variable
        for dca in range(get_plugin('DcaPlotter').SessionConfig['dca_count']):
            self.addChild(DcaMapBlock(parent=self))

    # @todo:
    #  - This method breaks the model/view paradigm by not alerting views that data is about/has been changed. For now, that doesn't really matter. However, it will later.
    #  - We also need to handle cases where a cue has been edited, and we need to update our current store.
    def _on_property_changed(self, cue, property_name, property_value):
        if property_name == 'dca_changes':
            dca_count = 0
            for dca in property_value:
                block = self.children[dca_count]
                for entry in dca['add']:
                    block.addChild(DcaMapEntry(entry, parent=block))
                for entry in dca['rem']:
                    block.addChild(DcaMapEntry(entry, parent=block))
                dca_count += 1

    def data(self, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            cue = Application().cue_model.get(self.cue_id)
            return "{} : {}".format(cue.index+1, cue.name)

        return super().data(role)

    def value(self):
        return Application().cue_model.get(self.cue_id).index

class DcaMapBlock(DcaMapBranchNode):
    '''Block class'''
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = False

    def addChild(self, child):
        self.children.insert(self.getInsertPoint(child.value()), child)

    def data(self, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return 'DCA {}'.format(self.parent.children.index(self) + 1) # @todo: Proper implementation of DCA names

        return super().data(role)

### LEAVES
class DcaMapEntry(DcaMapLeafNode):
    '''Entry class'''
    def __init__(self, value, **kwargs):
        super().__init__(**kwargs)
        self._value = value

    def data(self, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return get_mic_assign_name(self.value())
        if role == Qt.EditRole:
            return self.value

        return super().data(role)

    def value(self):
        return self._value

### MODEL
class DcaMappingModel(QAbstractItemModel):
    def __init__(self):
        super().__init__()
        self.root = DcaMapRootNode(model=self)

    def append_cue(self, cue_id):
        new_row = DcaMapRow(cue_id, parent=self.root)
        self._add_node(self.createIndex(self.root.childCount(), 0, self.root), new_row)

    def childCount(self, index):
        node = index.internalPointer() if index.isValid() else self.root
        return node.childCount()

    def columnCount(self, index):
        # pylint: disable=no-self-use
        return 1

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        return index.internalPointer().data(role)

    def flags(self, index):
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
        ## if destination is an index:
        parent_index = destination
        parent_node = parent_index.internalPointer()

        rownum = parent_node.getInsertPoint(new_node.value())
        self.beginInsertRows(parent_index, rownum, rownum)
        parent_node.addChild(new_node)
        self.endInsertRows()

    def _relocate_node(self, node_index, destination):
        '''Relocate a node from its parent node to another '''
        old_parent_index = node_index.parent()
        old_parent_node = old_parent_index.internalPointer()
        old_parent_rownum = node_index.rownum()

        ## if destination is an index:
        new_parent_index = destination
        new_parent_node = new_parent_index.internalPointer()
        ## else if destination is a node:
        #   new_parent_node = destination
        #   new_parent_index = self.createIndex(new_parent_node.rownum(), 0, new_parent_node)
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
        self.beginRemoveRows(node_index.parent(), node_index.rownum(), node_index.rownum())
        self.root_node.child(node_index.parent().rownum()).removeChild(node_index.rownum())
        self.endRemoveRows()
