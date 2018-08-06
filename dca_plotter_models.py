import logging

from PyQt5.QtCore import Qt, QAbstractItemModel, QModelIndex, QEvent, pyqtSignal
from PyQt5.QtWidgets import QStyledItemDelegate
from PyQt5.QtGui import QFont

from lisp.plugins.dca_plotter.utilities import get_mic_assign_name
from lisp.ui.icons import IconTheme

class DcaBlockNode():

    def __init__(self, model=None, parent_node=None, action=None):
        self.model = model
        self.parent_node = parent_node
        self.action = action

    def columnCount(self):
        return 2

    def data(self, col, role):
        if col == 1 and self.action:
            if role == Qt.ToolTipRole:
                return self.model.ACTIONS[self.action]['tooltip']
            if role == Qt.DecorationRole:
                return IconTheme.get(self.model.ACTIONS[self.action]['icon'])
        return None

    def row(self):
        return self.parent_node.children.index(self)

class DcaBlockBranch(DcaBlockNode):
    def __init__(self, caption, **kwargs):
        super().__init__(**kwargs)
        self.caption = caption
        self.children = []

    def addChild(self, child):
        '''Adds a Child

        If the child is a DcaBlockLeaf, then they are inserted in order
        of their given value. Else, it is appended to the end.
        '''
        if hasattr(child, 'value'):
            self.children.insert(self.getInsertPoint(child.value), child)
        else:
            self.children.append(child)

    def removeChild(self, row_num):
        return self.children.pop(row_num)

    def childCount(self):
        return len(self.children)

    def child(self, row):
        return self.children[row]

    def getChildIndexes(self):
        indexes = []
        for child in self.children:
            indexes.append(child.value)
        return indexes

    def getInsertPoint(self, mic_num):
        curr_indexes = self.getChildIndexes()
        curr_indexes.append(mic_num)
        curr_indexes.sort()
        return curr_indexes.index(mic_num)

    def callAction(self, row):
        if not self.action or not hasattr(self.model, self.action):
            return False

        getattr(self.model, self.action)()
        return True

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

    def callAction(self, index):
        if 'dest' in self.model.ACTIONS[self.action]:
            self.model.relocate_entry(index, self.action)
        else:
            self.model.remove_entry(index)
        return True

    def data(self, col, role=Qt.DisplayRole):
        if col != 0:
            return super().data(col, role)

        if role == Qt.DisplayRole:
            return get_mic_assign_name(self.value)

        if role == Qt.EditRole:
            return self.value

        return None

    def childCount(self):
        return 0;

class DcaBlockModel(QAbstractItemModel):

    CATEGORIES = {
        'assigns': {
            'caption': 'New Assigns',
            'action': 'add_assign',
            'child_action': 'remove_assign'
        },
        'inherited': {
            'caption': 'Inherited',
            'child_action': 'remove_inherited'
        },
        'unassigns': {
            'caption': 'Removed Assigns',
            'child_action': 'restore_inherited'
        }
    }

    ACTIONS = {
        'add_assign': {
            'tooltip': 'Add a new Assign to this DCA',
            'icon': 'list-add'
        },
        'remove_assign': {
            'tooltip': 'Remove this Assignment',
            'icon': 'list-remove'
        },
        'remove_inherited': {
            'tooltip': 'Remove this Assignment',
            'icon': 'list-remove',
            'dest': 'unassigns'
        },
        'restore_inherited': {
            'tooltip': 'Restore this Assignment',
            'icon': 'edit-undo',
            'dest': 'inherited'
        }
    }

    def __init__(self):
        super().__init__()
        self.root_node = DcaBlockBranch("Name")

        for defin in self.CATEGORIES.values():
            self.root_node.addChild(DcaBlockBranch(defin['caption'],
                                                   model=self,
                                                   parent_node=self.root_node,
                                                   action=defin.get('action', None)))

        # debug / test
        self.append_assign(2)
        self.append_assign(14)
        self.append_assign(9)
        self.append_assign(4)
        self.append_assign(12)
        self.append_assign(16)

        target = self.getCategoryNode('inherited')
        target.addChild(DcaBlockLeaf(10, model=self, parent_node=target, action='remove_inherited'))

        target = self.getCategoryNode('unassigns')
        target.addChild(DcaBlockLeaf(7, model=self, parent_node=target, action='restore_inherited'))
        target.addChild(DcaBlockLeaf(8, model=self, parent_node=target, action='restore_inherited'))
        target.addChild(DcaBlockLeaf(11, model=self, parent_node=target, action='restore_inherited'))
        target.addChild(DcaBlockLeaf(3, model=self, parent_node=target, action='restore_inherited'))
        target.addChild(DcaBlockLeaf(6, model=self, parent_node=target, action='restore_inherited'))


    def getCategoryNode(self, identifier):
        if identifier not in self.CATEGORIES:
            return None
        return self.root_node.child(list(self.CATEGORIES).index(identifier))

    def append_assign(self, mic_num):
        target = self.getCategoryNode('assigns')
        target.addChild(DcaBlockLeaf(mic_num,
                                     model=self,
                                     parent_node=target,
                                     action='remove_assign'))

    def add_assign(self):
        logging.warn('Assign')

    def remove_entry(self, index):
        '''Remove an entry from one of the lists'''
        self.beginRemoveRows(index.parent(), index.row(), index.row())
        self.root_node.child(index.parent().row()).removeChild(index.row())
        self.endRemoveRows()

    def relocate_entry(self, index, action):
        '''Relocate an entry from one of the lists to another'''
        source_parent = self.root_node.child(index.parent().row())
        dest_parent = self.getCategoryNode(self.ACTIONS[action]['dest'])
        dest_rownum = dest_parent.getInsertPoint(index.internalPointer().value)

        self.beginMoveRows(index.parent(),
                           index.row(),
                           index.row(),
                           self.createIndex(dest_parent.row(), 0, dest_parent),
                           dest_rownum)
        child = source_parent.removeChild(index.row())
        child.parent_node = dest_parent
        child.action = self.CATEGORIES[self.ACTIONS[action]['dest']]['child_action']
        dest_parent.addChild(child)
        self.endMoveRows()

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

    def callAction(self, index):
        if not index.isValid():
            return False
        return index.internalPointer().callAction(index)

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

class DcaBlockActionDelegate(QStyledItemDelegate):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def editorEvent(self, event, model, option, index):

        if event.type() == QEvent.MouseButtonRelease:
            return model.callAction(index)

        return super().editorEvent(event, model, option, index)
