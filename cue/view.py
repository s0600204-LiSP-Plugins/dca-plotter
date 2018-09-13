
from lisp.plugins.dca_plotter.modelview_abstract import DcaModelViewTemplate

class DcaCueView(DcaModelViewTemplate):

    def __init__(self, **kwargs):
        super().__init__("QTableView", **kwargs)

    def updateGeometries(self):
        self.horizontalScrollBar().setRange(0, max(0, self._ideal_width - self.viewport().width()))
