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

# pylint: disable=import-error
from lisp.plugins import get_plugin
from lisp.ui.settings.pages import SettingsPagesTabWidget
from lisp.ui.ui_utils import translate

from ..choir.choir_assign import ChoirAssignUi
from ..roles.roles_assign import RolesAssignUi
from .page_fx_assign import FxAssignUi
from .page_mic_assign import MicAssignUi

class ChannelAssignConfig(SettingsPagesTabWidget):
    '''Channel Assignment Setup'''
    Name = translate("DcaPlotter", "Channel Assignments")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.addPage(RolesAssignUi(parent=self))
        self.addPage(ChoirAssignUi(parent=self))
        self.addPage(MicAssignUi(parent=self))
        self.addPage(FxAssignUi(parent=self))

    def getSettings(self):
        return {"assigns": super().getSettings()}

    def loadSettings(self, settings):
        super().loadSettings(settings["assigns"])
