# nodes/ppm_channel_node.py
from PyQt5.QtWidgets import QStyleOptionButton, QStyle, QApplication
from PyQt5.QtCore import QRectF, QPointF, Qt
from PyQt5.QtGui import QBrush, QColor, QPen
from .base_node import BaseNode

class PPMChannelNode(BaseNode):
    def __init__(self, channel_number, x=0, y=0, parent=None, serial_manager=None):
        super().__init__(title=f"PPM Channel {channel_number}", x=x, y=y, w=180, h=140, parent=parent)
        self.channel_number = channel_number
        self.serial_manager = serial_manager
        self.inputs = 1
        self.inverted = False
        self.current_value = 0.0
        self.raw_input_value = 0.0
        self.inputs_occupied = [False]

        # Define local rects for interactive elements
        self.input_rect = QRectF(-5, 100 - 5, 10, 10)
        self.checkbox_rect = QRectF(10, 35, 120, 20)

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)

        # --- Manually Draw the Checkbox ---
        opt = QStyleOptionButton()
        opt.rect = self.checkbox_rect.toRect()
        opt.text = "Invert Output"
        opt.state = QStyle.State_Enabled
        if self.inverted:
            opt.state |= QStyle.State_On
        else:
            opt.state |= QStyle.State_Off

        painter.setPen(QPen(QColor("#E0E0E0"))) # Set text color for the checkbox
        QApplication.style().drawControl(QStyle.CE_CheckBox, opt, painter)

        # --- Draw Other UI Elements ---
        painter.setBrush(QBrush(QColor("#E0E0E0")))
        painter.drawEllipse(self.input_rect.center(), 5, 5)
        painter.drawText(QPointF(15, 100 + 5), "In")

        slider_x = self.width - 30
        slider_y = 70
        slider_width = 15
        slider_height = self.height - 85
        slider_rect = QRectF(slider_x, slider_y, slider_width, slider_height)
        painter.setBrush(QBrush(QColor("#333333")))
        painter.drawRoundedRect(slider_rect, 3, 3)

        fill_height = (self.current_value + 1.0) / 2.0 * slider_height
        fill_rect = QRectF(slider_x, slider_y + slider_height - fill_height, slider_width, fill_height)
        painter.setBrush(QBrush(QColor("#00FF00")))
        painter.setPen(Qt.NoPen)
        painter.drawRect(fill_rect)

        ppm_value = int(1500 + self.current_value * 500)
        painter.setPen(QPen(QColor("#E0E0E0")))
        painter.drawText(QPointF(15, self.height - 15), f"{ppm_value} µs")

    def mousePressEvent(self, event):
        # Handle clicks on our manually drawn checkbox
        if self.checkbox_rect.contains(event.pos()):
            self.inverted = not self.inverted
            self.update() # Trigger a repaint to show the new check state
            self.set_value(self.raw_input_value) # Recalculate output
            event.accept()
            return
        # Pass other clicks to the base class for dragging
        super().mousePressEvent(event)

    def get_hotspot_rects(self):
        return [self.input_rect, self.checkbox_rect]

    def get_input_dot_rects(self):
        scene_pos = self.mapToScene(self.input_rect.center())
        return [QRectF(scene_pos.x() - 5, scene_pos.y() - 5, 10, 10)]

    def set_value(self, value, input_index=0):
        val = float(value)
        self.raw_input_value = val

        if self.inverted:
            val = -val

        self.current_value = max(-1.0, min(1.0, val))
        self.update()

        ppm_value = int(1500 + self.current_value * 500)
        command = f"{self.channel_number}={ppm_value}"
        if self.serial_manager:
            self.serial_manager.send_command(command)

    def get_state(self):
        """Returns a dictionary of data to be saved."""
        state = super().get_state()
        state['inverted'] = self.inverted
        return state

    def set_state(self, data):
        """Restores node state from a dictionary."""
        super().set_state(data)
        if 'inverted' in data:
            is_inverted = data.get('inverted', False)
            self.inverted = is_inverted
            # Trigger a repaint to ensure the manually drawn checkbox shows the correct state
            self.update()
