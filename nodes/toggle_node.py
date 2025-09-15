# nodes/toggle_node.py
from PyQt5.QtWidgets import QGraphicsProxyWidget, QLabel, QWidget, QVBoxLayout
from PyQt5.QtCore import QRectF, QPointF, Qt
from PyQt5.QtGui import QColor, QPen
from .base_node import BaseNode, NodeSignalEmitter

class ToggleNode(BaseNode):
    def __init__(self, x=0, y=0, parent=None):
        super().__init__(title="Toggle Switch", x=x, y=y, w=180, h=140, parent=parent)
        self.inputs = 1
        self.output_value = -1.0
        self.inputs_occupied = [False]
        self.output_signal = NodeSignalEmitter()
        self.output_signals = [self.output_signal]
        self.is_on = False
        self.last_input_state = 0.0

        # UI Element at the top
        self.status_label = QLabel("OFF")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet(
            "font-size: 24px; font-weight: bold; color: #FFFFFF; background-color: #D32F2F; border-radius: 5px; padding: 5px;"
        )
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.status_label)
        proxy = QGraphicsProxyWidget(self)
        proxy.setWidget(widget)
        proxy.setPos(10, 30)
        proxy.resize(self.width - 20, 50)

        # Connection dots at the bottom
        self.input_rect = QRectF(-5, 105 - 5, 10, 10)
        self.output_rect = QRectF(self.width - 5, 105 - 5, 10, 10)
        self._update_output_and_ui()

    def set_value(self, value, input_index=0):
        current_input_value = float(value)
        if current_input_value > 0.5 and self.last_input_state < 0.5:
            self.is_on = not self.is_on
            self._update_output_and_ui()
        self.last_input_state = current_input_value

    def _update_output_and_ui(self):
        if self.is_on:
            self.output_value = 1.0
            self.status_label.setText("ON")
            self.status_label.setStyleSheet(
                "font-size: 24px; font-weight: bold; color: #FFFFFF; background-color: #4CAF50; border-radius: 5px; padding: 5px;"
            )
        else:
            self.output_value = -1.0
            self.status_label.setText("OFF")
            self.status_label.setStyleSheet(
                "font-size: 24px; font-weight: bold; color: #FFFFFF; background-color: #D32F2F; border-radius: 5px; padding: 5px;"
            )
        self.output_signal.output_signal.emit(self.output_value, 0)
        self.update()

    def get_hotspot_rects(self):
        return [self.input_rect, self.output_rect]

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        painter.setPen(QPen(QColor("#E0E0E0")))
        painter.setBrush(QColor("#E0E0E0"))

        painter.drawEllipse(self.input_rect.center(), 5, 5)
        painter.drawText(QPointF(15, 105 + 5), "In")

        painter.drawEllipse(self.output_rect.center(), 5, 5)
        painter.drawText(QPointF(self.width - 40, 105 + 5), "Out")

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
