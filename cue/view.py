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

# pylint: disable=no-name-in-module
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAction, QMenu

# pylint: disable=relative-beyond-top-level
from ..input_select_dialog import InputSelectDialog
from ..modelview_abstract import DcaModelViewTemplate
from ..model_primitives import AssignStateEnum, ModelsBlock, ModelsEntry
from ..utilities import get_channel_name

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
            if current_node.assignState() == AssignStateEnum.NONE:
                self._create_menu_action('Pin', self._pin_entry)

            # pylint: disable=pointless-string-statement
            ''' Logic:
            if ASSIGN and !inherited   => remove
            if ASSIGN and inherited    => unpin
            if inherited               => unassign
            if UNASSIGN and !inherited => remove
            if UNASSIGN and inherited  => restore
            '''
            caption = 'Remove'
            if current_node.inherited():
                if current_node.assignState() == AssignStateEnum.ASSIGN:
                    caption = 'Unpin'
                elif current_node.assignState() == AssignStateEnum.UNASSIGN:
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
            if entry.assignState() != AssignStateEnum.UNASSIGN:
                assigns.append(entry.value())

        # If there's no name explicitly given to the dca, and only one assign/inherit entry,
        #   then set the name of the dca to the name of that assign.
        if dca_node.inherited() and len(assigns) == 1:
            dca_node.setData(get_channel_name(assigns[0]), Qt.EditRole)

        # In no assign or inherit entries remaining in a block, clear the name
        elif not assigns:
            dca_node.setData(None, Qt.EditRole)

    def _add_new_assign_entry(self):
        selected_index = self.selectedIndexes()[0]
        selected_node = selected_index.internalPointer()

        selection_choices = self.model().get_input_selection_choice(0,
                                                                    selected_node.rownum(),
                                                                    AssignStateEnum.ASSIGN)
        self._input_select_dialog.set_entries(selection_choices)

        if self._input_select_dialog.exec_() == self._input_select_dialog.Accepted:
            for channel_tuple in self._input_select_dialog.selected_entries():
                self.model().add_new_entry(selected_node.rownum(),
                                           channel_tuple,
                                           AssignStateEnum.ASSIGN)

            self._auto_name(selected_node.rownum())

    def _add_new_unassign_entry(self):
        selected_index = self.selectedIndexes()[0]
        selected_node = selected_index.internalPointer()

        selection_choices = self.model().get_input_selection_choice(0,
                                                                    selected_node.rownum(),
                                                                    AssignStateEnum.UNASSIGN)
        self._input_select_dialog.set_entries(selection_choices)

        if self._input_select_dialog.exec_() == self._input_select_dialog.Accepted:
            for channel_tuple in self._input_select_dialog.selected_entries():
                self.model().add_new_entry(selected_node.rownum(),
                                           channel_tuple,
                                           AssignStateEnum.UNASSIGN)

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
