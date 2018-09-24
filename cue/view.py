
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAction, QMenu

from lisp.plugins.dca_plotter.input_select_dialog import InputSelectDialog
from lisp.plugins.dca_plotter.modelview_abstract import DcaModelViewTemplate
from lisp.plugins.dca_plotter.model_primitives import AssignStateEnum, ModelsBlock, ModelsEntry
from lisp.plugins.dca_plotter.utilities import get_mic_name

class DcaCueView(DcaModelViewTemplate):

    def __init__(self, **kwargs):
        super().__init__("QTableView", **kwargs)
        self._menu = QMenu(self)
        self._input_select_dialog = InputSelectDialog(parent=self)

    def contextMenuEvent(self, event):
        # For now, we can only select one item at a time. This makes this code easier.
        # To be able to select multiple items, rewrite the following code to handle it,
        #    then remove or change the `.setSelectionMode()` line in the parent class.
        indexes = self.selectedIndexes()
        if not indexes:
            super().contextMenuEvent(event)
            return

        current_index = indexes[0]
        current_node = current_index.internalPointer()
        self._menu.clear()

        if isinstance(current_node, ModelsBlock):
            self._create_menu_action('New Assign', self._add_new_assign_entry)
            if not self.model().inherits_enabled():
                self._create_menu_action('New Unassign', self._add_new_unassign_entry)

        elif isinstance(current_node, ModelsEntry):
            if current_node.assign_state() == AssignStateEnum.NONE:
                self._create_menu_action('Pin', self._pin_entry)

            '''
            if ASSIGN and !inherited   => remove
            if ASSIGN and inherited    => unpin
            if inherited               => unassign
            if UNASSIGN and !inherited => remove
            if UNASSIGN and inherited  => restore
            '''
            caption = 'Remove'
            if current_node.inherited():
                if current_node.assign_state() == AssignStateEnum.ASSIGN:
                    caption = 'Unpin'
                elif current_node.assign_state() == AssignStateEnum.UNASSIGN:
                    caption = 'Restore'
                else:
                    caption = 'Unassign'
            self._create_menu_action(caption, self._remove_entry)

        self._menu.popup(event.globalPos())
        super().contextMenuEvent(event)

    def _create_menu_action(self, caption, slot):
        new_action = QAction(caption, parent=self._menu)
        new_action.triggered.connect(slot)
        self._menu.addAction(new_action)

    def updateGeometries(self):
        self.horizontalScrollBar().setRange(0, max(0, self._ideal_width - self.viewport().width()))

    def _auto_name(self, dca_num):
        dca_node = self.model().root.child(0).child(dca_num)

        assigns = []
        for entry in dca_node.children:
            if entry.assign_state() != AssignStateEnum.UNASSIGN:
                assigns.append(entry.value())

        # If there's no name explicitly given to the dca, and only one assign/inherit entry,
        #   then set the name of the dca to the name of that assign.
        if dca_node.inherited() and len(assigns) == 1:
            dca_node.setData(get_mic_name(assigns[0]), Qt.EditRole)

        # In no assign or inherit entries remaining in a block, clear the name
        elif not assigns:
            dca_node.setData(None, Qt.EditRole)

    def _add_new_assign_entry(self):
        selected_index = self.selectedIndexes()[0]
        selected_node = selected_index.internalPointer()

        selection_choices = self.model().get_input_selection_choice(0, selected_node.rownum(), AssignStateEnum.ASSIGN)
        self._input_select_dialog.set_entries(selection_choices)

        if self._input_select_dialog.exec_() == self._input_select_dialog.Accepted:
            for mic_num in self._input_select_dialog.selected_entries():
                self.model().add_new_entry(selected_node.rownum(), mic_num, AssignStateEnum.ASSIGN)

            self._auto_name(selected_node.rownum())

    def _add_new_unassign_entry(self):
        selected_index = self.selectedIndexes()[0]
        selected_node = selected_index.internalPointer()

        selection_choices = self.model().get_input_selection_choice(0, selected_node.rownum(), AssignStateEnum.UNASSIGN)
        self._input_select_dialog.set_entries(selection_choices)

        if self._input_select_dialog.exec_() == self._input_select_dialog.Accepted:
            for mic_num in self._input_select_dialog.selected_entries():
                self.model().add_new_entry(selected_node.rownum(), mic_num, AssignStateEnum.UNASSIGN)

    def _remove_entry(self):
        parents = []
        for entry_index in self.selectedIndexes():
            if entry_index.parent() not in parents:
                parents.append(entry_index.parent())
            self.model().remove_entry(entry_index)

        for parent in parents:
            self._auto_name(parent.internalPointer().rownum())

    def _pin_entry(self):
        for entry_index in self.selectedIndexes():
            self.model().pin_entry(entry_index)
