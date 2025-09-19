# nodes/joystick_node.py
import pygame
from PyQt5.QtCore import QRectF, QPointF, Qt, QTimer
from PyQt5.QtGui import QBrush, QColor, QPen, QFontMetrics
from .base_node import BaseNode, NodeSignalEmitter

class JoystickNode(BaseNode):
    def __init__(self, joystick_id, x=0, y=0, parent=None):
        self.joystick = pygame.joystick.Joystick(joystick_id)
        self.joystick.init()

        self.joystick_id = joystick_id
        self.instance_id = self.joystick.get_instance_id()
        self.guid = self.joystick.get_guid()
        self.name = self.joystick.get_name()
        self.is_connected = True

        self._initialize_properties()

        item_height = 20
        hat_height = 40
        h = 50 + (self.num_axes * item_height) + (self.num_buttons * item_height) + (self.num_hats * hat_height)

        super().__init__(title=self.name, x=x, y=y, w=250, h=h, parent=parent)
        self._finish_init()

    @classmethod
    def create_disconnected(cls, node_data):
        instance = cls.__new__(cls)
        instance.is_connected = False
        instance.joystick_id = -1
        instance.instance_id = -1
        instance.guid = node_data.get('guid', '')
        instance.name = node_data.get('name', 'Unknown Joystick')

        instance._initialize_properties(defaults=node_data)

        item_height = 20
        hat_height = 40
        h = 40 + (instance.num_axes * item_height) + (instance.num_buttons * item_height) + (instance.num_hats * hat_height)

        super(JoystickNode, instance).__init__(title=f"{instance.name} (Disconnected)", x=node_data['x'], y=node_data['y'], w=250, h=h)
        instance._finish_init()
        instance.poll_timer.stop()
        return instance

    def _initialize_properties(self, defaults=None):
        if self.is_connected:
            self.num_axes = self.joystick.get_numaxes()
            self.num_buttons = self.joystick.get_numbuttons()
            self.num_hats = self.joystick.get_numhats()
        elif defaults:
            self.num_axes = defaults.get('num_axes', 4)
            self.num_buttons = defaults.get('num_buttons', 12)
            self.num_hats = defaults.get('num_hats', 1)
        else:
            self.num_axes, self.num_buttons, self.num_hats = 0, 0, 0

    def _finish_init(self):
        self.axis_values = [0.0] * self.num_axes
        self.button_values = [0] * self.num_buttons
        self.hat_values = [(0, 0)] * self.num_hats
        self.poll_timer = QTimer()
        self.poll_timer.setInterval(20)
        self.poll_timer.timeout.connect(self.update_joystick_state)
        if self.is_connected:
            self.poll_timer.start()
        num_outputs = self.num_axes + self.num_buttons + (self.num_hats * 2)
        self.output_signals = [NodeSignalEmitter() for _ in range(num_outputs)]

    def disconnect(self):
        self.is_connected = False
        self.poll_timer.stop()
        self.title = f"{self.name} (Disconnected)"
        self.update()

    def reconnect(self, new_joystick_id):
        self.joystick = pygame.joystick.Joystick(new_joystick_id)
        self.joystick.init()
        self.joystick_id = new_joystick_id
        self.instance_id = self.joystick.get_instance_id()
        self.is_connected = True
        self.poll_timer.start()
        self.title = self.name
        self.update()
        print(f"Reconnected '{self.name}' on ID {self.joystick_id}")

    def get_state(self):
        state = super().get_state()
        state['joystick_id'] = self.joystick_id
        state['guid'] = self.guid
        state['name'] = self.name
        state['num_axes'] = self.num_axes
        state['num_buttons'] = self.num_buttons
        state['num_hats'] = self.num_hats
        return state

    def update_joystick_state(self):
        if not self.is_connected: return
        pygame.event.pump()
        needs_update = False
        output_index = 0
        for i in range(self.num_axes):
            new_value = self.joystick.get_axis(i)
            if abs(self.axis_values[i] - new_value) > 1e-9:
                self.axis_values[i] = new_value
                self.output_signals[output_index].output_signal.emit(new_value, 0)
                needs_update = True
            output_index += 1
        for i in range(self.num_buttons):
            new_value = float(self.joystick.get_button(i))
            if self.button_values[i] != new_value:
                self.button_values[i] = new_value
                self.output_signals[output_index].output_signal.emit(new_value, 0)
                needs_update = True
            output_index += 1
        for i in range(self.num_hats):
            new_value = self.joystick.get_hat(i)
            if self.hat_values[i] != new_value:
                self.hat_values[i] = new_value
                self.output_signals[output_index].output_signal.emit(float(new_value[0]), 0)
                self.output_signals[output_index + 1].output_signal.emit(float(new_value[1]), 0)
                needs_update = True
            output_index += 2
        if needs_update:
            self.update()

    def _get_y_for_output(self, index):
        item_height = 20
        hat_height = 40
        y = 40
        if index < self.num_axes:
            return y + (index * item_height) + (item_height / 2)
        index -= self.num_axes
        y += self.num_axes * item_height
        if index < self.num_buttons:
            return y + (index * item_height) + (item_height / 2)
        index -= self.num_buttons
        y += self.num_buttons * item_height
        hat_index = index // 2
        is_y_output = index % 2
        y += hat_index * hat_height
        return y + (15 if not is_y_output else 30)

    def get_hotspot_rects(self):
        rects = []
        num_outputs = self.num_axes + self.num_buttons + (self.num_hats * 2)
        for i in range(num_outputs):
            y = self._get_y_for_output(i)
            rects.append(QRectF(self.width - 10, y - 5, 10, 10))
        return rects

    def get_output_dot_positions(self):
        num_outputs = len(self.output_signals)
        return [self.mapToScene(QPointF(self.width, self._get_y_for_output(i))) for i in range(num_outputs)]

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            for i, hotspot in enumerate(self.get_hotspot_rects()):
                if hotspot.contains(event.pos()):
                     pos = self.mapToScene(hotspot.center())
                     self.scene().start_connection_drag(pos, self, i)
                     event.accept()
                     return
        super().mousePressEvent(event)

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        if not self.is_connected:
            painter.setBrush(QColor(255, 0, 0, 80))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(self.rect, 10, 10)
        self._paint_axes(painter)
        self._paint_buttons(painter)
        self._paint_hats(painter)

    def _paint_axes(self, painter):
        for i in range(self.num_axes):
            y = self._get_y_for_output(i)
            self._paint_label(painter, f"Axis {i}:", y)
            slider_width = self.width - 80 - 30
            slider_y = y - 2.5
            painter.setBrush(QBrush(QColor("#333333")))
            painter.drawRect(int(80), int(slider_y), int(slider_width), 5)
            fill_width = (self.axis_values[i] + 1.0) / 2.0 * slider_width
            painter.setBrush(QBrush(QColor("#00FF00")))
            painter.drawRect(int(80), int(slider_y), int(fill_width), 5)
            painter.setBrush(QBrush(QColor("#E0E0E0")))
            painter.drawEllipse(QPointF(self.width, y), 5, 5)

    def _paint_buttons(self, painter):
        for i in range(self.num_buttons):
            output_index = self.num_axes + i
            y = self._get_y_for_output(output_index)
            self._paint_label(painter, f"Button {i}:", y)
            button_x = self.width - 30
            button_size = 10
            button_y = y - (button_size / 2)
            painter.setBrush(QBrush(QColor("#333333")))
            painter.drawRect(int(button_x), int(button_y), button_size, button_size)
            if self.button_values[i]:
                painter.setBrush(QBrush(QColor("#00FF00")))
                painter.drawRect(int(button_x), int(button_y), button_size, button_size)
            painter.setBrush(QBrush(QColor("#E0E0E0")))
            painter.drawEllipse(QPointF(self.width, y), 5, 5)

    def _paint_hats(self, painter):
        for i in range(self.num_hats):
            output_index = self.num_axes + self.num_buttons + (i * 2)
            y_base = self._get_y_for_output(output_index) - 15
            self._paint_label(painter, f"Hat {i}:", y_base + 20)
            dpad_size = 25
            dpad_x = 80
            dpad_y = y_base + 7.5
            painter.setBrush(QBrush(QColor("#333333")))
            painter.drawRoundedRect(int(dpad_x), int(dpad_y), int(dpad_size), int(dpad_size), 3, 3)
            dot_x = dpad_x + (dpad_size / 2) + (self.hat_values[i][0] * dpad_size / 2)
            dot_y = dpad_y + (dpad_size / 2) - (self.hat_values[i][1] * dpad_size / 2)
            painter.setBrush(QBrush(QColor("#00FF00")))
            painter.drawEllipse(QPointF(dot_x, dot_y), 3, 3)
            y_x = self._get_y_for_output(output_index)
            y_y = self._get_y_for_output(output_index + 1)
            painter.setBrush(QBrush(QColor("#E0E0E0")))
            painter.drawEllipse(QPointF(self.width, y_x), 5, 5)
            self._paint_label(painter, "Hat X", y_x, align_right=True)
            painter.drawEllipse(QPointF(self.width, y_y), 5, 5)
            self._paint_label(painter, "Hat Y", y_y, align_right=True)

    def _paint_label(self, painter, text, y, align_right=False):
        painter.setPen(QPen(QColor("#E0E0E0")))
        font_metrics = QFontMetrics(painter.font())
        text_y = y - (font_metrics.height() / 2) + font_metrics.ascent()
        if align_right:
            text_x = self.width - 20 - font_metrics.width(text)
            painter.drawText(QPointF(text_x, text_y), text)
        else:
            painter.drawText(QPointF(15, text_y), text)
