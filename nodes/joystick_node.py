import pygame
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsProxyWidget, QCheckBox, QLineEdit, QLabel, QWidget, QVBoxLayout, QPushButton, QHBoxLayout
from PyQt5.QtCore import QRectF, QPointF, Qt, QTimer, pyqtSignal, QObject, QVariant
from PyQt5.QtGui import QBrush, QColor, QPen, QFont, QFontMetrics
from .base_node import BaseNode, NodeSignalEmitter

class JoystickNode(BaseNode):
    def __init__(self, joystick_id, x=0, y=0, parent=None):
        pygame.joystick.init()
        joystick_count = pygame.joystick.get_count()
        if joystick_id >= joystick_count:
            raise ValueError("Joystick ID out of range")

        self.joystick = pygame.joystick.Joystick(joystick_id)
        self.joystick.init()

        self.num_axes = self.joystick.get_numaxes()
        self.num_buttons = self.joystick.get_numbuttons()
        self.num_hats = self.joystick.get_numhats()

        item_height = 20
        h = 40 + (self.num_axes + self.num_buttons + self.num_hats) * item_height
        w = 250

        super().__init__(title=self.joystick.get_name(), x=x, y=y, w=w, h=h, parent=parent)

        self.axis_values = [0.0] * self.num_axes
        self.button_values = [0] * self.num_buttons
        self.hat_values = [(0, 0)] * self.num_hats

        self.poll_timer = QTimer()
        self.poll_timer.setInterval(20)
        self.poll_timer.timeout.connect(self.update_joystick_state)
        self.poll_timer.start()

        self.output_signals = []
        for _ in range(self.num_axes + self.num_buttons + self.num_hats):
            self.output_signals.append(NodeSignalEmitter())

    def update_joystick_state(self):
        pygame.event.pump()

        for i in range(self.num_axes):
            new_value = self.joystick.get_axis(i)
            if self.axis_values[i] != new_value:
                self.axis_values[i] = new_value
                if i < len(self.output_signals):
                    self.output_signals[i].output_signal.emit(new_value, 0)

        for i in range(self.num_buttons):
            new_value = float(self.joystick.get_button(i))
            if self.button_values[i] != new_value:
                self.button_values[i] = new_value
                if self.num_axes + i < len(self.output_signals):
                    self.output_signals[self.num_axes + i].output_signal.emit(new_value, 0)

        for i in range(self.num_hats):
            new_value = self.joystick.get_hat(i)
            if self.hat_values[i] != new_value:
                self.hat_values[i] = new_value
                if self.num_axes + self.num_buttons + i < len(self.output_signals):
                    self.output_signals[self.num_axes + self.num_buttons + i].output_signal.emit(float(new_value[0]), 0)

        self.update()

    def get_output_dot_positions(self):
        positions = []
        y = 40
        line_height = 20
        output_x_offset = self.width - 10

        for _ in range(self.num_axes + self.num_buttons + self.num_hats):
            positions.append(self.mapToScene(QPointF(output_x_offset, y + line_height / 2)))
            y += line_height

        return positions

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            y = 40
            line_height = 20
            output_x_offset = self.width - 10

            for i in range(self.num_axes + self.num_buttons + self.num_hats):
                dot_y = y + line_height / 2
                dot_rect = QRectF(output_x_offset - 5, dot_y - 5, 10, 10)
                if dot_rect.contains(event.pos()):
                    self.scene().start_connection_drag(self.mapToScene(event.pos()), self, i)
                    event.accept()
                    return
                y += line_height

        super().mousePressEvent(event)

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)

        y = 40
        line_height = 20
        text_x_offset = 15
        slider_x_offset = 80
        hat_x_offset = 80
        output_x_offset = self.width - 10
        button_x_offset = self.width - 30

        font_metrics = QFontMetrics(painter.font())
        text_y_offset = font_metrics.ascent() + (line_height - font_metrics.height()) / 2

        painter.setPen(QPen(QColor("#E0E0E0")))

        for i in range(self.num_axes):
            painter.drawText(QPointF(text_x_offset, y + text_y_offset), f"Axis {i}:")

            slider_width = self.width - slider_x_offset - 30
            slider_y = y + int((line_height - 5) / 2)

            painter.setBrush(QBrush(QColor("#333333")))
            painter.drawRect(slider_x_offset, slider_y, slider_width, 5)

            fill_width = (self.axis_values[i] + 1.0) / 2.0 * slider_width
            painter.setBrush(QBrush(QColor("#00FF00")))
            painter.drawRect(slider_x_offset, slider_y, int(fill_width), 5)

            painter.setBrush(QBrush(QColor("#E0E0E0")))
            painter.drawEllipse(QPointF(output_x_offset, y + line_height / 2), 5, 5)

            y += line_height

        for i in range(self.num_buttons):
            painter.drawText(QPointF(text_x_offset, y + text_y_offset), f"Button {i}:")

            button_size = 10
            button_y = y + int((line_height - button_size) / 2)

            painter.setBrush(QBrush(QColor("#333333")))
            painter.drawRect(button_x_offset, button_y, button_size, button_size)

            if self.button_values[i]:
                painter.setBrush(QBrush(QColor("#00FF00")))
                painter.drawRect(button_x_offset, button_y, button_size, button_size)

            painter.setBrush(QBrush(QColor("#E0E0E0")))
            painter.drawEllipse(QPointF(output_x_offset, y + line_height / 2), 5, 5)

            y += line_height

        for i in range(self.num_hats):
            painter.drawText(QPointF(text_x_offset, y + text_y_offset), f"Hat {i}:")

            painter.drawText(QPointF(hat_x_offset, y + text_y_offset), str(self.hat_values[i]))

            painter.setBrush(QBrush(QColor("#E0E0E0")))
            painter.drawEllipse(QPointF(output_x_offset, y + line_height / 2), 5, 5)

            y += line_height

