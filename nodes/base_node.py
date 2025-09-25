# nodes/base_node.py
import uuid
from PyQt5.QtWidgets import QGraphicsItem
from PyQt5.QtCore import QRectF, QPointF, Qt, pyqtSignal, QObject
from PyQt5.QtGui import QBrush, QColor, QPen

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

        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
        self.setAcceptHoverEvents(True) # Enable hover events

        self.rect = QRectF(0, 0, self.width, self.height)
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
        title_rect = QRectF(0, 5, self.width, 25)
        painter.drawText(title_rect, Qt.AlignCenter, self.title)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            for conn in self.connections:
                conn.update_path()
        return super().itemChange(change, value)

    def remove_connection(self, connection_to_remove):
        if connection_to_remove in self.connections:
            self.connections.remove(connection_to_remove)

    # --- NEW METHOD ---
    def cleanup(self):
        """
        Clean up resources used by the node.
        Child classes should override this to stop timers, etc.
        """
        print(f"Cleaning up base node: {self.title}")
        # Base implementation does nothing, but it's here to be overridden.
        pass

    def get_state(self):
        return {
            'id': self.id,
            'type': self.__class__.__name__,
            'title': self.title,
            'x': self.pos().x(),
            'y': self.pos().y()
        }

    def set_state(self, data):
        self.setPos(data['x'], data['y'])

    def get_hotspot_rects(self):
        """Child classes must override this to return their connection dot hitboxes."""
        return []

    def hoverMoveEvent(self, event):
        """Enable/disable dragging based on cursor position."""
        hotspots = self.get_hotspot_rects()
        is_over_hotspot = any(rect.contains(event.pos()) for rect in hotspots)

        if is_over_hotspot:
            self.setFlag(QGraphicsItem.ItemIsMovable, False)
            self.setCursor(Qt.PointingHandCursor)
        else:
            self.setFlag(QGraphicsItem.ItemIsMovable, True)
            self.setCursor(Qt.ArrowCursor)
        super().hoverMoveEvent(event)

    def hoverEnterEvent(self, event):
        """When the mouse enters the node, highlight its connections."""
        for conn in self.connections:
            conn.set_highlighted(True)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        """When the mouse leaves the node, un-highlight its connections."""
        for conn in self.connections:
            conn.set_highlighted(False)
        super().hoverLeaveEvent(event)
