# -*- coding: utf-8 -*-
#
# This file is part of Linux Show Player
#
# Copyright 2012-2018 Francesco Ceruti <ceppofrancy@gmail.com>
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
                entry_num = block_node.getChildValues().index(change[1]['strip'])
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

    def calculate_diff_from_mapper(self, cue_id):
        cuerow = get_plugin('DcaPlotter').mapper().find_cuerow(cue_id)
        current_assigns = self.root.child(0).children

        cue_actions = []
        assign_changes = {}

        for dca_num, dca_node in enumerate(cuerow.children):
            if dca_node.data() and current_assigns[dca_num].data() != dca_node.data():
                cue_actions.append(_create_rename_action(dca_num, dca_node.data()))

            currently_assigned = current_assigns[dca_num].getChildValues()
            for entry in dca_node.children:
                if entry.value() not in currently_assigned:
                    if entry.assignState() != AssignStateEnum.UNASSIGN:
                        cue_actions.append(_create_assign_action(assign_changes,
                                                                 dca_num,
                                                                 entry.value()))
                elif entry.assignState() == AssignStateEnum.UNASSIGN:
                    cue_actions.append(_create_unassign_action(assign_changes,
                                                               dca_num,
                                                               entry.value()))

            cue_assigned = dca_node.getChildValues()
            for channel_tuple in currently_assigned:
                if channel_tuple not in cue_assigned:
                    cue_actions.append(_create_unassign_action(assign_changes,
                                                               dca_num,
                                                               channel_tuple))

        cue_actions.extend(_calculate_mutes(assign_changes))
        return cue_actions

    def calculate_diff(self, new_assigns):

        cue_actions = []
        current_assigns = self.root.child(0).children
        assign_changes = {}

        for dca_num, dca in enumerate(new_assigns):
            if dca['name'] and current_assigns[dca_num].data() != dca['name']:
                cue_actions.append(_create_rename_action(dca_num, dca['name']))

            for to_add in dca['add']:
                if to_add in current_assigns[dca_num].getChildValues():
                    continue
                cue_actions.append(_create_assign_action(assign_changes, dca_num, to_add))

            for to_rem in dca['rem']:
                if to_rem not in current_assigns[dca_num].getChildValues():
                    continue
                cue_actions.append(_create_unassign_action(assign_changes, dca_num, to_rem))

        cue_actions.extend(_calculate_mutes(assign_changes))
        return cue_actions

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

    messages = []
    for change in changes:
        command = ""
        args = {
            "channelType": change[1]['strip'][0],
            "channelNum": change[1]['strip'][1]
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
            args["arbitraryString"] = change[1]['name']

        messages.extend(profile.build_device_command(command, args))

    return messages
