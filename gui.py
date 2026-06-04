#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on May 31, 2026

@author: Antigravity

@description: Tesla UDS Diagnostic GUI - A standalone Python 3 CustomTkinter application
that connects to the UDS Bridge backend (Python 2.7) via JSON-RPC over TCP socket.
Provides a tabbed interface for ECU diagnostics, security access, DTC management, and memory operations.

Auto-launches the backend bridge (uds_bridge.py in uds-py27 environment) on startup.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import socket
import threading
import time
import queue
import traceback
import subprocess
import os
import sys
import shutil
from datetime import datetime


class UDSBridgeClient:
    """JSON-RPC client for communicating with uds_bridge.py backend."""
    
    def __init__(self, host='127.0.0.1', port=5000):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.req_id_counter = 1
        self.pending_responses = {}
        self.response_lock = threading.Lock()
        self.receive_thread = None
        
    def connect(self):
        """Connect to the UDS Bridge server."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receive_thread.start()
            return True
        except Exception as e:
            print("Failed to connect to UDS Bridge: {}".format(e))
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from the UDS Bridge server."""
        self.connected = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
    
    def call(self, method, params=None, timeout=10):
        """Call a JSON-RPC method and wait for response."""
        if not self.connected:
            raise Exception("Not connected to UDS Bridge")
        
        req_id = self.req_id_counter
        self.req_id_counter += 1
        
        request = {
            'jsonrpc': '2.0',
            'method': method,
            'params': params or {},
            'id': req_id
        }
        
        # Send request
        try:
            self.socket.sendall((json.dumps(request) + '\n').encode('utf-8'))
        except Exception as e:
            self.connected = False
            raise Exception("Failed to send request: {}".format(e))
        
        # Wait for response
        start_time = time.time()
        while time.time() - start_time < timeout:
            with self.response_lock:
                if req_id in self.pending_responses:
                    response = self.pending_responses.pop(req_id)
                    if 'error' in response:
                        raise Exception(response.get('error'))
                    return response.get('result')
            time.sleep(0.01)
        
        raise Exception("RPC call timeout for method: {}".format(method))
    
    def _receive_loop(self):
        """Background thread to receive responses from bridge."""
        buffer_data = ""
        while self.connected:
            try:
                data = self.socket.recv(4096)
                if not data:
                    self.connected = False
                    break
                
                buffer_data += data.decode('utf-8')
                
                while '\n' in buffer_data:
                    line, buffer_data = buffer_data.split('\n', 1)
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        response = json.loads(line)
                        req_id = response.get('id')
                        if req_id:
                            with self.response_lock:
                                self.pending_responses[req_id] = response
                    except:
                        pass
            except:
                if self.connected:
                    time.sleep(0.1)


# --- UDS Description Dictionaries ---
SESSION_DESCRIPTIONS = {
    "Default (0x01)": "Normal operation mode. Diagnostic capability is limited to reading basic data and DTCs.",
    "Programming (0x02)": "Unlocks memory erase/flash operations, bootloader access, and firmware transfer.",
    "Extended (0x03)": "Low-level engineering diagnostics, manual actuator overrides, routines, and protected DIDs.",
    "Safety System (0x04)": "Used for safety-critical component configuration and deployments."
}

RESET_DESCRIPTIONS = {
    "Hard Reset (0x01)": "Hard Reset - Full hardware power cycle (equivalent to disconnecting the battery).",
    "Soft Reset (0x02)": "Soft Reset - Software reboot (restarts execution thread/app code without power cycle).",
    "Key Off/On Reset (0x03)": "Key Off/On Reset - Simulates ignition key cycle to reset passive locks.",
    "Enable Rapid Power Shut Down (0x04)": "Enable Rapid Power Shut Down - Commands ECU to immediately shut down power rails to enter sleep mode.",
    "Disable Rapid Power Shut Down (0x05)": "Disable Rapid Power Shut Down - Cancels rapid power shut down state."
}

DID_DESCRIPTIONS = {
    "0x0101": ("Component and Firmware Type", "Indicates whether the ECU is currently running the Application, Bootloader, or Updater software module."),
    "0x0102": ("Module to Program", "Specifies the target memory module or partition configuration for programming."),
    "0x0103": ("Tool Serial Number", "The unique serial number of the diagnostic tool/hardware interface used for UDS communication."),
    "0xF011": ("Manufacturing Block", "Contains manufacturing details such as date of production, line identifier, and hardware build options."),
    "0xF012": ("Board Part Number", "The Tesla internal part number for the PCB assembly."),
    "0xF013": ("Board Serial Number", "The unique factory serial number of the physical circuit board."),
    "0xF014": ("Package Part Number", "The Tesla internal part number for the complete module assembly."),
    "0xF015": ("Package Serial Number", "The unique serial number of the complete module assembly."),
    "0xF016": ("Genealogy Version", "Tracks revision history and compatibility level of the board hardware genealogy."),
    "0xF017": ("Genealogy CRC", "Cyclic Redundancy Check (checksum) of the hardware genealogy metadata."),
    "0xF018": ("Genealogy Block", "Complete binary block of assembly lineage and genealogy tracing."),
    "0xF019": ("Calibration Version", "The version number of the calibration parameters currently loaded in the ECU."),
    "0xF01A": ("Calibration CRC", "Cyclic Redundancy Check (checksum) of the calibration parameter space."),
    "0xF01C": ("Assembly ID", "Unique identification number representing the overall system assembly configuration."),
    "0xF01D": ("Usage ID", "Specifies the deployment context or role of this ECU on the network."),
    "0xF01E": ("Sub Usage ID", "Further specifies sub-roles or secondary configurations."),
    "0xF01F": ("EEPROM Block Status", "Self-diagnostic status of the non-volatile EEPROM memory block."),
    "0xF020": ("Calibration Block", "Raw binary parameters defining the calibration values for hardware sensors and actuators."),
    "0xF180": ("Bootloader Version", "The software version of the low-level bootloader stored in ROM/protected flash."),
    "0xF181": ("App Version", "The software version of the main application code executing on the ECU."),
    "0xF190": ("VIN (Vehicle Identification Number)", "The vehicle's unique 17-character VIN stored in the ECU."),
    "0xF197": ("System Name", "Friendly name of the target diagnostic system."),
    "0xD001": ("HV Battery Voltage", "Real-time voltage of the High Voltage battery pack (in Volts). Scale: val / 10.0 V"),
    "0xD002": ("HV Battery Current", "Real-time current flow of the High Voltage battery pack (in Amperes). Scale: val / 10.0 A"),
    "0xD004": ("State of Charge (SOC)", "The remaining battery capacity expressed as a percentage (%). Scale: val / 10.0 %"),
    "0xD005": ("Average Cell Temp", "The averaged temperature sensor readings across all battery modules (in °C). Scale: val / 10.0 °C"),
    "0xD00D": ("12V Battery Voltage", "Voltage of the low-voltage auxiliary system battery (in Volts). Scale: val / 1000.0 V"),
}

ACTUATOR_DESCRIPTIONS = {
    "0x4001": ("Coolant Pump Control", "Overrides the speed of the primary battery/powertrain coolant pump (0-100%)."),
    "0x4002": ("A/C Compressor Speed", "Manual control of the air conditioning scroll compressor motor speed (RPM)."),
    "0x4003": ("Active Grille Shutter", "Commands the front active aero grille shutters to Open (100%) or Closed (0%)."),
    "0x4004": ("Cabin HVAC Blower Fan", "Overrides the passenger cabin climate blower fan speed (0-100%)."),
    "0x4005": ("Cooling Fan High Speed Relay", "Forces the radiator cooling fan to run at high speed (On/Off)."),
    "0x4006": ("Headlight Low Beam Relay", "Manual override to turn on the main headlight low beam bulbs (On/Off)."),
    "0x4007": ("Windshield Wiper Motor", "Forces the wiper motor to run in Low or High speed mode (Off/Low/High)."),
    "0x4008": ("HV Contactor Close Command", "Manually commands the battery pack high voltage contactors to close (Requires session unlock)."),
    "0x4009": ("Charge Port Latch Actuator", "Commands the charge port latch motor to lock or unlock the connector plug."),
    "0x400A": ("Body Controller Horn Relay", "Triggers the vehicle horn to blow (On/Off)."),
}

ROUTINE_DESCRIPTIONS = {
    "0xFF01": ("Erase Flash Memory", "Erases the application flash sector of the ECU memory to prepare for firmware flashing."),
    "0xFF02": ("Check Software Checksum", "Instructs the ECU to compute and verify the CRC32 checksum of the flashed application partition."),
    "0x0201": ("Steering Angle Sensor Calibration", "Zeroes the steering column absolute position sensor calibration offset."),
    "0x0202": ("Brake Bleeding Routine", "Runs the ESP hydraulic pump and cycles valves to assist in manual brake fluid bleeding."),
    "0x0203": ("HV Battery Pyrofuse Test", "Triggers a low-power continuity check on the high-voltage safety pyrofuse."),
    "0x0204": ("Thermal Runaway Self-Test", "Performs sensor verification for thermal runaway early warning sensors."),
    "0x0205": ("Radar Sensor Calibration", "Enables target alignment mode for front driving radar sensor calibration."),
    "0x0206": ("Coolant Loop Bleeding Routine", "Runs coolant pumps at high speed and cycles proportional valves to purge air bubbles from thermal loop."),
}

NRC_DESCRIPTIONS = {
    0x10: "General Reject",
    0x11: "Service Not Supported",
    0x12: "SubFunction Not Supported",
    0x13: "Incorrect Message Length Or Invalid Format",
    0x14: "Response Too Long",
    0x21: "Busy Repeat Request",
    0x22: "Conditions Not Correct",
    0x24: "Request Sequence Error",
    0x25: "No Response From Subnet Component",
    0x26: "Failure Prevents Execution Of Requested Action",
    0x31: "Request Out Of Range",
    0x33: "Security Access Denied",
    0x35: "Invalid Key",
    0x36: "Exceed Number Of Attempts",
    0x37: "Required Time Delay Not Expired",
    0x70: "Upload Download Not Accepted",
    0x71: "Transfer Data Suspended",
    0x72: "General Programming Failure",
    0x73: "Wrong Block Sequence Counter",
    0x78: "Request Correctly Received - Response Pending",
    0x7E: "SubFunction Not Supported In Active Session",
    0x7F: "Service Not Supported In Active Session",
}

