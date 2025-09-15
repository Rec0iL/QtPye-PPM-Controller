# nodes/switch_gate_node.py
from PyQt5.QtCore import QRectF, QPointF, Qt
from PyQt5.QtGui import QColor, QPen
from .base_node import BaseNode, NodeSignalEmitter

class SwitchGateNode(BaseNode):
    """
    Selects between two inputs (A or B) based on a third switch input.
    """
    def __init__(self, x=0, y=0, parent=None):
        super().__init__(title="Switch Gate", x=x, y=y, w=200, h=140, parent=parent)
        self.inputs = 3
        self.inputs_occupied = [False] * self.inputs
        self.output_signals = [NodeSignalEmitter()]

        # [Switch, Input A, Input B]
        self.input_values = [-1.0, 0.0, 0.0]

        # Define local rects for connection dots
        self.input_rects = [
            QRectF(-5, 45 - 5, 10, 10),  # Switch
            QRectF(-5, 75 - 5, 10, 10),  # Input A
            QRectF(-5, 105 - 5, 10, 10)  # Input B
        ]
        # Center the output dot vertically with Input A
        self.output_rect = QRectF(self.width - 5, 75 - 5, 10, 10)

    def set_value(self, value, input_index=0):
        if input_index < len(self.input_values):
            self.input_values[input_index] = float(value)
            self._recalculate_output()

    def _recalculate_output(self):
        switch_state = self.input_values[0]
        input_a = self.input_values[1]
        input_b = self.input_values[2]

        # If switch_state is positive (ON), pass Input B. Otherwise, pass Input A.
        output_value = input_b if switch_state > 0 else input_a

        self.output_signals[0].output_signal.emit(output_value, 0)

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        painter.setPen(QPen(QColor("#E0E0E0")))
        painter.setBrush(QColor("#E0E0E0"))

        painter.drawEllipse(self.input_rects[0].center(), 5, 5)
        painter.drawText(QPointF(15, 45 + 5), "Switch")
        painter.drawEllipse(self.input_rects[1].center(), 5, 5)
        painter.drawText(QPointF(15, 75 + 5), "Input A")
        painter.drawEllipse(self.input_rects[2].center(), 5, 5)
        painter.drawText(QPointF(15, 105 + 5), "Input B")

        painter.drawEllipse(self.output_rect.center(), 5, 5)
        painter.drawText(QPointF(self.width - 40, 75 + 5), "Out")

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
