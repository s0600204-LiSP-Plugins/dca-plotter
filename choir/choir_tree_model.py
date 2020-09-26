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
from PyQt5.QtCore import Qt

# pylint: disable=import-error
from lisp.ui.ui_utils import translate

from ..config.concept_assign_model import BaseRow, ConceptTreeModel, GroupRow
from ..utilities import get_channel_assignment_name


COLUMNS = ({
    'id': 'choir_name',
    'label': translate('DcaPlotterSettings', 'Choir Part & Assignments'),
},)


class ChoirAssignRow(BaseRow):
    def __init__(self, channel_tuple, **kwargs):
        super().__init__(**kwargs)
        self._channel = channel_tuple

    def data(self, col, role=Qt.DisplayRole):
        # pylint: disable=missing-docstring
        if col == -1 and role == ConceptTreeModel.AccessRole:
            return self._channel

        if col == 0 and role == Qt.DisplayRole:
            return get_channel_assignment_name(self._channel)

        return super().data(col, role)

    def flags(self, col):
        # pylint: disable=missing-docstring
        flags = Qt.ItemNeverHasChildren | Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if col == 0:
            return flags
        return super().flags(col)

    def setData(self, *_):
        # pylint: disable=invalid-name, missing-docstring, no-self-use
        return False


class ChoirTreeModel(ConceptTreeModel):

    def __init__(self):
        super().__init__('choir#{0}', COLUMNS, ChoirAssignRow, ['input'], False)

    def deserialise(self, data):
        if self._root.childCount():
            logger.error('Attempting to deserialise out of sequence.')
            return

        for group_id, group in data.items():
            group_row = GroupRow(group_id, group['name'], parent=self._root)
            self._root.addChild(group_row)
            self._group_count = max(self._group_count, int(group_id.split('#')[1]))

            for assign in group['assigns']:
                assign_row = ChoirAssignRow(tuple(assign), parent=group_row)
                group_row.addChild(assign_row)

        self._group_count += 1

    def serialise(self):
        '''Serialises the role assignment data, ready for saving to file.'''
        data = {}
        for group_row in self._root.children():
            group = {
                'name': group_row.data(0, Qt.EditRole),
                'assigns': [],
            }
            for assign_row in group_row.children():
                group['assigns'].append(assign_row.data(-1, self.AccessRole))

            group_id = group_row.data(-1, self.AccessRole)
            data[group_id] = group

        return data
