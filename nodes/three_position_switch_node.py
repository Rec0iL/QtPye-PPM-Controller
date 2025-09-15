# nodes/three_position_switch_node.py
from PyQt5.QtWidgets import QGraphicsProxyWidget, QLabel, QWidget, QVBoxLayout
from PyQt5.QtCore import QRectF, QPointF, Qt
from PyQt5.QtGui import QColor, QPen
from .base_node import BaseNode, NodeSignalEmitter

class ThreePositionSwitchNode(BaseNode):
    def __init__(self, x=0, y=0, parent=None):
        super().__init__(title="3-Position Switch", x=x, y=y, w=220, h=160, parent=parent)
        self.inputs = 2
        self.output_value = 0.000001
        self.inputs_occupied = [False] * self.inputs
        self.output_signal = NodeSignalEmitter()
        self.output_signals = [self.output_signal]

        self.current_position = 1
        self.last_input_states = [0.0, 0.0]

        # UI element at the top
        self.status_label = QLabel("MIDDLE")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #FFFFFF; background-color: #FBC02D; border-radius: 5px; padding: 5px;")
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.status_label)
        proxy = QGraphicsProxyWidget(self)
        proxy.setWidget(widget)
        proxy.setPos(10, 30)
        proxy.resize(self.width - 20, 50)

        # Connection dots at the bottom
        y_start = 100
        line_height = 25
        self.input_rects = [
            QRectF(-5, y_start - 5, 10, 10),
            QRectF(-5, y_start + line_height - 5, 10, 10)
        ]
        output_y = y_start + (line_height / 2)
        self.output_rect = QRectF(self.width - 5, output_y - 5, 10, 10)
        self._update_output_and_ui()

    def set_value(self, value, input_index=0):
        current_input_value = float(value)
        state_changed = False
        if current_input_value > 0.5 and self.last_input_states[input_index] < 0.5:
            if input_index == 0:
                if self.current_position < 2:
                    self.current_position += 1
                    state_changed = True
            elif input_index == 1:
                if self.current_position > 0:
                    self.current_position -= 1
                    state_changed = True
        self.last_input_states[input_index] = current_input_value
        if state_changed:
            self._update_output_and_ui()

    def _update_output_and_ui(self):
        if self.current_position == 0:
            self.output_value = -1.0
            self.status_label.setText("DOWN")
            self.status_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #FFFFFF; background-color: #D32F2F; border-radius: 5px; padding: 5px;")
        elif self.current_position == 1:
            self.output_value = 0.000001
            self.status_label.setText("MIDDLE")
            self.status_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #FFFFFF; background-color: #FBC02D; border-radius: 5px; padding: 5px;")
        else:
            self.output_value = 1.0
            self.status_label.setText("UP")
            self.status_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #FFFFFF; background-color: #4CAF50; border-radius: 5px; padding: 5px;")
        self.output_signal.output_signal.emit(self.output_value, 0)
        self.update()

    def get_hotspot_rects(self):
        return self.input_rects + [self.output_rect]

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        painter.setPen(QPen(QColor("#E0E0E0")))
        painter.setBrush(QColor("#E0E0E0"))

        painter.drawEllipse(self.input_rects[0].center(), 5, 5)
        painter.drawText(QPointF(10, self.input_rects[0].center().y() + 5), "Up")
        painter.drawEllipse(self.input_rects[1].center(), 5, 5)
        painter.drawText(QPointF(10, self.input_rects[1].center().y() + 5), "Down")

        painter.drawEllipse(self.output_rect.center(), 5, 5)
        painter.drawText(QPointF(self.width - 40, self.output_rect.center().y() + 5), "Out")

    def get_input_dot_rects(self):
        rects = []
        for r in self.input_rects:
            scene_pos = self.mapToScene(r.center())
            rects.append(QRectF(scene_pos.x() - 5, scene_pos.y() - 5, 10, 10))
        return rects

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
