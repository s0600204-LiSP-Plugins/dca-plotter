
from PyQt5.QtCore import QItemSelection, QModelIndex, QRect, Qt
from PyQt5.QtGui import QFontMetrics, QPainter, QPen, QRegion
from PyQt5.QtWidgets import QAbstractItemView, QApplication, QStyle

from lisp.plugins import get_plugin

class DcaModelViewTemplate(QAbstractItemView):

    BLOCK_MARGIN = 2
    BLOCKENTRY_MARGIN = 1
    CUEROW_MARGIN = 8
    CUEHEADER_MARGIN = 2
    MINIMUM_BLOCK_WIDTH = 128
    DRAW_CUEHEADER = False # <-- Overridden to True in the Mapper view

    _cell_sizes = []
    _cell_sizes_dirty = False
    _ideal_height = 0
    _ideal_width = 0

    def __init__(self, font_variant, **kwargs):
        super().__init__(**kwargs)
        self.setFont(QApplication.font(font_variant));
        self._fontmetrics = QFontMetrics(self.font())
        self.horizontalScrollBar().setRange(0, 0)
        self.verticalScrollBar().setRange(0, 0)
        self.setSelectionMode(QAbstractItemView.SingleSelection)

    def dataChanged(topLeft, bottomRight):
        '''This slot is called when the items with model indexes in the rectangle from topLeft to bottomRight change
        @arg topLeft QModelIndex
        @arg bottomRight QModelIndex
        @arg roles QVector<int> - optional
        '''
        self._cell_sizes_dirty = True
        super().dataChanged(topLeft, bottomRight)
        self.viewport().update()

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
        point.setX(point.x() + self.horizontalScrollBar().value())
        point.setY(point.y() + self.verticalScrollBar().value())
        self._recalculate_cell_size()

        for row_num, row_dimensions in enumerate(self._cell_sizes):

            if row_dimensions['rect'].contains(point):
                row_index = self.model().index(row_num, 0, self.rootIndex())

                if self.DRAW_CUEHEADER and row_dimensions['header_rect'].contains(point):
                    return row_index

                for block_num, block_dimensions in enumerate(row_dimensions['blocks']):
                    if block_dimensions['rect'].contains(point):
                        block_index = self.model().index(block_num, 0, row_index)

                        if block_dimensions['header_rect'].contains(point):
                            return block_index

                        for assign_num, assign_dimensions in enumerate(block_dimensions['entries']):
                            if assign_dimensions.contains(point):
                                return self.model().index(assign_num, 0, block_index)

        return QModelIndex()

    def isIndexHidden(self, index): # REQUIRED
        '''Returns true if the item at index is a hidden item (and therefore should not be shown)
        @arg index QModelIndex
        @return bool
        '''
        # @todo: Return True for cuerow indexes if not drawing those...
        return False

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

        def _get_selection_state(assign_index):
            state = 0
            if self.selectionModel().isSelected(assign_index):
                state |= QStyle.State_Selected
            if self.currentIndex() == assign_index:
                state |= QStyle.State_HasFocus
            return state

        # Update/Recalculate dimensions
        self._recalculate_cell_size()

        for row_num, row_dimensions in enumerate(self._cell_sizes):
            row_index = self.model().index(row_num, 0, self.rootIndex())

            if self.DRAW_CUEHEADER:
                # Draw the Cue Number & Name
                row_viewoptions = self.viewOptions()
                row_viewoptions.rect = self._viewport_rect_for_item(row_index)
                row_viewoptions.state |= _get_selection_state(row_index)
                self.itemDelegate().paint(painter, row_viewoptions, row_index)

            # Then each DCA block
            for block_num, block_dimensions in enumerate(row_dimensions['blocks']):
                block_index = self.model().index(block_num, 0, row_index)

                # Draw the DCA name
                # @todo: centre the text
                dcaname_viewoptions = self.viewOptions()
                dcaname_viewoptions.rect = self._viewport_rect_for_item(block_index)
                dcaname_viewoptions.state |= _get_selection_state(block_index)
                self.itemDelegate().paint(painter, dcaname_viewoptions, block_index)

                # And a line under it
                self._paint_line(painter,
                                 block_dimensions['line_rect'].adjusted(-self.horizontalScrollBar().value(),
                                                                        -self.verticalScrollBar().value(),
                                                                        -self.horizontalScrollBar().value(),
                                                                        -self.verticalScrollBar().value()))

                # Draw the assigns
                for assign_num, assign_dimensions in enumerate(block_dimensions['entries']):
                    assign_index = self.model().index(assign_num, 0, block_index)
                    assign_viewoptions = self.viewOptions()
                    assign_viewoptions.rect = self._viewport_rect_for_item(assign_index)
                    assign_viewoptions.state |= _get_selection_state(assign_index)
                    self.itemDelegate().paint(painter, assign_viewoptions, assign_index)

    def resizeEvent(self, event):
        '''Typically used to update the scrollbars
        @arg event QResizeEvent
        '''
        if not self.model():
            return
        self._cell_sizes_dirty = True
        self._recalculate_cell_size()
        self.updateGeometries()

    def rowsAboutToBeRemoved(self, parent, start, end):
        '''This slot is called when rows from start to end under parent are about to be removed
        @arg parent QModelIndex
        @arg start int
        @arg end int
        '''
        self._cell_sizes_dirty = True
        super().rowsAboutToBeRemoved(parent, start, end)
        self.viewport().update()

    def rowsInserted(self, parent, start, end):
        '''This slot is called when rows from start to end are inserted under the parent model index
        @arg parent QModelIndex
        @arg start int
        @arg end int
        '''
        self._cell_sizes_dirty = True
        super().rowsInserted(parent, start, end)
        self.viewport().update()

    def scrollContentsBy(self, dx, dy):
        '''Scrolls the view's viewport by dx and dy pixels
        @arg dx int
        @arg dy int
        '''
        self.viewport().scroll(dx, dy)
        self.viewport().update()

    def scrollTo(self, index, hint): # REQUIRED
        '''Scrolls the view to ensure that the item at the given model index is visible, and respecting the scroll hint as it scrolls
        @arg index QModelIndex
        @arg hint QAbstractItemView::ScrollHint
        '''
        view_rect = self.viewport().rect();
        item_rect = self.visualRect(index);
        horiz_scrollbar = self.horizontalScrollBar()
        verti_scrollbar = self.verticalScrollBar()

        if item_rect.left() < view_rect.left():
            horiz_scrollbar.setValue(horiz_scrollbar.value() + item_rect.left() - view_rect.left())
        elif item_rect.right() > view_rect.right():
            horiz_scrollbar.setValue(horiz_scrollbar.value() + min(item_rect.right() - view_rect.right(),
                                                                   item_rect.left() - view_rect.left()))

        if item_rect.top() < view_rect.top():
            verti_scrollbar.setValue(verti_scrollbar.value() + item_rect.top() - view_rect.top());
        elif item_rect.bottom() > view_rect.bottom():
            verti_scrollbar.setValue(verti_scrollbar.value() + min(item_rect.bottom() - view_rect.bottom(),
                                                                   item_rect.top() - view_rect.top()))

        self.viewport().update()

    def setModel(self, model):
        '''Makes the view use the given model
        @arg model QAbstractItemModel
        '''
        super().setModel(model)
        self._cell_sizes_dirty = True

    def setSelection(self, rect, flags): # REQUIRED
        '''Applies the selection flags to all of the items in or touching the rectangle rect
        @arg rect QRect
        @arg flags QItemSelectionModel::SelectionFlags
        '''
        rectangle = rect.translated(self.horizontalScrollBar().value(),
                                    self.verticalScrollBar().value()).normalized()
        self._recalculate_cell_size()
        something_selected = False

        for row_num, row_dimensions in enumerate(self._cell_sizes):

            if row_dimensions['rect'].intersects(rectangle):
                row_index = self.model().index(row_num, 0, self.rootIndex())

                if self.DRAW_CUEHEADER and row_dimensions['header_rect'].intersects(rectangle):
                    something_selected = True
                    self.selectionModel().select(QItemSelection(row_index,
                                                                row_index), flags)

                for block_num, block_dimensions in enumerate(row_dimensions['blocks']):
                    if block_dimensions['rect'].intersects(rectangle):
                        block_index = self.model().index(block_num, 0, row_index)

                        if block_dimensions['header_rect'].intersects(rectangle):
                            something_selected = True
                            self.selectionModel().select(QItemSelection(block_index,
                                                                        block_index), flags)

                        selectStart = len(block_dimensions['entries'])
                        selectEnd = -1

                        for assign_num, assign_dimensions in enumerate(block_dimensions['entries']):
                            if assign_dimensions.intersects(rectangle):
                                something_selected = True
                                selectStart = selectStart if selectStart < assign_num else assign_num
                                selectEnd = selectEnd if selectEnd > assign_num else assign_num

                        if selectStart != len(block_dimensions['entries']) and selectEnd != -1:
                            selection = QItemSelection(self.model().index(selectStart, 0, block_index),
                                                       self.model().index(selectEnd, 0, block_index))
                            self.selectionModel().select(selection, flags)

        if not something_selected:
            self.selectionModel().select(QItemSelection(QModelIndex(), QModelIndex()), flags)

    #def updateGeometries(self):
    #    '''Typically used to update the geometries of the view's child widgets, e.g., the scrollbars
    #    (no args or return)
    #    '''
    #    pass

    def verticalOffset(self): # REQUESTED
        '''Returns the view's vertical offset
        @return int
        '''
        return 0

    def visualRect(self, index): # REQUIRED REQUESTED
        '''Returns the rectangle occupied by the item at the given model index
        @arg index QModelIndex
        @return QRect
        '''
        if index.isValid():
            return self._viewport_rect_for_item(index)
        return QRect()

    def visualRegionForSelection(self, selection): # REQUIRED
        '''Returns the viewport region for the items in the selection
        @arg selection QItemSelection
        @return QRegion
        '''
        region = QRegion()
        for rng in selection:
            for index in rng.indexes():
                region += self.visualRect(index)
        return region

    def _recalculate_cell_size(self):
        if not self._cell_sizes_dirty:
            return
        self._cell_sizes = []

        DCA_COUNT = get_plugin('DcaPlotter').SessionConfig['dca_count']
        FONT_HEIGHT = self._fontmetrics.height()
        BLOCK_INDENT = (FONT_HEIGHT * 3) if self.DRAW_CUEHEADER else 0
        BLOCK_WIDTH = max(self.MINIMUM_BLOCK_WIDTH,
                          (self.viewport().width() - BLOCK_INDENT) / DCA_COUNT)
        CUEROW_WIDTH = DCA_COUNT * BLOCK_WIDTH + BLOCK_INDENT
        CUEROW_HEADER_WIDTH = CUEROW_WIDTH - self.CUEHEADER_MARGIN * 2
        BLOCK_HEADER_WIDTH = BLOCK_WIDTH - self.BLOCK_MARGIN * 2
        BLOCK_LINE_LENGTH = BLOCK_WIDTH - self.BLOCK_MARGIN * 4
        BLOCK_LINE_BREADTH = 1
        ENTRY_WIDTH = BLOCK_WIDTH - self.BLOCKENTRY_MARGIN * 2
        ENTRY_MARGINED_HEIGHT = FONT_HEIGHT + self.BLOCKENTRY_MARGIN

        running_y = 0
        for row_num in range(self.model().childCount(self.rootIndex())):
            row_index = self.model().index(row_num, 0, self.rootIndex())
            row_height = 0
            row_dict = {}

            if self.DRAW_CUEHEADER:
                # Rect for Cue Number & Name
                row_dict['header_rect'] = QRect(self.CUEHEADER_MARGIN,
                                                running_y + self.CUEHEADER_MARGIN,
                                                CUEROW_HEADER_WIDTH,
                                                FONT_HEIGHT)
                row_height += row_dict['header_rect'].height()
            row_height += self.CUEHEADER_MARGIN * 2

            # Calculate the DCA blocks
            row_dict['blocks'] = []
            block_max_height = 0
            for block_num in range(self.model().childCount(row_index)):
                block_dict = {}
                block_x = BLOCK_INDENT + block_num * BLOCK_WIDTH
                block_y = running_y + row_height
                block_index = self.model().index(block_num, 0, row_index)

                # The DCA name
                block_dict['header_rect'] = QRect(block_x + self.BLOCK_MARGIN,
                                                  block_y + self.BLOCK_MARGIN,
                                                  BLOCK_HEADER_WIDTH,
                                                  FONT_HEIGHT)
                block_y += block_dict['header_rect'].height() + self.BLOCK_MARGIN

                # And a line under it
                block_dict['line_rect'] = QRect(block_x + self.BLOCK_MARGIN * 2,
                                                block_y + self.BLOCK_MARGIN,
                                                BLOCK_LINE_LENGTH,
                                                BLOCK_LINE_BREADTH)
                block_y += block_dict['line_rect'].height()

                # And the assign entries
                entry_rects = []
                for assign_num in range(self.model().childCount(block_index)):
                    entry_rects.append(QRect(block_x + self.BLOCKENTRY_MARGIN,
                                             block_y + self.BLOCKENTRY_MARGIN,
                                             ENTRY_WIDTH,
                                             FONT_HEIGHT))
                    block_y += ENTRY_MARGINED_HEIGHT

                block_y += self.BLOCK_MARGIN

                block_dict['entries'] = entry_rects
                block_max_height = max(block_max_height, block_y - running_y - row_height)
                row_dict['blocks'].append(block_dict)

            # Set the basic rect of the blocks
            # (Can only be done once we have the max height of all the blocks)
            for block_num, block_dict in enumerate(row_dict['blocks']):
                block_dict['rect'] = QRect(BLOCK_INDENT + block_num * BLOCK_WIDTH,
                                           running_y + row_height,
                                           BLOCK_WIDTH,
                                           block_max_height)

            row_height += block_max_height

            if self.DRAW_CUEHEADER:
                row_height += FONT_HEIGHT

            row_dict['rect'] = QRect(0, running_y, CUEROW_WIDTH, row_height)
            self._cell_sizes.append(row_dict)
            running_y += row_height

        self._cell_sizes_dirty = False
        self._ideal_height = running_y + self.CUEHEADER_MARGIN * 2
        self._ideal_width = CUEROW_WIDTH
        self.viewport().update()

    def _paint_outline(self, painter, rect):
        rect = rect.adjusted(0, 0, -1, -1);
        painter.save();
        painter.setPen(QPen(self.palette().dark().color(), 0.5));
        painter.drawRect(rect);
        painter.restore();

    def _paint_line(self, painter, rect):
        painter.save();
        painter.setPen(QPen(self.palette().dark().color(), 0.5));
        painter.drawLine(rect.topLeft(), rect.bottomRight());
        painter.restore();

    def _viewport_rect_for_item(self, index):
        self._recalculate_cell_size()
        rect = self._widget_rect_for_item(index)
        if not rect.isValid():
            return rect
        return QRect(rect.x() - self.horizontalScrollBar().value(),
                     rect.y() - self.verticalScrollBar().value(),
                     rect.width(), rect.height())

    def _widget_rect_for_item(self, index):
        self._recalculate_cell_size()
        walk = []
        while index.isValid():
            walk.append(index.row())
            index = index.parent()
        walk.reverse()

        # This if...elif... is awkward
        # @todo: Replace with something better
        if len(walk) == 3:
            return self._cell_sizes[walk[0]]['blocks'][walk[1]]['entries'][walk[2]]
        elif len(walk) == 2:
            return self._cell_sizes[walk[0]]['blocks'][walk[1]]['header_rect']
        elif len(walk) == 1 and self.DRAW_CUEHEADER:
            return self._cell_sizes[walk[0]]['header_rect']
        return QRect()
