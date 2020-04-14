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

# pylint: disable=import-error
from lisp.ui.qdelegates import LineEditDelegate, SpinBoxDelegate
from lisp.ui.ui_utils import translate

from midi_fixture_control.ui import LabelDelegate

from .channel_assign_page import AssignUi

class FxAssignUi(AssignUi):
    '''FX Unit Assign UI'''
    Name = translate("DcaPlotter", "Effects Assignments")

    SessionConfigKey = 'fx'

    EntryLimit = {
        'caption': translate('DcaPlotter', '# of Effect Units'),
        'num': 16,
        'key': 'fx_channel_count',
    }

    TableHeadings = [
        translate('DcaPlotterSettings', 'Effect #'),
        translate('DcaPlotterSettings', 'FX Return #'),
        translate('DcaPlotterSettings', 'Name')
    ]
    TableColumns = [{
        'delegate': LabelDelegate(),
        'width': 64
    }, {
        'delegate': SpinBoxDelegate(minimum=1, maximum=96),
        'width': 80
    }, {
        'delegate': LineEditDelegate(max_length=16)
    }]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
