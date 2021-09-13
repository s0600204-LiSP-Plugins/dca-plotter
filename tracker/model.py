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

# pylint: disable=missing-docstring, invalid-name

import logging

# pylint: disable=no-name-in-module
from PyQt5.QtCore import Qt

# pylint: disable=import-error
from lisp.application import Application
from lisp.plugins import get_plugin
from lisp.plugins.midi.midi_utils import midi_from_dict

# pylint: disable=relative-beyond-top-level
from ..cue.change_cue import DcaChangeCue
from ..model_primitives import AssignStateEnum, DcaModelTemplate, ModelsAssignRow, ModelsEntry

logger = logging.getLogger(__name__) # pylint: disable=invalid-name

# This model does not contain cues.
#
# Instead it tracks:
# * Currently muted mics
# * Which mics are currently assigned where
# * Current (last sent) names of dca channels
#
# We do not explicitly track mute-status, instead make the (reasonable) assumption
# that if an input is assigned to a DCA, then it must be unmuted, and vice versa.
#
# We have a potential race-condition in this model:
# * When a cue is called, it is done in its own thread.
# * When a cue is selected, it is done on the main thread.
# This means it possible for a new cue to be selected before the current one has finished running.
#
# This is expected: it prevents the UI from locking up whilst an audio cue (or some other
# long-running cue) is active.
#
# This model contains listeners (or in Qt's definition: 'slots') for both these events. And
# unfortunately, there is the rare but annoying occasion where the MIDI takes more time to be
# transmitted than it does for the UI to select the next cue.
#
# Thus, we have a problem: one of the slots modifies the model data that the other slot reads.
#
# To prevent this, we don't call the entirety of the second slot - just enough so that as the first
# slot finishes, it's aware it needs to call the second slot directly.
class DcaTrackingModel(DcaModelTemplate):

    _cached_changes = []
    _last_selected_cue_id = None
    _midi_out = None
    _predictive_row_enabled = False
    _cue_in_progress = False

    def __init__(self, show_predictive_row):
        super().__init__()
        self._midi_out = get_plugin('Midi').output

        # Current/Active Assigns
        self._add_node(self.createIndex(0, 0, self.root), ModelsAssignRow(parent=self.root))

        # Predicted assign changes (ListLayout only)
        if show_predictive_row:
            self._add_node(self.createIndex(1, 0, self.root), ModelsAssignRow(parent=self.root))
            self._predictive_row_enabled = True

    def call_cue(self, cue):
        self._cue_in_progress = True
        if self._cached_changes and cue.id == self._last_selected_cue_id:
            changes = self._cached_changes
        elif isinstance(cue, DcaChangeCue):
            if self._predictive_row_enabled:
                changes = self.calculate_diff_from_mapper(cue.id)
            else:
                changes = self.calculate_diff(cue.dca_changes)
        elif cue.properties().get('force_clear'):
            changes = self.cancel_everything(cue.new_dca_name)
        else:
            changes = self.cancel_current(cue.new_dca_name)

        # Here we have the MIDI sends...
        # Alternatively, as this is a *tracking* model, the diff change could be passed back
        #   and the calling cue handles sending the MIDI.
        # Then again, we don't want update the 'currently active' if sending fails... so...
        midi_messages = determine_midi_messages(changes)
        for dict_msg in midi_messages:
            self._midi_out.send(midi_from_dict(dict_msg))

        # Update the currently active
        current_assigns = self.root.child(0).children
        for change in changes:
            if change[0] == 'assign':
                block_node = current_assigns[change[1]['dca']]
                self._add_node(block_node.index(),
                               ModelsEntry(change[1]['strip'], parent=block_node))
            elif change[0] == 'unassign':
                block_node = current_assigns[change[1]['dca']]
                try:
                    entry_num = block_node.getChildValues().index(change[1]['strip'])
                except ValueError:
                    pass
                else:
                    entry_node = block_node.child(entry_num)
                    self._remove_node(entry_node.index())
            elif change[0] == 'rename':
                current_assigns[change[1]['dca']].setData(change[1]['name'], Qt.EditRole)
                if self._predictive_row_enabled:
                    self.root.child(1).children[change[1]['dca']].setInherited(change[1]['name'])

        self._cue_in_progress = False

        if self._predictive_row_enabled:
            # If the cue selection has changed whilst the cue was running,
            # or this is the last cue in the list, call the slot again
            cue_model = Application().cue_model
            cue_next = cue_model.get(self._last_selected_cue_id)
            if cue_next and (cue.id != self._last_selected_cue_id or cue_next.index + 1 == len(cue_model)):
                self.select_cue(cue_next)

    def clear_current_diff(self):
        '''Clears current diff state.'''
        next_assigns = self.root.child(1).children
        for block_node in next_assigns:
            self._clear_node(block_node.index())
            block_node.setData("", Qt.EditRole)

    def regenerate_current(self):
        cue_model = Application().cue_model
        cue_next = cue_model.get(self._last_selected_cue_id)
        if cue_next:
            self.select_cue(cue_next)

    def select_cue(self, cue):
        self._last_selected_cue_id = cue.id

        # If the cue is still processing, return.
        if self._cue_in_progress:
            return

        self.clear_current_diff()

        if isinstance(cue, DcaChangeCue):
            if self._predictive_row_enabled:
                self._cached_changes = self.calculate_diff_from_mapper(cue.id)
            else:
                self._cached_changes = self.calculate_diff(cue.dca_changes)
        elif cue.properties().get('force_clear'):
            self._cached_changes = self.cancel_everything(cue.new_dca_name)
        else:
            self._cached_changes = self.cancel_current(cue.new_dca_name)

        next_assigns = self.root.child(1).children
        for change in self._cached_changes:
            if change[0] == 'assign':
                block_node = next_assigns[change[1]['dca']]
                self._add_node(block_node.index(),
                               ModelsEntry(change[1]['strip'],
                                           AssignStateEnum.ASSIGN,
                                           parent=block_node))
            elif change[0] == 'unassign':
                block_node = next_assigns[change[1]['dca']]
                self._add_node(block_node.index(),
                               ModelsEntry(change[1]['strip'],
                                           AssignStateEnum.UNASSIGN,
                                           parent=block_node))
            elif change[0] == 'rename':
                block_node = next_assigns[change[1]['dca']]
                block_node.setData(change[1]['name'], Qt.EditRole)

    def on_cue_update(self, cue, property_name, _):
        if cue.id != self._last_selected_cue_id or property_name != 'dca_changes':
            return
        self.select_cue(cue)

    def cancel_current(self, new_name):
        cue_actions = []
        assign_changes = {}
        for dca_num, dca_node in enumerate(self.root.child(0).children):
            cue_actions.append(_create_rename_action(dca_num, new_name))
            for entry_node in dca_node.children:
                cue_actions.append(_create_unassign_action(assign_changes,
                                                           dca_num,
                                                           entry_node.value()))

        cue_actions.extend(_calculate_mutes(assign_changes))
        return cue_actions

    def cancel_everything(self, new_name):
        cue_actions = []
        assign_changes = {}

        for dca_num, dca_node in enumerate(self.root.child(0).children):
            cue_actions.append(_create_rename_action(dca_num, new_name))

            mic_count = len(get_plugin('DcaPlotter').SessionConfig['assigns']['input'])
            for num in range(1, mic_count + 1):
                cue_actions.append(_create_unassign_action(assign_changes,
                                                           dca_num,
                                                           ('input', num)))

            fx_count = len(get_plugin('DcaPlotter').SessionConfig['assigns']['fx'])
            for num in range(1, fx_count + 1):
                cue_actions.append(_create_unassign_action(assign_changes,
                                                           dca_num,
                                                           ('fx', num)))

        cue_actions.extend(_calculate_mutes(assign_changes))
        return cue_actions

    def calculate_diff_from_mapper(self, cue_id):
        cuerow = get_plugin('DcaPlotter').mapper().find_cuerow(cue_id)
        current_assigns = self.root.child(0).children

        cue_actions = []
        assign_changes = {}
        explicit_singular_assigns = []
        choirs = []

        # Create assigns if not already assigned and explicit unassigns for single-assignments.
        for dca_num, dca_node in enumerate(cuerow.children):

            choirs.append({})

            if dca_node.data() and current_assigns[dca_num].data() != dca_node.data():
                cue_actions.append(_create_rename_action(dca_num, dca_node.data()))

            currently_assigned = current_assigns[dca_num].getChildValues()
            for entry in dca_node.children:

                if entry.value()[0] == 'choir':
                    choirs[dca_num][entry.value()[1]] = entry.assignState()
                    continue

                if entry.assignState() != AssignStateEnum.UNASSIGN:
                    explicit_singular_assigns.append(entry.value())

                if entry.value() not in currently_assigned:
                    if entry.assignState() != AssignStateEnum.UNASSIGN:
                        cue_actions.append(_create_assign_action(assign_changes,
                                                                 dca_num,
                                                                 entry.value()))
                elif entry.assignState() == AssignStateEnum.UNASSIGN:
                    cue_actions.append(_create_unassign_action(assign_changes,
                                                               dca_num,
                                                               entry.value()))

        # Create assigns if not already assigned and explicit unassigns for the members
        # of group-assignments, so long as they aren't already assigned out-of-group.
        for dca_num, dca_node in enumerate(cuerow.children):

            currently_assigned = current_assigns[dca_num].getChildValues()
            assigned_by_cue = dca_node.getChildValues()

            for choir_id, assign_action in choirs[dca_num].items():
                assigns = get_plugin('DcaPlotter').resolve_choir(choir_id)
                for assign in assigns:
                    if assign in explicit_singular_assigns:
                        continue
                    assigned_by_cue.append(assign)

                    if assign not in currently_assigned:
                        if assign_action != AssignStateEnum.UNASSIGN:
                            cue_actions.append(_create_assign_action(assign_changes,
                                                                     dca_num,
                                                                     assign))
                    elif assign_action == AssignStateEnum.UNASSIGN:
                        cue_actions.append(_create_unassign_action(assign_changes,
                                                                   dca_num,
                                                                   assign))

            # Unassign things that shouldn't be assigned
            for channel_tuple in currently_assigned:
                if channel_tuple not in assigned_by_cue:
                    cue_actions.append(_create_unassign_action(assign_changes,
                                                               dca_num,
                                                               channel_tuple))

        cue_actions.extend(_calculate_mutes(assign_changes))
        return cue_actions

    def calculate_diff(self, new_assigns):
        cue_actions = []
        current_assigns = self.root.child(0).children
        assign_changes = {}
        full_assigned = []
        choirs = {'add': [], 'rem': []}

        for dca_num, dca in enumerate(new_assigns):
            if dca['name'] and current_assigns[dca_num].data() != dca['name']:
                cue_actions.append(_create_rename_action(dca_num, dca['name']))

            full_assigned.extend(current_assigns[dca_num].getChildValues())

            for to_add in dca['add']:
                if to_add[0] == 'choir':
                    choirs['add'].append((to_add[1], dca_num))
                    continue
                if to_add in current_assigns[dca_num].getChildValues():
                    continue
                if to_add in full_assigned:
                    for inner_dca_num in range(len(current_assigns)):
                        if to_add in current_assigns[inner_dca_num].getChildValues():
                            cue_actions.append(_create_unassign_action(assign_changes, inner_dca_num, to_add))
                else:
                    full_assigned.append(to_add)
                cue_actions.append(_create_assign_action(assign_changes, dca_num, to_add))

            for to_rem in dca['rem']:
                if to_rem[0] == 'choir':
                    choirs['rem'].append((to_rem[1], dca_num))
                    continue
                if to_rem not in current_assigns[dca_num].getChildValues():
                    continue
                full_assigned.remove(to_rem)
                cue_actions.append(_create_unassign_action(assign_changes, dca_num, to_rem))

        for choir_id, dca_num in choirs['add']:
            assigns = get_plugin('DcaPlotter').resolve_choir(choir_id)
            for assign in assigns:
                if assign in full_assigned:
                    continue
                cue_actions.append(_create_assign_action(assign_changes, dca_num, assign))

        for choir_id, dca_num in choirs['rem']:
            assigns = get_plugin('DcaPlotter').resolve_choir(choir_id)
            for assign in assigns:
                if assign not in current_assigns[dca_num].getChildValues():
                    continue
                cue_actions.append(_create_unassign_action(assign_changes, dca_num, assign))

        cue_actions.extend(_calculate_mutes(assign_changes))
        return cue_actions

    def role_assign_swap(self, role_id, old_assign, new_assign):
        '''Swaps from one assign to another within the same Role

        Note: this transmits MIDI immediately if a swap is needed
        '''
        role_tuple = ('role', role_id)
        actions = []
        changes = {}

        # Find current active use of Role, and prep assign change
        for dca_num, dca in enumerate(self.root.child(0).children):
            if role_tuple in dca.getChildValues():
                actions.append(_create_unassign_action(changes, dca_num, old_assign))
                actions.append(_create_assign_action(changes, dca_num, new_assign))

        # If the Role not currently active, then no assign change necessary
        if not changes:
            return
        actions.extend(_calculate_mutes(changes))

        # Transmit change
        midi_messages = determine_midi_messages(actions)
        for dict_msg in midi_messages:
            self._midi_out.send(midi_from_dict(dict_msg))

