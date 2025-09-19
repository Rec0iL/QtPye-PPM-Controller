# nodes/channel_config_node.py
from PyQt5.QtWidgets import QGraphicsProxyWidget, QLabel, QLineEdit, QWidget, QGridLayout, QGraphicsItem
from PyQt5.QtCore import QRectF, QPointF, Qt
from PyQt5.QtGui import QColor, QPen, QPainterPath
from .base_node import BaseNode, NodeSignalEmitter

class CurveVisualizer(QGraphicsItem):
    def __init__(self, parent_node):
        super().__init__(parent_node)
        self.parent_node = parent_node

    def boundingRect(self):
        return QRectF(0, 0, 150, 100)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(painter.Antialiasing)
        bounds = self.boundingRect()

        painter.setPen(QPen(QColor("#555555"), 1))
        painter.drawRect(bounds)
        painter.drawLine(int(bounds.center().x()), int(bounds.top()), int(bounds.center().x()), int(bounds.bottom()))
        painter.drawLine(int(bounds.left()), int(bounds.center().y()), int(bounds.right()), int(bounds.center().y()))

        painter.setPen(QPen(QColor("#00BFFF"), 2))
        path = QPainterPath()

        node = self.parent_node

        for i in range(int(bounds.width()) + 1):
            x_norm = (i / bounds.width()) * 2.0 - 1.0

            # Apply full calculation chain to get final normalized output
            y_expo = (node.expo_amount * (x_norm ** 3)) + ((1 - node.expo_amount) * x_norm)
            y_weighted = y_expo * (node.weight / 100.0)
            y_us = 1500 + (y_weighted * 500)
            y_offset_us = y_us + node.offset_us
            y_final_norm = (y_offset_us - 1500) / 500.0
            y_clamped = max(-1.0, min(1.0, y_final_norm))

            y_pixel = bounds.height() - ((y_clamped + 1.0) / 2.0 * bounds.height())

            if i == 0: path.moveTo(i, y_pixel)
            else: path.lineTo(i, y_pixel)
        painter.drawPath(path)

        # Draw the current position dot
        input_val = node.current_input_value
        y_expo = (node.expo_amount * (input_val ** 3)) + ((1 - node.expo_amount) * input_val)
        y_weighted = y_expo * (node.weight / 100.0)
        y_us = 1500 + (y_weighted * 500)
        y_offset_us = y_us + node.offset_us
        y_final_norm = (y_offset_us - 1500) / 500.0
        y_clamped = max(-1.0, min(1.0, y_final_norm))

        x_pixel = (input_val + 1.0) / 2.0 * bounds.width()
        y_pixel = bounds.height() - ((y_clamped + 1.0) / 2.0 * bounds.height())

        painter.setBrush(QColor("#FF5722"))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(x_pixel, y_pixel), 4, 4)

