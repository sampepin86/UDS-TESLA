# -*- coding: utf-8 -*-
"""
Created on May 31, 2026

@author: Antigravity

@description: esp32_transport implements the CAN transport layer for udsClient SWIG
interfacing via ESP32 over either Serial (USB) or TCP Sockets (Wi-Fi).
"""
import time
import socket
import serial
import threading
from collections import deque
import traceback

# Tesla Python
from abstract_transport import AbstractTransport, threadsafe_check
import uds.constants as constants
import uds.utils as utils

MAX_MSG_LEN = 8
DEFAULT_RECEIVE_TIMEOUT = constants.DEFAULT_READ_TIMEOUT_SECONDS

class ESP32Transport(AbstractTransport):
    """
    Implements the CAN Transport layer functions for ESP32 Bridge
    """
    def __init__(self, connection_type='wifi', target='tesladiag.local', port=1337, baudrate=115200, logger=None, disable_threadsafety=False):
        """
        :param connection_type: 'wifi' or 'serial'
        :param target: IP address/hostname (for wifi) or COM port name (for serial)
        :param port: TCP port (default 1337)
        :param baudrate: Serial baudrate (default 115200)
        """
        super(ESP32Transport, self).__init__(logger, disable_threadsafety)
        self.connection_type = connection_type
        self.target = target
        self.port = port
        self.baudrate = baudrate
        self.receive_timeout_seconds = DEFAULT_RECEIVE_TIMEOUT

        self.device = None
        self.read_queues = {}
        self.read_thread = None
        self.running = False
        self.queue_lock = threading.Lock()

    @threadsafe_check
    def initialize(self, can_bus_id=None, can_baud='6'):
        """
        Initialize connection to ESP32 and open the CAN channel.
        :param can_baud: '6' for 500k, '8' for 1M, etc.
        """
        try:
            if self.connection_type == 'wifi':
                self._logger.info("ESP32Transport: Connecting to ESP32 over Wi-Fi at {}:{}".format(self.target, self.port))
                self.device = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.device.settimeout(5.0)
                self.device.connect((self.target, self.port))
                # Set to blocking for the thread
                self.device.settimeout(None)
            else:
                self._logger.info("ESP32Transport: Connecting to ESP32 over Serial at {} @ {}".format(self.target, self.baudrate))
                self.device = serial.Serial(self.target, self.baudrate, timeout=1.0)
                time.sleep(1.0) # Wait for serial bootloader window to pass

            # Start background reading thread
            self.running = True
            self.read_thread = threading.Thread(target=self._read_loop)
            self.read_thread.daemon = True
            self.read_thread.start()

            # Set CAN speed and Open CAN channel (best-effort - no car connected is OK)
            self._write_cmd("S{}\r".format(can_baud))
            time.sleep(0.1)
            self._write_cmd("O\r")
            time.sleep(0.2)  # Small delay to let ESP32 respond

            self._logger.info("ESP32Transport: Adapter connected. CAN channel open (car may not be connected yet).")
            return 0  # Always succeed once the TCP/serial link is established
        except Exception as e:
            self._logger.error("ESP32Transport: Initialization failed: {}".format(e.message))
            traceback.print_exc()
            return -1

    def _write_cmd(self, cmd):
        if self.connection_type == 'wifi':
            self.device.sendall(cmd)
        else:
            self.device.write(cmd)

    def _read_loop(self):
        buffer_data = ""
        while self.running:
            try:
                if self.connection_type == 'wifi':
                    chunk = self.device.recv(1024)
                    if not chunk:
                        self._logger.warning("ESP32Transport: Socket disconnected.")
                        break
                    buffer_data += chunk
                else:
                    chunk = self.device.read(self.device.in_waiting or 1)
                    if not chunk:
                        continue
                    buffer_data += chunk

                while '\r' in buffer_data:
                    line, buffer_data = buffer_data.split('\r', 1)
                    line = line.strip()
                    if len(line) > 0:
                        self._parse_line(line)
            except Exception as e:
                self._logger.error("ESP32Transport: Error in read loop: {}".format(e.message))
                time.sleep(0.1)

    def _parse_line(self, line):
        try:
            # Expected format: t[ID][LEN][DATA] or T[ID][LEN][DATA]
            if line[0] in ('t', 'T'):
                is_ext = (line[0] == 'T')
                id_len = 8 if is_ext else 3
                
                id_hex = line[1:1+id_len]
                can_id = int(id_hex, 16)
                
                dlc = int(line[1+id_len], 16)
                data_hex = line[1+id_len+1:1+id_len+1+(dlc*2)]
                
                data_bytes = []
                for i in range(dlc):
                    data_bytes.append(int(data_hex[i*2:(i*2)+2], 16))
                
                # Zero pad to 8 bytes as required by UDS core
                while len(data_bytes) < 8:
                    data_bytes.append(0)

                with self.queue_lock:
                    if can_id not in self.read_queues:
                        self.read_queues[can_id] = deque()
                    self.read_queues[can_id].append(data_bytes)
        except Exception as e:
            self._logger.warning("ESP32Transport: Failed to parse line '{}': {}".format(line, e.message))

    @threadsafe_check
    def transmit_frame(self, state, transmit_buffer):
        try:
            # double to bytes
            data_bytes = utils.from_pcan_byte_array(utils.double_to_array(transmit_buffer), MAX_MSG_LEN)
            data_hex = "".join("{:02X}".format(b) for b in data_bytes)
            
            # Construct SLCAN command
            cmd = "t{:03X}8{}\r".format(state.requestID, data_hex)
            self._write_cmd(cmd)
            return True
        except Exception as e:
            self._logger.error("ESP32Transport: Transmit error: {}".format(e.message))
            return False

    def receive_frame(self, state, receive_len):
        response_id = int(state.responseID)
        start_time = time.time()
        
        while (time.time() - start_time) < self.receive_timeout_seconds:
            with self.queue_lock:
                if response_id in self.read_queues and len(self.read_queues[response_id]) > 0:
                    data_bytes = self.read_queues[response_id].popleft()
                    frame = utils.array_to_double(data_bytes)
                    return 1, frame
            time.sleep(0.005) # Poll queue every 5ms
            
        self._logger.warning("ESP32Transport: Timeout waiting for response 0x{:03X}".format(response_id))
        return 0, 0x0000000000000000

    @threadsafe_check
    def clear_receive_queue(self, state):
        response_id = int(state.responseID)
        with self.queue_lock:
            if response_id in self.read_queues:
                self.read_queues[response_id].clear()
        return True

    @threadsafe_check
    def set_node(self, node):
        # Register read queue for the target response ID
        response_id = int(node.responseID)
        with self.queue_lock:
            if response_id not in self.read_queues:
                self.read_queues[response_id] = deque()

    @threadsafe_check
    def clear_node(self, node):
        response_id = int(node.responseID)
        with self.queue_lock:
            if response_id in self.read_queues:
                del self.read_queues[response_id]

    @threadsafe_check
    def wait_for_boot_id(self, node, periodic=False, boot_in_app=False):
        boot_id = int(node.bootID)
        start_time = time.time()
        
        # Register boot ID queue
        with self.queue_lock:
            if boot_id not in self.read_queues:
                self.read_queues[boot_id] = deque()
                
        timeout = 30.0
        while (time.time() - start_time) < timeout:
            with self.queue_lock:
                if len(self.read_queues[boot_id]) > 0:
                    data_bytes = self.read_queues[boot_id].popleft()
                    return utils.array_to_double(data_bytes)
            time.sleep(0.01)
            
        return None

    def finish(self):
        self._logger.info("ESP32Transport: Closing connection...")
        self.running = False
        try:
            self._write_cmd("C\r") # Close CAN channel
            time.sleep(0.1)
            if self.device:
                self.device.close()
        except Exception:
            pass