def get_nrc_description(nrc):
    """Get the description for a returned UDS error code."""
    if nrc == 0:
        return "Success"
        
    # Check for UDS library/API error ranges from SWIG wrapper
    upper_byte = nrc & 0xF00
    
    if upper_byte == 0x100:
        # True negative response from ECU. The lower byte is the actual NRC.
        real_nrc = nrc & 0xFF
        desc = NRC_DESCRIPTIONS.get(real_nrc, "Unknown Negative Response Code")
        return "0x{:02X} ({})".format(real_nrc, desc)
        
    elif upper_byte == 0x200:
        return "0x{:03X} (Receive SID is different from requested SID)".format(nrc)
        
    elif upper_byte == 0x300:
        if nrc == 0x300: return "0x300 (Mismatch in received sub function value)"
        if nrc == 0x301: return "0x301 (Invalid parameter passed to API)"
        if nrc == 0x303: return "0x303 (Server already in the requested security access level)"
        return "0x{:03X} (UDS API Parameter/Configuration Error)".format(nrc)
        
    elif upper_byte == 0x000 and nrc > 0 and nrc <= 0x1F:
        # Transport / CAN layer error
        transport_errors = {
            0x1: "CAN_TIMEOUT_A_01",
            0x4: "CAN_TIMEOUT_Bs_01",
            0x6: "CAN_TIMEOUT_Cr",
            0x7: "CAN_WRONG_SN",
            0xA: "CAN_UNEXP_PDU_01 (Unexpected protocol data unit)",
            0xB: "CAN_UNEXP_PDU_02 (Unexpected protocol data unit)",
            0x10: "CAN_BUFFER_OVFLW"
        }
        desc = transport_errors.get(nrc, "Transport Layer Error")
        return "0x{:02X} ({})".format(nrc, desc)
        
    # Fallback for pure NRCs (e.g. from simulated transport)
    desc = NRC_DESCRIPTIONS.get(nrc, "Unknown Error Code")
    return "0x{:02X} ({})".format(nrc, desc)


class DiagnosticFrame(ctk.CTkFrame):
    """Base class for diagnostic function panels."""
    
    def __init__(self, parent, bridge_client, node_name, **kwargs):
        super().__init__(parent, **kwargs)
        self.bridge_client = bridge_client
        self.node_name = node_name
        self.result_text = None
    
    def execute_command(self, method, params):
        """Execute a UDS method via the bridge."""
        try:
            result = self.bridge_client.call(method, params)
            return result
        except Exception as e:
            self.log_error(str(e))
            return None
    
    def log_result(self, msg):
        """Log a successful result."""
        if self.result_text:
            timestamp = datetime.now().strftime('%H:%M:%S')
            full_msg = "[{}] {}\n".format(timestamp, str(msg))
            self.result_text.configure(state='normal')
            self.result_text.insert('end', full_msg)
            self.result_text.see('end')
            self.result_text.configure(state='disabled')
    
    def log_error(self, error):
        """Log an error."""
        if self.result_text:
            timestamp = datetime.now().strftime('%H:%M:%S')
            full_msg = "[{}] ERROR: {}\n".format(timestamp, error)
            self.result_text.configure(state='normal')
            self.result_text.insert('end', full_msg, 'error')
            self.result_text.see('end')
            self.result_text.configure(state='disabled')


class SessionControlFrame(DiagnosticFrame):
    """Diagnostic Session Control & ECU Reset Panel (Services 0x10, 0x11)."""
    
    def __init__(self, parent, bridge_client, node_name, **kwargs):
        super().__init__(parent, bridge_client, node_name, **kwargs)
        self.grid_columnconfigure(1, weight=1)
        
        # --- Session Control Section ---
        sess_title = ctk.CTkLabel(self, text="Session Control (Service 0x10)", font=("Arial", 13, "bold"))
        sess_title.grid(row=0, column=0, columnspan=4, sticky='w', padx=10, pady=(10, 5))
        
        ctk.CTkLabel(self, text="Session Type:").grid(row=1, column=0, sticky='w', padx=10)
        self.session_type = ctk.CTkComboBox(self, values=list(SESSION_DESCRIPTIONS.keys()), command=self._on_session_change)
        self.session_type.set("Default (0x01)")
        self.session_type.grid(row=1, column=1, sticky='ew', padx=10)
        
        self.response_required_sess = ctk.CTkCheckBox(self, text="Response Required", checkbox_width=20, checkbox_height=20)
        self.response_required_sess.select()
        self.response_required_sess.grid(row=1, column=2, padx=10)
        
        info_btn_sess = ctk.CTkButton(self, text="(i)", width=30, command=self.show_info_sess)
        info_btn_sess.grid(row=1, column=3, padx=5)
        
        self.session_desc_label = ctk.CTkLabel(self, text=SESSION_DESCRIPTIONS["Default (0x01)"], text_color="gray", justify="left", wraplength=450)
        self.session_desc_label.grid(row=2, column=0, columnspan=4, sticky='w', padx=10, pady=(0, 5))
        
        exec_sess_btn = ctk.CTkButton(self, text="Start Session", command=self.execute_session)
        exec_sess_btn.grid(row=3, column=0, columnspan=4, pady=(5, 10))
        
        # Divider
        divider = ctk.CTkFrame(self, height=2, fg_color="gray")
        divider.grid(row=4, column=0, columnspan=4, sticky='ew', padx=10, pady=5)
        
        # --- ECU Reset Section ---
        reset_title = ctk.CTkLabel(self, text="ECU Reset (Service 0x11)", font=("Arial", 13, "bold"))
        reset_title.grid(row=5, column=0, columnspan=4, sticky='w', padx=10, pady=(10, 5))
        
        ctk.CTkLabel(self, text="Reset Type:").grid(row=6, column=0, sticky='w', padx=10)
        self.reset_type = ctk.CTkComboBox(self, values=list(RESET_DESCRIPTIONS.keys()), command=self._on_reset_change)
        self.reset_type.set("Hard Reset (0x01)")
        self.reset_type.grid(row=6, column=1, sticky='ew', padx=10)
        
        self.response_required_reset = ctk.CTkCheckBox(self, text="Response Required", checkbox_width=20, checkbox_height=20)
        self.response_required_reset.select()
        self.response_required_reset.grid(row=6, column=2, padx=10)
        
        info_btn_reset = ctk.CTkButton(self, text="(i)", width=30, command=self.show_info_reset)
        info_btn_reset.grid(row=6, column=3, padx=5)
        
        self.reset_desc_label = ctk.CTkLabel(self, text=RESET_DESCRIPTIONS["Hard Reset (0x01)"], text_color="gray", justify="left", wraplength=450)
        self.reset_desc_label.grid(row=7, column=0, columnspan=4, sticky='w', padx=10, pady=(0, 5))
        
        exec_reset_btn = ctk.CTkButton(self, text="Reboot ECU", command=self.execute_reset)
        exec_reset_btn.grid(row=8, column=0, columnspan=4, pady=(5, 10))
        
        # Result Log
        self.result_text = tk.Text(self, height=6, width=60, state='disabled')
        self.result_text.grid(row=9, column=0, columnspan=4, sticky='nsew', padx=10, pady=10)
        self.result_text.tag_config('error', foreground='red')
        
        self.grid_rowconfigure(9, weight=1)
    
    def _on_session_change(self, choice):
        self.session_desc_label.configure(text=SESSION_DESCRIPTIONS[choice])
        
    def _on_reset_change(self, choice):
        self.reset_desc_label.configure(text=RESET_DESCRIPTIONS[choice])
        
    def show_info_sess(self):
        messagebox.showinfo("Session Control", 
            "Sends Service 0x10 to set the diagnostic session type.\n\n"
            "• Default (0x01): Normal operation mode\n"
            "• Programming (0x02): Unlocks memory erase/flash operations\n"
            "• Extended (0x03): Low-level diagnostics and actuator overrides\n"
            "• Safety System (0x04): Safety-critical operations")
            
    def show_info_reset(self):
        messagebox.showinfo("ECU Reset", 
            "Sends Service 0x11 to reboot the target microprocessor.\n\n"
            "• Hard Reset: Restarts MCU by cycling hardware power lines\n"
            "• Soft Reset: Performs soft firmware restart\n"
            "• Rapid Power Shut Down: Shuts down power rails to sleep")
            
    def execute_session(self):
        session_map = {"Default (0x01)": 1, "Programming (0x02)": 2, "Extended (0x03)": 3, "Safety System (0x04)": 4}
        session_type = session_map[self.session_type.get()]
        params = {
            'session_type': session_type,
            'response_required': self.response_required_sess.get()
        }
        self.log_result("Executing Diagnostic Session Service 0x10 (type: 0x{:02X})...".format(session_type))
        res = self.execute_command('diagnostic_session', params)
        if res == 0:
            self.log_result("SUCCESS: Diagnostic session changed successfully.")
        elif res is not None:
            self.log_error("ECU returned negative response: {}".format(get_nrc_description(res)))
            
    def execute_reset(self):
        reset_map = {
            "Hard Reset (0x01)": 1, 
            "Soft Reset (0x02)": 2, 
            "Key Off/On Reset (0x03)": 3, 
            "Enable Rapid Power Shut Down (0x04)": 4, 
            "Disable Rapid Power Shut Down (0x05)": 5
        }
        reset_type = reset_map[self.reset_type.get()]
        params = {
            'reset_type': reset_type,
            'response_required': self.response_required_reset.get()
        }
        self.log_result("Executing ECU Reset Service 0x11 (type: 0x{:02X})...".format(reset_type))
        res = self.execute_command('ecu_reset', params)
        if res == 0:
            self.log_result("SUCCESS: ECU Reboot request processed.")
        elif res is not None:
            self.log_error("ECU returned negative response: {}".format(get_nrc_description(res)))


class SecurityAccessFrame(DiagnosticFrame):
    """Security Access / ECU Unlock Panel (Service 0x27)."""
    
    def __init__(self, parent, bridge_client, node_name, **kwargs):
        super().__init__(parent, bridge_client, node_name, **kwargs)
        self.grid_columnconfigure(1, weight=1)
        
        # Title
        title = ctk.CTkLabel(self, text="Security Access - ECU Unlock (Service 0x27)", font=("Arial", 14, "bold"))
        title.grid(row=0, column=0, columnspan=3, pady=10)
        
        # Security Level Selection
        ctk.CTkLabel(self, text="Security Level:").grid(row=1, column=0, sticky='w', padx=10)
        self.security_level = ctk.CTkComboBox(self, values=["Level 0x01 (App Unlock)", "Level 0x03 (Cal Unlock)", "Level 0x05 (Dev Unlock)", "Level 0x07 (System Unlock)"], command=self._on_level_change)
        self.security_level.set("Level 0x01 (App Unlock)")
        self.security_level.grid(row=1, column=1, sticky='ew', padx=10)
        
        info_btn = ctk.CTkButton(self, text="(i)", width=30, command=self.show_info)
        info_btn.grid(row=1, column=2, padx=5)
        
        self.level_desc_label = ctk.CTkLabel(self, text="Level 0x01: Unlocks general diagnostic operations and calibration writing.", text_color="gray", justify="left", wraplength=450)
        self.level_desc_label.grid(row=2, column=0, columnspan=3, sticky='w', padx=10, pady=(5, 10))
        
        # Execute Unlock Button
        unlock_btn = ctk.CTkButton(self, text="Run Security Unlock (Seed-Key)", command=self.run_unlock)
        unlock_btn.grid(row=3, column=0, columnspan=3, pady=10)
        
        # Result Log
        self.result_text = tk.Text(self, height=12, width=60, state='disabled')
        self.result_text.grid(row=4, column=0, columnspan=3, sticky='nsew', padx=10, pady=10)
        self.result_text.tag_config('error', foreground='red')
        
        self.grid_rowconfigure(4, weight=1)
        
    def _on_level_change(self, choice):
        descs = {
            "Level 0x01 (App Unlock)": "Level 0x01: Unlocks general diagnostic operations and calibration writing.",
            "Level 0x03 (Cal Unlock)": "Level 0x03: Unlocks restricted calibration data writing.",
            "Level 0x05 (Dev Unlock)": "Level 0x05: Unlocks internal low-level developer/engineering commands.",
            "Level 0x07 (System Unlock)": "Level 0x07: Unlocks safety system configuration and system programming."
        }
        self.level_desc_label.configure(text=descs.get(choice, ""))
        
    def show_info(self):
        messagebox.showinfo("Security Access", 
            "Sends Service 0x27 to unlock protected ECU functions.\n\n"
            "This performs a multi-step cryptographic handshake:\n"
            "1. Requests a random seed from the ECU\n"
            "2. Calculates the response key using the cryptographic mask (seed XOR 53)\n"
            "3. Sends the calculated key back to verify and unlock the ECU.")
            
    def run_unlock(self):
        level_map = {
            "Level 0x01 (App Unlock)": 1, 
            "Level 0x03 (Cal Unlock)": 3, 
            "Level 0x05 (Dev Unlock)": 5, 
            "Level 0x07 (System Unlock)": 7
        }
        level = level_map[self.security_level.get()]
        params = {'level': level}
        
        self.log_result("Initiating security unlock handshake for Level 0x{:02X}...".format(level))
        result = self.execute_command('security_access', params)
        if result == 0:
            self.log_result("SUCCESS: Security Access level 0x{:02X} granted!".format(level))
        elif result == 0x303:
            self.log_result("INFO: ECU reports Security Access is ALREADY UNLOCKED for this level.")
        elif result is not None:
            self.log_error("FAILED: Handshake completed but ECU returned error code: {}".format(get_nrc_description(result)))


