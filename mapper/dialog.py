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
from PyQt5.QtWidgets import QDialog, QVBoxLayout

from lisp.plugins import get_plugin

from .view import DcaMappingView

class DcaMappingDialog(QDialog):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.setWindowTitle('DCA Mapping')
        self.setMinimumSize(1080, 800)
        self.setLayout(QVBoxLayout())

        self.model = get_plugin('DcaPlotter').mapper()

        self.view = DcaMappingView()
        self.view.setModel(self.model)
        self.layout().addWidget(self.view)
