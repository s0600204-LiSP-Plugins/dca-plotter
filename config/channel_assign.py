
# pylint: disable=import-error
from lisp.plugins import get_plugin
from lisp.ui.settings.pages import SettingsPagesTabWidget
from lisp.ui.ui_utils import translate

from .page_fx_assign import FxAssignUi
from .page_mic_assign import MicAssignUi

class ChannelAssignConfig(SettingsPagesTabWidget):
    '''Channel Assignment Setup'''
    Name = translate("DcaPlotter", "Channel Assignments")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.addPage(MicAssignUi(parent=self))
        self.addPage(FxAssignUi(parent=self))

    def getSettings(self):
        return {"assigns": super().getSettings()}

    def loadSettings(self, settings):
        super().loadSettings(settings["assigns"])
