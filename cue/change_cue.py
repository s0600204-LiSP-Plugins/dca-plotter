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

# pylint: disable=missing-docstring, invalid-name, too-few-public-methods

# pylint: disable=no-name-in-module
from PyQt5.QtCore import QT_TRANSLATE_NOOP
from PyQt5.QtWidgets import QVBoxLayout

# pylint: disable=import-error
from lisp.core.has_properties import Property
from lisp.ui.settings.cue_settings import CueSettingsRegistry
from lisp.ui.settings.pages import SettingsPage

# pylint: disable=relative-beyond-top-level
from ..model_primitives import AssignStateEnum
from .dca_cue import DcaCue
from .model import DcaCueModel
from .view import DcaCueView

class DcaChangeCue(DcaCue):
    Name = QT_TRANSLATE_NOOP('CueName', 'DCA/VCA Change Cue')

    dca_changes = Property([])
    dca_names = Property([])

    def update_properties(self, properties):

        # When cue properties are saved, tuples (and lists) become JSON arrays
        # When the cues are loaded again, JSON arrays become python lists
        # However, we want tuples. So we turn them back to tuples.
        if 'dca_changes' in properties:
            for dca_changes in properties['dca_changes']:
                dca_changes['add'] = [tuple(channel) for channel in dca_changes['add']]
                dca_changes['rem'] = [tuple(channel) for channel in dca_changes['rem']]

        super().update_properties(properties)

    def validate_assigns(self, assigns_from_mapper):
        active = []

        for assign_change in assigns_from_mapper:
            if assign_change[2] in (AssignStateEnum.NONE, AssignStateEnum.ASSIGN):
                if assign_change[1] in active:
                    self._error()
                    return
                active.append(assign_change[1])

        self._clear_error()

class DcaChangeCueSettings(SettingsPage):
    Name = QT_TRANSLATE_NOOP('SettingsPageName', 'DCA/VCA Change Settings')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setLayout(QVBoxLayout())

        self.model = DcaCueModel()
        self.view = DcaCueView()
        self.view.setModel(self.model)
        self.layout().addWidget(self.view)

    def getSettings(self):
        return {'dca_changes': self.model.serialise()}

    def loadSettings(self, settings):
        self.model.deserialise(settings.get('dca_changes', []), settings['id'])

CueSettingsRegistry().add(DcaChangeCueSettings, DcaChangeCue)
