# nodes/mixer_node.py
from PyQt5.QtWidgets import QGraphicsProxyWidget, QLabel, QLineEdit, QWidget, QGridLayout
from PyQt5.QtCore import QRectF, QPointF, Qt
from PyQt5.QtGui import QColor, QPen
from .base_node import BaseNode, NodeSignalEmitter

class MixerNode(BaseNode):
    def __init__(self, x=0, y=0, parent=None):
        super().__init__(title="Mixer", x=x, y=y, w=220, h=200, parent=parent)
        self.inputs = 2
        self.inputs_occupied = [False] * self.inputs
        self.output_signals = [NodeSignalEmitter(), NodeSignalEmitter()]

        self.input_values = [0.0, 0.0]
        self.weights = { 'A1': 100, 'B1': 0, 'A2': 0, 'B2': 100 }

        # UI Elements at the top
        widget = QWidget()
        layout = QGridLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        labels = {
            'out1': QLabel("Out 1"), 'out2': QLabel("Out 2"),
            'inA': QLabel("In A"), 'inB': QLabel("In B")
        }
        for label in labels.values():
            label.setAlignment(Qt.AlignCenter)
        layout.addWidget(labels['out1'], 0, 1); layout.addWidget(labels['out2'], 0, 2)
        layout.addWidget(labels['inA'], 1, 0); layout.addWidget(labels['inB'], 2, 0)
        self.edit_A1 = QLineEdit(str(self.weights['A1'])); self.edit_B1 = QLineEdit(str(self.weights['B1']))
        self.edit_A2 = QLineEdit(str(self.weights['A2'])); self.edit_B2 = QLineEdit(str(self.weights['B2']))
        edits = [self.edit_A1, self.edit_B1, self.edit_A2, self.edit_B2]
        for edit in edits:
            edit.editingFinished.connect(self._update_weights)
            edit.setAlignment(Qt.AlignCenter)
            edit.setMaximumWidth(50)
        layout.addWidget(self.edit_A1, 1, 1); layout.addWidget(self.edit_A2, 1, 2)
        layout.addWidget(self.edit_B1, 2, 1); layout.addWidget(self.edit_B2, 2, 2)
        proxy = QGraphicsProxyWidget(self)
        proxy.setWidget(widget)
        proxy.setPos(0, 30)
        proxy.resize(self.width, 100)

        # Connection dots at the bottom
        y_start = 160
        line_height = 25
        self.input_rects = [
            QRectF(-5, y_start - 5, 10, 10),
            QRectF(-5, y_start + line_height - 5, 10, 10)
        ]
        self.output_rects = [
            QRectF(self.width - 5, y_start - 5, 10, 10),
            QRectF(self.width - 5, y_start + line_height - 5, 10, 10)
        ]

    def _update_weights(self):
        try:
            self.weights['A1'] = int(self.edit_A1.text()); self.weights['B1'] = int(self.edit_B1.text())
            self.weights['A2'] = int(self.edit_A2.text()); self.weights['B2'] = int(self.edit_B2.text())
            self._recalculate_outputs()
        except ValueError:
            self.edit_A1.setText(str(self.weights['A1'])); self.edit_B1.setText(str(self.weights['B1']))
            self.edit_A2.setText(str(self.weights['A2'])); self.edit_B2.setText(str(self.weights['B2']))

    def set_value(self, value, input_index=0):
        if input_index < len(self.input_values):
            self.input_values[input_index] = float(value)
            self._recalculate_outputs()

    def _recalculate_outputs(self):
        in_a, in_b = self.input_values
        w = self.weights
        out_1 = (in_a * w['A1'] / 100.0) + (in_b * w['B1'] / 100.0)
        out_2 = (in_a * w['A2'] / 100.0) + (in_b * w['B2'] / 100.0)
        out_1 = max(-1.0, min(1.0, out_1)); out_2 = max(-1.0, min(1.0, out_2))
        self.output_signals[0].output_signal.emit(out_1, 0)
        self.output_signals[1].output_signal.emit(out_2, 0)
        self.update()

    def get_hotspot_rects(self):
        return self.input_rects + self.output_rects

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        painter.setPen(QPen(QColor("#E0E0E0")))
        painter.setBrush(QColor("#E0E0E0"))

        painter.drawEllipse(self.input_rects[0].center(), 5, 5)
        painter.drawText(QPointF(15, self.input_rects[0].center().y() + 5), "In A")
        painter.drawEllipse(self.input_rects[1].center(), 5, 5)
        painter.drawText(QPointF(15, self.input_rects[1].center().y() + 5), "In B")

        painter.drawEllipse(self.output_rects[0].center(), 5, 5)
        painter.drawText(QPointF(self.width - 45, self.output_rects[0].center().y() + 5), "Out 1")
        painter.drawEllipse(self.output_rects[1].center(), 5, 5)
        painter.drawText(QPointF(self.width - 45, self.output_rects[1].center().y() + 5), "Out 2")

    def get_input_dot_rects(self):
        rects = []
        for r in self.input_rects:
            scene_pos = self.mapToScene(r.center())
            rects.append(QRectF(scene_pos.x() - 5, scene_pos.y() - 5, 10, 10))
        return rects

    def get_output_dot_positions(self):
        return [self.mapToScene(r.center()) for r in self.output_rects]

    def get_state(self):
        """Returns a dictionary of data to be saved."""
        state = super().get_state()
        state['weights'] = self.weights
        return state

    def set_state(self, data):
        """Restores node state from a dictionary."""
        super().set_state(data)
        if 'weights' in data:
            self.weights = data['weights']
            # Update the UI text boxes to match the loaded state
            self.edit_A1.setText(str(self.weights.get('A1', 100)))
            self.edit_B1.setText(str(self.weights.get('B1', 0)))
            self.edit_A2.setText(str(self.weights.get('A2', 0)))
            self.edit_B2.setText(str(self.weights.get('B2', 100)))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            output_hotspots = [
                QRectF(self.width - 10, r.y(), 10, 10) for r in self.output_rects
            ]
            for i, hotspot in enumerate(output_hotspots):
                if hotspot.contains(event.pos()):
                    pos = self.mapToScene(hotspot.center())
                    self.scene().start_connection_drag(pos, self, i)
                    event.accept()
                    return
        super().mousePressEvent(event)
