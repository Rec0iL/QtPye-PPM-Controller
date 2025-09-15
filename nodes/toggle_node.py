# nodes/toggle_node.py

from PyQt5.QtWidgets import QGraphicsProxyWidget, QLabel, QWidget, QVBoxLayout
from PyQt5.QtCore import QRectF, QPointF, Qt
from PyQt5.QtGui import QColor, QPen
from .base_node import BaseNode, NodeSignalEmitter

class ToggleNode(BaseNode):
    """
    A node that acts as a toggle switch. It changes its output state (0.0 or 1.0)
    each time it receives a rising edge signal from its input (e.g., a button press).
    """
    def __init__(self, x=0, y=0, parent=None):
        super().__init__(title="Toggle Switch", x=x, y=y, w=180, h=110, parent=parent)

        # --- Node Properties ---
        self.inputs = 1
        self.output_value = 0.0
        self.inputs_occupied = [False] * self.inputs
        self.output_signal = NodeSignalEmitter()
        self.output_signals = [self.output_signal]

        self.input_rects = [QRectF(-5, self.height / 2 - 5, 10, 10)]

        # --- Toggle State Logic ---
        self.is_on = False
        self.last_input_state = 0.0

        # --- UI Elements ---
        self.status_label = QLabel("OFF")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet(
            "font-size: 24px; font-weight: bold; color: #FFFFFF; background-color: #D32F2F; border-radius: 5px; padding: 5px;"
        )

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.addWidget(self.status_label)

        proxy = QGraphicsProxyWidget(self)
        proxy.setWidget(widget)
        proxy.setPos(5, 30)
        proxy.resize(self.width - 10, self.height - 40)

        # Set initial state
        self._update_output_and_ui()

    def set_value(self, value, input_index=0):
        current_input_value = float(value)

        # Rising-edge detection: toggle only when the button goes from off to on.
        if current_input_value > 0.5 and self.last_input_state < 0.5:
            self.is_on = not self.is_on
            self._update_output_and_ui()

        # Store the current input state for the next check
        self.last_input_state = current_input_value

    def _update_output_and_ui(self):
        """Updates the internal value, UI style, and emits the output signal."""
        if self.is_on:
            self.output_value = 1.0
            self.status_label.setText("ON")
            self.status_label.setStyleSheet(
                "font-size: 24px; font-weight: bold; color: #FFFFFF; background-color: #4CAF50; border-radius: 5px; padding: 5px;"
            )
        else:
            self.output_value = -1.0 # CHANGED FROM 0.0
            self.status_label.setText("OFF")
            self.status_label.setStyleSheet(
                "font-size: 24px; font-weight: bold; color: #FFFFFF; background-color: #D32F2F; border-radius: 5px; padding: 5px;"
            )

        self.output_signal.output_signal.emit(self.output_value, 0)
        self.update()

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)

        # Draw input and output dots
        painter.setPen(QPen(QColor("#C0C0C0"), 1))
        painter.setBrush(QColor("#E0E0E0"))
        painter.drawEllipse(QPointF(0, self.height / 2), 5, 5) # Input
        painter.drawEllipse(QPointF(self.width, self.height / 2), 5, 5) # Output

    def get_input_dot_rects(self):
        scene_pos = self.mapToScene(QPointF(0, self.height / 2))
        return [QRectF(scene_pos.x() - 5, scene_pos.y() - 5, 10, 10)]

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
