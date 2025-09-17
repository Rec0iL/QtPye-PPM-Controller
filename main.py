import sys
import json
import pygame
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QDockWidget, QTextEdit, QGraphicsView, QGraphicsScene,
                             QToolBar, QAction, QStatusBar, QDialog, QListWidget,
                             QPushButton, QHBoxLayout, QLabel, QCheckBox,
                             QGraphicsPathItem, QMenu, QToolButton)
from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5.QtGui import (QBrush, QColor, QPainterPath, QPainter,
                         QPen, QIcon)
from serial_manager import SerialManager
from nodes import (BaseNode, PPMChannelNode, JoystickNode, CustomLogicNode,
                   BoostControlNode, ToggleNode, ThreePositionSwitchNode,
                   ExpoCurveNode, MixerNode, AxisToButtonsNode, SwitchGateNode)
from connections import Connection

class PortSelectionDialog(QDialog):
    def __init__(self, ports):
        super().__init__()
        self.setWindowTitle("Select Serial Port")
        self.setGeometry(200, 200, 300, 200)
        layout = QVBoxLayout(self)
        self.port_list_widget = QListWidget()
        self.port_list_widget.addItems(ports)
        layout.addWidget(self.port_list_widget)
        select_button = QPushButton("Select")
        select_button.clicked.connect(self.accept)
        layout.addWidget(select_button)
        self.selected_port = None

    def accept(self):
        selected_items = self.port_list_widget.selectedItems()
        if selected_items:
            self.selected_port = selected_items[0].text()
        super().accept()

class ConnectionView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(self.NoDrag)
        self.setTransformationAnchor(self.AnchorUnderMouse)

        self.middle_mouse_button_pressed = False
        self.last_mouse_pos = QPointF()

    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            zoom_in_factor = 1.25
            zoom_out_factor = 1 / zoom_in_factor
            zoom_factor = zoom_out_factor
            if event.angleDelta().y() > 0:
                zoom_factor = zoom_in_factor
            self.scale(zoom_factor, zoom_factor)
        else:
            super().wheelEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.middle_mouse_button_pressed = True
            self.last_mouse_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.middle_mouse_button_pressed:
            delta = self.mapToScene(event.pos()) - self.mapToScene(self.last_mouse_pos)
            self.last_mouse_pos = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - int(delta.x()))
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - int(delta.y()))
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.middle_mouse_button_pressed = False
            self.setCursor(Qt.ArrowCursor)
        super().mouseReleaseEvent(event)

class PPMScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSceneRect(0, 0, 2000, 2000)
        self.setBackgroundBrush(QBrush(QColor("#323232")))
        self.temp_connection_line = None
        self.connection_start_node = None
        self.connection_start_index = -1
        self.connections = []

        self.update_timer = QTimer(self)
        self.update_timer.setInterval(50)
        self.update_timer.timeout.connect(self.update_all_connections)
        self.update_timer.start()

    def update_all_connections(self):
        for conn in self.connections:
            conn.update_path()

    def remove_all_connections(self):
        for conn in list(self.connections):
            self.remove_connection(conn)

    def remove_connection(self, conn):
        start_node = conn.start_node
        end_node = conn.end_node
        start_node.remove_connection(conn)
        end_node.set_input_occupied(conn.end_index, False)

        if hasattr(conn, 'slot') and conn.slot is not None:
            try:
                start_node.output_signals[conn.start_index].output_signal.disconnect(conn.slot)
            except TypeError:
                pass
        self.removeItem(conn)
        if conn in self.connections:
            self.connections.remove(conn)

    def start_connection_drag(self, start_pos, start_node, start_index):
        self.connection_start_node = start_node
        self.connection_start_index = start_index
        self.temp_connection_line = QGraphicsPathItem()
        self.temp_connection_line.setPen(QPen(QColor("#00BFFF"), 2, Qt.DotLine))
        self.addItem(self.temp_connection_line)
        self.update_temp_line(start_pos, start_pos)

    def mouseMoveEvent(self, event):
        if self.temp_connection_line:
            start_pos = self.connection_start_node.get_output_dot_positions()[self.connection_start_index]
            self.update_temp_line(start_pos, event.scenePos())
        super().mouseMoveEvent(event)

    def update_temp_line(self, start_pos, end_pos):
        path = QPainterPath(start_pos)
        dx = abs(start_pos.x() - end_pos.x()) * 0.5
        start_tangent = QPointF(start_pos.x() + dx, start_pos.y())
        end_tangent = QPointF(end_pos.x() - dx, end_pos.y())
        path.cubicTo(start_tangent, end_tangent, end_pos)
        self.temp_connection_line.setPath(path)

    def mouseReleaseEvent(self, event):
        if self.temp_connection_line:
            items = self.items(event.scenePos())
            valid_drop = False
            for item in items:
                if hasattr(item, 'get_input_dot_rects'):
                    input_rects = item.get_input_dot_rects()
                    for i, input_rect in enumerate(input_rects):
                        if input_rect.contains(event.scenePos()):
                            if item.is_input_occupied(i):
                                print(f"Error: Input {i} on {item.title} is already occupied.")
                            else:
                                self.create_connection(self.connection_start_node, self.connection_start_index, item, i)
                            valid_drop = True
                            break
                    if valid_drop:
                        break
            self.removeItem(self.temp_connection_line)
            self.temp_connection_line = None
            self.connection_start_node = None
            self.connection_start_index = -1
        super().mouseReleaseEvent(event)

    def create_connection(self, start_node, start_index, end_node, end_index=0):
        new_connection = Connection(start_node, start_index, end_node, end_index)
        self.addItem(new_connection)
        self.connections.append(new_connection)
        end_node.set_input_occupied(end_index, True)
        if start_index < len(start_node.output_signals):
            slot = lambda value: end_node.set_value(value, end_index)
            new_connection.slot = slot
            start_node.output_signals[start_index].output_signal.connect(slot)
            print(f"Connected {start_node.title} output {start_index} to {end_node.title} input {end_index}")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            selected_items = self.selectedItems()
            for item in selected_items:
                # Allow JoystickNode to be deleted as well
                if isinstance(item, (JoystickNode, CustomLogicNode, BoostControlNode, ToggleNode,
                                     ThreePositionSwitchNode, ExpoCurveNode, MixerNode, AxisToButtonsNode, SwitchGateNode)):
                    for conn in list(item.connections):
                        self.remove_connection(conn)
                    self.removeItem(item)
        else:
            super().keyPressEvent(event)

class PPMApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QtPye-PPM-Controller")
        self.setGeometry(100, 100, 1200, 800)

        pygame.init()
        pygame.joystick.init()
        print(f"Detected {pygame.joystick.get_count()} joysticks.")

        self.serial_manager = SerialManager()
        self.serial_manager.connection_status_changed.connect(self.update_status)
        self.serial_manager.log_message.connect(self.append_log)

        self.selected_port = None
        self.scene = PPMScene(self)
        self.view = ConnectionView(self.scene)
        self.setCentralWidget(self.view)

        # Default PPM nodes are still created
        self.ppm_nodes = []
        for i in range(8):
            node = PPMChannelNode(i + 1, 800, 50 + i * 110, serial_manager=self.serial_manager)
            self.ppm_nodes.append(node)
            self.scene.addItem(node)

        self.serial_console = QDockWidget("Serial Console", self)
        self.serial_console.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.TopDockWidgetArea)
        console_widget = QWidget()
        console_layout = QVBoxLayout(console_widget)
        self.console_text = QTextEdit()
        self.console_text.setReadOnly(True)
        console_layout.addWidget(self.console_text)
        raw_checkbox = QCheckBox("Raw")
        raw_checkbox.stateChanged.connect(self.toggle_raw_mode)
        console_layout.addWidget(raw_checkbox)
        self.serial_console.setWidget(console_widget)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.serial_console)
        self.serial_console.setVisible(False)

        toolbar = QToolBar("Controls")
        self.addToolBar(toolbar)

        # Build the "Add Node" menu, dynamically adding joystick options
        add_node_menu = QMenu(self)
        joystick_count = pygame.joystick.get_count()
        if joystick_count > 0:
            for i in range(joystick_count):
                joystick = pygame.joystick.Joystick(i)
                joystick.init()
                action = QAction(f"Input: {joystick.get_name()} (ID {i})", self)
                action.triggered.connect(lambda checked, jid=i: self.add_joystick_node(jid))
                add_node_menu.addAction(action)
            add_node_menu.addSeparator()

        add_single_input_node_action = QAction("1-Input Logic", self)
        add_single_input_node_action.triggered.connect(lambda: self.add_custom_node(1))
        add_node_menu.addAction(add_single_input_node_action)
        add_two_input_node_action = QAction("2-Input Logic", self)
        add_two_input_node_action.triggered.connect(lambda: self.add_custom_node(2))
        add_node_menu.addAction(add_two_input_node_action)
        add_boost_node_action = QAction("Boost Node", self)
        add_boost_node_action.triggered.connect(self.add_boost_node)
        add_node_menu.addAction(add_boost_node_action)
        add_toggle_node_action = QAction("Toggle Switch", self)
        add_toggle_node_action.triggered.connect(self.add_toggle_node)
        add_node_menu.addAction(add_toggle_node_action)
        add_3pos_switch_action = QAction("3-Position Switch", self)
        add_3pos_switch_action.triggered.connect(self.add_three_position_switch_node)
        add_node_menu.addAction(add_3pos_switch_action)
        add_expo_node_action = QAction("Expo Curve", self)
        add_expo_node_action.triggered.connect(self.add_expo_node)
        add_node_menu.addAction(add_expo_node_action)
        add_mixer_node_action = QAction("Mixer", self)
        add_mixer_node_action.triggered.connect(self.add_mixer_node)
        add_node_menu.addAction(add_mixer_node_action)
        add_axis_to_buttons_action = QAction("Axis to Buttons", self)
        add_axis_to_buttons_action.triggered.connect(self.add_axis_to_buttons_node)
        add_node_menu.addAction(add_axis_to_buttons_action)
        add_switch_gate_action = QAction("Switch Gate", self)
        add_switch_gate_action.triggered.connect(self.add_switch_gate_node)
        add_node_menu.addAction(add_switch_gate_action)

        add_node_button = QToolButton(self)
        add_node_button.setText("Add Node")
        add_node_button.setIcon(QIcon.fromTheme("list-add"))
        add_node_button.setMenu(add_node_menu)
        add_node_button.setPopupMode(QToolButton.InstantPopup)
        toolbar.addWidget(add_node_button)
        toolbar.addSeparator()

        select_port_action = QAction(QIcon.fromTheme("folder-remote"), "Select Port", self)
        select_port_action.triggered.connect(self.show_port_selection)
        toolbar.addAction(select_port_action)
        self.connect_action = QAction(QIcon.fromTheme("network-connect"), "Connect", self)
        self.connect_action.triggered.connect(self.connect_to_port)
        toolbar.addAction(self.connect_action)
        self.disconnect_action = QAction(QIcon.fromTheme("network-disconnect"), "Disconnect", self)
        self.disconnect_action.triggered.connect(self.serial_manager.disconnect)
        toolbar.addAction(self.disconnect_action)
        self.disconnect_action.setEnabled(False)
        self.load_action = QAction(QIcon.fromTheme("document-open"), "Load Layout", self)
        self.load_action.triggered.connect(self.load_layout)
        toolbar.addAction(self.load_action)
        self.save_action = QAction(QIcon.fromTheme("document-save"), "Save Layout", self)
        self.save_action.triggered.connect(self.save_layout)
        toolbar.addAction(self.save_action)
        toolbar.addSeparator()
        self.remove_all_action = QAction(QIcon.fromTheme("edit-clear"), "Remove All Connections", self)
        self.remove_all_action.triggered.connect(self.scene.remove_all_connections)
        toolbar.addAction(self.remove_all_action)
        toggle_console_action = self.serial_console.toggleViewAction()
        toggle_console_action.setText("Toggle Console")
        toggle_console_action.setIcon(QIcon.fromTheme("utilities-terminal"))
        toolbar.addAction(toggle_console_action)

        self.statusBar()
        self.status_label = QLabel("Disconnected")
        self.statusBar().addWidget(self.status_label)
        self.max_log_blocks = 500
        self.load_layout()
        self.auto_connect()

    def add_joystick_node(self, joystick_id):
        try:
            node = JoystickNode(joystick_id, x=50, y=50)
            self.scene.addItem(node)
        except ValueError as e:
            print(f"Error adding joystick {joystick_id}: {e}")

    def add_custom_node(self, inputs):
        node = CustomLogicNode(x=400, y=100, inputs=inputs)
        self.scene.addItem(node)

    def add_boost_node(self):
        node = BoostControlNode(x=400, y=100)
        self.scene.addItem(node)

    def add_toggle_node(self):
        node = ToggleNode(x=400, y=100)
        self.scene.addItem(node)

    def add_three_position_switch_node(self):
        node = ThreePositionSwitchNode(x=400, y=100)
        self.scene.addItem(node)

    def add_expo_node(self):
        node = ExpoCurveNode(x=400, y=100)
        self.scene.addItem(node)

    def add_mixer_node(self):
        node = MixerNode(x=400, y=100)
        self.scene.addItem(node)

    def add_axis_to_buttons_node(self):
        node = AxisToButtonsNode(x=400, y=100)
        self.scene.addItem(node)

    def add_switch_gate_node(self):
        node = SwitchGateNode(x=400, y=100)
        self.scene.addItem(node)

    def auto_connect(self):
        default_port = "/dev/ttyACM0"
        available_ports = self.serial_manager.list_ports()
        self.append_log("Attempting to auto-connect...", False)
        if default_port in available_ports:
            self.selected_port = default_port
            self.append_log(f"Default port {default_port} found. Connecting.", False)
            self.serial_manager.connect(self.selected_port)
        else:
            self.append_log(f"Default port {default_port} not found. Please select a port manually.", False)

    def show_port_selection(self):
        ports = self.serial_manager.list_ports()
        if not ports:
            self.append_log("No serial ports found.", False)
            return
        dialog = PortSelectionDialog(ports)
        if dialog.exec_() == QDialog.Accepted and dialog.selected_port:
            self.selected_port = dialog.selected_port
            self.append_log(f"Selected port: {self.selected_port}", False)
            self.connect_action.setEnabled(True)
        else:
            self.append_log("Port selection cancelled.", False)

    def connect_to_port(self):
        if self.selected_port:
            self.serial_manager.connect(self.selected_port)

    def update_status(self, is_connected):
        if is_connected:
            self.status_label.setText(f"Connected to {self.selected_port}")
            self.connect_action.setEnabled(False)
            self.disconnect_action.setEnabled(True)
        else:
            self.status_label.setText("Disconnected")
            self.connect_action.setEnabled(True)
            self.disconnect_action.setEnabled(False)

    def append_log(self, message, is_raw):
        document = self.console_text.document()
        if document.blockCount() > self.max_log_blocks:
            cursor = self.console_text.textCursor()
            cursor.movePosition(cursor.Start)
            cursor.movePosition(cursor.NextBlock, cursor.KeepAnchor,
                                document.blockCount() - self.max_log_blocks)
            cursor.removeSelectedText()
            cursor.movePosition(cursor.End)
        cursor = self.console_text.textCursor()
        cursor.movePosition(cursor.End)
        self.console_text.setTextCursor(cursor)
        if is_raw:
            self.console_text.insertHtml(f"<span style='color: #FFC107;'>[RAW] {message}</span><br>")
        else:
            self.console_text.insertPlainText(message + '\n')
        self.console_text.verticalScrollBar().setValue(self.console_text.verticalScrollBar().maximum())

    def toggle_raw_mode(self, state):
        self.serial_manager.is_raw_mode = (state == Qt.Checked)

    def save_layout(self):
        nodes = []
        for item in self.scene.items():
            if isinstance(item, BaseNode):
                nodes.append(item.get_state())
        connections = []
        for conn in self.scene.connections:
            connections.append({
                "start_node_id": conn.start_node.id,
                "start_node_output_index": conn.start_index,
                "end_node_id": conn.end_node.id,
                "end_node_input_index": conn.end_index
            })
        with open("layout.json", "w") as f:
            json.dump({"nodes": nodes, "connections": connections}, f, indent=4)
        print("Layout saved.")
        self.append_log("Layout saved to layout.json", False)

    def load_layout(self):
        try:
            with open("layout.json", "r") as f:
                data = json.load(f)

            # --- Clear existing custom nodes and connections ---
            for item in list(self.scene.items()):
                if isinstance(item, Connection):
                    self.remove_connection(item)
                elif not isinstance(item, (JoystickNode, PPMChannelNode)):
                    self.scene.removeItem(item)

            node_map_by_title = {item.title: item for item in self.scene.items() if isinstance(item, BaseNode)}
            node_map_by_id = {}

            # --- First Pass: Create/Reposition all nodes ---
            for node_data in data["nodes"]:
                node_type = node_data["type"]
                title = node_data["title"]
                node_id = node_data["id"]
                node = None

                if title in node_map_by_title:
                    node = node_map_by_title[title]
                    # Update state for default nodes (e.g., position)
                    node.set_state(node_data)
                else:
                    # Create a new custom node
                    node = None
                    if node_type == "JoystickNode":
                        joystick_id = node_data.get('joystick_id', 0)
                        if joystick_id < pygame.joystick.get_count():
                            node = JoystickNode(joystick_id, node_data['x'], node_data['y'])
                    elif node_type == "CustomLogicNode":
                        num_inputs = node_data.get('inputs', 1)
                        node = CustomLogicNode(x=node_data['x'], y=node_data['y'], inputs=num_inputs)
                    elif node_type == "BoostControlNode":
                        node = BoostControlNode(x=node_data['x'], y=node_data['y'])
                    elif node_type == "ToggleNode":
                        node = ToggleNode(x=node_data['x'], y=node_data['y'])
                    elif node_type == "ThreePositionSwitchNode":
                        node = ThreePositionSwitchNode(x=node_data['x'], y=node_data['y'])
                    elif node_type == "ExpoCurveNode":
                        node = ExpoCurveNode(x=node_data['x'], y=node_data['y'])
                    elif node_type == "MixerNode":
                        node = MixerNode(x=node_data['x'], y=node_data['y'])
                    elif node_type == "AxisToButtonsNode":
                        node = AxisToButtonsNode(x=node_data['x'], y=node_data['y'])
                    elif node_type == "SwitchGateNode":
                        node = SwitchGateNode(x=node_data['x'], y=node_data['y'])

                    # After creating any new node, restore its full state
                    if node:
                        node.set_state(node_data)

                if node:
                    node.id = node_id # Assign the saved ID
                    self.scene.addItem(node)
                    node_map_by_id[node.id] = node

            # --- Second Pass: Create all connections using unique IDs ---
            for conn_data in data["connections"]:
                start_node_id = conn_data["start_node_id"]
                end_node_id = conn_data["end_node_id"]

                if start_node_id in node_map_by_id and end_node_id in node_map_by_id:
                    start_node = node_map_by_id[start_node_id]
                    end_node = node_map_by_id[end_node_id]
                    self.scene.create_connection(
                        start_node, conn_data["start_node_output_index"],
                        end_node, conn_data["end_node_input_index"]
                    )

            print("Layout loaded.")
            self.append_log("Layout loaded from layout.json", False)
        except FileNotFoundError:
            print("No layout.json file found to load.")
            self.append_log("No layout.json file found to load.", False)
        except Exception as e:
            print(f"Error loading layout: {e}")
            self.append_log(f"Error loading layout: {e}", False)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PPMApp()
    window.show()
    sys.exit(app.exec_())
