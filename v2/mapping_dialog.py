
from PyQt5.QtWidgets import QDialog, QVBoxLayout

from lisp.plugins import get_plugin
from lisp.plugins.dca_plotter.v2.full_view import PlotterView

class DcaMappingDialog(QDialog):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.setWindowTitle('DCA Mapping')
        self.setMinimumSize(1080, 800)
        self.setLayout(QVBoxLayout())

        self.model = get_plugin('DcaPlotter').mapper()

        self.view = PlotterView()
        self.view.setModel(self.model)
        self.layout().addWidget(self.view)