class DTCManagerFrame(DiagnosticFrame):
    """DTC Management Panel (Services 0x19, 0x14, 0x85)."""
    
    def __init__(self, parent, bridge_client, node_name, **kwargs):
        super().__init__(parent, bridge_client, node_name, **kwargs)
        self.grid_columnconfigure(1, weight=1)
        
        # Title
        title = ctk.CTkLabel(self, text="DTC Manager - Diagnostic Trouble Codes", font=("Arial", 14, "bold"))
        title.grid(row=0, column=0, columnspan=4, pady=10)
        
        # --- Read/Clear DTC Section ---
        dtc_op_frame = ctk.CTkFrame(self)
        dtc_op_frame.grid(row=1, column=0, columnspan=4, sticky='ew', padx=10, pady=5)
        
        ctk.CTkLabel(dtc_op_frame, text="Read Status:").pack(side='left', padx=5)
        status_map = {"Active (0x09)": 0x09, "History (0x08)": 0x08, "All (0x0B)": 0x0B}
        self.status_mask = ctk.CTkComboBox(dtc_op_frame, values=list(status_map.keys()), width=120)
        self.status_mask.set("Active (0x09)")
        self.status_mask.pack(side='left', padx=5)
        
        read_btn = ctk.CTkButton(dtc_op_frame, text="Read DTCs", command=self.read_dtc, width=100)
        read_btn.pack(side='left', padx=5)
        
        ctk.CTkLabel(dtc_op_frame, text="Clear Group:").pack(side='left', padx=(15, 5))
        group_map = {"All (0xFFFFFF)": 0xFFFFFF, "Powertrain (0x0000FF)": 0x0000FF, "Chassis (0x00FF00)": 0x00FF00, "Body (0x00FFFF)": 0x00FFFF}
        self.dtc_group = ctk.CTkComboBox(dtc_op_frame, values=list(group_map.keys()), width=120)
        self.dtc_group.set("All (0xFFFFFF)")
        self.dtc_group.pack(side='left', padx=5)
        
        clear_btn = ctk.CTkButton(dtc_op_frame, text="Clear DTCs", fg_color="darkred", hover_color="red", command=self.clear_dtc, width=100)
        clear_btn.pack(side='left', padx=5)
        
        info_btn_dtc = ctk.CTkButton(dtc_op_frame, text="(i)", width=30, command=self.show_info_dtc)
        info_btn_dtc.pack(side='left', padx=5)
        
        # --- Control DTC Setting (Service 0x85) Section ---
        ctrl_frame = ctk.CTkFrame(self)
        ctrl_frame.grid(row=2, column=0, columnspan=4, sticky='ew', padx=10, pady=5)
        
        ctk.CTkLabel(ctrl_frame, text="DTC Recording (0x85):").pack(side='left', padx=5)
        self.dtc_record_mode = ctk.CTkComboBox(ctrl_frame, values=["Resume Recording (0x01)", "Suspend Recording (0x02)"], width=180)
        self.dtc_record_mode.set("Resume Recording (0x01)")
        self.dtc_record_mode.pack(side='left', padx=5)
        
        self.response_req_record = ctk.CTkCheckBox(ctrl_frame, text="Resp Req", checkbox_width=18, checkbox_height=18)
        self.response_req_record.select()
        self.response_req_record.pack(side='left', padx=5)
        
        exec_record_btn = ctk.CTkButton(ctrl_frame, text="Apply Setting", command=self.control_dtc, width=100)
        exec_record_btn.pack(side='left', padx=5)
        
        info_btn_ctrl = ctk.CTkButton(ctrl_frame, text="(i)", width=30, command=self.show_info_record)
        info_btn_ctrl.pack(side='left', padx=5)
        
        # DTC List Display
        ctk.CTkLabel(self, text="DTC Readout Display (Decoded):").grid(row=3, column=0, sticky='w', padx=10, pady=(10, 2))
        
        self.dtc_list = tk.Text(self, height=8, width=60, state='disabled')
        self.dtc_list.grid(row=4, column=0, columnspan=4, sticky='nsew', padx=10, pady=5)
        
        # Result Log
        self.result_text = tk.Text(self, height=4, width=60, state='disabled')
        self.result_text.grid(row=5, column=0, columnspan=4, sticky='nsew', padx=10, pady=5)
        self.result_text.tag_config('error', foreground='red')
        
        self.grid_rowconfigure(4, weight=1)
        self.grid_rowconfigure(5, weight=1)
        
    def show_info_dtc(self):
        messagebox.showinfo("DTC Read / Clear (Services 0x19 / 0x14)", 
            "Performs standard diagnostic trouble code (DTC) reading and clearing:\n\n"
            "• Read DTCs (0x19): Requests active, history, or all pending diagnostic trouble codes from the ECU.\n"
            "• Clear DTCs (0x14): Clears stored trouble codes and resets cycle counts for powertrain, chassis, body, or all groups.")
            
    def show_info_record(self):
        messagebox.showinfo("DTC Setting Control", 
            "Sends Service 0x85 to suspend or resume recording new fault codes in the ECU.\n\n"
            "• Resume Recording (0x01): Standard mode. Storing of newly occurring faults is enabled.\n"
            "• Suspend Recording (0x02): Disables fault code logging. Used during actuator tests/calibrations to prevent false codes from registering.")
            
    def read_dtc(self):
        status_map = {"Active (0x09)": 0x09, "History (0x08)": 0x08, "All (0x0B)": 0x0B}
        status = status_map[self.status_mask.get()]
        params = {
            'request_data': [0x02, status],
            'output_len': 200
        }
        
        self.log_result("Reading DTCs with status mask 0x{:02X}...".format(status))
        result = self.execute_command('read_dtc', params)
        
        if result and len(result) >= 2:
            err_code, byte_list = result[0], result[1]
            if err_code == 0:
                self.dtc_list.configure(state='normal')
                self.dtc_list.delete(1.0, 'end')
                
                if len(byte_list) <= 1:
                    self.dtc_list.insert('end', "No DTCs present in this ECU.\n")
                    self.log_result("Read DTCs: 0 faults found.")
                else:
                    avail_mask = byte_list[0]
                    self.dtc_list.insert('end', "DTC Availability Mask: 0x{:02X}\n\n".format(avail_mask))
                    self.dtc_list.insert('end', "{:<12} {:<10} {:<12} {}\n".format("DTC Code", "Symptom", "Status Hex", "Active Status Bits"))
                    self.dtc_list.insert('end', "---------------------------------------------------------\n")
                    idx = 1
                    count = 0
                    while idx + 3 < len(byte_list):
                        b1, b2, b3, stat = byte_list[idx], byte_list[idx+1], byte_list[idx+2], byte_list[idx+3]
                        idx += 4
                        count += 1
                        
                        prefix_val = (b1 >> 6) & 0x03
                        prefix_map = {0: 'P', 1: 'C', 2: 'B', 3: 'U'}
                        prefix = prefix_map[prefix_val]
                        
                        char2 = str((b1 >> 4) & 0x03)
                        dtc_code = prefix + char2 + format(b1 & 0x0F, 'X') + format(b2, '02X')
                        symptom = format(b3, '02X')
                        
                        status_flags = []
                        if stat & 0x01: status_flags.append("failed")
                        if stat & 0x02: status_flags.append("failedThisCycle")
                        if stat & 0x04: status_flags.append("pending")
                        if stat & 0x08: status_flags.append("confirmed")
                        if stat & 0x10: status_flags.append("notCompletedSinceClear")
                        if stat & 0x20: status_flags.append("failedSinceClear")
                        if stat & 0x40: status_flags.append("notCompletedThisCycle")
                        if stat & 0x80: status_flags.append("warningRequested")
                        
                        flags_str = ", ".join(status_flags) if status_flags else "None"
                        self.dtc_list.insert('end', "{:<12} {:<10} 0x{:02X}        {}\n".format(dtc_code, symptom, stat, flags_str))
                    
                    self.log_result("Read DTCs: {} faults found.".format(count))
                self.dtc_list.configure(state='disabled')
            else:
                self.log_error("DTC read failed: {}".format(get_nrc_description(err_code)))
                
    def clear_dtc(self):
        group_map = {"All (0xFFFFFF)": 0xFFFFFF, "Powertrain (0x0000FF)": 0x0000FF, "Chassis (0x00FF00)": 0x00FF00, "Body (0x00FFFF)": 0x00FFFF}
        group = group_map[self.dtc_group.get()]
        params = {'group': group}
        self.log_result("Clearing DTC group 0x{:06X}...".format(group))
        res = self.execute_command('clear_dtc', params)
        if res == 0:
            self.log_result("SUCCESS: Fault codes cleared successfully.")
            self.dtc_list.configure(state='normal')
            self.dtc_list.delete(1.0, 'end')
            self.dtc_list.configure(state='disabled')
        elif res is not None:
            self.log_error("ECU returned negative response: {}".format(get_nrc_description(res)))
            
    def control_dtc(self):
        setting_map = {"Resume Recording (0x01)": 1, "Suspend Recording (0x02)": 2}
        setting_type = setting_map[self.dtc_record_mode.get()]
        params = {
            'setting_type': setting_type,
            'record_len': 0,
            'record': [],
            'response_required': self.response_req_record.get()
        }
        self.log_result("Executing DTC Setting Control Service 0x85 (type: 0x{:02X})...".format(setting_type))
        res = self.execute_command('control_dtc', params)
        if res == 0:
            self.log_result("SUCCESS: DTC recording status updated.")
        elif res is not None:
            self.log_error("ECU returned negative response: {}".format(get_nrc_description(res)))


