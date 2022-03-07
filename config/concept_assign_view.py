# This file is a derivation of work on - and as such shares the same
# licence as - Linux Show Player
#
# Linux Show Player:
#   Copyright 2012-2020 Francesco Ceruti <ceppofrancy@gmail.com>
#
# This file:
#   Copyright 2020 s0600204
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

# pylint: disable=no-name-in-module
from PyQt5.QtWidgets import QAction, QMenu

from ..input_select_dialog import InputSelectDialog
from ..ui import SimpleTreeView

class ConceptTreeView(SimpleTreeView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._assign_select_dialog = InputSelectDialog(parent=self)
        self._menu = QMenu(self)

    def _assign_to_group(self):
        index = self.selectedIndexes()[0]

        selection_choices = self.model().get_assignable_selection_choice(index)
        self._assign_select_dialog.set_entries(selection_choices)

        if self._assign_select_dialog.exec_() == self._assign_select_dialog.Accepted:
            for channel_tuple in self._assign_select_dialog.selected_entries():
                self.model().addAssign(index, channel_tuple)

    def _create_menu_action(self, caption, slot):
        new_action = QAction(caption, parent=self._menu)
        new_action.triggered.connect(slot)
        self._menu.addAction(new_action)

    def _remove_from_group(self):
        index = self.selectedIndexes()[0]
        self.model().removeRow(index)

    def addGroup(self):
        index = self.model().addGroup("-")
        self.setExpanded(index, True)

    def removeGroup(self):
        selected = self.selectedIndexes()
        if not selected or selected[0].internalPointer().parent() != self.model().root():
            return
        self.model().removeRow(selected[0])
