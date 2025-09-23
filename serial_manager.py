import serial
import serial.tools.list_ports
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
import time

class SerialManager(QObject):
    connection_status_changed = pyqtSignal(bool)
    log_message = pyqtSignal(str, bool)
    sps_updated = pyqtSignal(int) # New signal for the SPS value

    def __init__(self):
        super().__init__()
        self.ser = None
        self.port_name = None
        self.baud_rate = 115200
        self.is_raw_mode = False

        self.channel_values = {i: 1500 for i in range(1, 9)}
        self.raw_log_batch = []
        self.sps_counter = 0 # Counter for signals per second

        # Timer for sending PPM data (50 Hz)
        self.transmit_timer = QTimer(self)
        self.transmit_timer.setInterval(20)
        self.transmit_timer.timeout.connect(self._transmit_channel_data)

        # Timer for reading incoming data
        self.read_timer = QTimer(self)
        self.read_timer.setInterval(50)
        self.read_timer.timeout.connect(self._read_serial_data)

        # New timer to batch log updates (5 Hz)
        self.log_update_timer = QTimer(self)
        self.log_update_timer.setInterval(200)
        self.log_update_timer.timeout.connect(self._emit_batched_logs)

        # New timer to report the SPS count once per second
        self.sps_timer = QTimer(self)
        self.sps_timer.setInterval(1000)
        self.sps_timer.timeout.connect(self._report_sps)

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
            self.log_update_timer.start()
            self.sps_timer.start() # Start the SPS timer
            return True
        except serial.SerialException as e:
            self.log_message.emit(f"Error connecting: {e}", False)
            self.connection_status_changed.emit(False)
            return False

    def disconnect(self):
        self.transmit_timer.stop()
        self.read_timer.stop()
        self.log_update_timer.stop()
        self.sps_timer.stop() # Stop the SPS timer
        self.sps_updated.emit(0) # Reset SPS display to 0
        self.raw_log_batch.clear()
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.log_message.emit("Disconnected.", False)
            self.connection_status_changed.emit(False)
        self.ser = None

    def send_command(self, command):
        try:
            channel_str, value_str = command.split('=')
            channel = int(channel_str)
            value = int(value_str)
            if 1 <= channel <= 8:
                self.channel_values[channel] = value
        except ValueError:
            self.log_message.emit(f"Invalid command format: {command}", False)

    def _transmit_channel_data(self):
        if self.ser and self.ser.is_open:
            try:
                for channel, value in self.channel_values.items():
                    command_str = f"{channel}={value}"
                    self.ser.write(command_str.encode())
                    self.sps_counter += 1 # Increment for each command sent

                    if self.is_raw_mode:
                        self.raw_log_batch.append(f"Sent: {command_str}")
            except serial.SerialException as e:
                self.log_message.emit(f"Error sending data: {e}", False)
                self.disconnect()

    def _read_serial_data(self):
        if self.ser and self.ser.is_open and self.ser.in_waiting > 0:
            data = self.ser.read_all()
            if self.is_raw_mode:
                self.raw_log_batch.append(f"Received (raw): {data}")
            else:
                try:
                    decoded_data = data.decode('utf-8', errors='ignore').strip()
                    if decoded_data:
                        self.log_message.emit(f"Received: {decoded_data}", False)
                except UnicodeDecodeError:
                    self.log_message.emit(f"Received (raw): {data}", True)

    def _emit_batched_logs(self):
        if self.raw_log_batch:
            full_log_message = "\n".join(self.raw_log_batch)
            self.log_message.emit(full_log_message, True)
            self.raw_log_batch.clear()

    def _report_sps(self):
        """Called once per second to report the signal count and reset it."""
        self.sps_updated.emit(self.sps_counter)
        self.sps_counter = 0