class DataViewerFrame(DiagnosticFrame):
    """Data Viewer Panel (Services 0x22, 0x2E)."""
    
    def __init__(self, parent, bridge_client, node_name, **kwargs):
        super().__init__(parent, bridge_client, node_name, **kwargs)
        self.grid_columnconfigure(1, weight=1)
        
        # Title
        title = ctk.CTkLabel(self, text="Data Explorer - RDBI/WDBI (Services 0x22/0x2E)", font=("Arial", 14, "bold"))
        title.grid(row=0, column=0, columnspan=4, pady=10)
        
        # DID dropdown list
        ctk.CTkLabel(self, text="Select Data ID:").grid(row=1, column=0, sticky='w', padx=10)
        self.did_list = []
        for hex_val, info in sorted(DID_DESCRIPTIONS.items()):
            self.did_list.append("{} - {}".format(hex_val, info[0]))
        self.did_list.append("Custom...")
        
        self.did_combo = ctk.CTkComboBox(self, values=self.did_list, command=self._on_did_select)
        self.did_combo.set("0xF190 - VIN (Vehicle Identification Number)")
        self.did_combo.grid(row=1, column=1, sticky='ew', padx=10)
        
        # Read Button
        read_btn = ctk.CTkButton(self, text="Read DID", command=self.read_data, width=80)
        read_btn.grid(row=1, column=2, padx=5)
        
        info_btn = ctk.CTkButton(self, text="(i)", width=30, command=self.show_info)
        info_btn.grid(row=1, column=3, padx=5)
        
        # Custom DID entry (initially hidden/disabled unless Custom is picked)
        self.custom_label = ctk.CTkLabel(self, text="Custom DID (Hex):")
        self.custom_entry = ctk.CTkEntry(self, placeholder_text="e.g. F190")
        
        # DID Description box
        self.did_desc_label = ctk.CTkLabel(self, text="Description: " + DID_DESCRIPTIONS["0xF190"][1], text_color="gray", justify="left", wraplength=450)
        self.did_desc_label.grid(row=3, column=0, columnspan=4, sticky='w', padx=10, pady=(5, 10))
        
        # Read Result display
        ctk.CTkLabel(self, text="Read Value:").grid(row=4, column=0, sticky='w', padx=10)
        self.read_result = ctk.CTkEntry(self, state='disabled')
        self.read_result.grid(row=4, column=1, columnspan=3, sticky='ew', padx=10)
        
        # Write Data section
        ctk.CTkLabel(self, text="Value to Write (Hex):").grid(row=5, column=0, sticky='w', padx=10, pady=(15, 0))
        self.write_value = ctk.CTkEntry(self, placeholder_text="e.g. 35594A...")
        self.write_value.grid(row=5, column=1, sticky='ew', padx=10, pady=(15, 0))
        
        write_btn = ctk.CTkButton(self, text="Write DID", fg_color="darkgreen", hover_color="green", command=self.write_data, width=80)
        write_btn.grid(row=5, column=2, padx=5, pady=(15, 0))
        
        # Result Log
        self.result_text = tk.Text(self, height=8, width=60, state='disabled')
        self.result_text.grid(row=6, column=0, columnspan=4, sticky='nsew', padx=10, pady=10)
        self.result_text.tag_config('error', foreground='red')
        
        self.grid_rowconfigure(6, weight=1)
        
    def show_info(self):
        messagebox.showinfo("Data Explorer (RDBI/WDBI)", 
            "Sends Service 0x22 (Read) or Service 0x2E (Write) to view or modify specific Data Identifier (DID) parameters on the ECU.\n\n"
            "• Read DID (0x22): Retrieves configuration, sensor readings, or serial numbers.\n"
            "• Write DID (0x2E): Modifies saved configuration values (e.g. VIN) or calibrations in the ECU memory.")
            
    def _on_did_select(self, choice):
        if choice == "Custom...":
            self.custom_label.grid(row=2, column=0, sticky='w', padx=10)
            self.custom_entry.grid(row=2, column=1, columnspan=3, sticky='ew', padx=10)
            self.did_desc_label.configure(text="Enter custom 2-byte hexadecimal Diagnostic Identifier code.")
        else:
            self.custom_label.grid_forget()
            self.custom_entry.grid_forget()
            did_hex = choice.split(" - ")[0]
            if did_hex in DID_DESCRIPTIONS:
                self.did_desc_label.configure(text="Description: " + DID_DESCRIPTIONS[did_hex][1])
                
    def _get_selected_did(self):
        choice = self.did_combo.get()
        if choice == "Custom...":
            custom_hex = self.custom_entry.get().strip().replace("0x", "")
            if not custom_hex:
                raise ValueError("Enter custom DID code")
            return int(custom_hex, 16)
        else:
            return int(choice.split(" - ")[0], 16)
            
    def read_data(self):
        try:
            data_id = self._get_selected_did()
            params = {'data_id': data_id, 'data_len': 128} # Use larger limit, bridge handles actual bytes returned
            
            self.log_result("Reading Data Identifier 0x{:04X}...".format(data_id))
            result = self.execute_command('read_data', params)
            
            if result and len(result) >= 2:
                err_code, byte_list = result[0], result[1]
                if err_code == 0:
                    hex_str = " ".join("{:02X}".format(b) for b in byte_list)
                    self.read_result.configure(state='normal')
                    self.read_result.delete(0, 'end')
                    self.read_result.insert(0, hex_str)
                    self.read_result.configure(state='disabled')
                    
                    # Attempt decodings
                    decode_msg = "Bytes: {}\n".format(hex_str)
                    
                    # Decoders based on DID
                    did_hex = "0x{:04X}".format(data_id)
                    if did_hex in ("0xF190", "0xF181", "0xF180", "0xF197"): # ASCII Strings
                        try:
                            ascii_str = "".join(chr(b) for b in byte_list if 32 <= b <= 126).strip()
                            decode_msg += "Decoded ASCII: {}".format(ascii_str)
                        except:
                            pass
                    elif did_hex in ("0xD001", "0xD002", "0xD004", "0xD005", "0xD00D") and len(byte_list) >= 2:
                        val = (byte_list[0] << 8) | byte_list[1]
                        # Handle signed 16-bit
                        if did_hex in ("0xD002", "0xD005") and (val & 0x8000):
                            val -= 65536
                            
                        if did_hex == "0xD001":
                            decode_msg += "Decoded Value: {} V".format(val / 10.0)
                        elif did_hex == "0xD002":
                            decode_msg += "Decoded Value: {} A".format(val / 10.0)
                        elif did_hex == "0xD004":
                            decode_msg += "Decoded Value: {} %".format(val / 10.0)
                        elif did_hex == "0xD005":
                            decode_msg += "Decoded Value: {} °C".format(val / 10.0)
                        elif did_hex == "0xD00D":
                            decode_msg += "Decoded Value: {} V".format(val / 1000.0)
                    else:
                        # Fallback printable ASCII check
                        printable_ratio = float(sum(1 for b in byte_list if 32 <= b <= 126)) / max(len(byte_list), 1)
                        if printable_ratio > 0.7:
                            ascii_str = "".join(chr(b) if 32 <= b <= 126 else "." for b in byte_list)
                            decode_msg += "ASCII Interpretation: {}".format(ascii_str)
                            
                    self.log_result(decode_msg)
                else:
                    self.log_error("RDBI failed: {}".format(get_nrc_description(err_code)))
        except Exception as e:
            self.log_error("Failed to read: {}".format(str(e)))
            
    def write_data(self):
        try:
            data_id = self._get_selected_did()
            write_val = self.write_value.get().strip().replace(" ", "")
            data_bytes = list(bytes.fromhex(write_val))
            
            params = {'data_id': data_id, 'data': data_bytes}
            self.log_result("Writing data to DID 0x{:04X}...".format(data_id))
            res = self.execute_command('write_data', params)
            if res == 0:
                self.log_result("SUCCESS: Data successfully written to DID.")
            elif res is not None:
                self.log_error("ECU returned negative response: {}".format(get_nrc_description(res)))
        except Exception as e:
            self.log_error("Invalid input or write failure: {}".format(str(e)))


