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

# pylint: disable=missing-docstring, invalid-name

# pylint: disable=no-name-in-module
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QVBoxLayout

# pylint: disable=import-error
from lisp.plugins import get_plugin

# pylint: disable=relative-beyond-top-level
from .view import DcaMappingView

class DcaMappingDialog(QDialog):

    def __init__(self, view_model, **kwargs):
        super().__init__(**kwargs)

        self.setWindowTitle('DCA Mapping')
        self.setMinimumSize(1280, 800)
        self.setSizeGripEnabled(True)
        self.setLayout(QVBoxLayout())

        # Set flags so we get the min & max buttons
        # (and so they actually function)
        flags = self.windowFlags()
        flags ^= Qt.Dialog
        flags |= Qt.WindowMinMaxButtonsHint
        self.setWindowFlags(flags)

        self.view = DcaMappingView()
        self.view.setModel(view_model)
        self.layout().addWidget(self.view)

    def setModel(self, model):
        self.view.setModel(model)
