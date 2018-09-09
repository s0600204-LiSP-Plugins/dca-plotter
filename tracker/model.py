
import logging

from lisp.plugins import get_plugin
from lisp.plugins.dca_plotter.model_primitives import DcaModelTemplate, ModelsRow, ModelsEntry

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
class DcaTrackingModel(DcaModelTemplate):

    _midi_out = None

    def __init__(self, show_go_row):
        super().__init__()
        self._midi_out = get_plugin('Midi').output

        # Current/Active Assigns
        self._add_node(self.createIndex(0, 0, self.root), ModelsRow(parent=self.root))

        # Next 'Go' (ListLayout only)
        if show_go_row:
            self._add_node(self.createIndex(1, 0, self.root), ModelsRow(parent=self.root))

    def call_cue(self, cue):
        # In "List" layout, we would already have this pre-calculated.
        # In "Cart" layout, we do this here.
        # However, at this point in development, we don't pre-calculate,
        #   instead doing it every time.
        changes = self.calculate_diff(cue.dca_changes)

        # Here we have the MIDI sends...
        # Alternatively, as this is a *tracking* model, the diff change could be passed back
        #   and the calling cue handles sending the MIDI.
        # Then again, we don't want update the 'currently active' if sending fails... so...
        midi_messages = self.determine_midi_messages(changes)
        for dict_msg in midi_messages:
             self._midi_out.send_from_dict(dict_msg)

        # Update the currently active
        current_assigns = self.root.child(0).children
        for change in changes:
            if change[0] == 'assign':
                block_node = current_assigns[change[1]['dca']]
                self._add_node(block_node.index(),
                               ModelsEntry(change[1]['strip'][1], parent=block_node))
            elif change[0] == 'unassign':
                block_node = current_assigns[change[1]['dca']]
                entry_num = block_node.getChildValues().index(change[1]['strip'][1])
                entry_node = block_node.child(entry_num)
                self._remove_node(entry_node.index())

    def determine_midi_messages(self, changes):
        midi_plugin_config = get_plugin('MidiFixtureControl').SessionConfig
        if not midi_plugin_config['dca_device']:
            logger.error("Please identify a device capable of remote VCA/DCA control.")
            return []

        library = get_plugin('MidiFixtureControl').get_library()

        patch_details = None
        for patch in midi_plugin_config['patches']:
            if patch['patch_id'] == midi_plugin_config['dca_device']:
                patch_details = patch
                break
        
        messages = []
        for change in changes:
            action = ""
            args = {
                "channelType": change[1]['strip'][0],
                "channelNum": change[1]['strip'][1]
            }

            if change[0] == 'assign' or change[0] == 'unassign':
                action = "dcaAssign" if change[0] == 'assign' else "dcaUnAssign"
                args['dcaNum'] = change[1]['dca'] + 1

            elif change[0] == 'mute' or change[0] == "unmute":
                action = "mute" if change[0] == 'mute' else "unmute"

            elif change[0] == 'rename':
                action = "setName"
                args["arbitraryString"] = change[1]['name']

            messages.extend(library.build_device_command(patch_details['fixture_id'],
                                                         patch_details['midi_channel'],
                                                         action,
                                                         args))

        return messages

    def calculate_diff(self, new_assigns):

        cue_actions = []
        current_assigns = self.root.child(0).children

        # Not present - No action
        # 0 = Mute
        # 1 = UnMute
        # -1 = No Action (Keep On - Assign moved from one DCA to another)
        assign_changes = {}

        for dca_num, dca in enumerate(new_assigns):
            for to_add in dca['add']:
                if to_add in current_assigns[dca_num].getChildValues():
                    continue
                cue_actions.append(['assign', {
                        'strip': ['input', to_add],
                        'dca': dca_num
                    }])
                if to_add not in assign_changes:
                    assign_changes[to_add] = 1
                elif assign_changes[to_add] == 0:
                    assign_changes[to_add] = -1

            for to_rem in dca['rem']:
                if to_rem not in current_assigns[dca_num].getChildValues():
                    continue
                cue_actions.append(['unassign', {
                        'strip': ['input', to_rem],
                        'dca': dca_num
                    }])
                if to_rem not in assign_changes:
                    assign_changes[to_rem] = 0
                elif assign_changes[to_rem] == 1:
                    assign_changes[to_rem] = -1

        for mic_num, state_change in assign_changes.items():
            if state_change == 1:
                cue_actions.append([
                    'unmute', {
                        'strip': ['input', mic_num]
                    }])
            elif state_change == 0:
                cue_actions.append([
                    'mute', {
                        'strip': ['input', mic_num]
                    }])

        return cue_actions
