# serial_manager.py
import serial
import serial.tools.list_ports
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
import time

class SerialManager(QObject):
    connection_status_changed = pyqtSignal(bool)
    log_message = pyqtSignal(str, bool)

    def __init__(self):
        super().__init__()
        self.ser = None
        self.port_name = None
        self.baud_rate = 115200
        self.is_raw_mode = False

        self.channel_values = {i: 1500 for i in range(1, 9)}

        self.transmit_timer = QTimer(self)
        self.transmit_timer.setInterval(20) # 20 ms = 50 Hz update rate
        self.transmit_timer.timeout.connect(self._transmit_channel_data)

        self.read_timer = QTimer(self)
        self.read_timer.setInterval(50)
        self.read_timer.timeout.connect(self._read_serial_data)

    def list_ports(self):
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def connect(self, port_name):
        if self.ser and self.ser.is_open:
            self.disconnect()
        try:
            self.ser = serial.Serial(port_name, self.baud_rate, timeout=0)
            self.port_name = port_name
            self.connection_status_changed.emit(True)
            self.log_message.emit(f"Connected to {port_name} at {self.baud_rate} baud.", False)
            self.read_timer.start()
            self.transmit_timer.start()
            return True
        except serial.SerialException as e:
            self.log_message.emit(f"Error connecting: {e}", False)
            self.connection_status_changed.emit(False)
            return False

    def disconnect(self):
        self.transmit_timer.stop()
        self.read_timer.stop()
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.log_message.emit("Disconnected.", False)
            self.connection_status_changed.emit(False)
        self.ser = None

    def send_command(self, command):
        """
        This method updates the local state for a channel.
        The transmit timer will send the actual command later.
        """
        try:
            channel_str, value_str = command.split('=')
            channel = int(channel_str)
            value = int(value_str)
            if 1 <= channel <= 8:
                self.channel_values[channel] = value
        except ValueError:
            self.log_message.emit(f"Invalid command format: {command}", False)

    def _transmit_channel_data(self):
        """
        Called by the timer to send the current state of all 8 channels
        using the correct ASCII Command Interface (ACI) format.
        """
        if self.ser and self.ser.is_open:
            try:
                # Loop through each channel and send its respective command
                for channel, value in self.channel_values.items():
                    # Format the command as "i=xxxx" e.g., "1=1500"
                    command_str = f"{channel}={value}"

                    # Send the command. Manual says no CR/LF is needed.
                    self.ser.write(command_str.encode())

                    if self.is_raw_mode:
                        self.log_message.emit(f"Sent: {command_str}", True)

            except serial.SerialException as e:
                self.log_message.emit(f"Error sending data: {e}", False)
                self.disconnect()

    def _read_serial_data(self):
        if self.ser and self.ser.is_open and self.ser.in_waiting > 0:
            data = self.ser.read_all()
            if self.is_raw_mode:
                self.log_message.emit(f"Received (raw): {data}", True)
            else:
                try:
                    decoded_data = data.decode('utf-8', errors='ignore').strip()
                    if decoded_data:
                        self.log_message.emit(f"Received: {decoded_data}", False)
                except UnicodeDecodeError:
                    self.log_message.emit(f"Received (raw): {data}", True)