def _calculate_mutes(assign_changes):
    cue_actions = []
    for strip, state_change in assign_changes.items():
        if state_change == 1:
            cue_actions.append([
                'unmute', {
                    'strip': strip
                }])
        elif state_change == 0:
            cue_actions.append([
                'mute', {
                    'strip': strip
                }])
    return cue_actions

def _create_assign_action(assign_changes, dca_num, channel_tuple):
    _update_assign_changes(assign_changes, "assign", channel_tuple)
    return ['assign', {
        'strip': channel_tuple,
        'dca': dca_num
    }]

def _create_rename_action(dca_num, new_name):
    return ['rename', {
        'name': new_name,
        'strip': ('dca', dca_num + 1),
        'dca': dca_num
    }]

def _create_unassign_action(assign_changes, dca_num, channel_tuple):
    _update_assign_changes(assign_changes, "unassign", channel_tuple)
    return ['unassign', {
        'strip': channel_tuple,
        'dca': dca_num
    }]

def _update_assign_changes(assign_changes, action, channel_tuple):

    # Assign changes key:
    #   Not present = No action
    #   0 = Mute
    #   1 = UnMute
    #   -1 = No Action (Keep On - Assign moved from one DCA to another)

    if action == "assign":
        if channel_tuple not in assign_changes:
            assign_changes[channel_tuple] = 1
        elif assign_changes[channel_tuple] == 0:
            assign_changes[channel_tuple] = -1
    elif action == "unassign":
        if channel_tuple not in assign_changes:
            assign_changes[channel_tuple] = 0
        elif assign_changes[channel_tuple] == 1:
            assign_changes[channel_tuple] = -1

