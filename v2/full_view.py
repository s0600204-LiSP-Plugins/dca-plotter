
from PyQt5.QtCore import QModelIndex # Qt
#from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QAbstractItemView

class PlotterView(QAbstractItemView):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    #def dataChanged(topLeft, bottomRight):
    #    '''This slot is called when the items with model indexes in the rectangle from topLeft to bottomRight change
    #    @arg topLeft QModelIndex
    #    @arg bottomRight QModelIndex
    #    @arg roles QVector<int> - optional
    #    '''

    def horizontalOffset(self): # REQUIRED REQUESTED
        '''Returns the view's horizontal offset.
        @return int
        '''
        return 0

    def indexAt(self, point): # REQUIRED REQUESTED
        '''Returns the model index of the item at position point in the view's viewport
        @arg point QPoint
        @return QModelIndex
        '''
        return QModelIndex()

    #def isIndexHidden(self, index): # REQUIRED
    #    '''Returns true if the item at index is a hidden item (and therefore should not be shown)
    #    @arg index QModelIndex
    #    @return bool
    #    '''

    #def mousePressEvent(self, event):
    #    '''Typically used to set the current model index to the index of the clicked item
    #    @arg event QMouseEvent
    #    '''

    def moveCursor(self, how, modifiers): # REQUIRED REQUESTED
        '''Returns the model index of the item after navigating how (e.g., up, down, left, or right), and accounting for the keyboard modifiers
        @arg how QAbstractItemView::CursorAction
        @arg modifiers Qt::KeyboardModifiers 
        @return QModelIndex
        '''
        return QModelIndex()

    #def paintEvent(self, event):
    #    '''Paints the view's contents on the viewport
    #    @arg event QPaintEvent
    #    '''

    #def resizeEvent(self, event):
    #    '''Typically used to update the scrollbars
    #    @arg event QResizeEvent
    #    '''

    #def rowsAboutToBeRemoved(self, parent, start, end):
    #    '''This slot is called when rows from start to end under parent are about to be removed
    #    @arg parent QModelIndex
    #    @arg start int
    #    @arg end int
    #    '''

    #def rowsInserted(self, parent, start, end):
    #    '''This slot is called when rows from start to end are inserted under the parent model index
    #    @arg parent QModelIndex
    #    @arg start int
    #    @arg end int
    #    '''

    #def scrollContentsBy(self, dx, dy):
    #    '''Scrolls the view's viewport by dx and dy pixels
    #    @arg dx int
    #    @arg dy int
    #    '''

    #def scrollTo(self, index, hint): # REQUIRED
    #    '''Scrolls the view to ensure that the item at the given model index is visible, and respecting the scroll hint as it scrolls
    #    @arg index QModelIndex
    #    @arg hint QAbstractItemView::ScrollHint
    #    '''

    #def setModel(self, model):
    #    '''Makes the view use the given model
    #    @arg model QAbstractItemModel
    #    '''

    #def setSelection(self, rect, flags): # REQUIRED
    #    '''Applies the selection flags to all of the items in or touching the rectangle rect
    #    @arg rect QRect
    #    @arg flags QItemSelectionModel::SelectionFlags
    #    '''

    #def updateGeometries(self):
    #    '''Typically used to update the geometries of the view's child widgets, e.g., the scrollbars
    #    (no args or return)
    #    '''

    def verticalOffset(self): # REQUESTED
        '''Returns the view's vertical offset
        @return int
        '''
        return 0

    #def visualRect(self, index): # REQUIRED
    #    '''Returns the rectangle occupied by the item at the given model index
    #    @arg index QModelIndex
    #    @return QRect
    #    '''

    #def visualRegionForSelection(self, selection): # REQUIRED
    #    '''Returns the viewport region for the items in the selection
    #    @arg selection QItemSelection
    #    @return QRegion
    #    '''

