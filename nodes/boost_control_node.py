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
        # Increased height to make space for dots at the bottom
        super().__init__(title="Boost Control", x=x, y=y, w=220, h=260, parent=parent)
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

        # UI elements are positioned at the top
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.addWidget(QLabel("Status:"))
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("font-weight: bold; color: green;")
        layout.addWidget(self.status_label)

        hbox1 = QHBoxLayout()
        hbox1.addWidget(QLabel("Boost Dur (s):"))
        self.boost_duration_edit = QLineEdit(str(self.boost_duration_s))
        hbox1.addWidget(self.boost_duration_edit)
        layout.addLayout(hbox1)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(QLabel("Cooldown (s):"))
        self.cooldown_duration_edit = QLineEdit(str(self.cooldown_duration_s))
        hbox2.addWidget(self.cooldown_duration_edit)
        layout.addLayout(hbox2)

        hbox3 = QHBoxLayout()
        hbox3.addWidget(QLabel("Boost Amt (µs):"))
        self.boost_amount_edit = QLineEdit(str(self.boost_amount_us))
        hbox3.addWidget(self.boost_amount_edit)
        layout.addLayout(hbox3)

        self.boost_duration_edit.editingFinished.connect(self._update_boost_duration)
        self.cooldown_duration_edit.editingFinished.connect(self._update_cooldown_duration)
        self.boost_amount_edit.editingFinished.connect(self._update_boost_amount)

        proxy = QGraphicsProxyWidget(self)
        proxy.setWidget(widget)
        proxy.setPos(10, 30)
        proxy.resize(self.width - 20, 160)

        # Connection dots are now positioned at the bottom
        self.input_rects = [
            QRectF(-5, 210 - 5, 10, 10),  # Input 1 (Throttle)
            QRectF(-5, 235 - 5, 10, 10)   # Input 2 (Button)
        ]
        output_y = (210 + 235) / 2 # Center between inputs
        self.output_rect = QRectF(self.width - 5, output_y - 5, 10, 10)

    def cleanup(self):
        """Stops and deletes the timers to prevent memory leaks."""
        if self.boost_timer:
            self.boost_timer.stop()
            self.boost_timer.deleteLater()
            self.boost_timer = None
        if self.cooldown_timer:
            self.cooldown_timer.stop()
            self.cooldown_timer.deleteLater()
            self.cooldown_timer = None
        print(f"Cleaned up timers for Boost Control Node")
        super().cleanup()

    def _update_boost_duration(self):
        try:
            val = float(self.boost_duration_edit.text())
            self.boost_duration_s = max(0.0, val)
            self.boost_duration_edit.setText(str(self.boost_duration_s))
        except ValueError:
            self.boost_duration_edit.setText(str(self.boost_duration_s))

    def _update_cooldown_duration(self):
        try:
            val = float(self.cooldown_duration_edit.text())
            self.cooldown_duration_s = max(0.0, val)
            self.cooldown_duration_edit.setText(str(self.cooldown_duration_s))
        except ValueError:
            self.cooldown_duration_edit.setText(str(self.cooldown_duration_s))

    def _update_boost_amount(self):
        try:
            val = int(self.boost_amount_edit.text())
            self.boost_amount_us = max(-1000, min(1000, val))
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
        painter.setPen(QPen(QColor("#E0E0E0")))

        # Draw input dots and labels
        painter.drawEllipse(self.input_rects[0].center(), 5, 5)
        painter.drawText(QPointF(15, self.input_rects[0].center().y() + 5), "Throttle")
        painter.drawEllipse(self.input_rects[1].center(), 5, 5)
        painter.drawText(QPointF(15, self.input_rects[1].center().y() + 5), "Button")

        # Draw output dot and label
        painter.drawEllipse(self.output_rect.center(), 5, 5)
        painter.drawText(QPointF(self.width - 45, self.output_rect.center().y() + 5), "Out")

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
            output_hotspot = QRectF(self.width-10, self.output_rect.y(), 10, 10)
            if output_hotspot.contains(event.pos()):
                pos = self.mapToScene(self.output_rect.center())
                self.scene().start_connection_drag(pos, self, 0)
                event.accept()
                return
        super().mousePressEvent(event)

    # --- NEUE METHODEN HINZUGEFÜGT ---

    def get_state(self):
        """Sammelt die spezifischen Werte dieses Nodes zum Speichern."""
        state = super().get_state()
        state['boost_duration_s'] = self.boost_duration_s
        state['cooldown_duration_s'] = self.cooldown_duration_s
        state['boost_amount_us'] = self.boost_amount_us
        return state

    def set_state(self, data):
        """Stellt den Zustand des Nodes aus den geladenen Daten wieder her."""
        super().set_state(data)
        # Lade die Werte aus den Daten, mit Standardwerten falls sie nicht existieren
        self.boost_duration_s = data.get('boost_duration_s', 2.0)
        self.cooldown_duration_s = data.get('cooldown_duration_s', 3.0)
        self.boost_amount_us = data.get('boost_amount_us', 500)

        # Aktualisiere die Textfelder in der UI, damit sie die geladenen Werte anzeigen
        self.boost_duration_edit.setText(str(self.boost_duration_s))
        self.cooldown_duration_edit.setText(str(self.cooldown_duration_s))
        self.boost_amount_edit.setText(str(self.boost_amount_us))
