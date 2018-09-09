
import logging
from lisp.plugins import get_plugin

logger = logging.getLogger(__name__) # pylint: disable=invalid-name

# This model does not contain cues.
#
# Instead it tracks:
# * Currently muted mics
# * Which mics are currently assigned where
# * Current (last sent) names of dca channels
#
# For a view of all the dca assign and reset cues, a filtered model-view of CueModel should be sufficient
# ... or not
#
# We do not explicitly track mute-status, instead make the (reasonable) assumption
# that if an input is assigned to a DCA, then it must be unmuted, and vice versa.
class DcaTrackingModel():

    def __init__(self):
        #super().__init__()
        self.current_active = []
        #self.current_names = [] # Coming in a future update ...
        self._midi_out = get_plugin('Midi').output

    def call_cue(self, new_assigns):
        # In "List" layout, we would already have this pre-calculated.
        # In "Cart" layout, we do this here.
        # However, at this point in development, we don't pre-calculate,
        #   instead doing it every time.
        changes = self.calculate_diff(new_assigns)
        
        # Here we have the MIDI sends...
        # Alternatively, as this is a *tracking* model, the diff change could be passed back
        #   and the calling cue handles sending the MIDI.
        # Then again, we don't want update the 'currently active' if sending fails... so...
        midi_messages = self.determine_midi_messages(changes)
        for dict_msg in midi_messages:
             self._midi_out.send_from_dict(dict_msg)

        # Update the currently active
        for change in changes:
            if change[0] == 'assign':
                self.current_active[change[1]['dca']].append(change[1]['strip'][1])
            elif change[0] == 'unassign':
                self.current_active[change[1]['dca']].remove(change[1]['strip'][1])
            elif change[0] == 'rename':
                self.current_names[change[1]['strip'][1]] = change[1]['name']

        # Until I build a proper UI:
        logger.info("Updated DCA arrangement: " + repr(self.current_active))

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

        # Not present - No action
        # 0 = Mute
        # 1 = UnMute
        # -1 = No Action (Keep On - Assign moved from one DCA to another)
        assign_changes = {}

        dca_num = 0
        for dca in new_assigns:
            for to_add in dca['add']:
                if to_add in self.current_active[dca_num]:
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
                if to_rem not in self.current_active[dca_num]:
                    continue
                cue_actions.append(['unassign', {
                        'strip': ['input', to_rem],
                        'dca': dca_num
                    }])
                if to_rem not in assign_changes:
                    assign_changes[to_rem] = 0
                elif assign_changes[to_rem] == 1:
                    assign_changes[to_rem] = -1

            dca_num += 1

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
