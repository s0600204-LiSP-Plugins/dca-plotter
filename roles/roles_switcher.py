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
from PyQt5.Qt import QSizePolicy
from PyQt5.QtWidgets import QDialog, QVBoxLayout

from lisp.plugins import get_plugin
from lisp.ui.ui_utils import translate

from .roles_switcher_model import RolesSwitcherModel
from .roles_switcher_view import RolesSwitcherView

class RolesSwitcher(QDialog):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle(translate('dca_plotter', 'Role Switcher'))
        self.setMinimumSize(200, 600)
        self.setSizePolicy(self.sizePolicy().horizontalPolicy(), QSizePolicy.Minimum)
        self.setLayout(QVBoxLayout())

        self._model = RolesSwitcherModel()
        self._model.renew(get_plugin('DcaPlotter').SessionConfig)

        self._view = RolesSwitcherView(parent=self)
        self._view.setModel(self._model)
        self.layout().addWidget(self._view)

    def current(self, role_id):
        return self._model.current(role_id)

    def renew(self):
        self._model.renew(get_plugin('DcaPlotter').SessionConfig)
