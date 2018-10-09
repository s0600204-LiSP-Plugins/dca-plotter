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

# pylint: disable=no-name-in-module
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAbstractItemView

from lisp.plugins import get_plugin

# pylint: disable=relative-beyond-top-level
from ..modelview_abstract import DcaModelViewTemplate

class DcaTrackingView(DcaModelViewTemplate):

    def __init__(self, **kwargs):
        super().__init__("QTableView", **kwargs)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setFocusPolicy(Qt.NoFocus)
        self.setSelectionMode(QAbstractItemView.NoSelection)
        get_plugin('DcaPlotter').initialised.connect(self._post_init_set_model)

    def _post_init_set_model(self):
        self.setModel(get_plugin('DcaPlotter').tracker())

    def _recalculate_cell_size(self):
        super()._recalculate_cell_size()

        if self.maximumHeight() != self._ideal_height:
            self.setMaximumHeight(self._ideal_height)
            self.setMinimumHeight(self._ideal_height)
