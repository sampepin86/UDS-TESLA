# Tesla UDS Diagnostic Tool - Quick Start

## ✓ Implementation Complete

All components have been successfully implemented and validated:

- ✅ **Backend Bridge** (`uds_bridge.py`) - JSON-RPC server for UDS operations
- ✅ **GUI Application** (`gui.py`) - CustomTkinter desktop interface
- ✅ **Test Suite** (`test_implementation.py`) - Validation tests
- ✅ **Documentation** - Setup and usage guides

---

## Architecture Summary

```
GUI (Python 3)           Backend (Python 2.7)
  gui.py        ←→        uds_bridge.py
CustomTkinter         (uds-py27 conda env)
   (Port 5000 JSON-RPC over TCP)
```

---

## Quick Setup (First Time Only)

### 1. Create Python 2.7 Environment

```bash
CONDA_SUBDIR=osx-64 conda create -n uds-py27 python=2.7
conda activate uds-py27
pip install pyserial enum34
```

### 2. Install CustomTkinter (Python 3)

```bash
pip install customtkinter
```

### 3. Verify Setup (Optional)

```bash
cd /Users/samuel/Desktop/uds-0.0.227-py2.7
python test_implementation.py
```

Should show: **✓ All tests passed!**

This test validates that everything is properly installed.

---

## Running the Application

### ✨ New: Single Command Startup

The GUI now **automatically launches the backend**! Simply run:

```bash
cd /Users/samuel/Desktop/uds-0.0.227-py2.7
python3 gui.py
```

That's it! The GUI will:
1. Detect if backend is running
2. Launch `uds_bridge.py` in `uds-py27` environment if needed
3. Connect to the backend
4. Display the diagnostic interface

⚡ **One command. That's all you need!**

### Manual Setup (Two Terminals - Still Supported)

If you prefer manual control:

**Terminal 1 - Backend:**
```bash
conda activate uds-py27
cd /Users/samuel/Desktop/uds-0.0.227-py2.7
python uds_bridge.py
```

**Terminal 2 - Frontend:**
```bash
cd /Users/samuel/Desktop/uds-0.0.227-py2.7
python3 gui.py
```

---

## GUI Features

Once connected, you can:

### 📊 **Session Control**
- Set diagnostic session type (Default, Programming, Extended, Safety)
- Auto-refresh tester present keepalive

### 🔐 **Security Access**
- Request seed from ECU
- Auto-calculate security key (XOR algorithm)
- Unlock ECU for protected operations

### 🚨 **DTC Manager**
- Read active/historical diagnostic trouble codes
- Clear fault codes
- Filter by status and group

### 📝 **Data Explorer**
- Read data by identifier (RDBI - Service 0x22)
- Write data by identifier (WDBI - Service 0x2E)
- Hex-based data manipulation

### 🔌 **ECU Selection**
- Sidebar lists all available ECUs (BMS, MCU, CHG, GTW, etc.)
- Click to switch ECU context
- Each ECU has independent diagnostic panels

---

## File Structure

```
/Users/samuel/Desktop/uds-0.0.227-py2.7/
├── gui.py                          # Python 3 CustomTkinter GUI
├── uds_bridge.py                   # Python 2.7 JSON-RPC backend
├── test_implementation.py          # Validation test suite
├── start.sh                        # Quick launch helper
├── README_GUI_SETUP.md             # Detailed setup guide
├── QUICKSTART.md                   # This file
├── uds/                            # UDS Protocol Library
│   ├── client.py
│   ├── nodes/
│   └── transport/
└── scratch/esp32_can_bridge/       # ESP32 firmware
```

---

## Troubleshooting

### Connection Failed
```
GUI shows "Status: Disconnected"
```
✓ Ensure Terminal 1 (backend) is running with `python uds_bridge.py`
✓ Check port 5000 is not in use: `lsof -i :5000`

### CustomTkinter Not Found
```
ModuleNotFoundError: No module named 'customtkinter'
```
✓ Install: `pip install customtkinter`

### uds-py27 Environment Missing
```
ERROR: uds-py27 environment not found
```
✓ Create it: `CONDA_SUBDIR=osx-64 conda create -n uds-py27 python=2.7`

### No ECUs Appearing
✓ Click "Connect" button in GUI
✓ Check backend terminal for error messages
✓ Run test: `python test_implementation.py`

---

## Development Notes

### Python Version Separation
- **Backend**: Must run Python 2.7 (native compiled UDS library requirement)
- **Frontend**: Python 3.8+ (CustomTkinter)
- **No modifications to UDS code** - kept as-is for compatibility

### Adding New Diagnostic Functions
1. Create `DiagnosticFrame` subclass in `gui.py`
2. Add RPC handler in `uds_bridge.py`
3. Register in ECU cockpit tab layout

### Transport Configuration
Backend automatically detects and supports:
- **Simulated** (default) - for testing
- **PCAN** - USB CAN adapter
- **ESP32** - Serial SLCAN or Wi-Fi (mDNS)

---

## Next Steps

1. **Verify Setup**: Run `python test_implementation.py`
2. **Start Backend**: `conda activate uds-py27 && python uds_bridge.py`
3. **Launch GUI**: `python3 gui.py` (in another terminal)
4. **Select ECU**: Click on ECU name in sidebar
5. **Perform Diagnostics**: Use tabbed panels for operations

---

## Support Resources

- **Setup Guide**: [README_GUI_SETUP.md](README_GUI_SETUP.md)
- **Implementation Plan**: [implementation_plan.md](implementation_plan.md)
- **Task Status**: [task.md](task.md)
- **Python Version Check**: `python3 --version` (should be 3.8+)
- **Conda Environment**: `conda env list` (should show uds-py27)

---

## Performance Tips

- **Tester Present Interval**: Adjust in Security tab (1-5 seconds)
- **CAN Bus Speed**: Default 500k baud - modify in backend init
- **Network Latency**: Default RPC timeout 10 seconds
- **Session Timeout**: Activate tester present to prevent ECU disconnect

---

**Ready to diagnose!** 🚗⚙️

For detailed technical information, see [README_GUI_SETUP.md](README_GUI_SETUP.md).
