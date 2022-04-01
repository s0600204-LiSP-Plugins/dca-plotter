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

# pylint: disable=missing-docstring, invalid-name, line-too-long

import logging

# pylint: disable=import-error
from lisp.plugins import get_plugin

# pylint: disable=relative-beyond-top-level
from ..model_primitives import AssignStateEnum, DcaModelTemplate, \
    ModelsAssignRow, ModelsEntry
from ..utilities import get_blank_dca_name

logger = logging.getLogger(__name__) # pylint: disable=invalid-name

class DcaCueModel(DcaModelTemplate):

    _inherits_enabled = False

    def __init__(self):
        super().__init__()

        self._add_node(self.createIndex(0, 0, self.root), ModelsAssignRow(parent=self.root))
        self._inherits_enabled = get_plugin('DcaPlotter').mapper_enabled()

    def deserialise(self, assign_changes, cue_id):
        if self._inherits_enabled:
            cuerow = get_plugin('DcaPlotter').mapper().find_cuerow(cue_id)

        for dca_num, dca_assign_actions in enumerate(assign_changes):
            dca_node = self.root.child(0).child(dca_num)

            # Set the Adds and Removes
            for action, channels in dca_assign_actions.items():
                if action == 'name':
                    dca_node.deserialiseName(channels)
                    continue

                assign_action = AssignStateEnum.UNASSIGN if action == 'rem' else AssignStateEnum.ASSIGN
                for channel_tuple in channels:
                    self._add_node(dca_node.index(), ModelsEntry(channel_tuple, assign_action, parent=dca_node))

        # Set the inheritance flags
        for dca_num, dca_node in enumerate(self.root.child(0).children):
            if self._inherits_enabled:
                previous_cuerow = cuerow.prev_sibling()
                if previous_cuerow:
                    if previous_cuerow.cue.type == "DcaChangeCue":
                        dca_node.setInherited(previous_cuerow.child(dca_num).data())
                    else:
                        dca_node.setInherited(get_blank_dca_name())

                for entry in cuerow.child(dca_num).children:
                    values = dca_node.getChildValues()
                    if entry.inherited():
                        if entry.value() in values:
                            dca_node.child(values.index(entry.value())).setInherited(True)
                        else:
                            new_entry = ModelsEntry(entry.value(), parent=dca_node)
                            new_entry.setInherited(True)
                            self._add_node(dca_node.index(), new_entry)

    def serialise(self):
        assigns = []
        for dca_node in self.root.child(0).children:
            add = []
            rem = []
            for entry in dca_node.children:
                if entry.assignState() == AssignStateEnum.ASSIGN:
                    add.append(entry.value())
                elif entry.assignState() == AssignStateEnum.UNASSIGN:
                    rem.append(entry.value())
            assigns.append({
                'name': dca_node.serialiseName(),
                'add': add,
                'rem': rem
            })
        return assigns

    def add_new_entry(self, dca_num, channel_tuple, assign_state):
        dca_node = self.root.child(0).child(dca_num)
        self._add_node(dca_node.index(), ModelsEntry(channel_tuple, assign_state, parent=dca_node))

    def inherits_enabled(self):
        return self._inherits_enabled

    def pin_entry(self, entry_index):
        # pylint: disable=no-self-use
        entry_node = entry_index.internalPointer()
        entry_node.setAssignState(AssignStateEnum.ASSIGN)

    def remove_entry(self, entry_index):
        entry_node = entry_index.internalPointer()
        if not entry_node.inherited():
            self._remove_node(entry_index)
        elif entry_node.assignState() == AssignStateEnum.NONE:
            entry_node.setAssignState(AssignStateEnum.UNASSIGN)
        else:
            entry_node.setAssignState(AssignStateEnum.NONE)

    def get_assignable_selection_choice(self, target_dca_num, intention):
        channel_tuples = get_plugin('DcaPlotter').assignables(['role', 'choir', 'input', 'fx'])

        for dca_num, dca_node in enumerate(self.root.child(0).children):
            for entry in dca_node.children:

                if entry.value() not in channel_tuples:
                    # If this is true, we have something assigned to more than one DCA.
                    # Warning the user about this is dealt with elsewhere.
                    continue

                # We filter any assigns/unassigns in the currently selected DCA block
                # If adding a new assign, we filter out any assigns explicit/implicit that are already in the current row.
                # If adding a new unassign, we filter out any unassigns already in the current row.
                if dca_num == target_dca_num or \
                    intention == AssignStateEnum.ASSIGN and entry.assignState() != AssignStateEnum.UNASSIGN or \
                    intention == AssignStateEnum.UNASSIGN and entry.assignState() == AssignStateEnum.UNASSIGN:
                    channel_tuples.remove(entry.value())

        return channel_tuples
