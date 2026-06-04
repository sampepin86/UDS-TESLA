# Tesla UDS Diagnostic Tool - Setup & Execution Guide

## Overview

The standalone Tesla UDS Diagnostic Tool consists of three main components:

1. **Backend Bridge (`uds_bridge.py`)** - Python 2.7 process running in Conda environment `uds-py27`
2. **Frontend GUI (`gui.py`)** - Python 3 CustomTkinter desktop application
3. **Hardware Transports** - ESP32 Bridge or PCAN adapter connectivity

---

## Prerequisites

### System Requirements
- macOS M3 with Apple Silicon (or x86_64 Mac with Rosetta 2)
- Python 3.8+ (for GUI)
- Python 2.7 via Conda (for backend)
- Conda package manager

### Required Python Packages

#### Python 3 (GUI environment)
```bash
pip install customtkinter
```

#### Python 2.7 (UDS backend environment)
```bash
CONDA_SUBDIR=osx-64 conda create -n uds-py27 python=2.7
conda activate uds-py27
pip install pyserial enum34
```

---

## Setup Instructions

### 1. Create Python 2.7 Conda Environment

```bash
# Create x86_64 Python 2.7 environment (runs via Rosetta 2)
CONDA_SUBDIR=osx-64 conda create -n uds-py27 python=2.7

# Activate environment
conda activate uds-py27

# Install dependencies
pip install pyserial enum34
```

### 2. Verify CustomTkinter Installation

```bash
# In your Python 3 environment (not uds-py27)
pip install customtkinter
python -c "import customtkinter; print('CustomTkinter OK')"
```

---

## Running the Application

### Single Command Startup (Recommended)

The GUI automatically launches the backend for you:

```bash
cd /Users/samuel/Desktop/uds-0.0.227-py2.7
python3 gui.py
```

**What happens automatically:**
1. Detects if backend is already running on port 5000
2. If not running, launches `uds_bridge.py` in `uds-py27` environment
3. Waits for backend to start listening
4. Connects and loads ECU list
5. Displays the diagnostic interface

**Expected Terminal Output:**
```
[HH:MM:SS] Initializing UDS Bridge...
[HH:MM:SS] Starting backend process...
[HH:MM:SS] Connected to UDS Bridge successfully
[HH:MM:SS] Loaded 12 ECUs
```

### Manual Two-Terminal Setup (Alternative)

If you prefer manual control or need to run the backend separately:

**Terminal 1 (Backend - Python 2.7):**
```bash
conda activate uds-py27
cd /Users/samuel/Desktop/uds-0.0.227-py2.7
python uds_bridge.py
```

**Terminal 2 (Frontend - Python 3):**
```bash
cd /Users/samuel/Desktop/uds-0.0.227-py2.7
python3 gui.py
```

---

## GUI Features

### Main Interface
- **Status Bar**: Connection status indicator (top-left)
- **ECU Sidebar**: Scrollable list of available ECUs on the vehicle network
- **Content Area**: Dynamic tabbed diagnostic interface for selected ECU
- **Activity Log**: Real-time operation log (bottom)

### Diagnostic Functions (Per ECU)

#### Session Control Tab
- **Service 0x10**: Set diagnostic session type
- Session types: Default, Programming, Extended, Safety System
- Response requirement toggle

#### Security Access Tab
- **Service 0x27**: Unlock ECU with seed-key authentication
- Automatic key generation using Tesla's XOR algorithm (seed XOR 0x53)
- Manual key input option
- Security levels: 0x01, 0x03, 0x05, 0x07

#### DTCs Tab
- **Service 0x19**: Read Diagnostic Trouble Codes
- **Service 0x14**: Clear stored DTCs
- **Service 0x85**: Control DTC recording
- Status mask filtering (Active, History, All)
- DTC group selection (All, Powertrain, Chassis, Body)

#### Data Tab
- **Service 0x22**: Read Data by Identifier (RDBI)
- **Service 0x2E**: Write Data by Identifier (WDBI)
- Hex-based data ID input (e.g., F190 for VIN)
- Read/write value display and editing

### Additional Capabilities (Planned)
- IO Control (Service 0x2F) - Actuator overrides
- Routine Control (Service 0x31) - Diagnostic procedures
- Memory Operations (Services 0x23/0x3D) - Direct memory access
- Firmware Flashing - Complete flash sequence with progress

---

## Transport Configuration

### Simulated Transport (Default)
- No hardware required
- Useful for testing and development
- Connects to simulated ECU responses

### PCAN Transport
- Requires PCAN USB adapter connected
- Automatically detected if available

