# This file is a derivation of work on - and as such shares the same
# licence as - Linux Show Player
#
# Linux Show Player:
#   Copyright 2012-2022 Francesco Ceruti <ceppofrancy@gmail.com>
#
# This file:
#   Copyright 2022 s0600204
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
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QSizePolicy,
    QVBoxLayout,
)


class FloatingTrackerDialog(QDialog):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.setWindowTitle('Current DCA Assignments')
        self.setMinimumSize(1024, 0)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.resize(0, 0)
        self.setWindowFlags(Qt.Tool)

        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(4, 4, 4, 4)

    def reject(self):
        # Don't close the dialog
        pass