class ActuatorsFrame(DiagnosticFrame):
    """Input/Output Actuator Override Control Panel (Service 0x2F)."""
    
    def __init__(self, parent, bridge_client, node_name, **kwargs):
        super().__init__(parent, bridge_client, node_name, **kwargs)
        self.grid_columnconfigure(1, weight=1)
        
        # Title
        title = ctk.CTkLabel(self, text="Actuator Testing / Override Control (Service 0x2F)", font=("Arial", 14, "bold"))
        title.grid(row=0, column=0, columnspan=3, pady=10)
        
        # Actuator dropdown selection
        ctk.CTkLabel(self, text="Select Actuator:").grid(row=1, column=0, sticky='w', padx=10)
        self.act_list = []
        for hex_val, info in sorted(ACTUATOR_DESCRIPTIONS.items()):
            self.act_list.append("{} - {}".format(hex_val, info[0]))
        self.act_list.append("Custom...")
        
        self.act_combo = ctk.CTkComboBox(self, values=self.act_list, command=self._on_actuator_select)
        self.act_combo.set("0x4001 - Coolant Pump Control")
        self.act_combo.grid(row=1, column=1, sticky='ew', padx=10)
        
        info_btn = ctk.CTkButton(self, text="(i)", width=30, command=self.show_info)
        info_btn.grid(row=1, column=2, padx=5)
        
        # Custom ID fields
        self.custom_label = ctk.CTkLabel(self, text="Custom Actuator ID (Hex):")
        self.custom_entry = ctk.CTkEntry(self, placeholder_text="e.g. 4001")
        
        # Actuator description box
        self.act_desc_label = ctk.CTkLabel(self, text="Description: " + ACTUATOR_DESCRIPTIONS["0x4001"][1], text_color="gray", justify="left", wraplength=450)
        self.act_desc_label.grid(row=3, column=0, columnspan=3, sticky='w', padx=10, pady=(5, 10))
        
        # Control Type selector
        ctk.CTkLabel(self, text="Control Option:").grid(row=4, column=0, sticky='w', padx=10)
        self.io_type = ctk.CTkComboBox(self, values=["Return Control to ECU (0x00)", "Reset to Default (0x01)", "Freeze Current State (0x02)", "Short Term Adjustment (0x03)"])
        self.io_type.set("Return Control to ECU (0x00)")
        self.io_type.grid(row=4, column=1, columnspan=2, sticky='ew', padx=10)
        
        # Control Values parameters
        ctk.CTkLabel(self, text="Parameters (Hex bytes):").grid(row=5, column=0, sticky='w', padx=10, pady=(5, 0))
        self.input_data_entry = ctk.CTkEntry(self, placeholder_text="e.g. 64 (for 100% pump speed)")
        self.input_data_entry.grid(row=5, column=1, columnspan=2, sticky='ew', padx=10, pady=(5, 0))
        
        # Execute button
        exec_btn = ctk.CTkButton(self, text="Execute Actuator Command", fg_color="darkblue", command=self.execute_actuator)
        exec_btn.grid(row=6, column=0, columnspan=3, pady=15)
        
        # Result Log
        self.result_text = tk.Text(self, height=8, width=60, state='disabled')
        self.result_text.grid(row=7, column=0, columnspan=3, sticky='nsew', padx=10, pady=10)
        self.result_text.tag_config('error', foreground='red')
        
        self.grid_rowconfigure(7, weight=1)
        
    def _on_actuator_select(self, choice):
        if choice == "Custom...":
            self.custom_label.grid(row=2, column=0, sticky='w', padx=10)
            self.custom_entry.grid(row=2, column=1, columnspan=2, sticky='ew', padx=10)
            self.act_desc_label.configure(text="Enter custom 2-byte hexadecimal actuator identifier.")
        else:
            self.custom_label.grid_forget()
            self.custom_entry.grid_forget()
            act_hex = choice.split(" - ")[0]
            if act_hex in ACTUATOR_DESCRIPTIONS:
                self.act_desc_label.configure(text="Description: " + ACTUATOR_DESCRIPTIONS[act_hex][1])
                
    def show_info(self):
        messagebox.showinfo("Actuator Testing (0x2F)", 
            "Sends Service 0x2F to override vehicle ECU state and manually command hardware relays, fans, pumps, or lights.\n\n"
            "• Return Control to ECU (0x00): Exits manual override and hands control back to normal ECU operation.\n"
            "• Reset to Default (0x01): Resets the actuator back to its factory default value.\n"
            "• Freeze Current State (0x02): Freezes the current state of the actuator.\n"
            "• Short Term Adjustment (0x03): Actively overrides the actuator with custom parameter bytes.")
            
    def execute_actuator(self):
        try:
            choice = self.act_combo.get()
            if choice == "Custom...":
                custom_hex = self.custom_entry.get().strip().replace("0x", "")
                if not custom_hex:
                    raise ValueError("Enter custom actuator ID")
                act_id = int(custom_hex, 16)
            else:
                act_id = int(choice.split(" - ")[0], 16)
                
            type_map = {
                "Return Control to ECU (0x00)": 0,
                "Reset to Default (0x01)": 1,
                "Freeze Current State (0x02)": 2,
                "Short Term Adjustment (0x03)": 3
            }
            opt_type = type_map[self.io_type.get()]
            
            param_str = self.input_data_entry.get().strip().replace(" ", "")
            param_bytes = list(bytes.fromhex(param_str)) if param_str else []
            
            params = {
                'io_id': act_id,
                'io_type': opt_type,
                'input_data': param_bytes,
                'output_len': 10
            }
            
            self.log_result("Executing Actuator 0x{:04X} override (Option: 0x{:02X})...".format(act_id, opt_type))
            result = self.execute_command('io_control', params)
            
            if result and len(result) >= 2:
                err_code, byte_list = result[0], result[1]
                if err_code == 0:
                    hex_str = " ".join("{:02X}".format(b) for b in byte_list) if byte_list else "None"
                    self.log_result("SUCCESS: Override accepted by ECU. Returned parameters: {}".format(hex_str))
                else:
                    self.log_error("IO Control failed: {}".format(get_nrc_description(err_code)))
        except Exception as e:
            self.log_error("Failed to execute Actuator override: {}".format(str(e)))


class RoutinesFrame(DiagnosticFrame):
    """Routine Control Panel (Service 0x31)."""
    
    def __init__(self, parent, bridge_client, node_name, **kwargs):
        super().__init__(parent, bridge_client, node_name, **kwargs)
        self.grid_columnconfigure(1, weight=1)
        
        # Title
        title = ctk.CTkLabel(self, text="Routine Control (Service 0x31)", font=("Arial", 14, "bold"))
        title.grid(row=0, column=0, columnspan=3, pady=10)
        
        # Routine dropdown list
        ctk.CTkLabel(self, text="Select Routine:").grid(row=1, column=0, sticky='w', padx=10)
        self.rt_list = []
        for hex_val, info in sorted(ROUTINE_DESCRIPTIONS.items()):
            self.rt_list.append("{} - {}".format(hex_val, info[0]))
        self.rt_list.append("Custom...")
        
        self.rt_combo = ctk.CTkComboBox(self, values=self.rt_list, command=self._on_routine_select)
        self.rt_combo.set("0xFF01 - Erase Flash Memory")
        self.rt_combo.grid(row=1, column=1, sticky='ew', padx=10)
        
        info_btn = ctk.CTkButton(self, text="(i)", width=30, command=self.show_info)
        info_btn.grid(row=1, column=2, padx=5)
        
        # Custom Routine entries
        self.custom_label = ctk.CTkLabel(self, text="Custom Routine ID (Hex):")
        self.custom_entry = ctk.CTkEntry(self, placeholder_text="e.g. FF01")
        
        # Routine Description
        self.rt_desc_label = ctk.CTkLabel(self, text="Description: " + ROUTINE_DESCRIPTIONS["0xFF01"][1], text_color="gray", justify="left", wraplength=450)
        self.rt_desc_label.grid(row=3, column=0, columnspan=3, sticky='w', padx=10, pady=(5, 10))
        
        # Routine Type
        ctk.CTkLabel(self, text="Command Type:").grid(row=4, column=0, sticky='w', padx=10)
        self.rc_type = ctk.CTkComboBox(self, values=["Start Routine (0x01)", "Stop Routine (0x02)", "Request Routine Results (0x03)"])
        self.rc_type.set("Start Routine (0x01)")
        self.rc_type.grid(row=4, column=1, columnspan=2, sticky='ew', padx=10)
        
        # Routine parameters
        ctk.CTkLabel(self, text="Parameters (Hex bytes):").grid(row=5, column=0, sticky='w', padx=10, pady=(5, 0))
        self.input_data_entry = ctk.CTkEntry(self, placeholder_text="e.g. 0102")
        self.input_data_entry.grid(row=5, column=1, columnspan=2, sticky='ew', padx=10, pady=(5, 0))
        
        # Execute button
        exec_btn = ctk.CTkButton(self, text="Execute Routine Command", fg_color="darkblue", command=self.execute_routine)
        exec_btn.grid(row=6, column=0, columnspan=3, pady=15)
        
        # Result Log
        self.result_text = tk.Text(self, height=8, width=60, state='disabled')
        self.result_text.grid(row=7, column=0, columnspan=3, sticky='nsew', padx=10, pady=10)
        self.result_text.tag_config('error', foreground='red')
        
        self.grid_rowconfigure(7, weight=1)
        
    def _on_routine_select(self, choice):
        if choice == "Custom...":
            self.custom_label.grid(row=2, column=0, sticky='w', padx=10)
            self.custom_entry.grid(row=2, column=1, columnspan=2, sticky='ew', padx=10)
            self.rt_desc_label.configure(text="Enter custom 2-byte hexadecimal Routine Identifier.")
        else:
            self.custom_label.grid_forget()
            self.custom_entry.grid_forget()
            rt_hex = choice.split(" - ")[0]
            if rt_hex in ROUTINE_DESCRIPTIONS:
                self.rt_desc_label.configure(text="Description: " + ROUTINE_DESCRIPTIONS[rt_hex][1])
                
    def show_info(self):
        messagebox.showinfo("Routine Control (0x31)", 
            "Sends Service 0x31 to run pre-programmed diagnostic sub-routines inside the ECU micro-controller.\n\n"
            "• Start Routine (0x01): Starts routine execution.\n"
            "• Stop Routine (0x02): Stops active routine execution.\n"
            "• Request Routine Results (0x03): Reads output results or status code from active or completed routines.")
            
    def execute_routine(self):
        try:
            choice = self.rt_combo.get()
            if choice == "Custom...":
                custom_hex = self.custom_entry.get().strip().replace("0x", "")
                if not custom_hex:
                    raise ValueError("Enter custom Routine ID")
                rt_id = int(custom_hex, 16)
            else:
                rt_id = int(choice.split(" - ")[0], 16)
                
            type_map = {
                "Start Routine (0x01)": 1,
                "Stop Routine (0x02)": 2,
                "Request Routine Results (0x03)": 3
            }
            opt_type = type_map[self.rc_type.get()]
            
            param_str = self.input_data_entry.get().strip().replace(" ", "")
            param_bytes = list(bytes.fromhex(param_str)) if param_str else []
            
            params = {
                'rc_id': rt_id,
                'rc_type': opt_type,
                'input_data': param_bytes,
                'output_len': 10
            }
            
            self.log_result("Executing Routine 0x{:04X} command (Type: 0x{:02X})...".format(rt_id, opt_type))
            result = self.execute_command('routine_control', params)
            
            if result and len(result) >= 2:
                err_code, byte_list = result[0], result[1]
                if err_code == 0:
                    hex_str = " ".join("{:02X}".format(b) for b in byte_list) if byte_list else "None"
                    self.log_result("SUCCESS: Routine accepted. Returned data: {}".format(hex_str))
                else:
                    self.log_error("Routine execution failed: {}".format(get_nrc_description(err_code)))
        except Exception as e:
            self.log_error("Failed to execute Routine: {}".format(str(e)))