class ChannelConfigNode(BaseNode):
    def __init__(self, x=0, y=0, parent=None):
        super().__init__(title="Channel Config", x=x, y=y, w=250, h=300, parent=parent)
        self.inputs = 1
        self.inputs_occupied = [False]
        self.output_signal = NodeSignalEmitter()
        self.output_signals = [self.output_signal]

        self.expo_amount = 0.0
        self.weight = 100.0
        self.offset_us = 0
        self.current_input_value = 0.0

        # UI Elements
        widget = QWidget()
        layout = QGridLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.addWidget(QLabel("Expo %:"), 0, 0)
        self.expo_edit = QLineEdit(str(int(self.expo_amount * 100)))
        layout.addWidget(self.expo_edit, 0, 1)
        layout.addWidget(QLabel("Weight %:"), 1, 0)
        self.weight_edit = QLineEdit(str(int(self.weight)))
        layout.addWidget(self.weight_edit, 1, 1)
        layout.addWidget(QLabel("Offset µs:"), 2, 0)
        self.offset_edit = QLineEdit(str(self.offset_us))
        layout.addWidget(self.offset_edit, 2, 1)

        edits = [self.expo_edit, self.weight_edit, self.offset_edit]
        for edit in edits:
            edit.editingFinished.connect(self._update_settings)

        proxy = QGraphicsProxyWidget(self)
        proxy.setWidget(widget)
        proxy.setPos(5, 30)

        self.visualizer = CurveVisualizer(self)
        self.visualizer.setPos(50, 165)

        dot_y = 285
        self.input_rect = QRectF(-5, dot_y - 5, 10, 10)
        self.output_rect = QRectF(self.width - 5, dot_y - 5, 10, 10)

    def _update_settings(self):
        try:
            expo_val = max(0, min(100, int(self.expo_edit.text())))
            self.expo_amount = expo_val / 100.0
            self.expo_edit.setText(str(expo_val))

            weight_val = max(-1000, min(1000, int(self.weight_edit.text())))
            self.weight = float(weight_val)
            self.weight_edit.setText(str(weight_val))

            offset_val = max(-1000, min(1000, int(self.offset_edit.text())))
            self.offset_us = offset_val
            self.offset_edit.setText(str(offset_val))
        except ValueError:
            # On invalid input, revert to saved values
            self.expo_edit.setText(str(int(self.expo_amount * 100)))
            self.weight_edit.setText(str(int(self.weight)))
            self.offset_edit.setText(str(self.offset_us))

        self.visualizer.update()
        self.set_value(self.current_input_value) # Recalculate output with new settings

    def set_value(self, value, input_index=0):
        self.current_input_value = float(value)

        y_expo = (self.expo_amount * (self.current_input_value ** 3)) + ((1 - self.expo_amount) * self.current_input_value)
        y_weighted = y_expo * (self.weight / 100.0)
        y_us = 1500 + (y_weighted * 500)
        y_offset_us = y_us + self.offset_us
        y_final_norm = (y_offset_us - 1500) / 500.0

        output_value = max(-1.0, min(1.0, y_final_norm))

        self.output_signal.output_signal.emit(output_value, 0)
        self.visualizer.update()

    def get_state(self):
        state = super().get_state()
        state['expo_amount'] = self.expo_amount
        state['weight'] = self.weight
        state['offset_us'] = self.offset_us
        return state

    def set_state(self, data):
        super().set_state(data)
        if 'expo_amount' in data: self.expo_amount = data['expo_amount']
        if 'weight' in data: self.weight = data['weight']
        if 'offset_us' in data: self.offset_us = data['offset_us']

        self.expo_edit.setText(str(int(self.expo_amount * 100)))
        self.weight_edit.setText(str(int(self.weight)))
        self.offset_edit.setText(str(self.offset_us))
        self.visualizer.update()

    def get_hotspot_rects(self):
        return [self.input_rect, self.output_rect]

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        painter.setPen(QPen(QColor("#E0E0E0")))
        painter.setBrush(QColor("#E0E0E0"))
        painter.drawEllipse(self.input_rect.center(), 5, 5)
        painter.drawText(QPointF(15, self.input_rect.center().y() + 5), "In")
        painter.drawEllipse(self.output_rect.center(), 5, 5)
        painter.drawText(QPointF(self.width - 40, self.output_rect.center().y() + 5), "Out")

    def get_input_dot_rects(self):
        scene_pos = self.mapToScene(self.input_rect.center())
        return [QRectF(scene_pos.x() - 5, scene_pos.y() - 5, 10, 10)]

    def get_output_dot_positions(self):
        return [self.mapToScene(self.output_rect.center())]

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            output_hotspot = QRectF(self.width - 10, self.output_rect.y(), 10, 10)
            if output_hotspot.contains(event.pos()):
                pos = self.mapToScene(output_hotspot.center())
                self.scene().start_connection_drag(pos, self, 0)
                event.accept()
                return
        super().mousePressEvent(event)
