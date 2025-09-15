# nodes/ppm_channel_node.py
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsProxyWidget, QCheckBox, QLineEdit, QLabel, QWidget, QVBoxLayout, QPushButton, QHBoxLayout
from PyQt5.QtCore import QRectF, QPointF, Qt, QTimer, pyqtSignal, QObject, QVariant
from PyQt5.QtGui import QBrush, QColor, QPen, QFont, QFontMetrics
from .base_node import BaseNode, NodeSignalEmitter

class PPMChannelNode(BaseNode):
    def __init__(self, channel_number, x=0, y=0, parent=None, serial_manager=None):
        super().__init__(title=f"PPM Channel {channel_number}", x=x, y=y, w=180, h=100, parent=parent)
        self.channel_number = channel_number
        self.inverted = False
        self.current_value = 0.0
        self.serial_manager = serial_manager
        self.is_digital = False

        self.inputs_occupied = [False]
        self.input_rect = QRectF(0, self.height / 2 - 5, 10, 10)

        self.inv_checkbox = QCheckBox("Inv")
        proxy_widget = QGraphicsProxyWidget(self)
        proxy_widget.setWidget(self.inv_checkbox)
        proxy_widget.setPos(self.width - self.inv_checkbox.sizeHint().width() - 10, 10)

        self.inv_checkbox.stateChanged.connect(self._toggle_inversion)

    def boundingRect(self):
        return QRectF(0, 0, self.width, self.height)

    def is_input_occupied(self, index):
        return self.inputs_occupied[index]

    def set_input_occupied(self, index, occupied):
        self.inputs_occupied[index] = occupied

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)

        painter.setBrush(QBrush(QColor("#E0E0E0")))
        painter.drawEllipse(self.input_rect)

        slider_x = self.width - 25
        slider_y = 35
        slider_width = 10
        slider_height = self.height - 50
        slider_rect = QRectF(slider_x, slider_y, slider_width, slider_height)

        painter.setBrush(QBrush(QColor("#333333")))
        painter.drawRoundedRect(slider_rect, 3, 3)

        if self.is_digital:
            fill_height = self.current_value * slider_height
        else:
            fill_height = (self.current_value + 1.0) / 2.0 * slider_height

        fill_rect = QRectF(slider_x, slider_y + slider_height - fill_height, slider_width, fill_height)

        painter.setBrush(QBrush(QColor("#00FF00")))
        painter.setPen(Qt.NoPen)
        painter.drawRect(fill_rect)

        if self.is_digital:
            ppm_value = int(1000 + self.current_value * 1000)
        else:
            ppm_value = int(1500 + self.current_value * 500)

        painter.setPen(QPen(QColor("#E0E0E0")))
        painter.drawText(QPointF(10, self.height - 20), f"{ppm_value} µs")

    def _toggle_inversion(self, state):
        self.inverted = (state == Qt.Checked)
        print(f"PPM Channel {self.channel_number} inversion set to: {self.inverted}")
        self.set_value(self.current_value)

    def get_input_dot_rects(self):
        """Returns a list of input dot rectangles in scene coordinates."""
        scene_pos = self.mapToScene(self.input_rect.center())
        return [QRectF(scene_pos.x() - 5, scene_pos.y() - 5, 10, 10)]

    def set_value(self, value, input_index=0):
        if self.inverted:
            value = -value

        self.current_value = max(-1.0, min(1.0, value))
        self.update()

        # The single analog formula now works for all node types
        ppm_value = int(1500 + self.current_value * 500)

        command = f"{self.channel_number}={ppm_value}"
        if self.serial_manager:
            self.serial_manager.send_command(command)