class MemoryFrame(DiagnosticFrame):
    """Memory Examiner Panel (Service 0x23 / 0x3D)."""
    
    def __init__(self, parent, bridge_client, node_name, **kwargs):
        super().__init__(parent, bridge_client, node_name, **kwargs)
        self.grid_columnconfigure(1, weight=1)
        
        # Title
        title = ctk.CTkLabel(self, text="Memory Examiner - RMBA/WMBA (Services 0x23/0x3D)", font=("Arial", 14, "bold"))
        title.grid(row=0, column=0, columnspan=3, pady=10)
        
        # Operation Selector
        ctk.CTkLabel(self, text="Operation:").grid(row=1, column=0, sticky='w', padx=10)
        self.operation = ctk.CTkComboBox(self, values=["Read Memory (0x23)", "Write Memory (0x3D)"], command=self._on_operation_change)
        self.operation.set("Read Memory (0x23)")
        self.operation.grid(row=1, column=1, sticky='ew', padx=10)
        
        info_btn = ctk.CTkButton(self, text="(i)", width=30, command=self.show_info)
        info_btn.grid(row=1, column=2, padx=5)
        
        # Address entry
        ctk.CTkLabel(self, text="Address (Hex):").grid(row=2, column=0, sticky='w', padx=10, pady=5)
        self.memory_address = ctk.CTkEntry(self, placeholder_text="e.g. 00018000")
        self.memory_address.grid(row=2, column=1, columnspan=2, sticky='ew', padx=10, pady=5)
        
        # Memory Size / Write parameters
        self.size_label = ctk.CTkLabel(self, text="Length (Bytes):")
        self.size_label.grid(row=3, column=0, sticky='w', padx=10, pady=5)
        
        self.memory_size = ctk.CTkEntry(self, placeholder_text="e.g. 4")
        self.memory_size.grid(row=3, column=1, columnspan=2, sticky='ew', padx=10, pady=5)
        
        # Execute button
        self.exec_btn = ctk.CTkButton(self, text="Execute Read", command=self.execute_operation)
        self.exec_btn.grid(row=4, column=0, columnspan=3, pady=15)
        
        # Description
        self.desc_label = ctk.CTkLabel(self, text="Read Memory (0x23) accesses direct physical microcontroller sectors by raw hardware address. Requires security levels unlocked.", text_color="gray", justify="left", wraplength=450)
        self.desc_label.grid(row=5, column=0, columnspan=3, sticky='w', padx=10, pady=5)
        
        # Result Log
        self.result_text = tk.Text(self, height=8, width=60, state='disabled')
        self.result_text.grid(row=6, column=0, columnspan=3, sticky='nsew', padx=10, pady=10)
        self.result_text.tag_config('error', foreground='red')
        
        self.grid_rowconfigure(6, weight=1)
        
    def show_info(self):
        messagebox.showinfo("Memory Examiner (RMBA/WMBA)", 
            "Sends Service 0x23 (Read) or Service 0x3D (Write) to directly access raw microprocessor memory blocks.\n\n"
            "• Read Memory (0x23): Retrieves raw byte values by physical memory address.\n"
            "• Write Memory (0x3D): Overwrites raw memory sectors with custom binary instructions/data. Danger: Writing to active memory registers can freeze or damage the ECU.")
            
    def _on_operation_change(self, choice):
        if choice == "Write Memory (0x3D)":
            self.size_label.configure(text="Data (Hex bytes):")
            self.memory_size.delete(0, 'end')
            self.memory_size.configure(placeholder_text="e.g. AABBCCDD")
            self.exec_btn.configure(text="Execute Write")
            self.desc_label.configure(text="Write Memory (0x3D) writes raw machine code or variables directly to target sector. Warning: Unrestricted memory writes can corrupt ECU state.")
        else:
            self.size_label.configure(text="Length (Bytes):")
            self.memory_size.delete(0, 'end')
            self.memory_size.configure(placeholder_text="e.g. 4")
            self.exec_btn.configure(text="Execute Read")
            self.desc_label.configure(text="Read Memory (0x23) accesses direct physical microcontroller sectors by raw hardware address. Requires security levels unlocked.")
            
    def execute_operation(self):
        try:
            op = self.operation.get()
            addr_str = self.memory_address.get().strip().replace("0x", "")
            if not addr_str:
                raise ValueError("Address required")
            address = int(addr_str, 16)
            
            if op == "Read Memory (0x23)":
                size_str = self.memory_size.get().strip()
                size = int(size_str) if size_str else 4
                
                params = {
                    'address': address,
                    'size': size,
                    'output_len': size
                }
                
                self.log_result("Reading memory address 0x{:08X} ({} bytes)...".format(address, size))
                result = self.execute_command('read_memory', params)
                
                if result and len(result) >= 2:
                    err_code, byte_list = result[0], result[1]
                    if err_code == 0:
                        hex_str = " ".join("{:02X}".format(b) for b in byte_list)
                        self.log_result("SUCCESS: Memory read accepted:\n{}".format(hex_str))
                    else:
                        self.log_error("Memory Read failed: {}".format(get_nrc_description(err_code)))
            else:
                data_str = self.memory_size.get().strip().replace(" ", "")
                if not data_str:
                    raise ValueError("Data required")
                data_bytes = list(bytes.fromhex(data_str))
                
                params = {
                    'address': address,
                    'data': data_bytes
                }
                
                self.log_result("Writing {} bytes to memory address 0x{:08X}...".format(len(data_bytes), address))
                res = self.execute_command('write_memory', params)
                if res == 0:
                    self.log_result("SUCCESS: Memory write accepted.")
                elif res is not None:
                    self.log_error("Memory Write failed: {}".format(get_nrc_description(res)))
        except Exception as e:
            self.log_error("Memory Examiner error: {}".format(str(e)))


class FlasherFrame(DiagnosticFrame):
    """ECU Firmware Flashing Panel (Services 0x34, 0x36, 0x37)."""
    
    def __init__(self, parent, bridge_client, node_name, **kwargs):
        super().__init__(parent, bridge_client, node_name, **kwargs)
        self.grid_columnconfigure(1, weight=1)
        
        # Title
        title = ctk.CTkLabel(self, text="ECU Firmware Flashing Suite", font=("Arial", 14, "bold"))
        title.grid(row=0, column=0, columnspan=3, pady=10)
        
        info_btn = ctk.CTkButton(self, text="(i)", width=30, command=self.show_info)
        info_btn.grid(row=0, column=2, sticky='e', padx=10)
        
        # File selector
        ctk.CTkLabel(self, text="Firmware File (.hex):").grid(row=1, column=0, sticky='w', padx=10)
        self.file_path_entry = ctk.CTkEntry(self, placeholder_text="No file selected")
        self.file_path_entry.grid(row=1, column=1, sticky='ew', padx=10)
        
        browse_btn = ctk.CTkButton(self, text="Browse...", command=self.browse_file, width=80)
        browse_btn.grid(row=1, column=2, padx=5)
        
        # Progress indicator
        ctk.CTkLabel(self, text="Flash Progress:").grid(row=2, column=0, sticky='w', padx=10, pady=(15, 0))
        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.grid(row=2, column=1, columnspan=2, sticky='ew', padx=10, pady=(15, 0))
        self.progress_bar.set(0.0)
        
        self.progress_label = ctk.CTkLabel(self, text="0%")
        self.progress_label.grid(row=3, column=1, columnspan=2, pady=2)
        
        # Start Flash button
        self.flash_btn = ctk.CTkButton(self, text="Start Flashing", fg_color="darkblue", hover_color="blue", command=self.start_flashing)
        self.flash_btn.grid(row=4, column=0, columnspan=3, pady=15)
        
        # Result Log
        self.result_text = tk.Text(self, height=8, width=60, state='disabled')
        self.result_text.grid(row=5, column=0, columnspan=3, sticky='nsew', padx=10, pady=10)
        self.result_text.tag_config('error', foreground='red')
        
        self.grid_rowconfigure(5, weight=1)
        
    def show_info(self):
        messagebox.showinfo("ECU Flasher & Bootloader", 
            "Manages the full firmware flashing lifecycle using UDS Services:\n\n"
            "• Request Download Init (0x34): Initiates transfer, specifying start address and data size.\n"
            "• Transfer Data (0x36): Iteratively sends binary segments of the firmware file to the ECU.\n"
            "• Request Transfer Exit (0x37): Finalizes transfer and triggers checksum verification on the ECU.\n"
            "• Wait for Boot ID: Automatically listens on the CAN bus for the ECU to report its boot ID after rebooting.")
            
    def browse_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("Intel Hex Files", "*.hex"), ("All Files", "*.*")])
        if filepath:
            self.file_path_entry.delete(0, 'end')
            self.file_path_entry.insert(0, filepath)
            self.log_result("Selected firmware file: {}".format(os.path.basename(filepath)))
            
    def start_flashing(self):
        filepath = self.file_path_entry.get().strip()
        if not filepath:
            self.log_error("Please select a valid .hex file first.")
            return
            
        self.flash_btn.configure(state='disabled')
        threading.Thread(target=self._flash_thread_loop, args=(filepath,), daemon=True).start()
        
    def _flash_thread_loop(self, filepath):
        try:
            self.log_result("Starting firmware flash sequence...")
            self.progress_bar.set(0.0)
            self.progress_label.configure(text="0%")
            
            # 1. Parse hex file to get regions info
            self.log_result("Parsing HEX file regions...")
            regions = self.execute_command('parse_data_get_size', {'filename': filepath})
            if not regions:
                self.log_error("Failed to parse HEX file regions.")
                self.flash_btn.configure(state='normal')
                return
                
            self.log_result("Parsed {} memory regions to flash.".format(len(regions)))
            
            # Calculate total size across all regions
            total_bytes = sum(length for addr, length in regions)
            bytes_flashed = 0
            
            # 2. Iterate and flash regions
            for idx, (address, length) in enumerate(regions):
                self.log_result("Processing Region {}/{} (Addr: 0x{:08X}, Len: {} bytes)".format(idx+1, len(regions), address, length))
                
                # Request Download Init (Service 0x34)
                self.log_result("Sending Request Download Init (Service 0x34)...")
                init_res = self.execute_command('request_download_init', {'address': address, 'size': length})
                if not init_res or init_res[0] != 0:
                    err_msg = get_nrc_description(init_res[0]) if init_res else "No response"
                    self.log_error("Request Download Init failed for region {}: {}".format(idx+1, err_msg))
                    self.flash_btn.configure(state='normal')
                    return
                    
                buffer_size = init_res[1]
                self.log_result("ECU accepted download init. Allowed Buffer Size: {} bytes.".format(buffer_size))
                
                # Transfer Data (Service 0x36) loop
                self.log_result("Transferring data chunks (Service 0x36)...")
                transfer_res = self.execute_command('transfer_data', {
                    'start_address': address,
                    'buffer_size': buffer_size,
                    'memory_size': length
                })
                
                if transfer_res != 0:
                    self.log_error("Transfer Data failed for region {}: {}".format(idx+1, get_nrc_description(transfer_res)))
                    self.flash_btn.configure(state='normal')
                    return
                    
                bytes_flashed += length
                pct = float(bytes_flashed) / total_bytes
                self.progress_bar.set(pct)
                self.progress_label.configure(text="{}%".format(int(pct * 100)))
                
                # Request Transfer Exit (Service 0x37)
                self.log_result("Finalizing region transfer (Service 0x37)...")
                exit_res = self.execute_command('request_transfer_exit', {})
                if exit_res != 0:
                    self.log_error("Request Transfer Exit failed for region {}: {}".format(idx+1, get_nrc_description(exit_res)))
                    self.flash_btn.configure(state='normal')
                    return
                    
            # 3. Reset the ECU
            self.log_result("All regions flashed successfully! Issuing Hard Reset to reboot ECU (Service 0x11)...")
            self.execute_command('ecu_reset', {'reset_type': 1, 'response_required': False})
            
            # Wait for boot ID
            self.log_result("Waiting for Boot ID response from the rebooted ECU...")
            try:
                boot_res = self.execute_command('wait_for_boot_id', {})
                self.log_result("Boot ID response received: {}".format(boot_res))
            except Exception as e:
                self.log_result("Note: Did not receive Boot ID response (normal in simulation): {}".format(e))
            
            self.progress_bar.set(1.0)
            self.progress_label.configure(text="100% - SUCCESS")
            self.log_result("FLASH SEQUENCE COMPLETED SUCCESSFULLY!")
            
        except Exception as e:
            self.log_error("Flash sequence exception: {}".format(str(e)))
        finally:
            self.flash_btn.configure(state='normal')


