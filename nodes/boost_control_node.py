# nodes/boost_control_node.py
from PyQt5.QtWidgets import QGraphicsProxyWidget, QLineEdit, QLabel, QWidget, QVBoxLayout, QHBoxLayout
from PyQt5.QtCore import QRectF, QPointF, Qt, QTimer
from PyQt5.QtGui import QBrush, QColor, QPen
from .base_node import BaseNode, NodeSignalEmitter

class BoostControlNode(BaseNode):
    BOOST_STATE_READY = 0
    BOOST_STATE_BOOSTING = 1
    BOOST_STATE_COOLDOWN = 2

    def __init__(self, x=0, y=0, parent=None):
        super().__init__(title="Boost Control", x=x, y=y, w=220, h=200, parent=parent)
        self.inputs = 2
        self.input_values = [0.0, 0.0]
        self.output_value = 0.0
        self.inputs_occupied = [False] * self.inputs
        self.output_signal = NodeSignalEmitter()
        self.output_signals = [self.output_signal]

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
        layout.setContentsMargins(10, 5, 10, 5)
        layout.addWidget(QLabel("Status:"))
        layout.addWidget(self.status_label)

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
        proxy.setPos(5, 30)
        proxy.resize(self.width - 10, self.height - 40)

        # Define local rects for connection dots
        self.input_rects = [
            QRectF(-5, 60 - 5, 10, 10),  # Input 1 (Throttle)
            QRectF(-5, 100 - 5, 10, 10) # Input 2 (Button)
        ]
        self.output_rect = QRectF(self.width - 5, self.height / 2 - 5, 10, 10)

    def _update_boost_duration(self):
        try:
            self.boost_duration_s = float(self.boost_duration_edit.text())
            if self.boost_duration_s < 0: self.boost_duration_s = 0.0
            self.boost_duration_edit.setText(str(self.boost_duration_s))
        except ValueError:
            self.boost_duration_edit.setText(str(self.boost_duration_s))

    def _update_cooldown_duration(self):
        try:
            self.cooldown_duration_s = float(self.cooldown_duration_edit.text())
            if self.cooldown_duration_s < 0: self.cooldown_duration_s = 0.0
            self.cooldown_duration_edit.setText(str(self.cooldown_duration_s))
        except ValueError:
            self.cooldown_duration_edit.setText(str(self.cooldown_duration_s))

    def _update_boost_amount(self):
        try:
            self.boost_amount_us = int(self.boost_amount_edit.text())
            self.boost_amount_us = max(-1000, min(1000, self.boost_amount_us))
            self.boost_amount_edit.setText(str(self.boost_amount_us))
        except ValueError:
            self.boost_amount_edit.setText(str(self.boost_amount_us))
        self._recalculate_output()

    def set_value(self, value, input_index=0):
        if input_index < len(self.input_values):
            self.input_values[input_index] = value
        self._recalculate_output()

    def _recalculate_output(self):
        throttle_input_normalized = self.input_values[0]
        boost_button_state = self.input_values[1]
        base_throttle_ppm = int(1500 + throttle_input_normalized * 500)
        output_ppm = base_throttle_ppm

        if self.state == self.BOOST_STATE_READY:
            self.status_label.setText("Ready")
            self.status_label.setStyleSheet("font-weight: bold; color: green;")
            if boost_button_state > 0.5:
                self._start_boost()
                return
        elif self.state == self.BOOST_STATE_BOOSTING:
            self.status_label.setText("Boosting")
            self.status_label.setStyleSheet("font-weight: bold; color: orange;")
            output_ppm = base_throttle_ppm + self.boost_amount_us
            if boost_button_state < 0.5:
                self._end_boost()
                return
        elif self.state == self.BOOST_STATE_COOLDOWN:
            self.status_label.setText("Cooldown")
            self.status_label.setStyleSheet("font-weight: bold; color: red;")

        output_ppm = max(1000, min(2000, output_ppm))
        self.output_value = (output_ppm - 1500) / 500.0
        self.output_signal.output_signal.emit(self.output_value, 0)
        self.update()

    def _start_boost(self):
        self.state = self.BOOST_STATE_BOOSTING
        self.boost_timer.start(int(self.boost_duration_s * 1000))
        self._recalculate_output()

    def _end_boost(self):
        if self.state == self.BOOST_STATE_BOOSTING:
            self.state = self.BOOST_STATE_COOLDOWN
            self.cooldown_timer.start(int(self.cooldown_duration_s * 1000))
            self._recalculate_output()

    def _end_cooldown(self):
        self.state = self.BOOST_STATE_READY
        self._recalculate_output()

    def get_hotspot_rects(self):
        return self.input_rects + [self.output_rect]

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        painter.setBrush(QBrush(QColor("#E0E0E0")))
        for rect in self.input_rects:
            painter.drawEllipse(rect.center(), 5, 5)
        painter.drawEllipse(self.output_rect.center(), 5, 5)

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
