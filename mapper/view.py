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

# pylint: disable=missing-docstring, invalid-name

from math import trunc

# pylint: disable=no-name-in-module
from PyQt5.QtWidgets import QAbstractItemView

# pylint: disable=relative-beyond-top-level
from ..modelview_abstract import DcaModelViewTemplate

class DcaMappingView(DcaModelViewTemplate):

    DRAW_CUEHEADER = True

    def __init__(self, **kwargs):
        super().__init__("QTreeView", **kwargs)

        # Temporarily disable selections and editing for this view.
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.NoSelection)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)

    def updateGeometries(self):
        self.verticalScrollBar().setRange(0, max(0, self._ideal_height - self.viewport().height()))
        self.verticalScrollBar().setSingleStep(trunc(self._fontmetrics.height() / 3))
        self.verticalScrollBar().setPageStep(self.viewport().height())

    def verticalOffset(self):
        return self.verticalScrollBar().value()