def determine_midi_messages(changes):
    midi_plugin_config = get_plugin('MidiFixtureControl').SessionConfig
    if not midi_plugin_config['dca_device']:
        logger.error("Please identify a device capable of remote VCA/DCA control.")
        return []

    profile = get_plugin('MidiFixtureControl').get_profile(midi_plugin_config['dca_device'])
    fx_variant = 'fx_return' if 'fx_return' in profile.parameter_values('mute')['channelType'] else 'fx'
    input_variant = 'input_mono' if 'input_mono' in profile.parameter_values('mute')['channelType'] else 'input'

    strip_assigns = get_plugin('DcaPlotter').SessionConfig['assigns']

    messages = []
    for change in changes:
        command = ""

        strip_type = change[1]['strip'][0]
        strip_number = change[1]['strip'][1]

        # Temporarily skip choir groupings
        if strip_type == 'choir':
            continue

        # Resolve Role aliasing
        if strip_type == 'role':
            role_assign = get_plugin('DcaPlotter').resolve_role(strip_number)
            if not role_assign:
                logger.warning("A role has just been used that does not have anything assigned to it.")
                continue
            strip_type = role_assign[0]
            strip_number = role_assign[1]

        if strip_type != 'dca':
            # Support e.g. Microphone 2 being actually Desk Channel 7
            strip_number = strip_assigns[strip_type][strip_number - 1]['in']

        channelType = strip_type
        if strip_type == 'fx':
            channelType = fx_variant
        elif strip_type == 'input':
            channelType = input_variant

        args = {
            "channelType": channelType,
            "channelNum": strip_number
        }

        if change[0] == 'assign' or change[0] == 'unassign':
            command = 'dcaAssign'
            args['assignAction'] = 'assign' if change[0] == 'assign' else 'unassign'
            args['dcaNum'] = change[1]['dca'] + 1

        elif change[0] == 'mute' or change[0] == "unmute":
            command = 'mute'
            args['muteAction'] = 'mute' if change[0] == 'mute' else 'unmute'

        elif change[0] == 'rename':
            command = 'setName'
            args["asciiString"] = change[1]['name']

        messages.extend(profile.build_command(command, args))

    return messages