class ECUCockpitFrame(ctk.CTkFrame):
    """Main ECU diagnostic cockpit with tabbed panels."""
    
    def __init__(self, parent, bridge_client, ecu_name, **kwargs):
        super().__init__(parent, **kwargs)
        self.bridge_client = bridge_client
        self.ecu_name = ecu_name
        
        # Title
        title = ctk.CTkLabel(self, text="{} - Diagnostic Cockpit".format(ecu_name), 
                            font=("Arial", 16, "bold"))
        title.pack(pady=5)
        
        # Create tabbed interface
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Session Control Tab
        session_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(session_frame, text="Session")
        SessionControlFrame(session_frame, bridge_client, ecu_name).pack(fill='both', expand=True)
        
        # Security Access Tab
        security_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(security_frame, text="Security")
        SecurityAccessFrame(security_frame, bridge_client, ecu_name).pack(fill='both', expand=True)
        
        # DTC Manager Tab
        dtc_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(dtc_frame, text="DTCs")
        DTCManagerFrame(dtc_frame, bridge_client, ecu_name).pack(fill='both', expand=True)
        
        # Data Viewer Tab
        data_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(data_frame, text="Data")
        DataViewerFrame(data_frame, bridge_client, ecu_name).pack(fill='both', expand=True)
        
        # Actuators Tab
        actuators_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(actuators_frame, text="Actuators")
        ActuatorsFrame(actuators_frame, bridge_client, ecu_name).pack(fill='both', expand=True)
        
        # Routines Tab
        routines_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(routines_frame, text="Routines")
        RoutinesFrame(routines_frame, bridge_client, ecu_name).pack(fill='both', expand=True)
        
        # Memory Tab
        memory_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(memory_frame, text="Memory")
        MemoryFrame(memory_frame, bridge_client, ecu_name).pack(fill='both', expand=True)
        
        # Flasher Tab
        flasher_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(flasher_frame, text="Flasher")
        FlasherFrame(flasher_frame, bridge_client, ecu_name).pack(fill='both', expand=True)



