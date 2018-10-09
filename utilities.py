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

# get_mic_assign_name
from lisp.plugins import get_plugin

def build_default_dca_name(num):
    # TODO: translate string
    return "DCA {0}".format(num)

def build_default_mic_name(num):
    # TODO: translate string
    return "Microphone {0}".format(num)

def get_mic_assign_name(numid):
    return '{id} : {name}'.format_map({
        'id': numid,
        'name': get_mic_name(numid)
    })

def get_mic_name(numid):
    inputs = get_plugin('DcaPlotter').SessionConfig['inputs']
    return inputs[numid - 1]['name'] if inputs else build_default_mic_name(numid)
