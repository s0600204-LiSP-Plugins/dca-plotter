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
from PyQt5.QtWidgets import QAction, QHBoxLayout, QMenu, QPushButton, QVBoxLayout, QWidget

# pylint: disable=import-error
from lisp.ui.qdelegates import LineEditDelegate
from lisp.ui.settings.pages import SettingsPage
from lisp.ui.ui_utils import translate

from midi_fixture_control.ui import LabelDelegate, RadioButtonHidableDelegate

from ..input_select_dialog import InputSelectDialog
from ..ui import SimpleTreeView
from .roles_tree_model import AssignRow, RoleRow, RolesTreeModel

class RolesAssignUi(SettingsPage):
    '''Parts Assign UI'''
    Name = translate("DcaPlotter", "Role Assignments")

    # Keep this in sync with roles_tree_model.columns
    TreeColumns = [{
        'delegate': LineEditDelegate(max_length=16)
    }, {
        'delegate': RadioButtonHidableDelegate(),
        'width': 64
    }]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setLayout(QVBoxLayout())

        # Tree
        self.tree_model = RolesTreeModel()
        self.tree_view = RolesTreeView(self.tree_model, self.TreeColumns, parent=self)
        self.layout().addWidget(self.tree_view)

        # Buttons at bottom
        self.buttons_group = QWidget(self)
        self.buttons_group.setLayout(QHBoxLayout())
        self.layout().addWidget(self.buttons_group)

        self.button_add = QPushButton(self.buttons_group)
        self.button_add.setText("Add New Role")
        self.button_add.clicked.connect(self.tree_view.addRole)
        self.buttons_group.layout().addWidget(self.button_add)

        self.button_rem = QPushButton(self.buttons_group)
        self.button_rem.setText("Remove Role")
        self.button_rem.clicked.connect(self.tree_view.removeRole)
        self.buttons_group.layout().addWidget(self.button_rem)

    def getSettings(self):
        # pylint: disable=invalid-name, missing-docstring
        return {}

    def loadSettings(self, settings):
        # pylint: disable=invalid-name, missing-docstring
        pass


class RolesTreeView(SimpleTreeView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._assign_select_dialog = InputSelectDialog(parent=self)
        self._menu = QMenu(self)

    def _assign_to_role(self):
        index = self.selectedIndexes()[0]
        node = index.internalPointer()

        selection_choices = self.model().get_assignable_selection_choice(index)
        self._assign_select_dialog.set_entries(selection_choices)

        if self._assign_select_dialog.exec_() == self._assign_select_dialog.Accepted:
            for channel_tuple in self._assign_select_dialog.selected_entries():
                self.model().addAssign(index, channel_tuple)

    def _create_menu_action(self, caption, slot):
        new_action = QAction(caption, parent=self._menu)
        new_action.triggered.connect(slot)
        self._menu.addAction(new_action)

    def _remove_from_role(self):
        index = self.selectedIndexes()[0]
        self.model().removeRow(index)

    def addRole(self):
        index = self.model().addRole("-")
        self.setExpanded(index, True)

    def contextMenuEvent(self, event):
        indexes = self.selectedIndexes()
        if not indexes:
            super().contextMenuEvent(event)
            return

        current_index = indexes[0]
        current_node = current_index.internalPointer()
        self._menu.clear()

        if isinstance(current_node, AssignRow):
            self._create_menu_action('Remove Assignment', self._remove_from_role)

        elif isinstance(current_node, RoleRow):
            self._create_menu_action('Assign to Role', self._assign_to_role)

        self._menu.popup(event.globalPos())
        super().contextMenuEvent(event)

    def removeRole(self):
        selected = self.selectedIndexes()
        if not selected or selected[0].internalPointer().parent() != self.model().root():
            return
        self.model().removeRow(selected[0])
