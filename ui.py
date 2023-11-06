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
from PyQt5.QtCore import Qt, QEvent, QModelIndex
from PyQt5.QtGui import QBrush, QMouseEvent, QPalette, QPen
from PyQt5.QtWidgets import (
    QApplication,
    QHeaderView,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionToolButton,
    QTreeView,
)

LINE_COLOR = QApplication.palette().light().color()
LINE_PEN = QPen(LINE_COLOR, 0.5)

BASE_TEXT_COLOR = QApplication.palette().light().color()
BASE_TEXT_BRUSH = QBrush(BASE_TEXT_COLOR)

class ToggleButtonDelegate(QStyledItemDelegate):
    '''Toggle Button Delegate

    When clicked, the state of the delegate toggles between "checked" and "unchecked".
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_clicked_index = QModelIndex()

    def createEditor(self, parent, option, index):
        # pylint: disable=invalid-name, no-self-use, unused-argument,
        '''Do not create an Editor (on double-click)'''
        return None

    def editorEvent(self, event, model, option, index):
        # pylint: disable=invalid-name
        '''Toggle checked/unchecked on mouse click'''
        if event.type() == QEvent.MouseButtonPress:
            self.last_clicked_index = index

        elif event.type() == QEvent.MouseButtonRelease:

            if index.row() is not self.last_clicked_index.row() or \
               index.column() is not self.last_clicked_index.column():
                return False

            e = QMouseEvent(event)
            if int(e.button()) is not int(Qt.LeftButton):
                return False

            self.last_clicked_index = QModelIndex()

            if index.data(Qt.CheckStateRole) is Qt.Checked:
                return False

            model.setData(index, Qt.Checked, Qt.CheckStateRole)
            return True

        return super().editorEvent(event, model, option, index)

    def paint(self, painter, option, index):
        # pylint: disable=no-self-use
        '''Draws the button'''

        button_option = QStyleOptionToolButton()
        button_option.palette = option.palette
        button_option.rect = option.rect
        button_option.text = index.data(Qt.DisplayRole)

        if index.data(Qt.CheckStateRole) == Qt.Checked:
            button_option.palette.setColor(QPalette.Button,
                                           option.palette.highlight().color())
            button_option.palette.setColor(QPalette.ButtonText,
                                           option.palette.highlightedText().color())
            button_option.state |= QStyle.State_On
        else:
            button_option.state |= QStyle.State_Off

        QApplication.style().drawPrimitive(QStyle.PE_PanelButtonTool, button_option, painter)
        QApplication.style().drawControl(QStyle.CE_ToolButtonLabel, button_option, painter)


class SimpleTreeView(QTreeView):
    # pylint: disable=too-few-public-methods
    """Simple implementation of a QTreeView"""

    def __init__(self, model, columns, **kwargs):
        super().__init__(**kwargs)

        self.setAllColumnsShowFocus(True)
        self.setUniformRowHeights(True)

        self.header().setSectionResizeMode(QHeaderView.Fixed)
        self.header().setStretchLastSection(False)
        self.header().setSectionsMovable(False)

        self.setModel(model)

        self.columns = columns
        for col_idx, col_spec in enumerate(self.columns):
            if col_spec is None:
                self.setColumnHidden(col_idx, True)
                continue

            self.setItemDelegateForColumn(col_idx, col_spec['delegate'])

            if 'width' in col_spec:
                self.header().resizeSection(col_idx, col_spec['width'])
            else:
                self.header().setSectionResizeMode(col_idx, QHeaderView.Stretch)
