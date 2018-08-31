
from PyQt5.QtCore import Qt, QModelIndex, QRect
from PyQt5.QtGui import QFontMetrics, QPainter, QPen # QMouseEvent
from PyQt5.QtWidgets import QAbstractItemView, QApplication

class PlotterView(QAbstractItemView):

    CUEROW_MARGIN = 8
    CUEHEADER_PADDING = 2
    BLOCK_PADDING = 2
    BLOCKENTRY_PADDING = 1

    _cueid_width = 0
    _cuerow_height = []
    _cuerow_height_dirty = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setFont(QApplication.font("QTreeView"));
        self._fontmetrics = QFontMetrics(self.font())

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
        #return self.horizontalScrollBar().value()
        return 0 # Intention is to scale dca blocks horizontally so we'll never need to scroll horizontally

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
    #    return False

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

    def paintEvent(self, event):
        '''Paints the view's contents on the viewport
        @arg event QPaintEvent
        '''
        painter = QPainter(self.viewport())

        # @todo: calculate (and set) this elsewhere
        self._cueid_width = self._fontmetrics.height() * 3

        # Update/Recalculate dimensions
        self._recalculate_cuerow_heights()

        viewport_y = 0

        for row_num in range(self.model().childCount(self.rootIndex())):
            row_x = 0
            row_y = viewport_y
            row_index = self.model().index(row_num, 0, self.rootIndex())

            # Draw the Cue Number & Name
            row_viewoptions = self.viewOptions()
            row_viewoptions.rect = QRect(self.CUEHEADER_PADDING,
                                         row_y + self.CUEHEADER_PADDING,
                                         self.viewport().width() - self.CUEHEADER_PADDING * 2,
                                         self._fontmetrics.height())
            self.itemDelegate().paint(painter, row_viewoptions, row_index)
            viewport_y += self._fontmetrics.height() + self.CUEHEADER_PADDING * 2

            # Draw the DCA blocks
            block_x = self._cueid_width
            block_width = (self.viewport().width() - self._cueid_width) / self.model().childCount(row_index)
            for block_num in range(self.model().childCount(row_index)):
                block_y = viewport_y
                block_index = self.model().index(block_num, 0, row_index)

                # Draw the DCA name
                # @todo: centre the text
                dcaname_viewoptions = self.viewOptions()
                dcaname_viewoptions.rect = QRect(block_x + self.BLOCK_PADDING,
                                                 block_y + self.BLOCK_PADDING,
                                                 block_width - self.BLOCK_PADDING * 2,
                                                 self._fontmetrics.height())
                self.itemDelegate().paint(painter, dcaname_viewoptions, block_index)
                block_y += self._fontmetrics.height() + self.BLOCK_PADDING

                # And a line under it
                self._paint_line(painter, QRect(block_x + self.BLOCK_PADDING * 2,
                                                block_y + self.BLOCK_PADDING,
                                                block_width - self.BLOCK_PADDING * 4,
                                                1))
                block_y += self.BLOCK_PADDING

                # Draw the assigns
                for assign_num in range(self.model().childCount(block_index)):
                    assign_index = self.model().index(assign_num, 0, block_index)
                    assign_viewoptions = self.viewOptions()
                    assign_viewoptions.rect = QRect(block_x + self.BLOCKENTRY_PADDING,
                                                    block_y + self.BLOCKENTRY_PADDING,
                                                    block_width - self.BLOCKENTRY_PADDING * 2,
                                                    self._fontmetrics.height())
                    self.itemDelegate().paint(painter, assign_viewoptions, assign_index)
                    block_y += self._fontmetrics.height() + self.BLOCKENTRY_PADDING

                # Draw a rectangle round the block
                #block_outline_rect = QRect(block_x, viewport_y, block_width, self._cuerow_height[row_num])
                #self._paint_outline(painter, block_outline_rect)
                block_x += block_width

            viewport_y += self._cuerow_height[row_num]

            # Draw a rectangle around the entire cue
            # Temporary - probably will remove or replace this
            # However, for debugging, so we have a visual guide of where things are being drawn
            #outline_rect = QRect(row_x, row_y, self.viewport().width(), viewport_y - row_y)
            #self._paint_outline(painter, outline_rect)

            viewport_y += self.CUEROW_MARGIN


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

    def setModel(self, model):
        '''Makes the view use the given model
        @arg model QAbstractItemModel
        '''
        super().setModel(model)
        self._cuerow_height_dirty = [rownum for rownum in range(self.model().childCount(self.rootIndex()))]
        self._cuerow_height = [0 for rownum in range(self.model().childCount(self.rootIndex()))]

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
        return self.verticalScrollBar().value()

    #def visualRect(self, index): # REQUIRED REQUESTED
    #    '''Returns the rectangle occupied by the item at the given model index
    #    @arg index QModelIndex
    #    @return QRect
    #    '''

    #def visualRegionForSelection(self, selection): # REQUIRED
    #    '''Returns the viewport region for the items in the selection
    #    @arg selection QItemSelection
    #    @return QRegion
    #    '''

    def _mark_rowheight_dirty(self, rownum):
        self._cuerow_height_dirty.append(rownum)

    def _recalculate_cuerow_heights(self):
        entry_height = self._fontmetrics.height() + self.BLOCKENTRY_PADDING
        while len(self._cuerow_height_dirty):
            entry_count = 0
            row_num = self._cuerow_height_dirty[0]
            row_index = self.model().index(row_num, 0, self.rootIndex())

            for block_num in range(self.model().childCount(row_index)):
                block_index = self.model().index(block_num, 0, row_index)
                entry_count = max(entry_count, self.model().childCount(block_index))

            self._cuerow_height[row_num] = self._fontmetrics.height() + self.BLOCK_PADDING * 2
            self._cuerow_height[row_num] += max(1, entry_count) * entry_height
            self._cuerow_height[row_num] += self.BLOCKENTRY_PADDING
            self._cuerow_height_dirty.remove(row_num)


    def _paint_outline(self, painter, rect):
        rect = rect.adjusted(0, 0, -1, -1);
        painter.save();
        painter.setPen(QPen(self.palette().dark().color(), 0.5));
        painter.drawRect(rect);
        painter.restore();

    def _paint_line(self, painter, rect):
        #rect = rect.adjusted(0, 0, -1, -1);
        painter.save();
        painter.setPen(QPen(self.palette().dark().color(), 0.5));
        painter.drawLine(rect.topLeft(), rect.bottomRight());
        painter.restore();
