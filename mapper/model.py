
import copy

# pylint: disable=no-name-in-module
from PyQt5.QtCore import QModelIndex, Qt

from lisp.plugins.dca_plotter.model_primitives import AssignStateEnum, DcaModelTemplate, \
    ModelsAssignRow, ModelsResetRow, ModelsEntry

class DcaMappingModel(DcaModelTemplate):

    def amend_cuerow(self, cue, property_name, property_value):
        if property_name != 'dca_changes' or cue.type == "DcaResetCue":
            return

        cuerow = self.find_cuerow(cue.id)
        before = self._change_tuples_derive(cuerow)

        # Update assigns for this cuerow.
        self._set_initial_assigns(cuerow, property_value, True)

        # For the "Assigns" that were removed.
        after = self._change_tuples_derive(cuerow)
        for change in before:
            if change not in after and change[2] == AssignStateEnum.ASSIGN:
                after.append((change[0], change[1], None))

        # Update the cuerows beyond it.
        self._change_tuples_cascade_apply(cuerow, after)

    def append_cuerow(self, cue):
        '''Append a cue-row to the model

        Warning: If a cue is created between two other cues,
                                            this function will not pick that fact up...
                 Thankfully, creating a cue 'tween two others is not currently possible.
        '''

        if cue.type == "DcaChangeCue":
            new_cuerow = ModelsAssignRow(cue, parent=self.root)
            self._add_node(self.createIndex(self.root.childCount(), 0, self.root), new_cuerow)
            self._set_initial_assigns(new_cuerow, cue.dca_changes, False)

        elif cue.type == "DcaResetCue":
            new_cuerow = ModelsResetRow(cue, parent=self.root)
            self._add_node(self.createIndex(self.root.childCount(), 0, self.root), new_cuerow)

        # Attach listener so we get cue property changes
        cue.property_changed.connect(self.amend_cuerow)

    def move_cuerow(self, cue, new_cue_index):
        '''Called when a cue is moved in the main cue list'''
        cuerow = self.find_cuerow(cue.id)

        old_index = cuerow.rownum()
        new_index = sorted(self.root.getChildValues()).index(new_cue_index)

        # If there's no change (for us):
        if old_index == new_index:
            return

        # Update assign entries at the leave point
        if cue.type == "DcaChangeCue":
            changes = self._change_tuples_invert(self._change_tuples_derive(cuerow))
        else:
            changes = self._change_tuples_derive(cuerow.prev_sibling())
        self._change_tuples_cascade_apply(cuerow, changes)

        # When moving down, all other things move up. In this case, the new index is one out.
        if old_index < new_index:
            new_index += 1

        self.beginMoveRows(QModelIndex(), old_index, old_index, QModelIndex(), new_index)
        self.root.children.sort(key=ModelsResetRow.value)
        self.endMoveRows()

        # Update assign entries at the entry point
        # First, cleanup the moved cue down to its basic assign/unassigns
        for dca_node in cuerow.children:
            for entry in copy.copy(dca_node.children):
                entry.setInherited(False)
                if entry.assign_state() == AssignStateEnum.NONE:
                    self._remove_node(entry.index())

        # Then, update from the new previous cue row
        prev_sibling = cuerow.prev_sibling()
        if prev_sibling and prev_sibling.cue.type == "DcaChangeCue":
            changes = self._change_tuples_derive(prev_sibling)
            self._change_tuples_apply(cuerow, changes)

        # Finally, cascade changes.
        if cuerow.cue.type == "DcaResetCue":
            changes = self._change_tuples_clear(self._change_tuples_derive(cuerow.prev_sibling()))
        else:
            changes = self._change_tuples_derive(cuerow)
        self._change_tuples_cascade_apply(cuerow, changes)

    def remove_cuerow(self, cue):
        '''Removes the cue-row from the model'''
        cue.property_changed.disconnect(self.amend_cuerow)
        cuerow = self.find_cuerow(cue.id)

        # Update assign entries
        if cue.type == "DcaChangeCue":
            changes = self._change_tuples_invert(self._change_tuples_derive(cuerow))
        else:
            changes = self._change_tuples_derive(cuerow.prev_sibling())
        self._change_tuples_cascade_apply(cuerow, changes)

        # And remove the cuerow from the model
        self._remove_node(cuerow.index())

    def _change_tuples_apply(self, cuerow, changes):

        if cuerow.cue.type == "DcaResetCue":
            changes.clear()
            return

        for change in copy.copy(changes):
            block_node = cuerow.child(change[0])
            block_index = block_node.index()
            block_entry_values = block_node.getChildValues()

            if change[1] not in block_entry_values:
                if change[2] != AssignStateEnum.UNASSIGN:
                    new_entry = ModelsEntry(change[1], parent=block_node)
                    new_entry.setInherited(True)
                    self._add_node(block_index, new_entry)
            else:
                entry_node = block_node.child(block_entry_values.index(change[1]))
                if entry_node.assign_state() != AssignStateEnum.NONE:
                    changes.remove(change)
                    entry_node.setInherited(change[2] != AssignStateEnum.UNASSIGN)
                elif not change[2] or change[2] == AssignStateEnum.UNASSIGN:
                    self._remove_node(entry_node.index())

    def _change_tuples_cascade_apply(self, cuerow, changes):
        next_rownum = cuerow.rownum() + 1

        while changes and next_rownum < self.root.childCount():
            self._change_tuples_apply(self.root.child(next_rownum), changes)
            next_rownum += 1

    def _change_tuples_clear(self, old_changes):
        new_changes = []
        for change in old_changes:
            new_state = None
            if change[2] != AssignStateEnum.UNASSIGN:
                new_state = AssignStateEnum.UNASSIGN

            if new_state:
                new_changes.append((change[0],
                                    change[1],
                                    new_state))
        return new_changes

    def _change_tuples_derive(self, cuerow):
        changes = []
        if not cuerow or cuerow.cue.type == "DcaResetCue":
            return changes
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

    def find_cuerow(self, cue_id):
        '''Find and return the cue-row that matches the given cue-id'''
        for cuerow in self.root.children:
            if cuerow.cue.id == cue_id:
                return cuerow
        return None

    def _set_initial_assigns(self, cuerow, cue_defined_assigns, clear_first):
        # Set base add and remove assigns
        for dca_num, assign_actions in enumerate(cue_defined_assigns):
            block_node = cuerow.child(dca_num)
            block_index = block_node.index()

            if clear_first:
                self._clear_node(block_index)

            for entry in assign_actions['add']:
                self._add_node(block_index,
                               ModelsEntry(entry, AssignStateEnum.ASSIGN, parent=block_node))

            for entry in assign_actions['rem']:
                self._add_node(block_index,
                               ModelsEntry(entry, AssignStateEnum.UNASSIGN, parent=block_node))

        # Get inherits from previous cue row
        prev_sibling = cuerow.prev_sibling()
        if prev_sibling and prev_sibling.cue.type == "DcaChangeCue":
            changes = self._change_tuples_derive(prev_sibling)
            self._change_tuples_apply(cuerow, changes)
