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

# pylint: disable=missing-docstring

"""Dialog allowing for selection of multiple microphones, for assigning to a DCA"""

# pylint: disable=no-name-in-module
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAbstractItemView, QDialog, QDialogButtonBox, QLabel, \
    QListWidget, QListWidgetItem, QVBoxLayout

from .utilities import get_channel_assignment_name, get_channel_group_name

DataRole = Qt.UserRole + 1 # pylint: disable=invalid-name

class InputSelectDialog(QDialog):
    """Dialog allowing for selection of multiple microphones, for assigning to a DCA"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.setWindowTitle('Assignment Selection')
        self.setMinimumSize(300, 400)

        self.setLayout(QVBoxLayout())

        self.label = QLabel(self)
        self.label.setText('Select what to assign...')
        font = self.label.font()
        font.setBold(True)
        self.label.setFont(font)
        self.layout().addWidget(self.label)

        self.list = QListWidget(self)
        self.list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.layout().addWidget(self.list)

        self.buttons = QDialogButtonBox(self)
        self.buttons.addButton(QDialogButtonBox.Cancel)
        self.buttons.addButton(QDialogButtonBox.Ok)
        self.layout().addWidget(self.buttons)

        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

    def _create_list_header(self, channel_type):
        header = QListWidgetItem()
        header.setText(get_channel_group_name(channel_type))
        header.setFlags(Qt.NoItemFlags)
        font = header.font()
        font.setBold(True)
        header.setFont(font)
        return header

    def _create_list_item(self, channel_tuple):
        item = QListWidgetItem()
        item.setText(get_channel_assignment_name(channel_tuple))
        item.setData(DataRole, channel_tuple)
        return item

    def set_entries(self, entries):
        """Set the entries that should appear in the dialog, auto-grouping by type."""
        self.list.clear()

        groupings = {}
        for channel_tuple in entries:
            if channel_tuple[0] not in groupings:
                groupings[channel_tuple[0]] = []
            groupings[channel_tuple[0]].append(channel_tuple)

        for group_type, group_entries in groupings.items():
            self.list.addItem(self._create_list_header(group_type))
            for channel_tuple in group_entries:
                self.list.addItem(self._create_list_item(channel_tuple))

    def selected_entries(self):
        """Returns the user-selected entries"""
        items = []
        for item in self.list.selectedItems():
            items.append(item.data(DataRole))
        return items
