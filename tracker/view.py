
#from PyQt5.QtCore import QModelIndex, Qt, QRect
from PyQt5.QtGui import QFontMetrics, #QPainter, QPen # QMouseEvent
from PyQt5.QtWidgets import QAbstractItemView, QApplication

from lisp.plugins import get_plugin

class DcaTrackingView(QAbstractItemView):

    BLOCK_MARGIN = 2
    BLOCKENTRY_MARGIN = 1

    _cell_sizes = {}
    _cell_sizes_dirty = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setFont(QApplication.font("QTableView"));
        self._fontmetrics = QFontMetrics(self.font())
