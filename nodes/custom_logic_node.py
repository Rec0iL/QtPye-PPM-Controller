# nodes/custom_logic_node.py
from PyQt5.QtWidgets import QGraphicsProxyWidget, QLineEdit, QLabel, QWidget, QVBoxLayout
from PyQt5.QtCore import QRectF, QPointF, Qt
from PyQt5.QtGui import QBrush, QColor, QPen
from .base_node import BaseNode, NodeSignalEmitter

class CustomLogicNode(BaseNode):
    def __init__(self, x=0, y=0, inputs=1, parent=None):
        # Precise height calculation to fit all elements
        content_y_start = 130
        line_height = 25
        content_height = inputs * line_height
        h = content_y_start + content_height
        super().__init__(title="Custom Logic", x=x, y=y, w=250, h=h, parent=parent)

        self.inputs = inputs
        self.input_values = [0.0] * inputs
        self.output_value = 0.0
        self.output_signal = NodeSignalEmitter()
        self.output_signals = [self.output_signal]
        self.inputs_occupied = [False] * self.inputs

        # UI Elements (positioned at the top)
        self.formula_line_edit = QLineEdit()
        if self.inputs == 1: self.formula_line_edit.setText("Y = X1")
        else: self.formula_line_edit.setText("Y = X1 + X2")
        self.formula_label = QLabel("Formula:")
        self.formula_line_edit.textChanged.connect(self.evaluate_formula)

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(self.formula_label)
        layout.addWidget(self.formula_line_edit)
        proxy = QGraphicsProxyWidget(self)
        proxy.setWidget(widget)
        proxy.setPos(10, 30)
        proxy.resize(self.width - 20, 60)

        # Connection Dots (positioned below the UI)
        self.input_rects = []
        for i in range(self.inputs):
            y = content_y_start + (i * line_height)
            self.input_rects.append(QRectF(-5, y - 5, 10, 10))

        first_input_y = content_y_start
        last_input_y = content_y_start + ((inputs - 1) * line_height)
        output_y = (first_input_y + last_input_y) / 2
        self.output_rect = QRectF(self.width - 5, output_y - 5, 10, 10)

    def get_state(self):
        state = super().get_state()
        state['inputs'] = self.inputs
        state['formula'] = self.formula_line_edit.text()
        return state

    def set_state(self, data):
        """Restores node state from a dictionary."""
        super().set_state(data)
        if 'formula' in data:
            self.formula_line_edit.setText(data.get('formula', ''))

    def set_value(self, value, input_index=0):
        if input_index < len(self.input_values):
            self.input_values[input_index] = value
            self.evaluate_formula()

    def evaluate_formula(self):
        local_vars = {}
        for i, val in enumerate(self.input_values):
            local_vars[f"X{i+1}"] = val
        formula_text = self.formula_line_edit.text().strip()
        if formula_text.startswith("Y ="): formula_text = formula_text[3:].strip()
        try:
            result = eval(formula_text, {"__builtins__": None}, local_vars)
            self.output_value = float(result)
        except Exception as e:
            print(f"Error evaluating formula: {e}")
            self.output_value = 0.0
        self.output_signal.output_signal.emit(self.output_value, 0)
        self.update()

    def get_hotspot_rects(self):
        return self.input_rects + [self.output_rect]

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        painter.setBrush(QBrush(QColor("#E0E0E0")))
        painter.setPen(QPen(QColor("#E0E0E0")))
        for i, rect in enumerate(self.input_rects):
            painter.drawEllipse(rect.center(), 5, 5)
            painter.drawText(QPointF(15, rect.center().y() + 5), f"X{i+1}")
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
            output_hotspot = QRectF(self.width - 10, self.output_rect.y(), 10, 10)
            if output_hotspot.contains(event.pos()):
                pos = self.mapToScene(output_hotspot.center())
                self.scene().start_connection_drag(pos, self, 0)
                event.accept()
                return
        super().mousePressEvent(event)
