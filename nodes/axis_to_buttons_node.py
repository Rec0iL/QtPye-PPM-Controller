# nodes/axis_to_buttons_node.py
from PyQt5.QtWidgets import QGraphicsProxyWidget, QLineEdit, QLabel, QWidget, QHBoxLayout
from PyQt5.QtCore import QRectF, QPointF, Qt
from PyQt5.QtGui import QColor, QPen
from .base_node import BaseNode, NodeSignalEmitter

class AxisToButtonsNode(BaseNode):
    def __init__(self, x=0, y=0, parent=None):
        # Increased height slightly for better layout
        super().__init__(title="Axis to Buttons", x=x, y=y, w=250, h=140, parent=parent)
        self.inputs = 1
        self.inputs_occupied = [False]
        self.output_signals = [NodeSignalEmitter(), NodeSignalEmitter()]

        self.deadzone = 0.25
        self.output_values = [-1.0, -1.0]

        # UI Elements are now at the top
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.addWidget(QLabel("Deadzone:"))
        self.deadzone_edit = QLineEdit(str(self.deadzone))
        self.deadzone_edit.editingFinished.connect(self._update_deadzone)
        layout.addWidget(self.deadzone_edit)

        proxy = QGraphicsProxyWidget(self)
        proxy.setWidget(widget)
        proxy.setPos(10, 30)
        proxy.resize(self.width - 20, 40)

        # Dots and labels are positioned below the UI
        self.input_rect = QRectF(-5, 100 - 5, 10, 10)
        self.output_rects = [
            QRectF(self.width - 5, 85 - 5, 10, 10),
            QRectF(self.width - 5, 115 - 5, 10, 10)
        ]

    def _update_deadzone(self):
        try:
            val = float(self.deadzone_edit.text())
            self.deadzone = max(0.0, min(1.0, val))
            self.deadzone_edit.setText(str(self.deadzone))
        except ValueError:
            self.deadzone_edit.setText(str(self.deadzone))

    def get_state(self):
        state = super().get_state()
        state['deadzone'] = self.deadzone
        return state

    def set_state(self, data):
        super().set_state(data)
        if 'deadzone' in data:
            self.deadzone = data['deadzone']
            self.deadzone_edit.setText(str(self.deadzone))

    def set_value(self, value, input_index=0):
        input_val = float(value)
        pos_active = 1.0 if input_val > self.deadzone else -1.0
        if pos_active != self.output_values[0]:
            self.output_values[0] = pos_active
            self.output_signals[0].output_signal.emit(pos_active, 0)

        neg_active = 1.0 if input_val < -self.deadzone else -1.0
        if neg_active != self.output_values[1]:
            self.output_values[1] = neg_active
            self.output_signals[1].output_signal.emit(neg_active, 0)
        self.update()

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        painter.setPen(QPen(QColor("#E0E0E0")))
        painter.setBrush(QColor("#E0E0E0"))

        # Draw input dot and label
        painter.drawEllipse(self.input_rect.center(), 5, 5)
        painter.drawText(QPointF(15, 100 + 5), "Axis In")

        # Draw output dots and labels
        painter.drawEllipse(self.output_rects[0].center(), 5, 5)
        painter.drawText(QPointF(self.width - 85, 85 + 5), "Positive +")

        painter.drawEllipse(self.output_rects[1].center(), 5, 5)
        painter.drawText(QPointF(self.width - 85, 115 + 5), "Negative -")

    def get_hotspot_rects(self):
        return [self.input_rect] + self.output_rects

    def get_input_dot_rects(self):
        scene_pos = self.mapToScene(self.input_rect.center())
        return [QRectF(scene_pos.x() - 5, scene_pos.y() - 5, 10, 10)]

    def get_output_dot_positions(self):
        return [self.mapToScene(r.center()) for r in self.output_rects]

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            output_hotspots = [
                QRectF(self.width - 10, 85 - 5, 10, 10),
                QRectF(self.width - 10, 115 - 5, 10, 10)
            ]
            for i, hotspot in enumerate(output_hotspots):
                if hotspot.contains(event.pos()):
                    pos = self.mapToScene(hotspot.center())
                    self.scene().start_connection_drag(pos, self, i)
                    event.accept()
                    return
        super().mousePressEvent(event)
