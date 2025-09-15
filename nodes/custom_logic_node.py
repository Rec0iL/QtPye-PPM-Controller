# nodes/custom_logic_node.py
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsProxyWidget, QCheckBox, QLineEdit, QLabel, QWidget, QVBoxLayout, QPushButton, QHBoxLayout
from PyQt5.QtCore import QRectF, QPointF, Qt, QTimer, pyqtSignal, QObject, QVariant
from PyQt5.QtGui import QBrush, QColor, QPen, QFont, QFontMetrics
from .base_node import BaseNode, NodeSignalEmitter

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

    def get_state(self):
        # Start with the base node's state
        state = super().get_state()
        # Add custom properties for this node
        state['inputs'] = self.inputs
        state['formula'] = self.formula_line_edit.text()
        return state
