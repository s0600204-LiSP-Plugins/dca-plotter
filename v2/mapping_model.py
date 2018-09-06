
import copy
import enum

# pylint: disable=no-name-in-module
from PyQt5.QtCore import Qt, QAbstractItemModel, QModelIndex
from PyQt5.QtGui import QBrush, QFont
from PyQt5.QtWidgets import QApplication

from lisp.plugins import get_plugin
from lisp.plugins.dca_plotter.utilities import get_mic_assign_name

class AssignStateEnum(enum.Enum):
    ASSIGN = enum.auto()
    UNASSIGN = enum.auto()
    NONE = enum.auto()

### ABSTRACTS
class DcaMapNode():
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
    def __init__(self, cue, **kwargs):
        super().__init__(**kwargs)
        self.cue = cue

        # pylint: disable=unused-variable
        for dca in range(get_plugin('DcaPlotter').SessionConfig['dca_count']):
            self.addChild(DcaMapBlock(parent=self))

    def data(self, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return "{} : {}".format(self.cue.index + 1, self.cue.name)
        return super().data(role)

    def value(self):
        return self.cue.index

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
    def __init__(self, value, state=AssignStateEnum.NONE, **kwargs):
        super().__init__(**kwargs)
        self._value = value
        self._is_inherited = state == AssignStateEnum.NONE
        self._assign_state = state

    def data(self, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            name = get_mic_assign_name(self.value())
            if self._assign_state == AssignStateEnum.NONE:
                return "({})".format(name)
            return name

        if role == Qt.EditRole:
            return self.value

        if role == Qt.ForegroundRole: # Text colour:
            if self._assign_state == AssignStateEnum.ASSIGN:
                return QBrush(Qt.green)
            if self._assign_state == AssignStateEnum.UNASSIGN:
                return QBrush(Qt.red)
            if self._assign_state == AssignStateEnum.NONE:
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
class DcaMappingModel(QAbstractItemModel):
    def __init__(self):
        super().__init__()
        self.root = DcaMapRootNode(model=self)

    def amend_cuerow(self, cue, property_name, property_value):
        if property_name != 'dca_changes':
            return

        cuerow = self._find_cuerow(cue.id)

        # Clear each dca block and set the new children
        for dca_num, assign_actions in enumerate(property_value):
            block_node = cuerow.child(dca_num)
            block_index = self.createIndex(block_node.rownum(), 0, block_node)
            self._clear_node(block_index)

            for entry in assign_actions['add']:
                self._add_node(block_index,
                               DcaMapEntry(entry, AssignStateEnum.ASSIGN, parent=block_node))

            for entry in assign_actions['rem']:
                self._add_node(block_index,
                               DcaMapEntry(entry, AssignStateEnum.UNASSIGN, parent=block_node))

        if cuerow.prev_sibling():
            # Get inherits from previous cue row
            changes = self._change_tuples_derive(cuerow.prev_sibling())
            self._change_tuples_apply(cuerow, changes)

        self._change_tuples_cascade_apply(cuerow)

    def append_cuerow(self, cue):
        '''Append a cue-row to the model

        Warning: If a cue is created between two other cues,
                                            this function will not pick that fact up...
                 Thankfully, creating a cue 'tween two others is not currently possible.
        '''
        new_cuerow = DcaMapRow(cue, parent=self.root)
        self._add_node(self.createIndex(self.root.childCount(), 0, self.root), new_cuerow)

        if new_cuerow.prev_sibling():
            # Get inherits from previous cue row
            changes = self._change_tuples_derive(new_cuerow.prev_sibling())
            self._change_tuples_apply(new_cuerow, changes)

        # Attach listener so we get cue property changes
        cue.property_changed.connect(self.amend_cuerow)

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

    def move_cuerow(self, cue, new_cue_index):
        '''Called when a cue is moved in the main cue list'''
        cuerow = self._find_cuerow(cue.id)

        old_index = cuerow.rownum()
        new_index = sorted(self.root.getChildValues()).index(new_cue_index)

        # If there's no change (for us):
        if old_index == new_index:
            return

        # Update assign entries at the leave point
        changes = self._change_tuples_invert(self._change_tuples_derive(cuerow))
        self._change_tuples_cascade_apply(cuerow, changes)

        # When moving down, all other things move up. In this case, the new index is one out.
        if old_index < new_index:
            new_index += 1

        self.beginMoveRows(QModelIndex(), old_index, old_index, QModelIndex(), new_index)
        self.root.children.sort(key=DcaMapRow.value)
        self.endMoveRows()

        # Update assign entries at the entry point
        # First, cleanup the moved cue down to its basic assign/unassigns
        for dca_node in cuerow.children:
            for entry in copy.copy(dca_node.children):
                entry.setInherited(False)
                if entry.assign_state() == AssignStateEnum.NONE:
                    self._remove_node(entry.index())

        # Then, update from the new previous cue row
        if cuerow.prev_sibling():
            changes = self._change_tuples_derive(cuerow.prev_sibling())
            self._change_tuples_apply(cuerow, changes)

        # Finally, cascade changes.
        self._change_tuples_cascade_apply(cuerow)

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        parent = index.internalPointer().parent
        if parent == self.root:
            return QModelIndex()

        return self.createIndex(parent.rownum(), 0, parent)

    def remove_cuerow(self, cue):
        '''Removes the cue-row from the model'''
        cue.property_changed.disconnect(self.amend_cuerow)
        cuerow = self._find_cuerow(cue.id)

        # Update assign entries
        changes = self._change_tuples_invert(self._change_tuples_derive(cuerow))
        self._change_tuples_cascade_apply(cuerow, changes)

        # And remove the cuerow from the model
        self._remove_node(cuerow.index())

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

    def _change_tuples_apply(self, cuerow, changes):
        for change in copy.copy(changes):
            block_node = cuerow.child(change[0])
            block_index = block_node.index()
            block_entry_values = block_node.getChildValues()

            if change[1] not in block_entry_values:
                if change[2] != AssignStateEnum.UNASSIGN:
                    self._add_node(block_index, DcaMapEntry(change[1], parent=block_node))
            else:
                entry_node = block_node.child(block_entry_values.index(change[1]))
                if entry_node.assign_state() != AssignStateEnum.NONE:
                    changes.remove(change)
                    entry_node.setInherited(change[2] != AssignStateEnum.UNASSIGN)
                elif change[2] == AssignStateEnum.UNASSIGN:
                    self._remove_node(entry_node.index())

    def _change_tuples_cascade_apply(self, cuerow, changes=None):
        if not changes:
            changes = self._change_tuples_derive(cuerow)
        next_rownum = cuerow.rownum() + 1

        while changes and next_rownum < self.root.childCount():
            self._change_tuples_apply(self.root.child(next_rownum), changes)
            next_rownum += 1

    def _change_tuples_derive(self, cuerow):
        changes = []
        for dca_num, dca_node in enumerate(cuerow.children):
            for entry in dca_node.children:
                changes.append((dca_num, entry.value(), entry.assign_state()))
        return changes

    def _change_tuples_invert(self, old_changes):
        new_changes = []
        for change in old_changes:
            new_state = change[2]
            if new_state == AssignStateEnum.ASSIGN:
                new_state = AssignStateEnum.UNASSIGN
            elif new_state == AssignStateEnum.UNASSIGN:
                new_state = AssignStateEnum.ASSIGN

            new_changes.append((change[0],
                                change[1],
                                new_state))
        return new_changes

    def _clear_node(self, node_index):
        '''Clear a node of all its children'''
        node = node_index.internalPointer()
        self.beginRemoveRows(node_index, 0, node.childCount())
        while node.childCount():
            node.removeChild(0)
        self.endRemoveRows()

    def _find_cuerow(self, cue_id):
        '''Find and return the cue-row that matches the given cue-id'''
        for cuerow in self.root.children:
            if cuerow.cue.id == cue_id:
                return cuerow
        return None

    def _relocate_node(self, node_index, destination):
        '''Relocate a node from its parent node to the end of another '''
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
        if not node_index.isValid():
            return

        self.beginRemoveRows(self.parent(node_index), node_index.row(), node_index.row())
        node_index.internalPointer().parent.removeChild(node_index.row())
        self.endRemoveRows()
