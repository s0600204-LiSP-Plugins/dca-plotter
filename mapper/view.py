
from PyQt5.QtCore import Qt, QModelIndex, QRect
from PyQt5.QtGui import QFontMetrics, QPainter, QPen # QMouseEvent
from PyQt5.QtWidgets import QAbstractItemView, QApplication

from lisp.plugins import get_plugin
from lisp.plugins.dca_plotter.modelview_abstract import DcaModelViewTemplate

class DcaMappingView(DcaModelViewTemplate):

    DRAW_CUEHEADER = True

    def __init__(self, **kwargs):
        super().__init__("QTreeView", **kwargs)

    def updateGeometries(self):
        self.verticalScrollBar().setRange(0, max(0, self._ideal_height - self.viewport().height()))

    def verticalOffset(self):
        return self.verticalScrollBar().value()
