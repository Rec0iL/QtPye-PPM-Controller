# connections.py
import random
from PyQt5.QtWidgets import QGraphicsItem
from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QPen, QColor, QPainterPath, QBrush

class Connection(QGraphicsItem):
    def __init__(self, start_node, start_index, end_node, end_index=0, parent=None):
        super().__init__(parent)
        self.start_node = start_node
        self.start_index = start_index
        self.end_node = end_node
        self.end_index = end_index
        self.slot = None

        self.setZValue(1)
        self.connection_color = self._generate_random_color()
        self.update_path()
        self.start_node.connections.append(self)
        self.end_node.connections.append(self)

    def _generate_random_color(self):
        """Generates a random, saturated color."""
        hue = random.randint(0, 359)
        saturation = 255
        value = 255
        return QColor.fromHsv(hue, saturation, value)

    def boundingRect(self):
        return self.path.boundingRect().normalized().adjusted(-10, -10, 10, 10)

    def paint(self, painter, option, widget=None):
        pen = QPen(self.connection_color, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        painter.setRenderHint(painter.Antialiasing, True)
        painter.drawPath(self.path)

        painter.setBrush(QBrush(self.connection_color))
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        start_pos = self.start_node.get_output_dot_positions()[self.start_index]

        if hasattr(self.end_node, 'input_rects'):
            end_pos = self.end_node.mapToScene(self.end_node.input_rects[self.end_index].center())
        else:
            end_pos = self.end_node.mapToScene(self.end_node.input_rect.center())

        painter.drawEllipse(start_pos, 4, 4)
        painter.drawEllipse(end_pos, 4, 4)

    def update_path(self):
        self.prepareGeometryChange()

        if self.start_node and self.end_node:
            start_pos = self.start_node.get_output_dot_positions()[self.start_index]

            if hasattr(self.end_node, 'input_rects'):
                end_pos = self.end_node.mapToScene(self.end_node.input_rects[self.end_index].center())
            else:
                end_pos = self.end_node.mapToScene(self.end_node.input_rect.center())

            self.path = QPainterPath(start_pos)
            dx = abs(start_pos.x() - end_pos.x()) * 0.5
            start_tangent = QPointF(start_pos.x() + dx, start_pos.y())
            end_tangent = QPointF(end_pos.x() - dx, end_pos.y())
            self.path.cubicTo(start_tangent, end_tangent, end_pos)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            if self.scene():
                self.scene().remove_connection(self)
            event.accept()
        super().mousePressEvent(event)
