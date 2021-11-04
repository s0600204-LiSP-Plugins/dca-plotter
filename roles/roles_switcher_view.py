# This file is a derivation of work on - and as such shares the same
# licence as - Linux Show Player
#
# Linux Show Player:
#   Copyright 2012-2021 Francesco Ceruti <ceppofrancy@gmail.com>
#
# This file:
#   Copyright 2021 s0600204
#
# Linux Show Player is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Linux Show Player is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Linux Show Player.  If not, see <http://www.gnu.org/licenses/>.

# pylint: disable=no-name-in-module
from PyQt5.QtCore import QModelIndex, QRect, QSize, Qt
from PyQt5.QtGui import QFontMetrics, QPainter, QRegion
from PyQt5.QtWidgets import QAbstractItemView

from midi_fixture_control.ui import LabelDelegate

from ..ui import LINE_PEN, ToggleButtonDelegate

class RolesSwitcherView(QAbstractItemView):

    _Margin = 4
    _cell_sizes = []
    _ideal_height = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        font = self.font()
        font.setBold(True)
        self._fontmetrics = QFontMetrics(font)
        self.setSelectionMode(QAbstractItemView.SingleSelection)

        self._button_delegate = ToggleButtonDelegate()
        self._label_delegate = LabelDelegate()
        self.setItemDelegate(self._button_delegate)
        self.setItemDelegateForColumn(0, self._label_delegate)

    def modelDataRenewed(self):
        #pylint: disable=invalid-name
        self._recalculate_cell_size()

    def horizontalOffset(self): # REQUIRED REQUESTED
        # pylint: disable=invalid-name, no-self-use
        '''Returns the view's horizontal offset.
        @return int
        '''
        return 0

    def indexAt(self, point): # REQUIRED REQUESTED
        # pylint: disable=invalid-name
        '''Returns the model index of the item at position point in the view's viewport
        @arg point QPoint
        @return QModelIndex
        '''
        self._recalculate_cell_size()

        for row, row_dimensions in enumerate(self._cell_sizes):
            if not row_dimensions:
                continue

            if row_dimensions['assigns_rect'].contains(point):
                for col, rect in enumerate(row_dimensions['assigns']):
                    if rect.contains(point):
                        return self.model().index(row, col + 1)

        return QModelIndex()

    def isIndexHidden(self, _): # REQUIRED
        # pylint: disable=invalid-name, no-self-use
        '''Returns true if the item at index is a hidden item (and therefore should not be shown)
        @arg index QModelIndex
        @return bool
        '''
        return False

    def moveCursor(self, *_): # REQUIRED REQUESTED
        # pylint: disable=invalid-name, no-self-use, unused-argument
        '''Returns the model index of the item after navigating how (e.g. up, down, left, or right),
           and accounting for the keyboard modifiers
        @arg how QAbstractItemView::CursorAction
        @arg modifiers Qt::KeyboardModifiers
        @return QModelIndex
        '''
        return QModelIndex()

    def paintEvent(self, _):
        # pylint: disable=invalid-name
        '''Paints the view's contents on the viewport
        @arg event QPaintEvent
        '''
        painter = QPainter(self.viewport())
        model = self.model()

        # Update/Recalculate dimensions
        self._recalculate_cell_size()

        for role_num in range(model.rowCount(model.index(0, 0))):
            if not self._cell_sizes[role_num]:
                continue

            # Role Name
            role_viewoptions = self.viewOptions()
            role_viewoptions.displayAlignment = Qt.AlignHCenter
            role_viewoptions.font.setBold(True)
            role_viewoptions.rect = self._cell_sizes[role_num]['name_rect']
            self.itemDelegateForColumn(0).paint(painter, role_viewoptions, model.index(role_num, 0))

            # Line
            for line in self._cell_sizes[role_num]['line_rects']:
                self._paint_line(painter, line)

            # Assigns
            for assign_num in range(model.columnCount(model.index(role_num, 0))):
                ass_viewoptions = self.viewOptions()
                ass_viewoptions.rect = self._cell_sizes[role_num]['assigns'][assign_num]
                self.itemDelegate().paint(painter, ass_viewoptions, model.index(role_num, assign_num + 1))

    def resizeEvent(self, _):
        # pylint: disable=invalid-name
        '''Typically used to update the scrollbars
        @arg event QResizeEvent
        '''
        if not self.model():
            return
        self._recalculate_cell_size()

    def scrollTo(self, *_): # REQUIRED, REQUESTED
        # pylint: disable=invalid-name
        '''Scrolls the view to ensure that the item at the given model index is visible,
           respecting the scroll hint as it scrolls
        @arg index QModelIndex
        @arg hint QAbstractItemView::ScrollHint
        '''

    def setModel(self, model):
        # pylint: disable=invalid-name
        '''Makes the view use the given model
        @arg model QAbstractItemModel
        '''
        super().setModel(model)
        self.model().dataRenewed.connect(self.modelDataRenewed)
        self._recalculate_cell_size()

    def setSelection(self, *_): # REQUIRED, REQUESTED
        # pylint: disable=invalid-name, no-self-use
        '''Applies the selection flags to all of the items in or touching the rectangle rect
        @arg rect QRect
        @arg flags QItemSelectionModel::SelectionFlags
        '''

    def verticalOffset(self): # REQUESTED
        # pylint: disable=invalid-name, no-self-use
        '''Returns the view's vertical offset
        @return int
        '''
        return 0

    def visualRect(self, index): # REQUIRED REQUESTED
        # pylint: disable=invalid-name
        '''Returns the rectangle occupied by the item at the given model index
        @arg index QModelIndex
        @return QRect
        '''
        if not index.isValid():
            return QRect()

        row = index.row()
        col = index.column()
        if row >= len(self._cell_sizes):
            return QRect()

        if col == 0:
            return self._cell_sizes[row]['name_rect']

        col -= 1
        if col >= len(self._cell_sizes[row]['assigns']):
            return QRect()

        return self._cell_sizes[row]['assigns'][col]

    def visualRegionForSelection(self, selection): # REQUIRED
        # pylint: disable=invalid-name
        '''Returns the viewport region for the items in the selection
        @arg selection QItemSelection
        @return QRegion
        '''
        region = QRegion()
        for sel in selection:
            for index in sel.indexes():
                region += self.visualRect(index)
        return region

    def _recalculate_cell_size(self):
        self._cell_sizes = []

        font_height = self._fontmetrics.height()
        general_width = self.viewport().width() - self._Margin * 2
        line_breadth = 1
        assign_height = font_height * 2.5

        running_y = self._Margin * 2
        for role_num in range(self.model().rowCount(self.model().index(0, 0))):

            # If a role only has one assign (or doesn't have any) there's no point in displaying it
            assign_count = self.model().columnCount(self.model().index(role_num, 0))
            if assign_count < 2:
                self._cell_sizes.append(None)
                continue

            role_dimen = {}

            # Name
            role_dimen['name_rect'] = QRect(self._Margin,
                                            running_y,
                                            general_width,
                                            font_height)

            running_y += font_height / 2 + self._Margin

            # Lines
            name_width = self._fontmetrics.boundingRect(self.model().data(self.model().index(role_num, 0))).width()
            line_length = (general_width - name_width) / 2 - self._Margin
            role_dimen['line_rects'] = [QRect(self._Margin,
                                              running_y,
                                              line_length,
                                              line_breadth),
                                        QRect(self._Margin + (general_width - line_length),
                                              running_y,
                                              line_length,
                                              line_breadth)]
            running_y += font_height / 2

            # Assigns
            role_dimen['assigns'] = []
            for _ in range(assign_count):
                role_dimen['assigns'].append(QRect(self._Margin,
                                             running_y,
                                             general_width,
                                             assign_height))
                running_y += assign_height + self._Margin

            role_dimen['assigns_rect'] = role_dimen['assigns'][0] | role_dimen['assigns'][len(role_dimen['assigns']) - 1]

            self._cell_sizes.append(role_dimen)

            # Gap 'tween the groupings
            running_y += self._Margin

        self._ideal_height = running_y
        self.updateGeometry()

    def minimumSizeHint(self):
        return QSize(200, self._ideal_height)

    def _paint_line(self, painter, rect):
        painter.save()
        painter.setPen(LINE_PEN)
        painter.drawLine(rect.topLeft(), rect.bottomRight())
        painter.restore()
