# Tesla UDS over CAN Diagnostic Tool & ESP32 Bridge

This repository contains a robust diagnostic tool stack for Tesla vehicles utilizing Unified Diagnostic Services (UDS) over Controller Area Network (CAN). It bridges a Python-based GUI / UDS client with an ESP32 hardware transceiver adapter.

---

## 📐 Architecture Stack

```
   ┌───────────────────────────────────────────────────────────┐
   │                  Python 3 CustomTkinter GUI               │
   │  (Diagnostic session management, DTC reading, flashing)   │
   └─────────────────────────────┬─────────────────────────────┘
                                 │ JSON-RPC over TCP / USB
   ┌─────────────────────────────▼─────────────────────────────┐
   │                 Python 2.7 UDS Bridge (IPC)               │
   │      (Interacts with SWIG-wrapped C++ udsClient library)   │
   └─────────────────────────────┬─────────────────────────────┘
                                 │ SLCAN Commands over TCP/Serial
   ┌─────────────────────────────▼─────────────────────────────┐
   │                    ESP32 Bridge Firmware                  │
   │   (Dual-core FreeRTOS TWAI driver, Web Portal & OTA Tasks)│
   └─────────────────────────────┬─────────────────────────────┘
                                 │ ISO-TP (ISO 15765-2) over CAN
   ┌─────────────────────────────▼─────────────────────────────┐
   │                     Physical CAN Bus                      │
   │                  (Tesla vehicle network)                  │
   └───────────────────────────────────────────────────────────┘
```

---

## 🔌 Hardware Setup & Pin Mapping

The ESP32 interfaces with the CAN transceiver (e.g., SN65HVD230) using the built-in Two-Wire Automotive Interface (TWAI) peripheral.

| ESP32 Pin | Transceiver Pin | Function |
|:---|:---|:---|
| **GPIO 5** | TXD | TWAI (CAN) Transmit |
| **GPIO 4** | RXD | TWAI (CAN) Receive |
| **GND** | GND | Ground Reference |
| **3.3V** | VCC | Transceiver Power |

---

## ⚡ ESP32 Bridge Firmware Features

The firmware located in `scratch/esp32_can_bridge/` runs as a dual-core FreeRTOS application:
1. **CAN Bus Controller (Core 1, Priority 5):** Handles time-critical CAN transmit queues and receive interrupts. Includes automatic bus-off recovery.
2. **Network & Portal (Core 0, Priority 2):** Serves the configuration web server, manages Wi-Fi credentials in non-volatile storage (NVS), runs mDNS (`tesladiag.local`), and handles JSON-RPC/SLCAN sockets.
3. **Dedicated OTA Task (Core 0, Priority 3):** Handles over-the-air updates independently to prevent blocking.

---

## 📡 Remote Firmware Updates (OTA)

For robustness, two secure pathways are provided to update the ESP32 firmware without requiring a USB connection:

### 1. Web browser Upload (HTTP)
* **Access Point IP:** `192.168.4.1` (or local station IP like `192.168.40.199`)
* **Endpoint:** `/update`
* **Authentication:** Username: `admin`, Password: `tesladiag` (configurable via NVS)
* **How it works:**
  1. Open `http://<IP>/update` in a browser.
  2. Log in, select the compiled firmware `.bin` file, and click **Flash Firmware**.
  3. Or upload via `curl` from a terminal:
     ```bash
     curl -u admin:tesladiag -F "firmware=@build/esp32_can_bridge.ino.bin" http://<IP>/update
     ```

### 2. Network Flash (ArduinoOTA / UDP)
* **Port:** `3232`
* **Hostname:** `tesladiag-esp32.local`
* **Method:** Flash directly from the Arduino IDE or via CLI tools.

### 🛡️ OTA Safety & Robustness
* **Automatic CAN Suspension:** The TWAI controller driver is stopped and uninstalled safely before flash writes begin, avoiding interrupt collisions or writing to flash during active bus traffic.
* **Failure Recovery:** If the update is aborted or fails integrity checks, the CAN driver is automatically re-initiated.
* **Integrity Validation:** Every payload is verified using MD5 hash validation via the ESP32 `Update` library.

---

## 🚀 Quick Start

### 1. Compile & Upload Firmware (USB Initial Flash)
Ensure `arduino-cli` or Arduino IDE is configured for the ESP32 board manager.
```bash
arduino-cli compile --fqbn esp32:esp32:esp32 scratch/esp32_can_bridge
arduino-cli upload -p <port> --fqbn esp32:esp32:esp32 scratch/esp32_can_bridge
```

### 2. Connect to Wi-Fi Portal
1. Connect to the ESP32 Wi-Fi access point: **SSID:** `TeslaDiag-ESP32` (open network).
2. Open `http://192.168.4.1` to scan networks and save credentials.
3. The device will restart and connect to your local network.

### 3. Run the GUI
Ensure dependencies are installed and run the CustomTkinter dashboard:
```bash
python3 gui.py
```
