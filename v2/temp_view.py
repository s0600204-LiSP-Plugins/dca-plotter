
from PyQt5.QtWidgets import QDialog, QGridLayout, QTreeView, QTableView

from lisp.plugins import get_plugin

class DcaPlotterTempDialog(QDialog):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.setWindowTitle('Temporary Viewer')
        self.setMinimumSize(600, 400)
        self.setLayout(QGridLayout())

        self.model = get_plugin('DcaPlotter').mapping_model

        self.view = DcaPlotterTempView(model=self.model, parent=self)
        self.layout().addWidget(self.view, 0, 0)



class DcaPlotterTempView(QTableView):

    def __init__(self, model, **kwargs):
        super().__init__(**kwargs)
        self.setModel(model)
