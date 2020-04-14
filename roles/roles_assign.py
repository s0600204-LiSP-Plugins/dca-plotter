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
from PyQt5.QtWidgets import QPushButton, QHBoxLayout, QVBoxLayout, QWidget

# pylint: disable=import-error
from lisp.ui.qdelegates import LineEditDelegate
from lisp.ui.settings.pages import SettingsPage
from lisp.ui.ui_utils import translate

from midi_fixture_control.ui import RadioButtonDelegate

from ..ui import SimpleTreeView
from .roles_tree_model import RolesTreeModel

class RolesAssignUi(SettingsPage):
    '''Parts Assign UI'''
    Name = translate("DcaPlotter", "Role Assignments")

    # Keep this in sync with roles_tree_model.columns
    TreeColumns = [None, {
        'delegate': LineEditDelegate(max_length=16)
    }, {
        'delegate': RadioButtonDelegate(),
        'width': 64
    }]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setLayout(QVBoxLayout())

        # Tree
        self.tree_model = RolesTreeModel()
        self.tree_view = SimpleTreeView(self.tree_model, self.TreeColumns, parent=self)
        self.layout().addWidget(self.tree_view)

        # Buttons at bottom
        self.buttons_group = QWidget(self)
        self.buttons_group.setLayout(QHBoxLayout())
        self.layout().addWidget(self.buttons_group)

        self.button_add = QPushButton(self.buttons_group)
        self.button_add.setText("Add New Role")
        self.buttons_group.layout().addWidget(self.button_add)

        self.button_rem = QPushButton(self.buttons_group)
        self.button_rem.setText("Remove Role")
        self.buttons_group.layout().addWidget(self.button_rem)

    def getSettings(self):
        # pylint: disable=invalid-name, missing-docstring
        return {}

    def loadSettings(self, settings):
        # pylint: disable=invalid-name, missing-docstring
        pass