class BackendLauncher:
    """Manages the backend UDS Bridge process."""
    
    def __init__(self, port=5000, host='127.0.0.1'):
        self.process = None
        self.workspace = os.path.dirname(os.path.realpath(__file__))
        self.bridge_path = os.path.join(self.workspace, 'uds_bridge.py')
        self.port = port
        self.host = host
    
    def is_running(self):
        """Check if the configured port belongs to the UDS bridge by using a JSON-RPC handshake."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.connect((self.host, self.port))
            request = json.dumps({'jsonrpc': '2.0', 'method': 'get_nodes', 'params': {}, 'id': 1}) + '\n'
            sock.sendall(request.encode('utf-8'))
            data = b''
            while b'\n' not in data:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                data += chunk
            sock.close()
            if not data:
                return False
            try:
                response = json.loads(data.decode('utf-8').strip())
                return response.get('id') == 1
            except:
                return False
        except:
            return False
    
    def launch(self, timeout=10):
        """Launch the backend process."""
        if self.is_running():
            print("Backend already running on port {}".format(self.port))
            return True
        
        if not os.path.exists(self.bridge_path):
            print("Error: uds_bridge.py not found at {}".format(self.bridge_path))
            return False
        
        try:
            print("Launching UDS Bridge backend on port {}...".format(self.port))
            python_exec = os.environ.get('PYTHON2_EXECUTABLE') or shutil.which('python2')
            use_conda = False
            if not python_exec:
                conda_exec = shutil.which('conda')
                if conda_exec:
                    python_exec = conda_exec
                    use_conda = True
                else:
                    python_exec = sys.executable
                    print("Warning: python2 executable not found and conda not available; launching backend with current Python interpreter.")

            if use_conda:
                command = [python_exec, 'run', '-n', 'uds-py27', 'python', self.bridge_path, '--port', str(self.port)]
                print("Using conda run to launch backend: {}".format(' '.join(command)))
            else:
                command = [python_exec, self.bridge_path, '--port', str(self.port)]
                print("Using interpreter: {}".format(python_exec))

            log_path = os.path.join(self.workspace, 'bridge_debug.log')
            log_file = open(log_path, 'w')
            self.process = subprocess.Popen(
                command,
                cwd=self.workspace,
                shell=False,
                stdout=log_file,
                stderr=log_file,
                preexec_fn=os.setsid if sys.platform != 'win32' else None
            )
            
            # Wait for backend to start listening
            start_time = time.time()
            while time.time() - start_time < timeout:
                if self.process.poll() is not None:
                    stderr = self.process.stderr.read().decode('utf-8', errors='replace')
                    stdout = self.process.stdout.read().decode('utf-8', errors='replace')
                    print("Backend process exited early. stdout:\n{}\nstderr:\n{}".format(stdout, stderr))
                    return False
                if self.is_running():
                    print("Backend started successfully")
                    return True
                time.sleep(0.5)
            
            print("Backend launch timeout - backend may not be responding")
            return False
            
        except Exception as e:
            print("Failed to launch backend: {}".format(e))
            return False
    
    def shutdown(self):
        """Shutdown the backend process."""
        if self.process:
            try:
                # Try graceful shutdown first
                self.process.terminate()
                self.process.wait(timeout=5)
            except:
                # Force kill if needed
                try:
                    self.process.kill()
                except:
                    pass
            self.process = None


class TeslaDiagnosticGUI(ctk.CTk):
    """Main Tesla Diagnostic GUI Application."""
    
    def __init__(self):
        super().__init__()
        self.title("Tesla UDS Diagnostic Tool")
        self.geometry("1400x800")
        
        # Initialize backend launcher and bridge client on a configurable port
        self.backend_port = 5001
        self.backend_launcher = BackendLauncher(port=self.backend_port)
        
        # Initialize bridge client
        self.bridge_client = UDSBridgeClient(host='127.0.0.1', port=self.backend_port)
        self.connected = False
        self.transport_initialized = False
        self.current_ecu = None
        self.ecu_frames = {}
        
        # Create UI layout
        self._create_layout()
        
        # Launch backend and try to connect
        self.after(500, self._startup_backend)
    
    def _create_layout(self):
        """Create the main GUI layout."""
        # Top Connection Bar
        top_frame = ctk.CTkFrame(self, fg_color="#2B2B2B")
        top_frame.pack(fill='x', padx=10, pady=5)
        
        self.status_label = ctk.CTkLabel(top_frame, text="Status: Disconnected", text_color="red")
        self.status_label.pack(side='left', padx=10)
        
        connect_btn = ctk.CTkButton(top_frame, text="Connect", command=self._connect)
        connect_btn.pack(side='left', padx=5)
        
        disconnect_btn = ctk.CTkButton(top_frame, text="Disconnect", command=self._disconnect)
        disconnect_btn.pack(side='left', padx=5)
        
        backend_port_label = ctk.CTkLabel(top_frame, text="Backend Port:")
        backend_port_label.pack(side='left', padx=(15, 0))
        self.backend_port_entry = ctk.CTkEntry(top_frame, width=80)
        self.backend_port_entry.insert(0, str(self.backend_port))
        self.backend_port_entry.pack(side='left', padx=5)
        
        self.transport_status_label = ctk.CTkLabel(top_frame, text="Transport: Not initialized", text_color="orange")
        self.transport_status_label.pack(side='left', padx=10)
        
        # Tester Present Controls (Right-aligned in top_frame)
        tp_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        tp_frame.pack(side='right', padx=10)
        
        self.tp_switch = ctk.CTkSwitch(tp_frame, text="Tester Present", command=self._toggle_tester_present)
        self.tp_switch.pack(side='left', padx=5)
        
        self.tp_interval_label = ctk.CTkLabel(tp_frame, text="Interval: 2.0s")
        self.tp_interval_label.pack(side='left', padx=5)
        
        self.tp_interval_slider = ctk.CTkSlider(tp_frame, from_=0.5, to=5.0, number_of_steps=9, width=100, command=self._on_tp_interval_change)
        self.tp_interval_slider.set(2.0)
        self.tp_interval_slider.pack(side='left', padx=5)
        
        # Transport Configuration Bar
        transport_frame = ctk.CTkFrame(self, fg_color="#292929")
        transport_frame.pack(fill='x', padx=10, pady=5)
        
        ctk.CTkLabel(transport_frame, text="Transport:", width=90).pack(side='left', padx=(5, 0))
        self.transport_type = ctk.CTkOptionMenu(transport_frame, values=["simulated", "esp32_usb", "esp32_wifi"], command=self._on_transport_type_change)
        self.transport_type.set("simulated")
        self.transport_type.pack(side='left', padx=5)
        
        self.transport_target = ctk.CTkEntry(transport_frame, placeholder_text="Target (IP or Serial)", width=220)
        self.transport_target.pack(side='left', padx=5)
        
        self.scan_btn = ctk.CTkButton(transport_frame, text="Scan", width=60, command=self._scan_esp32_network)
        self.scan_btn.pack(side='left', padx=(0, 5))
        self.scan_btn.configure(state='disabled') # disabled by default (simulated mode)
        
        self.transport_port = ctk.CTkEntry(transport_frame, placeholder_text="Port", width=80)
        self.transport_port.insert(0, "1337")
        self.transport_port.pack(side='left', padx=5)
        
        self.transport_baudrate = ctk.CTkEntry(transport_frame, placeholder_text="Baudrate", width=90)
        self.transport_baudrate.insert(0, "115200")
        self.transport_baudrate.pack(side='left', padx=5)
        
        self.transport_canbaud = ctk.CTkOptionMenu(transport_frame, values=["6 - 500k", "8 - 1M"])
        self.transport_canbaud.set("6 - 500k")
        self.transport_canbaud.pack(side='left', padx=5)
        
        self.init_transport_btn = ctk.CTkButton(transport_frame, text="Connect Adapter", command=self._initialize_transport)
        self.init_transport_btn.pack(side='left', padx=5)
        
        self._update_transport_fields()
        
        # Main Content Area with Sidebar
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # ECU Selector Sidebar
        sidebar = ctk.CTkFrame(main_frame, width=150, fg_color="#1F1F1F")
        sidebar.pack(side='left', fill='y', padx=(0, 10))
        sidebar.pack_propagate(False)
        
        ctk.CTkLabel(sidebar, text="ECUs", font=("Arial", 12, "bold")).pack(pady=10)
        
        self.ecu_listbox = tk.Listbox(sidebar, bg="#2B2B2B", fg="white", height=20)
        self.ecu_listbox.pack(fill='both', expand=True, padx=5, pady=5)
        self.ecu_listbox.bind('<<ListboxSelect>>', self._on_ecu_select)
        
        # Content Area
        self.content_frame = ctk.CTkFrame(main_frame)
        self.content_frame.pack(side='left', fill='both', expand=True)
        
        # Empty state message
        self.empty_label = ctk.CTkLabel(self.content_frame, text="Select an ECU to begin",
                                        font=("Arial", 14), text_color="gray")
        self.empty_label.pack(expand=True)
        
        # Log Area at bottom
        ctk.CTkLabel(self, text="Activity Log:", font=("Arial", 10, "bold")).pack(anchor='w', padx=10)
        
        self.log_text = tk.Text(self, height=4, bg="#2B2B2B", fg="white")
        self.log_text.pack(fill='x', padx=10, pady=(0, 10))
    
    def _get_transport_settings(self):
        """Collect transport settings from the UI."""
        transport_type = self.transport_type.get()
        can_baud_value = self.transport_canbaud.get().split()[0] if self.transport_canbaud.get() else '6'
        params = {
            'type': transport_type,
            'target': self.transport_target.get().strip(),
            'port': int(self.transport_port.get().strip() or 0),
            'baudrate': int(self.transport_baudrate.get().strip() or 115200),
            'can_baud': can_baud_value
        }
        return params
    
    def _on_transport_type_change(self, choice):
        """Update transport field hints when the transport type changes."""
        if choice == 'esp32_usb':
            self.transport_target.configure(placeholder_text='Serial Device (e.g. /dev/cu.usbserial-0001)')
            self.transport_port.configure(state='disabled')
            self.transport_baudrate.configure(state='normal')
            self.scan_btn.configure(state='normal', text="Scan Ports")
        elif choice == 'esp32_wifi':
            self.transport_target.configure(placeholder_text='ESP32 IP Address (e.g. 192.168.4.1)')
            self.transport_port.configure(state='normal')
            self.transport_baudrate.configure(state='disabled')
            self.scan_btn.configure(state='normal', text="Scan")
        else:
            self.transport_target.configure(placeholder_text='Target not required for simulated')
            self.transport_port.configure(state='disabled')
            self.transport_baudrate.configure(state='disabled')
            self.scan_btn.configure(state='disabled', text="Scan")
        if self.transport_initialized:
            self.transport_initialized = False
            self.transport_status_label.configure(text="Transport: Needs re-init", text_color="orange")
        self._update_transport_fields()
        
    def _scan_esp32_network(self):
        """Scan for ESP32 — UDP broadcast for WiFi, serial port list for USB."""
        mode = self.transport_type.get()
        if mode == 'esp32_usb':
            self._scan_serial_ports()
        else:
            self._scan_esp32_wifi()

    def _scan_serial_ports(self):
        import glob
        ports = sorted(glob.glob('/dev/cu.usb*') + glob.glob('/dev/cu.tty*') + glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*'))
        if not ports:
            messagebox.showinfo("No Devices", "No USB serial devices found. Make sure the ESP32 is plugged in.")
            return
        # Show a simple selection popup
        popup = ctk.CTkToplevel(self)
        popup.title("Select Serial Port")
        popup.geometry("340x300")
        popup.grab_set()
        ctk.CTkLabel(popup, text="Available USB Serial Devices:", font=("Arial", 12, "bold")).pack(pady=(15, 5))
        lb = tk.Listbox(popup, bg="#2B2B2B", fg="white", font=("Courier", 11), height=8)
        lb.pack(fill='both', expand=True, padx=15, pady=5)
        for p in ports:
            lb.insert('end', p)
        if ports:
            lb.selection_set(0)
        def on_select():
            sel = lb.curselection()
            if sel:
                port = lb.get(sel[0])
                self.transport_target.delete(0, 'end')
                self.transport_target.insert(0, port)
                self._log("Selected serial port: {}".format(port))
            popup.destroy()
        ctk.CTkButton(popup, text="Select", command=on_select).pack(pady=10)

    def _scan_esp32_wifi(self):
        import socket
        import json
        import threading
        
        self.scan_btn.configure(text="Scanning...", state="disabled")
        self._log("Scanning local network for ESP32 UDS Bridge via UDP broadcast (port 1338)...")
        
        def scan_thread():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                sock.settimeout(2.0)
                
                message = b"DISCOVER_TESLADIAG"
                sock.sendto(message, ('<broadcast>', 1338))
                sock.sendto(message, ('255.255.255.255', 1338))
                
                data, addr = sock.recvfrom(1024)
                try:
                    resp = json.loads(data.decode('utf-8'))
                    ip = resp.get('ip')
                    # Fallback to sender address if reported IP is 0.0.0.0
                    target_ip = ip if (ip and ip != "0.0.0.0") else addr[0]
                    self.after(0, lambda: self._on_scan_success(target_ip))
                except Exception as parse_e:
                    self.after(0, lambda: messagebox.showerror("Scan Error", "Invalid response from ESP32: {}".format(parse_e)))
            except socket.timeout:
                self.after(0, lambda: messagebox.showinfo("Scan Complete", "No ESP32 devices found on the local network.\\nEnsure you are connected to the same Wi-Fi router or the ESP32's hotspot (192.168.4.1)."))
                self.after(0, lambda: self._log("Scan timeout: No devices responded."))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Scan Error", str(e)))
            finally:
                sock.close()
                self.after(0, lambda: self.scan_btn.configure(text="Scan", state="normal"))
                
        threading.Thread(target=scan_thread).start()
        
    def _on_scan_success(self, ip):
        self.transport_target.delete(0, 'end')
        self.transport_target.insert(0, ip)
        self._log("SUCCESS: ESP32 auto-discovered at {}".format(ip))
    
    def _update_transport_fields(self):
        """Enable/disable transport fields based on selected transport type."""
        transporter = self.transport_type.get()
        if transporter == 'simulated':
            self.transport_target.configure(state='disabled')
            self.transport_port.configure(state='disabled')
            self.transport_baudrate.configure(state='disabled')
        elif transporter == 'esp32_usb':
            self.transport_target.configure(state='normal')
            self.transport_port.configure(state='disabled')
            self.transport_baudrate.configure(state='normal')
        elif transporter == 'esp32_wifi':
            self.transport_target.configure(state='normal')
            self.transport_port.configure(state='normal')
            self.transport_baudrate.configure(state='disabled')
        else:
            self.transport_target.configure(state='normal')
            self.transport_port.configure(state='normal')
            self.transport_baudrate.configure(state='normal')
            
    def _toggle_tester_present(self):
        """Toggle Tester Present messages on the CAN bus."""
        if not self.connected:
            self._log("Cannot toggle Tester Present: Not connected to Bridge")
            self.tp_switch.deselect()
            return
        
        active = bool(self.tp_switch.get())
        interval = float(self.tp_interval_slider.get())
        try:
            result = self.bridge_client.call('tester_present_toggle', {'active': active, 'interval': interval})
            self._log("Tester Present toggled to {} (Interval: {}s)".format(active, interval))
        except Exception as e:
            self._log("Failed to toggle Tester Present: {}".format(e))
            if active:
                self.tp_switch.deselect()
            else:
                self.tp_switch.select()
                
    def _on_tp_interval_change(self, value):
        """Handle Tester Present interval slider adjustment."""
        val_float = round(float(value), 1)
        self.tp_interval_label.configure(text="Interval: {}s".format(val_float))
        if self.connected and hasattr(self, 'tp_switch') and bool(self.tp_switch.get()):
            try:
                self.bridge_client.call('tester_present_toggle', {'active': True, 'interval': val_float})
            except Exception as e:
                self._log("Failed to update Tester Present interval: {}".format(e))
    
    def _initialize_transport(self):
        """Initialize the selected transport in the backend bridge."""
        if not self.connected:
            self._log("Cannot initialize transport: UDS Bridge not connected")
            raise Exception("UDS Bridge not connected")

        params = self._get_transport_settings()
        self._log("Initializing transport: {}".format(params['type']))
        try:
            result = self.bridge_client.call('init_transport', params)
            self.transport_initialized = True
            self.transport_status_label.configure(text="Transport: Connected ({})".format(params['type']), text_color="green")
            self._log("{}".format(result))
            return result
        except Exception as e:
            self.transport_initialized = False
            self.transport_status_label.configure(text="Transport: Initialization failed", text_color="red")
            self._log("Transport init failed: {}".format(str(e)))
            raise
    
    def _startup_backend(self):
        """Launch backend and establish connection."""
        self._log("Initializing UDS Bridge...")
        
        self.backend_port = int(self.backend_port_entry.get().strip() or self.backend_port)
        self.bridge_client.port = self.backend_port
        self.backend_launcher.port = self.backend_port
        
        # Try launching backend if not already running
        if not self.backend_launcher.is_running():
            self._log("Starting backend process on port {}...".format(self.backend_port))
            if not self.backend_launcher.launch(timeout=15):
                self._log("Warning: Backend launch may have failed")
        
        # Now try to connect
        self._auto_connect()
    
    def _auto_connect(self):
        """Try to auto-connect to bridge."""
        if self.bridge_client.connect():
            self.connected = True
            self.status_label.configure(text="Status: Connected", text_color="green")
            self._load_ecu_list()
            self._log("Connected to UDS Bridge successfully")
        else:
            self._log("Failed to connect to UDS Bridge. Make sure uds_bridge.py is running.")
    
    def _connect(self):
        """Connect to the bridge."""
        if self.connected:
            self._log("Already connected")
            return
        self._auto_connect()
    
    def _disconnect(self):
        """Disconnect from the bridge."""
        if self.connected:
            if hasattr(self, 'tp_switch'):
                self.tp_switch.deselect()
            self.bridge_client.disconnect()
            self.connected = False
            self.transport_initialized = False
            self.status_label.configure(text="Status: Disconnected", text_color="red")
            self.transport_status_label.configure(text="Transport: Not initialized", text_color="orange")
            self._log("Disconnected from UDS Bridge")
    
    def _load_ecu_list(self):
        """Load available ECUs from the bridge."""
        try:
            result = self.bridge_client.call('get_nodes')
            self.ecu_listbox.delete(0, 'end')
            for ecu in result:
                self.ecu_listbox.insert('end', ecu)
            self._log("Loaded {} ECUs".format(len(result)))
        except Exception as e:
            self._log("Error loading ECUs: {}".format(str(e)))
    
    def _on_ecu_select(self, event):
        """Handle ECU selection."""
        selection = self.ecu_listbox.curselection()
        if not selection:
            return
        
        ecu_index = selection[0]
        ecu_name = self.ecu_listbox.get(ecu_index)
        
        self._switch_to_ecu(ecu_name)
    
    def _switch_to_ecu(self, ecu_name):
        """Switch to a specific ECU cockpit."""
        if self.current_ecu == ecu_name:
            return
        
        # Hide previous content
        for frame in self.content_frame.winfo_children():
            frame.pack_forget()
        
        # Do not allow ECU connection if transport isn't connected
        if not self.transport_initialized:
            messagebox.showerror("Not Connected", "Please connect to the adapter (ESP32/PCAN) first!")
            return
        
        # Create or retrieve ECU frame
        if ecu_name not in self.ecu_frames:
            try:
                self.bridge_client.call('set_node', {'node': ecu_name})
                
                # Create ECU cockpit
                ecu_frame = ECUCockpitFrame(self.content_frame, self.bridge_client, ecu_name)
                self.ecu_frames[ecu_name] = ecu_frame
                self._log("Initialized {} cockpit".format(ecu_name))
            except Exception as e:
                self._log("Error initializing {}: {}".format(ecu_name, str(e)))
                return
        
        # Show ECU frame
        self.ecu_frames[ecu_name].pack(fill='both', expand=True)
        self.current_ecu = ecu_name
        self._log("Switched to {} ECU".format(ecu_name))
    
    def _log(self, message):
        """Log a message to the activity log."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        msg = "[{}] {}\n".format(timestamp, message)
        self.log_text.insert('end', msg)
        self.log_text.see('end')
    
    def on_closing(self):
        """Handle application close."""
        self._log("Shutting down...")
        self._disconnect()
        # Shutdown backend if we launched it
        if self.backend_launcher and self.backend_launcher.process:
            self._log("Stopping backend...")
            self.backend_launcher.shutdown()
        self.destroy()


def main():
    """Main entry point."""
    app = TeslaDiagnosticGUI()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == '__main__':
    main()
