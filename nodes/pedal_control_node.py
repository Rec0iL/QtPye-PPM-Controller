# nodes/pedal_control_node.py
from PyQt5.QtWidgets import QGraphicsProxyWidget, QLineEdit, QLabel, QWidget, QGridLayout
from PyQt5.QtCore import QRectF, QPointF, Qt
from PyQt5.QtGui import QColor, QPen
from .base_node import BaseNode, NodeSignalEmitter

class PedalControlNode(BaseNode):
    def __init__(self, x=0, y=0, parent=None):
        super().__init__(title="Pedal Control", x=x, y=y, w=250, h=230, parent=parent)
        self.inputs = 2
        self.inputs_occupied = [False] * self.inputs
        self.output_signals = [NodeSignalEmitter()]

        # State
        self.throttle_limit = 100
        self.brake_limit = 100
        self.brake_deadzone = 5  # Default 5% deadzone for brake activation
        self.center_us = 1500    # Default 1500us center point
        self.input_values = [-1.0, -1.0] # [Throttle, Brake]

        # UI Elements
        widget = QWidget()
        layout = QGridLayout(widget)
        layout.setContentsMargins(10, 5, 10, 5)

        layout.addWidget(QLabel("Throttle Limit %:"), 0, 0)
        self.throttle_edit = QLineEdit(str(self.throttle_limit))
        layout.addWidget(self.throttle_edit, 0, 1)

        layout.addWidget(QLabel("Brake Limit %:"), 1, 0)
        self.brake_edit = QLineEdit(str(self.brake_limit))
        layout.addWidget(self.brake_edit, 1, 1)

        layout.addWidget(QLabel("Brake Deadzone %:"), 2, 0)
        self.deadzone_edit = QLineEdit(str(self.brake_deadzone))
        layout.addWidget(self.deadzone_edit, 2, 1)

        layout.addWidget(QLabel("Center (µs):"), 3, 0)
        self.center_edit = QLineEdit(str(self.center_us))
        layout.addWidget(self.center_edit, 3, 1)

        # Connect all edit fields to the same update function
        edits = [self.throttle_edit, self.brake_edit, self.deadzone_edit, self.center_edit]
        for edit in edits:
            edit.editingFinished.connect(self._update_settings)

        proxy = QGraphicsProxyWidget(self)
        proxy.setWidget(widget)
        proxy.setPos(5, 30)
        proxy.resize(self.width - 10, 120)

        # Connection dots at the bottom
        y_start = 190
        line_height = 25
        self.input_rects = [
            QRectF(-5, y_start - 5, 10, 10),
            QRectF(-5, y_start + line_height - 5, 10, 10)
        ]
        output_y = y_start + (line_height / 2)
        self.output_rect = QRectF(self.width - 5, output_y - 5, 10, 10)

    def _update_settings(self):
        try:
            self.throttle_limit = max(0, min(100, int(self.throttle_edit.text())))
            self.brake_limit = max(0, min(100, int(self.brake_edit.text())))
            self.brake_deadzone = max(0, min(100, int(self.deadzone_edit.text())))
            self.center_us = max(1000, min(2000, int(self.center_edit.text())))
        except ValueError:
            pass # Ignore invalid input

        self.throttle_edit.setText(str(self.throttle_limit))
        self.brake_edit.setText(str(self.brake_limit))
        self.deadzone_edit.setText(str(self.brake_deadzone))
        self.center_edit.setText(str(self.center_us))
        self._recalculate_output()

    def get_state(self):
        state = super().get_state()
        state['throttle_limit'] = self.throttle_limit
        state['brake_limit'] = self.brake_limit
        state['brake_deadzone'] = self.brake_deadzone
        state['center_us'] = self.center_us
        return state

    def set_state(self, data):
        super().set_state(data)
        if 'throttle_limit' in data:
            self.throttle_limit = data['throttle_limit']
            self.throttle_edit.setText(str(self.throttle_limit))
        if 'brake_limit' in data:
            self.brake_limit = data['brake_limit']
            self.brake_edit.setText(str(self.brake_limit))
        if 'brake_deadzone' in data:
            self.brake_deadzone = data['brake_deadzone']
            self.deadzone_edit.setText(str(self.brake_deadzone))
        if 'center_us' in data:
            self.center_us = data['center_us']
            self.center_edit.setText(str(self.center_us))

    def set_value(self, value, input_index=0):
        if input_index < len(self.input_values):
            self.input_values[input_index] = float(value)
            self._recalculate_output()

    def _recalculate_output(self):
        raw_throttle, raw_brake = self.input_values

        norm_throttle = (raw_throttle + 1.0) / 2.0
        norm_brake = (raw_brake + 1.0) / 2.0

        limited_throttle = norm_throttle * (self.throttle_limit / 100.0)
        limited_brake = norm_brake * (self.brake_limit / 100.0)

        combined_output = 0.0
        # Brake has priority over throttle only if it's past the deadzone
        if limited_brake > (self.brake_deadzone / 100.0):
            combined_output = -limited_brake
        elif limited_throttle > 0.01:
            combined_output = limited_throttle

        # Convert the [-1, 1] signal to microseconds using the custom center
        span_positive = 2000 - self.center_us
        span_negative = self.center_us - 1000

        output_us = self.center_us
        if combined_output > 0:
            output_us = self.center_us + (combined_output * span_positive)
        elif combined_output < 0:
            output_us = self.center_us + (combined_output * span_negative)

        # Re-normalize the microsecond value back to the standard [-1, 1] range for output
        # This keeps it compatible with the PPM Channel Node
        final_normalized_output = (output_us - 1500) / 500.0

        self.output_signals[0].output_signal.emit(final_normalized_output, 0)
        self.update()

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        painter.setPen(QPen(QColor("#E0E0E0")))
        painter.setBrush(QColor("#E0E0E0"))

        painter.drawEllipse(self.input_rects[0].center(), 5, 5)
        painter.drawText(QPointF(15, self.input_rects[0].center().y() + 5), "Throttle")
        painter.drawEllipse(self.input_rects[1].center(), 5, 5)
        painter.drawText(QPointF(15, self.input_rects[1].center().y() + 5), "Brake")

        painter.drawEllipse(self.output_rect.center(), 5, 5)
        painter.drawText(QPointF(self.width - 80, self.output_rect.center().y() + 5), "Combined Out")

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
            output_hotspot = QRectF(self.width - 10, self.output_rect.y(), 10, 10)
            if output_hotspot.contains(event.pos()):
                pos = self.mapToScene(self.output_rect.center())
                self.scene().start_connection_drag(pos, self, 0)
                event.accept()
                return
        super().mousePressEvent(event)
