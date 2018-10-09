
from PyQt5.QtCore import QModelIndex, Qt, QRect
from PyQt5.QtGui import QFontMetrics, QPainter, QPen # QMouseEvent
from PyQt5.QtWidgets import QAbstractItemView, QApplication

from lisp.plugins import get_plugin

# pylint: disable=relative-beyond-top-level
from ..modelview_abstract import DcaModelViewTemplate

class DcaTrackingView(DcaModelViewTemplate):

    def __init__(self, **kwargs):
        super().__init__("QTableView", **kwargs)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setFocusPolicy(Qt.NoFocus)
        self.setSelectionMode(QAbstractItemView.NoSelection)
        get_plugin('DcaPlotter').initialised.connect(self._post_init_set_model)

    def _post_init_set_model(self):
        self.setModel(get_plugin('DcaPlotter').tracker())

    def _recalculate_cell_size(self):
        super()._recalculate_cell_size()

        if self.maximumHeight() != self._ideal_height:
            self.setMaximumHeight(self._ideal_height)
            self.setMinimumHeight(self._ideal_height)
