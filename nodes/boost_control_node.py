import pygame
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsProxyWidget, QCheckBox, QLineEdit, QLabel, QWidget, QVBoxLayout, QPushButton, QHBoxLayout
from PyQt5.QtCore import QRectF, QPointF, Qt, QTimer, pyqtSignal, QObject, QVariant
from PyQt5.QtGui import QBrush, QColor, QPen, QFont, QFontMetrics
from .base_node import BaseNode, NodeSignalEmitter

class BoostControlNode(BaseNode):
    BOOST_STATE_READY = 0
    BOOST_STATE_BOOSTING = 1
    BOOST_STATE_COOLDOWN = 2

    def __init__(self, x=0, y=0, parent=None):
        super().__init__(title="Boost Control", x=x, y=y, w=220, h=240, parent=parent)
        self.inputs = 2
        self.input_values = [0.0, 0.0]
        self.output_value = 0.0

        self.boost_duration_s = 2.0
        self.cooldown_duration_s = 3.0
        self.boost_amount_us = 500

        self.state = self.BOOST_STATE_READY

        self.boost_timer = QTimer()
        self.boost_timer.setSingleShot(True)
        self.boost_timer.timeout.connect(self._end_boost)

        self.cooldown_timer = QTimer()
        self.cooldown_timer.setSingleShot(True)
        self.cooldown_timer.timeout.connect(self._end_cooldown)

        # UI elements
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("font-weight: bold; color: green;")
        self.boost_duration_edit = QLineEdit(str(self.boost_duration_s))
        self.cooldown_duration_edit = QLineEdit(str(self.cooldown_duration_s))
        self.boost_amount_edit = QLineEdit(str(self.boost_amount_us))

        self.boost_duration_edit.editingFinished.connect(self._update_boost_duration)
        self.cooldown_duration_edit.editingFinished.connect(self._update_cooldown_duration)
        self.boost_amount_edit.editingFinished.connect(self._update_boost_amount)

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)

        layout.addWidget(QLabel("Status:"))
        layout.addWidget(self.status_label)

        # QHBoxLayout for labels and edits for better layout
        hbox1 = QHBoxLayout()
        hbox1.addWidget(QLabel("Boost Dur (s):"))
        hbox1.addWidget(self.boost_duration_edit)
        layout.addLayout(hbox1)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(QLabel("Cooldown (s):"))
        hbox2.addWidget(self.cooldown_duration_edit)
        layout.addLayout(hbox2)

        hbox3 = QHBoxLayout()
        hbox3.addWidget(QLabel("Boost Amt (µs):"))
        hbox3.addWidget(self.boost_amount_edit)
        layout.addLayout(hbox3)

        proxy = QGraphicsProxyWidget(self)
        proxy.setWidget(widget)
        # Position adjusted to accommodate node title and input/output dots
        proxy.setPos(5, 30)
        proxy.resize(self.width - 10, self.height - 40) # Ensure it fits within the node

        self.output_signal = NodeSignalEmitter()
        self.output_signals = [self.output_signal]
        self.inputs_occupied = [False] * self.inputs

        self.input_dot_y_offset = 50 # Adjusted vertical offset for input dots
        self.output_dot_y_offset = 120 # Adjusted vertical offset for output dot
        self.input_rects = []
        for i in range(self.inputs):
            y = self.input_dot_y_offset + i * 40
            self.input_rects.append(QRectF(-5, y - 5, 10, 10))


    def is_input_occupied(self, index):
        if index < len(self.inputs_occupied):
            return self.inputs_occupied[index]
        return False

    def set_input_occupied(self, index, occupied):
        if index < len(self.inputs_occupied):
            self.inputs_occupied[index] = occupied

    def _update_boost_duration(self):
        try:
            self.boost_duration_s = float(self.boost_duration_edit.text())
            if self.boost_duration_s < 0: self.boost_duration_s = 0.0 # Prevent negative
            self.boost_duration_edit.setText(str(self.boost_duration_s))
        except ValueError:
            self.boost_duration_edit.setText(str(self.boost_duration_s))

    def _update_cooldown_duration(self):
        try:
            self.cooldown_duration_s = float(self.cooldown_duration_edit.text())
            if self.cooldown_duration_s < 0: self.cooldown_duration_s = 0.0 # Prevent negative
            self.cooldown_duration_edit.setText(str(self.cooldown_duration_s))
        except ValueError:
            self.cooldown_duration_edit.setText(str(self.cooldown_duration_s))

    def _update_boost_amount(self): # New: Update boost amount
        try:
            self.boost_amount_us = int(self.boost_amount_edit.text())
            # Clamp boost amount to a reasonable range for PPM (e.g., 0-1000us)
            self.boost_amount_us = max(0, min(1000, self.boost_amount_us))
            self.boost_amount_edit.setText(str(self.boost_amount_us))
        except ValueError:
            self.boost_amount_edit.setText(str(self.boost_amount_us))
        self._recalculate_output() # NEW: Force update on value change

    def set_value(self, value, input_index=0):
        # Update input value and then immediately recalculate output based on new value
        if input_index < len(self.input_values):
            self.input_values[input_index] = value

        self._recalculate_output()


    def _recalculate_output(self):
        throttle_input_normalized = self.input_values[0]
        boost_button_state = self.input_values[1]

        # Determine the PPM value of the throttle input alone
        base_throttle_ppm = int(1500 + throttle_input_normalized * 500)

        output_ppm = 0
        if self.state == self.BOOST_STATE_READY:
            self.status_label.setText("Ready")
            self.status_label.setStyleSheet("font-weight: bold; color: green;")

            output_ppm = base_throttle_ppm

            if boost_button_state > 0.5:
                self._start_boost()
                return # <-- ADD THIS LINE
        elif self.state == self.BOOST_STATE_BOOSTING:
            self.status_label.setText("Boosting")
            self.status_label.setStyleSheet("font-weight: bold; color: orange;")

            output_ppm = base_throttle_ppm + self.boost_amount_us
            if boost_button_state < 0.5:
                self._end_boost()
                return # <-- ADD THIS LINE
        elif self.state == self.BOOST_STATE_COOLDOWN:
            self.status_label.setText("Cooldown")
            self.status_label.setStyleSheet("font-weight: bold; color: red;")

            output_ppm = base_throttle_ppm

        output_ppm = max(1000, min(2000, output_ppm))
        self.output_value = (output_ppm - 1500) / 500.0

        self.output_signal.output_signal.emit(self.output_value, 0)
        self.update()


    def _start_boost(self):
        self.state = self.BOOST_STATE_BOOSTING
        self.boost_timer.start(int(self.boost_duration_s * 1000))
        self._recalculate_output() # Force immediate update


    def _end_boost(self):
        # Only transition to cooldown if boosting state. If button released during cooldown, stay in cooldown.
        if self.state == self.BOOST_STATE_BOOSTING:
            self.state = self.BOOST_STATE_COOLDOWN
            self.cooldown_timer.start(int(self.cooldown_duration_s * 1000))
            self._recalculate_output() # Force immediate update


    def _end_cooldown(self):
        self.state = self.BOOST_STATE_READY
        self._recalculate_output() # Force immediate update


    def paint(self, painter, option, widget=None):
        # Draw the rounded rect background and title as in BaseNode
        painter.setBrush(QBrush(QColor("#4A4A4A")))
        painter.setPen(QPen(QColor("#C0C0C0"), 2))
        painter.drawRoundedRect(self.rect, 10, 10)

        painter.setPen(QPen(QColor("#E0E0E0")))
        title_rect = QRectF(5, 5, self.width - 10, 20) # Define a smaller rect for title
        painter.drawText(title_rect, Qt.AlignLeft | Qt.AlignTop, self.title)

        # Draw input dots
        input_y_pos = self.input_dot_y_offset # Starting Y for first input dot
        for i in range(self.inputs):
            painter.setBrush(QBrush(QColor("#E0E0E0")))
            painter.drawEllipse(QPointF(0, input_y_pos), 5, 5) # Input dot on the left edge
            painter.setPen(QPen(QColor("#E0E0E0")))
            painter.drawText(QPointF(10, input_y_pos + 5), f"X{i+1}") # Input label
            input_y_pos += 40 # Space out input dots vertically

        # Draw output dot
        painter.setBrush(QBrush(QColor("#E0E0E0")))
        painter.drawEllipse(QPointF(self.width - 5, self.output_dot_y_offset), 5, 5) # Output dot on the right edge


    def get_input_dot_rects(self):
        rects = []
        input_y_pos = self.input_dot_y_offset
        for i in range(self.inputs):
            # Convert node-local coordinates to scene coordinates
            scene_pos = self.mapToScene(QPointF(0, input_y_pos))
            rects.append(QRectF(scene_pos.x() - 5, scene_pos.y() - 5, 10, 10))
            input_y_pos += 40
        return rects

    def get_output_dot_positions(self):
        # Output dot position for connections
        return [self.mapToScene(QPointF(self.width - 5, self.output_dot_y_offset))]

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Check if output dot was pressed to start a connection drag
            output_dot_rect = QRectF(self.width - 10, self.output_dot_y_offset - 5, 10, 10)
            if output_dot_rect.contains(event.pos()):
                self.scene().start_connection_drag(self.mapToScene(event.pos()), self, 0)
                event.accept()
                return
        super().mousePressEvent(event) # Call base class for dragging and selection
