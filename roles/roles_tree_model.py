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

# pylint: disable=no-name-in-module
from PyQt5.QtCore import Qt

# pylint: disable=import-error
from lisp.ui.ui_utils import translate

from ..config.concept_assign_model import BaseRow, ConceptTreeModel, GroupRow
from ..utilities import get_channel_assignment_name


COLUMNS = ({
    'id': 'role_name',
    'label': translate('DcaPlotterSettings', 'Role Name & Assignments'),
}, {
    'id': 'default_indicator',
    'label': translate('DcaPlotterSettings', 'Default'),
})

class RoleAssignRow(BaseRow):
    def __init__(self, channel_tuple, **kwargs):
        super().__init__(**kwargs)
        self._channel = channel_tuple
        self._is_default = self._parent.childCount() == 0

    def data(self, col, role=Qt.DisplayRole):
        # pylint: disable=missing-docstring
        if col == -1 and role == ConceptTreeModel.AccessRole:
            return self._channel

        if col == 0 and role == Qt.DisplayRole:
            return get_channel_assignment_name(self._channel)

        if col == 1 and role == Qt.CheckStateRole:
            return Qt.Checked if self._is_default else Qt.Unchecked

        return super().data(col, role)

    def flags(self, col):
        # pylint: disable=missing-docstring
        flags = Qt.ItemNeverHasChildren | Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if col == 0:
            return flags
        if col == 1:
            return flags | Qt.ItemIsEditable | Qt.ItemIsUserCheckable
        return super().flags(col)

    def setData(self, col, data, role):
        # pylint: disable=invalid-name, missing-docstring
        if col == 1 and role == Qt.CheckStateRole:
            self._is_default = data == Qt.Checked
            if data == Qt.Unchecked:
                return False

            for sibling in self._parent.children():
                if sibling == self:
                    continue
                sibling.setData(col, Qt.Unchecked, role)

            model = self._parent.model()
            model.dataChanged.emit(
                model.createIndex(0, 1, self),
                model.createIndex(self._parent.childCount(), 1, self),
                [Qt.CheckStateRole])
            return True
        return False


class RolesTreeModel(ConceptTreeModel):

    def __init__(self):
        super().__init__('role#{0:02}', COLUMNS, RoleAssignRow, ['input', 'fx'], True)

    def deserialise(self, data):
        if self._root.childCount():
            logger.error('Attempting to deserialise out of sequence.')
            return

        for group_id, group in data.items():
            group_row = GroupRow(group_id, group['name'], parent=self._root)
            self._root.addChild(group_row)
            self._group_count = max(self._group_count, int(group_id.split('#')[1]))

            for assign in group['assigns']:
                assign_row = RoleAssignRow(tuple(assign), parent=group_row)
                group_row.addChild(assign_row)
                if assign == group['default']:
                    assign_row.setData(1, Qt.Checked, Qt.CheckStateRole)

        self._group_count += 1

    def serialise(self):
        '''Serialises the role assignment data, ready for saving to file.'''
        data = {}
        for group_row in self._root.children():
            group = {
                'name': group_row.data(0, Qt.EditRole),
                'assigns': [],
                'default': '',
            }
            for assign_row in group_row.children():
                group['assigns'].append(assign_row.data(-1, self.AccessRole))
                if assign_row.data(1, Qt.CheckStateRole) == Qt.Checked:
                    group['default'] = group['assigns'][len(group['assigns']) - 1]

            group_id = group_row.data(-1, self.AccessRole)
            data[group_id] = group

        return data
