import logging

from PyQt5.QtCore import Qt, QAbstractItemModel, QModelIndex, QEvent, pyqtSignal
from PyQt5.QtWidgets import QStyledItemDelegate
from PyQt5.QtGui import QFont

from lisp.plugins import get_plugin
from lisp.plugins.dca_plotter.utilities import get_mic_assign_name
from lisp.ui.icons import IconTheme

ActionRole = Qt.UserRole + 1

class DcaBlockNode():

    def __init__(self, model=None, parent_node=None, actions=[]):
        self.model = model
        self.parent_node = parent_node
        self.actions = actions
        self.flags = Qt.ItemFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

    def data(self, col, role):
        idx = self.model.columnCount(None) - col - 1
        action = self.actions[idx] if idx < len(self.actions) else None
        if action:
            if role == ActionRole:
                return action
            if role == Qt.ToolTipRole:
                return self.model.ACTIONS[action]['tooltip']
            if role == Qt.DecorationRole:
                return IconTheme.get(self.model.ACTIONS[action]['icon'])
        return None

    def row(self):
        '''Returns integer'''
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

    def callAction(self, index):
        action = self.data(index.column(), ActionRole)
        if not action or not hasattr(self.model, action):
            return False

        getattr(self.model, action)()
        return True

    def data(self, col, role=Qt.DisplayRole):
        if col == 0:
            if role == Qt.DisplayRole:
                return self.caption

            if role == Qt.FontRole:
                font = QFont()
                font.setBold(True)
                return font

        return super().data(col, role)

class DcaBlockLeaf(DcaBlockNode):
    def __init__(self, value, **kwargs):
        super().__init__(**kwargs)
        self.value = value
        self.flags |= Qt.ItemNeverHasChildren

    def callAction(self, index):
        action = self.data(index.column(), ActionRole)
        if not action:
            return False

        self.model.remove_or_relocate_entry(index, action)
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
        return 0

