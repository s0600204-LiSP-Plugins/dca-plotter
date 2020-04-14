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
from PyQt5.QtWidgets import QDialog, QVBoxLayout

# pylint: disable=import-error
from lisp.plugins import get_plugin

# pylint: disable=relative-beyond-top-level
from .view import DcaMappingView

class DcaMappingDialog(QDialog):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.setWindowTitle('DCA Mapping')
        self.setMinimumSize(1280, 800)
        self.setLayout(QVBoxLayout())

        self.model = get_plugin('DcaPlotter').mapper()

        self.view = DcaMappingView()
        self.view.setModel(self.model)
        self.layout().addWidget(self.view)
