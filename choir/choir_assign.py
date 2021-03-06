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

# pylint: disable=no-name-in-module
from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QVBoxLayout, QWidget

# pylint: disable=import-error
from lisp.ui.qdelegates import LineEditDelegate
from lisp.ui.settings.pages import SettingsPage
from lisp.ui.ui_utils import translate

from ..config.concept_assign_model import GroupRow
from ..config.concept_assign_view import ConceptTreeView
from .choir_tree_model import ChoirAssignRow, ChoirTreeModel

class ChoirAssignUi(SettingsPage):
    '''Choir Groups Assign UI'''
    Name = translate("DcaPlotter", "Choir Assignment")

    # Keep this in sync with roles_tree_model.columns
    TreeColumns = [{
        'delegate': LineEditDelegate(max_length=16)
    }]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setLayout(QVBoxLayout())

        # Tree
        self.tree_model = ChoirTreeModel()
        self.tree_view = ChoirTreeView(self.tree_model, self.TreeColumns, parent=self)
        self.layout().addWidget(self.tree_view)

        # Buttons at bottom
        self.buttons_group = QWidget(self)
        self.buttons_group.setLayout(QHBoxLayout())
        self.layout().addWidget(self.buttons_group)

        self.button_add = QPushButton(self.buttons_group)
        self.button_add.setText("Add New Choir Grouping")
        self.button_add.clicked.connect(self.tree_view.addGroup)
        self.buttons_group.layout().addWidget(self.button_add)

        self.button_rem = QPushButton(self.buttons_group)
        self.button_rem.setText("Remove Choir Grouping")
        self.button_rem.clicked.connect(self.tree_view.removeGroup)
        self.buttons_group.layout().addWidget(self.button_rem)

    def getSettings(self):
        # pylint: disable=invalid-name
        '''Gets serialised data from model, ready for saving'''
        return {
            "choir": self.tree_model.serialise()
        }

    def loadSettings(self, settings):
        # pylint: disable=invalid-name
        '''Passes loaded data to model to deserialise'''
        if "choir" in settings:
            self.tree_model.deserialise(settings["choir"])


class ChoirTreeView(ConceptTreeView):

    def contextMenuEvent(self, event):
        indexes = self.selectedIndexes()
        if not indexes:
            super().contextMenuEvent(event)
            return

        current_index = indexes[0]
        current_node = current_index.internalPointer()
        self._menu.clear()

        if isinstance(current_node, ChoirAssignRow):
            self._create_menu_action('Remove Assignment', self._remove_from_group)

        elif isinstance(current_node, GroupRow):
            self._create_menu_action('Assign to Choir Grouping', self._assign_to_group)

        self._menu.popup(event.globalPos())
        super().contextMenuEvent(event)
