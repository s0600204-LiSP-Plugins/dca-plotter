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
        if not action:
            return False

        self.model.add_new_entry(index, action)
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
            'actions': ['new_assign'],
            'child_actions': ['remove_assign']
        },
        'inherited': {
            'caption': 'Inherited Assigns',
            'child_actions': ['remove_inherited', 'pin_inherited']
        },
        'unassigns': {
            'caption': 'Removed Assigns',
            'actions': ['new_unassign'],
            'child_actions': ['restore_inherited']
        }
    }

    ACTIONS = {
        'new_assign': {
            'tooltip': 'Add a new Assign to this DCA',
            'icon': 'list-add',
            'dest': 'assigns'
        },
        'new_unassign': {
            'tooltip': 'Add a new Unassign to this DCA',
            'icon': 'list-add',
            'dest': 'unassigns'
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
        self.inherited = []

        for defin in self.CATEGORIES.values():
            self.root_node.addChild(DcaBlockBranch(defin['caption'],
                                                   model=self,
                                                   parent_node=self.root_node,
                                                   actions=defin.get('actions', [])))

    def deserialise(self, assign_changes):
        for mic_num in assign_changes['add']:
            self.append_entry(mic_num, 'assigns')
        for mic_num in assign_changes['rem']:
            self.append_entry(mic_num, 'unassigns')

        self.inherited = assign_changes['inherit']
        for mic_num in assign_changes['inherit']:
            if mic_num not in assign_changes['add'] and mic_num not in assign_changes['rem']:
                self.append_entry(mic_num, 'inherited')

    def serialise(self):
        assigns = {
            'add': [],
            'rem': []
        }
        for leaf in self.getCategoryNode('assigns').children:
            assigns['add'].append(leaf.value)
        for leaf in self.getCategoryNode('unassigns').children:
            assigns['rem'].append(leaf.value)
        return assigns

    def getCategoryNode(self, identifier):
        if identifier not in self.CATEGORIES:
            return None
        return self.root_node.child(list(self.CATEGORIES).index(identifier))

    def append_entry(self, mic_num, category):
        dest_parent = self.getCategoryNode(category)
        dest_parent.addChild(DcaBlockLeaf(mic_num,
                                          model=self,
                                          parent_node=dest_parent,
                                          actions=self.CATEGORIES[category]['child_actions']))

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

    def add_new_entry(self, index, action):
        self.selection_dialog.set_entries(self.get_values_not_used())
        if self.selection_dialog.exec_() == self.selection_dialog.Accepted:
            selected = self.selection_dialog.selected_entries()
            if selected:
                parent_node = index.internalPointer()
                parent_index = self.createIndex(index.row(), 0, parent_node)
                for mic_num in selected:
                    rownum = parent_node.getInsertPoint(mic_num)
                    self.beginInsertRows(parent_index, rownum, rownum)
                    self.append_entry(mic_num, self.ACTIONS[action]['dest'])
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
