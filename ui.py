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
from PyQt5.QtWidgets import QHeaderView, QTreeView

class SimpleTreeView(QTreeView):
    # pylint: disable=too-few-public-methods
    """Simple implementation of a QTreeView"""

    def __init__(self, model, columns, **kwargs):
        super().__init__(**kwargs)

        self.setAllColumnsShowFocus(True)
        self.setUniformRowHeights(True)

        self.header().setSectionResizeMode(QHeaderView.Fixed)
        self.header().setStretchLastSection(False)
        self.header().setSectionsMovable(False)

        self.setModel(model)

        self.columns = columns
        for col_idx, col_spec in enumerate(self.columns):
            if col_spec is None:
                self.setColumnHidden(col_idx, True)
                continue

            self.setItemDelegateForColumn(col_idx, col_spec['delegate'])

            if 'width' in col_spec:
                self.header().resizeSection(col_idx, col_spec['width'])
            else:
                self.header().setSectionResizeMode(col_idx, QHeaderView.Stretch)
