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

from ..model_primitives import ModelsBranchNode, ModelsLeafNode, DcaModelTemplate


class RolesRow(ModelsBranchNode):
    '''Row that represents a role'''


class AssignRow(ModelsLeafNode):
    '''Row that represents an assignment

    Has no child rows.
    '''

class RolesTreeModel(DcaModelTemplate):
    def __init__(self):
        super().__init__()
        self.columns = [{
            'id': 'role_id',
            'label': 'Role ID',
            'flags': Qt.NoItemFlags,
        }, {
            'id': 'role_name',
            'label': translate('DcaPlotterSettings', 'Role Name & Assignments'),
            'flags': Qt.ItemIsEditable | Qt.ItemIsSelectable
        }, {
            'id': 'default_indicator',
            'label': translate('DcaPlotterSettings', 'Default'),
            'flags': Qt.ItemIsEditable | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable, # pylint: disable=line-too-long
            'flags_alt': Qt.ItemIsEditable | Qt.ItemIsSelectable
        }]

    def columnCount(self, _):
        # pylint: disable=invalid-name, missing-docstring
        return len(self.columns)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        # pylint: disable=invalid-name, missing-docstring
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.columns[section]['label']

        return None
