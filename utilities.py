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

# pylint: disable=missing-docstring

# pylint: disable=import-error
from lisp.plugins import get_plugin
from lisp.ui.ui_utils import translate

def build_default_dca_name(num):
    return translate("DcaPlotter", "DCA {0}").format(num)

def build_default_channel_name(channel_tuple):
    if channel_tuple[0] == 'input':
        return translate("DcaPlotter", "Microphone {0}").format(channel_tuple[1])
    if channel_tuple[0] == 'fx':
        return translate("DcaPlotter", "FX {0}").format(channel_tuple[1])
    return str(channel_tuple)

def get_channel_assignment_name(channel_tuple):
    if channel_tuple[0] == 'role':
        return get_role_name(channel_tuple)

    return '{id} : {name}'.format_map({
        'id': channel_tuple[1],
        'name': get_channel_name(channel_tuple)
    })

def get_channel_name(channel_tuple):
    if channel_tuple[0] == 'role':
        return get_role_name(channel_tuple)
    assigns = get_plugin('DcaPlotter').SessionConfig['assigns'][channel_tuple[0]]
    return assigns[channel_tuple[1] - 1]['name'] if assigns else build_default_channel_name(channel_tuple)

def get_role_name(role_tuple):
    for role in get_plugin('DcaPlotter').SessionConfig['assigns']['role']:
        if role['id'] == role_tuple[1]:
            return role['name']
