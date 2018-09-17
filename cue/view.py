
from PyQt5.QtWidgets import QAction, QMenu

from lisp.plugins.dca_plotter.input_select_dialog import InputSelectDialog
from lisp.plugins.dca_plotter.modelview_abstract import DcaModelViewTemplate
from lisp.plugins.dca_plotter.model_primitives import AssignStateEnum, ModelsBlock, ModelsEntry

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

    def _add_new_assign_entry(self):
        selected_index = self.selectedIndexes()[0]
        selected_node = selected_index.internalPointer()

        selection_choices = self.model().get_input_selection_choice(0, selected_node.rownum(), AssignStateEnum.ASSIGN)
        self._input_select_dialog.set_entries(selection_choices)

        if self._input_select_dialog.exec_() == self._input_select_dialog.Accepted:
            for mic_num in self._input_select_dialog.selected_entries():
                self.model().add_new_entry(selected_node.rownum(), mic_num, AssignStateEnum.ASSIGN)

    def _add_new_unassign_entry(self):
        selected_index = self.selectedIndexes()[0]
        selected_node = selected_index.internalPointer()

        selection_choices = self.model().get_input_selection_choice(0, selected_node.rownum(), AssignStateEnum.UNASSIGN)
        self._input_select_dialog.set_entries(selection_choices)

        if self._input_select_dialog.exec_() == self._input_select_dialog.Accepted:
            for mic_num in self._input_select_dialog.selected_entries():
                self.model().add_new_entry(selected_node.rownum(), mic_num, AssignStateEnum.UNASSIGN)

    def _remove_entry(self):
        for entry_index in self.selectedIndexes():
            self.model().remove_entry(entry_index)

    def _pin_entry(self):
        for entry_index in self.selectedIndexes():
            self.model().pin_entry(entry_index)
