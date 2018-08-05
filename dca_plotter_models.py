import logging
from PyQt5.QtCore import Qt, QAbstractItemModel, QModelIndex
from PyQt5.QtGui import QFont

from lisp.plugins.dca_plotter.utilities import get_mic_assign_name

class DcaBlockNode():

    def __init__(self, parent_node=None, action=None):
        self.parent_node = parent_node
        self.action = action

    def columnCount(self):
        return 2

    def data(self, col, role):
        if role == Qt.DisplayRole and col == 1:
            return self.action
        return None

    def row(self):
        return self.parent_node.children.index(self)

class DcaBlockBranch(DcaBlockNode):
    def __init__(self, caption, **kwargs):
        super().__init__(**kwargs)
        self.caption = caption
        self.children = []

    def appendChild(self, child):
        self.children.append(child)

    def removeChild(self, child):
        self.children.remove(child)

    def childCount(self):
        return len(self.children)

    def child(self, row):
        return self.children[row]

    def data(self, col, role=Qt.DisplayRole):
        if col == 0:
            if role == Qt.DisplayRole:
                return self.caption;

            if role == Qt.FontRole:
                font = QFont()
                font.setBold(True)
                return font

        return super().data(col, role)

class DcaBlockLeaf(DcaBlockNode):
    def __init__(self, value, **kwargs):
        super().__init__(**kwargs)
        self.value = value

    def data(self, col, role=Qt.DisplayRole):
        if col != 0:
            return super().data(col, role)

        if role == Qt.DisplayRole:
            return get_mic_assign_name(self.value)
        return None

    def childCount(self):
        return 0;

class DcaBlockModel(QAbstractItemModel):

    CATEGORIES = {
        'assign': {
            'caption': 'New Assigns',
            'action': 'add'
        },
        'inherit': {
            'caption': 'Inherited'
        },
        'unassign': {
            'caption': 'Removed Assigns'
        }
    }

    def __init__(self):
        super().__init__()
        self.root_node = DcaBlockBranch("Name")

        for defin in self.CATEGORIES.values():
            self.root_node.appendChild(DcaBlockBranch(defin['caption'],
                                                      parent_node=self.root_node,
                                                      action=defin.get('action', None)))

        # debug / test
        target = self.getCategoryNode('assign')
        target.appendChild(DcaBlockLeaf(14, parent_node=target))
        target.appendChild(DcaBlockLeaf(8, parent_node=target))

        target = self.getCategoryNode('inherit')
        target.appendChild(DcaBlockLeaf(7, parent_node=target))

    def getCategoryNode(self, identifier):
        if identifier not in self.CATEGORIES:
            return None
        return self.root_node.child(list(self.CATEGORIES).index(identifier))

    def columnCount(self, parent_idx):
        return 2

    def index(self, row_num, col_num, parent_idx):
        if not self.hasIndex(row_num, col_num, parent_idx):
            return QModelIndex()

        parent_node = parent_idx.internalPointer() if parent_idx.isValid() else self.root_node
        child_node = parent_node.child(row_num)

        if child_node:
            return self.createIndex(row_num, col_num, child_node)
        return QModelIndex()

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        return index.internalPointer().data(index.column(), role)

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        child_node = index.internalPointer()
        parent_node = child_node.parent_node;

        if parent_node == self.root_node:
            return QModelIndex()
        return self.createIndex(parent_node.row(), 0, parent_node);

    def rowCount(self, parent_idx):
        parent_node = parent_idx.internalPointer() if parent_idx.isValid() else self.root_node
        return parent_node.childCount()
