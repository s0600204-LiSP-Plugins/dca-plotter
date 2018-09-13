
import logging

from lisp.plugins import get_plugin
from lisp.plugins.dca_plotter.model_primitives import AssignStateEnum, DcaModelTemplate, ModelsAssignRow, ModelsEntry

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
            for action, nums in dca_assign_actions.items():
                assign_action = AssignStateEnum.UNASSIGN if action == 'rem' else AssignStateEnum.ASSIGN
                for mic_num in nums:
                    self._add_node(dca_node.index(), ModelsEntry(mic_num, assign_action, parent=dca_node))

        # Set the inheritance flags
        for dca_num, dca_node in enumerate(self.root.child(0).children):
            if self._inherits_enabled:
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
                if entry.assign_state() == AssignStateEnum.ASSIGN:
                    add.append(entry.value())
                elif entry.assign_state() == AssignStateEnum.UNASSIGN:
                    rem.append(entry.value())
            assigns.append({
                'add': add,
                'rem': rem
            })
        return assigns