### ESP32 Transport
- **USB Connection**: Serial-over-USB with SLCAN protocol
- **Wi-Fi Connection**: TCP connection to ESP32 at `tesladiag.local` (mDNS)
- Configure in backend initialization

---

## Architecture Overview

```
┌─────────────────────────────────────────┐
│  gui.py (Python 3 / CustomTkinter)     │
│  - Desktop standalone window            │
│  - Tabbed diagnostic interface          │
└──────────────┬──────────────────────────┘
               │ JSON-RPC over TCP Socket
               │ (Port 5000)
               ▼
┌─────────────────────────────────────────┐
│  uds_bridge.py (Python 2.7 / uds-py27) │
│  - Loads native _udsClient.so           │
│  - Manages transport layers             │
│  - Coordinates UDS sequences            │
└──────────────┬──────────────────────────┘
               │ UDS Protocol
               ▼
     ┌─────────┴──────────┐
     ▼                    ▼
  PCAN/USB          ESP32 Wi-Fi/USB
     │                    │
     └─────────┬──────────┘
               ▼
        Vehicle CAN Bus
```

---

## Troubleshooting

### "Failed to connect to UDS Bridge"
- Ensure `uds_bridge.py` is running in Terminal 1
- Check that port 5000 is not in use: `lsof -i :5000`
- Verify Python 2.7 environment has required packages: `conda activate uds-py27 && python -m pip list`

### "No module named customtkinter"
- Install in your Python 3 environment: `pip install customtkinter`
- Verify with: `python3 -c "import customtkinter; print(customtkinter.__version__)"`

### GUI doesn't appear
- Check terminal for error messages
- Verify Python 3.8+ is being used: `python3 --version`
- Try running without conda: `python3 gui.py`

### ECU List not populating
- Ensure `uds_bridge.py` is running and responding
- Check Activity Log for error messages
- Click "Connect" button to retry connection

### "Hex file path does not exist"
- Provide absolute path to firmware file
- Verify file exists: `ls -la /path/to/firmware.hex`

---

## Development Notes

### Adding New Diagnostic Functions

1. Create a new `DiagnosticFrame` subclass in `gui.py`
2. Implement the `execute()` method to call bridge RPC methods
3. Add corresponding RPC handler in `uds_bridge.py`
4. Register in ECU cockpit tab layout

### Extending Transport Drivers

1. Subclass `AbstractTransport` in transport layer
2. Implement `initialize()`, `send_frame()`, `recv_frame()`, `finish()`
3. Register in backend's `init_transport` RPC method

### Python 2.7 Compatibility Notes

- Backend runs under Python 2.7 for native library compatibility
- All string formatting uses `.format()` for Python 2 compatibility
- Exception handling uses older syntax: `except Exception as e: e.message`
- No f-strings or type hints in backend code

---

## Performance Tuning

### Network Latency
- Adjust JSON-RPC timeout: Modify `UDSBridgeClient.call()` timeout parameter
- Default is 10 seconds per RPC call

### CAN Bus Speed
- Edit transport initialization parameters in GUI connection logic
- Supported: 125k, 250k, 500k, 1M baud rates

### Tester Present Interval
- Adjustable in Security tab (1-5 seconds)
- Prevents session timeout during operations

---

## File Structure

```
/Users/samuel/Desktop/uds-0.0.227-py2.7/
├── gui.py                              # CustomTkinter GUI (Python 3)
├── uds_bridge.py                       # JSON-RPC Backend Bridge (Python 2.7)
├── uds/                                # UDS Protocol Library
│   ├── client.py                       # Main UDS client interface
│   ├── nodes/                          # ECU node definitions
│   │   └── nodes.json                  # Vehicle network topology
│   └── transport/                      # Transport layer drivers
│       ├── pcan_transport.py
│       ├── esp32_transport.py
│       └── simulated_transport.py
├── scratch/esp32_can_bridge/           # ESP32 firmware source
│   └── esp32_can_bridge.ino            # FreeRTOS dual-core implementation
└── README.md                           # This file
```

---

## License & Attribution

Standalone Tesla UDS Diagnostic Tool
- Antigravity (May 31, 2026)
- Hybrid dual-process Python 2.7/3 architecture with CustomTkinter UI
- JSON-RPC IPC protocol with secure transport abstraction

Based on the UDS protocol library and transport drivers from the UDS project.

---

## Support

For issues or questions, refer to:
- Implementation Plan: `implementation_plan.md`
- Task Status: `task.md`
- UDS Protocol Documentation: `uds/README.md`
