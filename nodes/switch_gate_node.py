# nodes/switch_gate_node.py
from PyQt5.QtWidgets import QGraphicsProxyWidget, QLabel, QWidget, QVBoxLayout
from PyQt5.QtCore import QRectF, QPointF, Qt
from PyQt5.QtGui import QColor, QPen
from .base_node import BaseNode, NodeSignalEmitter

class SwitchGateNode(BaseNode):
    """
    Selects between two inputs (A or B) based on a third switch input.
    """
    def __init__(self, x=0, y=0, parent=None):
        super().__init__(title="Switch Gate", x=x, y=y, w=220, h=180, parent=parent)
        self.inputs = 3
        self.inputs_occupied = [False] * self.inputs
        self.output_signals = [NodeSignalEmitter()]

        # [Switch, Input A, Input B]
        self.input_values = [-1.0, 0.0, 0.0]

        # --- UI Elements (at the top) ---
        self.status_label = QLabel("PASSING A")
        self.status_label.setAlignment(Qt.AlignCenter)
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.status_label)
        proxy = QGraphicsProxyWidget(self)
        proxy.setWidget(widget)
        proxy.setPos(10, 30)
        proxy.resize(self.width - 20, 50)

        # --- Connection Dots (at the bottom) ---
        y_start = 100
        line_height = 25
        self.input_rects = [
            QRectF(-5, y_start - 5, 10, 10),
            QRectF(-5, y_start + line_height - 5, 10, 10),
            QRectF(-5, y_start + (line_height * 2) - 5, 10, 10)
        ]
        output_y = y_start + line_height # Align with Input A
        self.output_rect = QRectF(self.width - 5, output_y - 5, 10, 10)

        self._update_ui() # Set initial UI state

    def set_value(self, value, input_index=0):
        if input_index < len(self.input_values):
            self.input_values[input_index] = float(value)
            self._recalculate_output()

    def _recalculate_output(self):
        switch_state = self.input_values[0]
        input_a = self.input_values[1]
        input_b = self.input_values[2]

        output_value = input_b if switch_state > 0 else input_a

        self.output_signals[0].output_signal.emit(output_value, 0)
        self._update_ui()

    def _update_ui(self):
        switch_state = self.input_values[0]
        if switch_state > 0:
            self.status_label.setText("PASSING B")
            self.status_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #FFFFFF; background-color: #4CAF50; border-radius: 5px; padding: 5px;")
        else:
            self.status_label.setText("PASSING A")
            self.status_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #FFFFFF; background-color: #00BFFF; border-radius: 5px; padding: 5px;")
        self.update()

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        painter.setPen(QPen(QColor("#E0E0E0")))
        painter.setBrush(QColor("#E0E0E0"))

        painter.drawEllipse(self.input_rects[0].center(), 5, 5)
        painter.drawText(QPointF(15, self.input_rects[0].center().y() + 5), "Switch")
        painter.drawEllipse(self.input_rects[1].center(), 5, 5)
        painter.drawText(QPointF(15, self.input_rects[1].center().y() + 5), "Input A")
        painter.drawEllipse(self.input_rects[2].center(), 5, 5)
        painter.drawText(QPointF(15, self.input_rects[2].center().y() + 5), "Input B")

        painter.drawEllipse(self.output_rect.center(), 5, 5)
        painter.drawText(QPointF(self.width - 40, self.output_rect.center().y() + 5), "Out")

    def get_hotspot_rects(self):
        return self.input_rects + [self.output_rect]

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
            if self.output_rect.contains(event.pos()):
                pos = self.mapToScene(self.output_rect.center())
                self.scene().start_connection_drag(pos, self, 0)
                event.accept()
                return
        super().mousePressEvent(event)