class CustomLogicNode(BaseNode):
    def __init__(self, x=0, y=0, inputs=1, parent=None):
        super().__init__(title="Custom Logic", x=x, y=y, w=250, h=150, parent=parent)
        self.inputs = inputs
        self.input_values = [0.0] * inputs
        self.output_value = 0.0

        self.output_signal = NodeSignalEmitter()
        self.output_signals = [self.output_signal]
        self.inputs_occupied = [False] * self.inputs

        self.formula_line_edit = QLineEdit()

        if self.inputs == 1:
            self.formula_line_edit.setText("Y = X1")
        else:
            self.formula_line_edit.setText("Y = X1 + X2")

        self.formula_label = QLabel("Formula:")
        self.formula_line_edit.textChanged.connect(self.evaluate_formula)

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(self.formula_label)
        layout.addWidget(self.formula_line_edit)

        proxy = QGraphicsProxyWidget(self)
        proxy.setWidget(widget)
        proxy.setPos(15, 40)
        proxy.resize(self.width - 30, 80)

        y_offset = 40
        line_height = 20
        self.input_rects = []
        for i in range(self.inputs):
            y = y_offset + i * line_height + 5
            self.input_rects.append(QRectF(-5, y - 5, 10, 10))

    def is_input_occupied(self, index):
        if index < len(self.inputs_occupied):
            return self.inputs_occupied[index]
        return False

    def set_input_occupied(self, index, occupied):
        if index < len(self.inputs_occupied):
            self.inputs_occupied[index] = occupied

    def set_value(self, value, input_index=0):
        if input_index < len(self.input_values):
            self.input_values[input_index] = value
            self.evaluate_formula()

    def evaluate_formula(self):
        local_vars = {"X1": self.input_values[0]}
        if self.inputs > 1:
            local_vars["X2"] = self.input_values[1]

        formula_text = self.formula_line_edit.text().strip()

        if formula_text.startswith("Y ="):
            formula_text = formula_text[3:].strip()

        try:
            result = eval(formula_text, {"__builtins__": None}, local_vars)
            self.output_value = float(result)
            self.output_signal.output_signal.emit(self.output_value, 0)
            self.update()
        except Exception as e:
            print(f"Error evaluating formula: {e}")
            self.output_value = 0.0
            self.output_signal.output_signal.emit(self.output_value, 0)
            self.update()

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)

        y_offset = 40
        line_height = 20

        for i in range(self.inputs):
            y = y_offset + i * line_height
            painter.setBrush(QBrush(QColor("#E0E0E0")))
            painter.drawEllipse(QPointF(0, y + 5), 5, 5)
            painter.drawText(QPointF(10, y + 10), f"X{i+1}")

        output_dot_y = y_offset + (self.inputs - 1) * line_height
        painter.setBrush(QBrush(QColor("#E0E0E0")))
        painter.drawEllipse(QPointF(self.width - 5, output_dot_y + 5), 5, 5)

    def get_input_dot_rects(self):
        rects = []
        y_offset = 40
        line_height = 20
        for i in range(self.inputs):
            y = y_offset + i * line_height + 5
            rects.append(QRectF(self.pos().x() - 5, self.pos().y() + y - 5, 10, 10))
        return rects

    def get_output_dot_positions(self):
        output_dot_y = 40 + (self.inputs - 1) * 20 + 5
        return [self.mapToScene(QPointF(self.width - 5, output_dot_y))]

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            output_dot_y = 40 + (self.inputs - 1) * 20 + 5
            output_dot_rect = QRectF(self.width - 10, output_dot_y - 5, 10, 10)
            if output_dot_rect.contains(event.pos()):
                self.scene().start_connection_drag(self.mapToScene(event.pos()), self, 0)
                event.accept()
                return
        super().mousePressEvent(event)

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

        self.output_signal = NodeSignalEmitter()
        self.output_signals = [self.output_signal]
        self.inputs_occupied = [False] * self.inputs

        self.input_dot_y_offset = 50
        self.output_dot_y_offset = 120
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
            self.boost_amount_us = max(0, min(1000, self.boost_amount_us))
            self.boost_amount_edit.setText(str(self.boost_amount_us))
        except ValueError:
            self.boost_amount_edit.setText(str(self.boost_amount_us))

    def set_value(self, value, input_index=0):
        if input_index < len(self.input_values):
            self.input_values[input_index] = value

        self._recalculate_output()

    def _recalculate_output(self):
        throttle_input_normalized = self.input_values[0]
        boost_button_state = self.input_values[1]

        output_ppm = 0
        if self.state == self.BOOST_STATE_READY:
            self.status_label.setText("Ready")
            self.status_label.setStyleSheet("font-weight: bold; color: green;")

            output_ppm = int(1500 + throttle_input_normalized * 500)

            if boost_button_state > 0.5:
                self._start_boost()
        elif self.state == self.BOOST_STATE_BOOSTING:
            self.status_label.setText("Boosting")
            self.status_label.setStyleSheet("font-weight: bold; color: orange;")

            output_ppm = int(1500 + throttle_input_normalized * 500) + self.boost_amount_us
            if boost_button_state < 0.5:
                self._end_boost()
        elif self.state == self.BOOST_STATE_COOLDOWN:
            self.status_label.setText("Cooldown")
            self.status_label.setStyleSheet("font-weight: bold; color: red;")

            output_ppm = int(1500 + throttle_input_normalized * 500)

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

    def paint(self, painter, option, widget=None):
        painter.setBrush(QBrush(QColor("#4A4A4A")))
        painter.setPen(QPen(QColor("#C0C0C0"), 2))
        painter.drawRoundedRect(self.rect, 10, 10)

        painter.setPen(QPen(QColor("#E0E0E0")))
        title_rect = QRectF(5, 5, self.width - 10, 20)
        painter.drawText(title_rect, Qt.AlignLeft | Qt.AlignTop, self.title)

        input_y_pos = 50
        for i in range(self.inputs):
            painter.setBrush(QBrush(QColor("#E0E0E0")))
            painter.drawEllipse(QPointF(0, input_y_pos), 5, 5)
            painter.setPen(QPen(QColor("#E0E0E0")))
            painter.drawText(QPointF(10, input_y_pos + 5), f"X{i+1}")
            input_y_pos += 40

        painter.setBrush(QBrush(QColor("#E0E0E0")))
        painter.drawEllipse(QPointF(self.width - 5, 120), 5, 5)

    def get_input_dot_rects(self):
        rects = []
        input_y_pos = 50
        for i in range(self.inputs):
            scene_pos = self.mapToScene(QPointF(0, input_y_pos))
            rects.append(QRectF(scene_pos.x() - 5, scene_pos.y() - 5, 10, 10))
            input_y_pos += 40
        return rects

    def get_output_dot_positions(self):
        return [self.mapToScene(QPointF(self.width - 5, 120))]

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            output_dot_rect = QRectF(self.width - 10, 120 - 5, 10, 10)
            if output_dot_rect.contains(event.pos()):
                self.scene().start_connection_drag(self.mapToScene(event.pos()), self, 0)
                event.accept()
                return
        super().mousePressEvent(event)
