# nodes/expo_curve_node.py
from PyQt5.QtWidgets import QGraphicsProxyWidget, QLabel, QLineEdit, QWidget, QHBoxLayout, QGraphicsItem
from PyQt5.QtCore import QRectF, QPointF, Qt
from PyQt5.QtGui import QColor, QPen, QPainterPath
from .base_node import BaseNode, NodeSignalEmitter

class CurveVisualizer(QGraphicsItem):
    """A simple widget to draw the expo curve and current position."""
    def __init__(self, parent_node):
        super().__init__(parent_node)
        self.parent_node = parent_node

    def boundingRect(self):
        return QRectF(0, 0, 100, 100)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(painter.Antialiasing)
        bounds = self.boundingRect()

        painter.setPen(QPen(QColor("#555555"), 1))
        painter.drawRect(bounds)
        painter.drawLine(int(bounds.center().x()), int(bounds.top()), int(bounds.center().x()), int(bounds.bottom()))
        painter.drawLine(int(bounds.left()), int(bounds.center().y()), int(bounds.right()), int(bounds.center().y()))

        painter.setPen(QPen(QColor("#00BFFF"), 2))
        path = QPainterPath()
        expo = self.parent_node.expo_amount

        for i in range(int(bounds.width()) + 1):
            x_norm = (i / bounds.width()) * 2.0 - 1.0
            y_norm = (expo * (x_norm ** 3)) + ((1 - expo) * x_norm)
            y_pixel = bounds.height() - ((y_norm + 1.0) / 2.0 * bounds.height())
            if i == 0: path.moveTo(i, y_pixel)
            else: path.lineTo(i, y_pixel)
        painter.drawPath(path)

        input_val = self.parent_node.current_input_value
        y_norm_dot = (expo * (input_val ** 3)) + ((1 - expo) * input_val)
        x_pixel = (input_val + 1.0) / 2.0 * bounds.width()
        y_pixel = bounds.height() - ((y_norm_dot + 1.0) / 2.0 * bounds.height())

        painter.setBrush(QColor("#FF5722"))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(x_pixel, y_pixel), 4, 4)

class ExpoCurveNode(BaseNode):
    def __init__(self, x=0, y=0, parent=None):
        super().__init__(title="Expo Curve", x=x, y=y, w=200, h=220, parent=parent)
        self.inputs = 1
        self.output_value = 0.0
        self.inputs_occupied = [False]
        self.output_signal = NodeSignalEmitter()
        self.output_signals = [self.output_signal]

        self.expo_amount = 0.0
        self.current_input_value = 0.0

        # UI Elements at the top
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.addWidget(QLabel("Expo %:"))
        self.expo_edit = QLineEdit("0")
        self.expo_edit.editingFinished.connect(self._update_expo)
        layout.addWidget(self.expo_edit)
        proxy = QGraphicsProxyWidget(self)
        proxy.setWidget(widget)
        proxy.setPos(5, 30)
        proxy.resize(self.width - 10, 40)

        # Curve Visualizer below the editor
        self.visualizer = CurveVisualizer(self)
        self.visualizer.setPos(50, 70)

        # Connection dots at the bottom
        dot_y = 195
        self.input_rect = QRectF(-5, dot_y - 5, 10, 10)
        self.output_rect = QRectF(self.width - 5, dot_y - 5, 10, 10)

    def _update_expo(self):
        try:
            val = int(self.expo_edit.text())
            val = max(0, min(100, val))
            self.expo_amount = val / 100.0
            self.expo_edit.setText(str(val))
            self.visualizer.update()
        except ValueError:
            self.expo_edit.setText(str(int(self.expo_amount * 100)))

    def set_value(self, value, input_index=0):
        input_val = float(value)
        self.current_input_value = input_val
        expo = self.expo_amount
        self.output_value = (expo * (input_val ** 3)) + ((1 - expo) * input_val)
        self.output_signal.output_signal.emit(self.output_value, 0)
        self.visualizer.update()

    def get_hotspot_rects(self):
        return [self.input_rect, self.output_rect]

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        painter.setPen(QPen(QColor("#E0E0E0")))
        painter.setBrush(QColor("#E0E0E0"))

        painter.drawEllipse(self.input_rect.center(), 5, 5)
        painter.drawText(QPointF(15, self.input_rect.center().y() + 5), "In")

        painter.drawEllipse(self.output_rect.center(), 5, 5)
        painter.drawText(QPointF(self.width - 40, self.output_rect.center().y() + 5), "Out")

    def get_input_dot_rects(self):
        scene_pos = self.mapToScene(self.input_rect.center())
        return [QRectF(scene_pos.x() - 5, scene_pos.y() - 5, 10, 10)]

    def get_output_dot_positions(self):
        return [self.mapToScene(self.output_rect.center())]

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            output_hotspot = QRectF(self.width - 10, self.output_rect.y(), 10, 10)
            if output_hotspot.contains(event.pos()):
                pos = self.mapToScene(output_hotspot.center())
                self.scene().start_connection_drag(pos, self, 0)
                event.accept()
                return
        super().mousePressEvent(event)
