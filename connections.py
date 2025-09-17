# connections.py
from PyQt5.QtWidgets import QGraphicsItem
from PyQt5.QtCore import QPointF, Qt, QTimer
from PyQt5.QtGui import QPen, QColor, QPainterPath, QBrush, QPainterPathStroker

class Connection(QGraphicsItem):
    # A palette of 20 distinct hues, spaced out for variety
    COLOR_PALETTE = [i * 18 for i in range(20)]
    next_color_index = 0

    def __init__(self, start_node, start_index, end_node, end_index=0, parent=None):
        super().__init__(parent)
        self.start_node = start_node
        self.start_index = start_index
        self.end_node = end_node
        self.end_index = end_index
        self.slot = None
        self.is_highlighted = False

        self.setZValue(1)
        self.setAcceptHoverEvents(True) # Enable hover events for this item

        # --- New Color and Pen Logic ---
        hue = Connection.COLOR_PALETTE[Connection.next_color_index]
        Connection.next_color_index = (Connection.next_color_index + 1) % len(Connection.COLOR_PALETTE)

        base_color = QColor.fromHsv(hue, 255, 255)
        highlight_color = base_color.lighter(150)

        self.normal_pen = QPen(base_color, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        self.highlight_pen = QPen(highlight_color, 4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)

        self.update_path()
        self.start_node.connections.append(self)
        self.end_node.connections.append(self)

    def hoverEnterEvent(self, event):
        """When the mouse enters the connection's shape, highlight it."""
        self.set_highlighted(True)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        """When the mouse leaves, un-highlight it."""
        self.set_highlighted(False)
        super().hoverLeaveEvent(event)

    def set_highlighted(self, highlighted):
        """Toggles the highlighted state and triggers a repaint."""
        self.is_highlighted = highlighted
        self.update()

    def shape(self):
        """Returns a precise shape for collision detection."""
        stroker = QPainterPathStroker()
        stroker.setWidth(10) # Create a 10-pixel wide clickable area
        stroker.setCapStyle(Qt.RoundCap)
        stroker.setJoinStyle(Qt.RoundJoin)
        return stroker.createStroke(self.path)

    def boundingRect(self):
        return self.shape().boundingRect()

    def paint(self, painter, option, widget=None):
        if self.is_highlighted:
            painter.setPen(self.highlight_pen)
        else:
            painter.setPen(self.normal_pen)

        painter.setRenderHint(painter.Antialiasing, True)
        painter.drawPath(self.path)

        painter.setBrush(QBrush(self.normal_pen.color()))
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        start_pos = self.start_node.get_output_dot_positions()[self.start_index]

        if hasattr(self.end_node, 'get_input_dot_rects'):
            end_pos = self.end_node.get_input_dot_rects()[self.end_index].center()
        else:
            end_pos = self.end_node.mapToScene(self.end_node.input_rect.center())

        painter.drawEllipse(start_pos, 4, 4)
        painter.drawEllipse(end_pos, 4, 4)

    def update_path(self):
        self.prepareGeometryChange()
        if self.start_node and self.end_node:
            start_pos = self.start_node.get_output_dot_positions()[self.start_index]

            if hasattr(self.end_node, 'get_input_dot_rects'):
                end_pos = self.end_node.get_input_dot_rects()[self.end_index].center()
            else:
                 end_pos = self.end_node.mapToScene(self.end_node.input_rect.center())

            self.path = QPainterPath(start_pos)
            dx = abs(start_pos.x() - end_pos.x()) * 0.5
            start_tangent = QPointF(start_pos.x() + dx, start_pos.y())
            end_tangent = QPointF(end_pos.x() - dx, end_pos.y())
            self.path.cubicTo(start_tangent, end_tangent, end_pos)
        self.update() # Ensure bounding rect is updated with the path

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            if self.scene():
                QTimer.singleShot(0, lambda: self.scene().remove_connection(self))
            event.accept()
        else:
            super().mousePressEvent(event)
