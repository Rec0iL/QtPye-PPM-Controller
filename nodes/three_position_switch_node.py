# nodes/three_position_switch_node.py

from PyQt5.QtWidgets import QGraphicsProxyWidget, QLabel, QWidget, QVBoxLayout
from PyQt5.QtCore import QRectF, QPointF, Qt
from PyQt5.QtGui import QColor, QPen
from .base_node import BaseNode, NodeSignalEmitter

class ThreePositionSwitchNode(BaseNode):
    """
    A node that uses two button inputs to cycle through three output states
    (Down, Middle, Up), corresponding to output values (-1.0, 0.0, 1.0).
    """
    def __init__(self, x=0, y=0, parent=None):
        super().__init__(title="3-Position Switch", x=x, y=y, w=200, h=120, parent=parent)

        # --- Node Properties ---
        self.inputs = 2
        self.output_value = 0.0
        self.inputs_occupied = [False] * self.inputs
        self.output_signal = NodeSignalEmitter()
        self.output_signals = [self.output_signal]
        self.input_rects = [
            QRectF(-5, 40 - 5, 10, 10),
            QRectF(-5, 70 - 5, 10, 10)
        ]

        # --- State Logic ---
        # Positions: 0=Down, 1=Middle, 2=Up
        self.current_position = 1  # Start in the middle
        self.last_input_states = [0.0, 0.0]

        # --- UI Elements ---
        self.status_label = QLabel("MIDDLE")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet(
            "font-size: 22px; font-weight: bold; color: #FFFFFF; background-color: #FBC02D; border-radius: 5px; padding: 5px;"
        )

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.addWidget(self.status_label)

        proxy = QGraphicsProxyWidget(self)
        proxy.setWidget(widget)
        proxy.setPos(5, 35)
        proxy.resize(self.width - 10, self.height - 50)

        # Set initial state
        self._update_output_and_ui()

    def set_value(self, value, input_index=0):
        current_input_value = float(value)
        state_changed = False

        # Rising-edge detection for the given input button
        if current_input_value > 0.5 and self.last_input_states[input_index] < 0.5:
            # Input 0 is the "Up" button
            if input_index == 0:
                if self.current_position < 2:
                    self.current_position += 1
                    state_changed = True
            # Input 1 is the "Down" button
            elif input_index == 1:
                if self.current_position > 0:
                    self.current_position -= 1
                    state_changed = True

        # Store the current input state for the next check
        self.last_input_states[input_index] = current_input_value

        if state_changed:
            self._update_output_and_ui()

    def _update_output_and_ui(self):
        """Updates the internal value, UI style, and emits the output signal."""
        if self.current_position == 0: # Down
            self.output_value = -1.0
            self.status_label.setText("DOWN")
            self.status_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #FFFFFF; background-color: #D32F2F; border-radius: 5px; padding: 5px;")
        elif self.current_position == 1: # Middle
            self.output_value = 0.000001
            self.status_label.setText("MIDDLE")
            self.status_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #FFFFFF; background-color: #FBC02D; border-radius: 5px; padding: 5px;")
        else: # Up
            self.output_value = 1.0
            self.status_label.setText("UP")
            self.status_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #FFFFFF; background-color: #4CAF50; border-radius: 5px; padding: 5px;")

        self.output_signal.output_signal.emit(self.output_value, 0)
        self.update()

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)

        painter.setPen(QPen(QColor("#E0E0E0")))
        painter.setBrush(QColor("#E0E0E0"))
        # Draw input dots and labels
        painter.drawEllipse(self.input_rects[0].center(), 5, 5)
        painter.drawText(QPointF(10, 45), "Up (X1)")
        painter.drawEllipse(self.input_rects[1].center(), 5, 5)
        painter.drawText(QPointF(10, 75), "Down (X2)")

        # Draw output dot
        painter.drawEllipse(QPointF(self.width, self.height / 2), 5, 5)

    def get_input_dot_rects(self):
        rects = []
        for rect in self.input_rects:
            scene_pos = self.mapToScene(rect.center())
            rects.append(QRectF(scene_pos.x() - 5, scene_pos.y() - 5, 10, 10))
        return rects

    def get_output_dot_positions(self):
        return [self.mapToScene(QPointF(self.width, self.height / 2))]

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            output_dot_rect = QRectF(self.width - 10, self.height / 2 - 5, 10, 10)
            if output_dot_rect.contains(event.pos()):
                self.scene().start_connection_drag(self.mapToScene(event.pos()), self, 0)
                event.accept()
                return
        super().mousePressEvent(event)
