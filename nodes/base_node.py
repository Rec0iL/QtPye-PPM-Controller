# nodes/base_node.py
import uuid
import pygame
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsProxyWidget, QCheckBox, QLineEdit, QLabel, QWidget, QVBoxLayout, QPushButton, QHBoxLayout
from PyQt5.QtCore import QRectF, QPointF, Qt, QTimer, pyqtSignal, QObject, QVariant
from PyQt5.QtGui import QBrush, QColor, QPen, QFont, QFontMetrics

class NodeSignalEmitter(QObject):
    output_signal = pyqtSignal(float, int)

class BaseNode(QGraphicsItem):
    def __init__(self, title="Node", x=0, y=0, w=150, h=100, parent=None):
        super().__init__(parent)
        self.id = str(uuid.uuid4())
        self.title = title
        self.setPos(x, y)
        self.width = w
        self.height = h

        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)

        self.rect = QRectF(0, 0, self.width, self.height)
        self.is_dragging = False
        self.drag_start_pos = QPointF()

        self.connections = []
        self.inputs_occupied = [False]

    def boundingRect(self):
        return self.rect

    def is_input_occupied(self, index):
        if index < len(self.inputs_occupied):
            return self.inputs_occupied[index]
        return False

    def set_input_occupied(self, index, occupied):
        if index < len(self.inputs_occupied):
            self.inputs_occupied[index] = occupied

    def paint(self, painter, option, widget=None):
        painter.setBrush(QBrush(QColor("#4A4A4A")))
        painter.setPen(QPen(QColor("#C0C0C0"), 2))
        painter.drawRoundedRect(self.rect, 10, 10)

        painter.setPen(QPen(QColor("#E0E0E0")))
        title_rect = self.rect.adjusted(5, 5, -5, -5)
        painter.drawText(title_rect, Qt.AlignLeft | Qt.AlignTop, self.title)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            for conn in self.connections:
                conn.update_path()
        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.drag_start_pos = event.pos()
            event.accept()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_dragging:
            new_pos = self.pos() + (event.pos() - self.drag_start_pos)
            self.setPos(new_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.is_dragging:
            self.is_dragging = False
            event.accept()
        super().mouseReleaseEvent(event)

    def remove_connection(self, connection_to_remove):
        self.connections.remove(connection_to_remove)

    def get_state(self):
        """Returns a dictionary of data to be saved."""
        return {
            'id': self.id,
            'type': self.__class__.__name__,
            'title': self.title,
            'x': self.pos().x(),
            'y': self.pos().y()
        }

    def set_state(self, data):
        """Restores node state from a dictionary."""
        self.setPos(data['x'], data['y'])