class DcaBlockModel(QAbstractItemModel):

    CATEGORIES = {
        'assigns': {
            'caption': 'New Assigns',
            'actions': ['add_new_assign'],
            'child_actions': ['remove_assign']
        },
        'inherited': {
            'caption': 'Inherited',
            'child_actions': ['remove_inherited', 'pin_inherited']
        },
        'unassigns': {
            'caption': 'Removed Assigns',
            'actions': ['add_new_unassign'],
            'child_actions': ['restore_inherited']
        }
    }

    ACTIONS = {
        'add_new_assign': {
            'tooltip': 'Add a new Assign to this DCA',
            'icon': 'list-add'
        },
        'add_new_unassign': {
            'tooltip': 'Add a new Unassign to this DCA',
            'icon': 'list-add'
        },
        'remove_assign': {
            'tooltip': 'Remove/Unpin this Assignment',
            'icon': 'list-remove',
            'dest': 'inherited'
        },
        'pin_inherited': {
            'tooltip': 'Pin this Assignment',
            'icon': 'linked',
            'dest': 'assigns'
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

    def __init__(self, selection_dialog):
        super().__init__()
        self.root_node = DcaBlockBranch("Name")
        self.selection_dialog = selection_dialog
        self.inherited = [3, 6, 7, 10, 11]

        for defin in self.CATEGORIES.values():
            self.root_node.addChild(DcaBlockBranch(defin['caption'],
                                                   model=self,
                                                   parent_node=self.root_node,
                                                   actions=defin.get('actions', [])))

        # debug / test
        self.append_assign(2)

        target = self.getCategoryNode('inherited')
        target.addChild(DcaBlockLeaf(10, model=self, parent_node=target, actions=['remove_inherited', 'pin_inherited']))

        target = self.getCategoryNode('unassigns')
        target.addChild(DcaBlockLeaf(7, model=self, parent_node=target, actions=['restore_inherited']))
        target.addChild(DcaBlockLeaf(8, model=self, parent_node=target, actions=['restore_inherited']))
        target.addChild(DcaBlockLeaf(11, model=self, parent_node=target, actions=['restore_inherited']))
        target.addChild(DcaBlockLeaf(3, model=self, parent_node=target, actions=['restore_inherited']))
        target.addChild(DcaBlockLeaf(6, model=self, parent_node=target, actions=['restore_inherited']))

    def getCategoryNode(self, identifier):
        if identifier not in self.CATEGORIES:
            return None
        return self.root_node.child(list(self.CATEGORIES).index(identifier))

    def append_assign(self, mic_num):
        pass

    def get_values_not_used(self):
        current_values = []
        for cat in self.root_node.children:
            for leaf in cat.children:
                current_values.append(leaf.value)

        possible_values = []
        for num in range(1, get_plugin('DcaPlotter').get_microphone_count() + 1):
            if num not in current_values:
                possible_values.append(num)
        return possible_values

    def add_new_assign(self):
        self.selection_dialog.set_entries(self.get_values_not_used())
        if self.selection_dialog.exec_() == self.selection_dialog.Accepted:
            selected = self.selection_dialog.selected_entries()
            if selected:
                dest_parent = self.getCategoryNode('assigns')
                # TODO: A more elegant way of doing the following
                # (instead of going in & out of insert status)
                # Also, deal with selected entries that are inherited and removed
                for mic_num in selected:
                    dest_rownum = dest_parent.getInsertPoint(mic_num)
                    self.beginInsertRows(self.createIndex(dest_parent.row(), 0, dest_parent), dest_rownum, dest_rownum)
                    dest_parent.addChild(DcaBlockLeaf(mic_num,
                                                      model=self,
                                                      parent_node=dest_parent,
                                                      actions=self.CATEGORIES['assigns']['child_actions']))
                    self.endInsertRows()

    def add_new_unassign(self):
        self.selection_dialog.set_entries(self.get_values_not_used())
        if self.selection_dialog.exec_() == self.selection_dialog.Accepted:
            selected = self.selection_dialog.selected_entries()
            if selected:
                dest_parent = self.getCategoryNode('unassigns')
                # TODO: A more elegant way of doing the following
                # (instead of going in & out of insert status)
                # Also, deal with selected entries that are inherited and removed
                for mic_num in selected:
                    dest_rownum = dest_parent.getInsertPoint(mic_num)
                    self.beginInsertRows(self.createIndex(dest_parent.row(), 0, dest_parent), dest_rownum, dest_rownum)
                    dest_parent.addChild(DcaBlockLeaf(mic_num,
                                                      model=self,
                                                      parent_node=dest_parent,
                                                      actions=self.CATEGORIES['unassigns']['child_actions']))
                    self.endInsertRows()

    def remove_or_relocate_entry(self, index, action):
        if index.internalPointer().value in self.inherited:
            self.relocate_entry(index, self.ACTIONS[action]['dest'])
        else:
            self.remove_entry(index)

    def remove_entry(self, index):
        '''Remove an entry from one of the lists'''
        self.beginRemoveRows(index.parent(), index.row(), index.row())
        self.root_node.child(index.parent().row()).removeChild(index.row())
        self.endRemoveRows()

    def relocate_entry(self, index, dest):
        '''Relocate an entry from one of the lists to another'''
        source_parent = self.root_node.child(index.parent().row())
        dest_parent = self.getCategoryNode(dest)
        dest_rownum = dest_parent.getInsertPoint(index.internalPointer().value)

        self.beginMoveRows(index.parent(),
                           index.row(),
                           index.row(),
                           self.createIndex(dest_parent.row(), 0, dest_parent),
                           dest_rownum)
        child = source_parent.removeChild(index.row())
        child.parent_node = dest_parent
        child.actions = self.CATEGORIES[dest]['child_actions']
        dest_parent.addChild(child)
        self.endMoveRows()

    def columnCount(self, parent_idx):
        return 3

    def flags(self, index):
        if not index.isValid():
            return None
        return index.internalPointer().flags

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
