# Standalone Tesla UDS Diagnostic App - Implementation Plan (Updated)

This document outlines the hybrid standalone architecture for the local Tesla UDS diagnostic tool. 

To satisfy the technical constraints of the native compiled library (`_udsClient.so` requiring Python 2.7) while providing a premium, modern desktop interface without using a web browser, we will implement a **two-process hybrid architecture**:

1. **Frontend Desktop App (`gui.py`)**: A Python 3 application using **CustomTkinter** or **PyQt5** to render a native standalone window. It displays standard and advanced UDS capabilities, live updates, information icons, and a scrollable log.
2. **Backend UDS Bridge (`uds_bridge.py`)**: A lightweight Python 2.7 bridge running in a local `py27` Conda environment. It handles loading the native C++ library (`_udsClient.so`) and communicating with the CAN interfaces (PCAN/ESP32).
3. **IPC Bridge**: The frontend and backend communicate locally via JSON-RPC over a local TCP socket.

```
┌────────────────────────────────────────────────────────┐
│             Desktop GUI (Python 3 / Native)            │
│   [CustomTkinter / PyQt5 Standalone Window App]        │
│   (Tabbed Panels, Info Icons, Live Graphs, DTC List)   │
└──────────────────────────┬─────────────────────────────┘
                           │ (Local TCP Socket / JSON-RPC)
                           ▼
┌────────────────────────────────────────────────────────┐
│           UDS Execution Bridge (Python 2.7)            │
│          [Conda Environment 'uds-py27']                │
│    (Loads uds.client, runs ISO-TP & transport layers)  │
└──────────────────────────┬─────────────────────────────┘
                           │ (UDS callbacks)
                           ▼
┌────────────────────────────────────────────────────────┐
│                Native UDS Engine (.so)                 │
└──────────────────────────┬─────────────────────────────┘
                           │ (Transport Interface)
                           ▼
             ┌─────────────┴─────────────┐
             ▼                           ▼
 ┌──────────────────────┐    ┌──────────────────────┐
 │    PCAN Transport    │    │   ESP32 Transport    │
 │ (libpcanbasic Driver)│    │ (Serial SLCAN Bridge)│
 └──────────┬───────────┘    └──────────┬───────────┘
            ▼                           ▼
   [ PCAN USB Dongle ]        [ ESP32 (Wi-Fi or USB) ]
            │                           │
            └─────────────┬─────────────┘
                          ▼
                  [ Vehicle CAN Bus ]
```

---

## User Review Required

> [!IMPORTANT]
> **Python 2.7 Conda Environment:**
> To run the backend UDS bridge, we need to create a dedicated local Conda environment on your macOS M3:
> `CONDA_SUBDIR=osx-64 conda create -n uds-py27 python=2.7`
> This installs an x86_64 Python 2.7 environment that runs transparently using Rosetta 2, allowing the compiled `_udsClient.so` binary to load.
>
> We will automate the setup, activation, and dependency installation (like `enum34` and `pyserial`) for you.

---

## Dynamic ECU Cockpit Navigation (New Interface Layout)

Instead of a single global node configuration, the GUI will dynamically parse the `nodes.json` configuration database and generate a **dedicated independent layout (tab/workspace) for each ECU on the Tesla network**:

* **ECU Selector Sidebar**: A scrollable vertical navigation panel displaying all detected ECUs (e.g. `BMS` [Battery Management], `MCU` [Infotainment], `CHG` [Charger], `GTW` [Gateway], `BCC` [Body Controller], `EPAS` [Power Steering]).
* **Dedicated ECU Cockpits**: Selecting an ECU in the sidebar opens its specific, pre-configured diagnostic dashboard containing all **20 UDS functions** mapped to that node's CAN addresses:

```
┌──────────────────────────────────────────────┐
│  TESLA STANDALONE DIAGNOSTIC TOOL            │
├───────────┬──────────────────────────────────┤
│ ECU LIST  │  BMS - BATTERY MANAGEMENT COCKPIT│
│ ┌───────┐ │  ┌───────────────┐ ┌───────────┐ │
│ │  BMS  │ │  │Session Control│ │  Security │ │
│ ├───────┤ │  │(Default/Prog) │ │  Seed-Key │ │
│ │  MCU  │ │  └───────────────┘ └───────────┘ │
│ ├───────┤ │  ┌───────────────┐ ┌───────────┐ │
│ │  CHG  │ │  │  DTC Manager  │ │Data Viewer│ │
│ ├───────┤ │  │ (Read/Clear)  │ │ (RDBI/WDBI│ │
│ │  GTW  │ │  └───────────────┘ └───────────┘ │
│ ├───────┤ │  ┌───────────────┐ ┌───────────┐ │
│ │  ...  │ │  │  IO Actuators │ │  Flasher  │ │
│ └───────┘ │  └───────────────┘ └───────────┘ │
└───────────┴──────────────────────────────────┘
```

---

## ESP32 Wi-Fi & USB Bridge Architecture

To ensure high-speed, non-blocking CAN communication while supporting concurrent Wi-Fi (TCP Server + Web portal for settings) and USB Serial communication, the ESP32 firmware will be designed around **FreeRTOS Dual-Core Tasks** and **Queue-based IPC**:

### 1. Dual-Core Task Segregation
* **Core 1 (Real-time CAN Task)**: Handled by the native ESP32 TWAI (Two-Wire Automotive Interface) driver. It polls CAN frames at high speed, manages ISO-TP flow controls, and places them into a thread-safe FreeRTOS Ring Buffer.
  * **Bus Fault Isolation**: If the CAN bus is disconnected, shorted, or missing a termination resistor, the TWAI driver will trigger alert loops and self-recover (Bus-Off Recovery) without stalling the CPU or interfering with Wi-Fi/Serial tasks.
* **Core 0 (Network & Interface Task)**: 
  * **USB Serial Parser**: Polls the hardware UART interface for SLCAN ASCII protocol messages.
  * **TCP Server (Port 1337)**: Listens for incoming socket connections from the Python bridge to transfer raw SLCAN frames over Wi-Fi.
  * **Wi-Fi Manager**: Launches a soft-AP (e.g. `TeslaDiag-ESP32` / IP `192.168.4.1`) that is **always active**. Simultaneously connects to a saved local home/workshop Wi-Fi router (STA mode). 

### 2. Wi-Fi Manager Web GUI
When connecting to the ESP32's Access Point via a browser, it serves an embedded, ultra-lightweight HTML portal:
* **Scan Button**: Triggers an active Wi-Fi scan and returns a list of SSIDs and signal strengths (RSSI).
* **Save Network**: Saves selected SSID and password to non-volatile storage (NVS) so it persists across reboots.

### 3. Automatic Discovery Protocol
To completely eliminate the need to search for the ESP32's IP address when connected to a local Wi-Fi router, we will implement **two auto-discovery mechanisms**:
* **mDNS / Bonjour (Native macOS Resolution)**:
  * The ESP32 hosts an mDNS responder advertising host `tesladiag`.
  * The macOS Python app can connect to **`tesladiag.local`** directly. The macOS system network resolver will resolve this name to the correct local IP automatically.
* **UDP Broadcast Discovery Protocol**:
  * The ESP32 listens on UDP Port `1338` for a broadcast probe packet (`"DISCOVER_TESLADIAG"`).
  * When received, it responds with a JSON payload containing its IP address, connection status, and device info.
  * The Python GUI has a **"Scan Network"** button that sends a UDP broadcast on the local subnet to auto-populate any active ESP32 interfaces.

---

## Exhaustive Diagnostic GUI Feature Map

To ensure no function is omitted, **every single method** defined in the `uds.client.Client` class is mapped below to its corresponding interface elements, user inputs, options, and informative `(i)` icons:

### 1. General & Connection Management
* **`set_node(self, node)`**
  * **GUI Placement**: Triggers automatically whenever switching between ECU tabs/workspaces.
  * **`(i)` Tooltip**: *Sets the active node identifier. Configures specific request CAN ID, response CAN ID, and network bus parameters for the target ECU.*

---

### 2. Diagnostic Session Control & Keepalive
* **`diagnostic_session(self, diagnosticSessionType, responseRequired)`**
  * **GUI Placement**: Session Control Panel.
  * **Inputs**:
    * `diagnosticSessionType` dropdown: `0x01` (Default), `0x02` (Programming), `0x03` (Extended), `0x04` (Safety System).
    * `responseRequired` checkbox (default True).
  * **`(i)` Tooltip**: *Sends Service 0x10. Programming Session (0x02) unlocks memory erasures/flashing. Extended Session (0x03) enables low-level engineering diagnostics and actuator overrides.*
* **`tester_present(self, responseRequired)`**
  * **GUI Placement**: Sidebar Persistent Toggle Switch.
  * **Inputs**:
    * Interval slider: `1` to `5` seconds (default 2s).
    * `responseRequired` checkbox (default True).
  * **`(i)` Tooltip**: *Sends Service 0x3E periodic heartbeat packets to the ECU. Keeps active programming sessions and security levels from timing out and resetting back to the default state.*

---

### 3. ECU Reset Control
* **`ecu_reset(self, resetType, responseRequired)`**
  * **GUI Placement**: Reset Command Box.
  * **Inputs**:
    * `resetType` dropdown: `0x01` (Hard Reset - power cycle), `0x02` (Soft Reset - software reboot), `0x03` (Key Off/On Reset), `0x04` (Enable Rapid Power Shut Down), `0x05` (Disable Rapid Power Shut Down).
    * `responseRequired` checkbox (default True).
  * **`(i)` Tooltip**: *Sends Service 0x11 to reboot the target microprocessor. Caution: Hard Reset triggers full ECU reboot and can drop CAN communications temporarily.*

---

### 4. Security Access (ECU Unlocking)
* **`security_access(self, level)`**
  * **GUI Placement**: Security Authorization Panel.
  * **Inputs**:
    * `level` selection: `0x01`, `0x03`, `0x05`, `0x07` (corresponds to request seed level).
    * Calculated key text input (pre-populated by automatic key generation).
  * **Key Generation Details**: Uses standard Tesla XOR keygen (`key = seed ^ 53`) automatically. Supports a custom manual key input box.
  * **`(i)` Tooltip**: *Sends Service 0x27. First requests a seed from the ECU. Then applies a cryptographic algorithm (XOR mask) to calculate the key, and sends the key back to unlock protected memory partitions and configuration options.*

---

### 5. DTC Management (Diagnostic Trouble Codes)
* **`read_dtc(self, requestData, outputDataLen)`**
  * **GUI Placement**: DTC Center Tab (List & Read View).
  * **Inputs**:
    * Pre-populated subfunction list (e.g. `0x02` - Report DTC By Status Mask, `0x01` - Report Number Of DTC By Status Mask).
    * Status mask input (default `0x09` or `0x0B` for Active/History faults).
  * **`(i)` Tooltip**: *Sends Service 0x19 to read active or historical fault codes from the ECU's non-volatile memory.*
* **`clear_dtc(self, dtcGroup)`**
  * **GUI Placement**: Clear Faults Button in DTC Center Tab.
  * **Inputs**:
    * `dtcGroup` selection: `0xFFFFFF` (All Groups), `0x0000FF` (Powertrain), `0x00FF00` (Chassis), `0x00FFFF` (Body).
  * **`(i)` Tooltip**: *Sends Service 0x14 to clear stored trouble codes and reset trip/cycle counters.*
* **`control_dtc(self, dtcSettingType, recordLen, dtcSettingControlOptionRecord, responseRequired)`**
  * **GUI Placement**: DTC Settings Options.
  * **Inputs**:
    * `dtcSettingType`: `0x01` (DTC Setting On), `0x02` (DTC Setting Off).
  * **`(i)` Tooltip**: *Sends Service 0x85 to suspend or resume the recording of new DTC fault codes in the ECU during active maintenance operations.*

---

### 6. Data Explorer (RDBI/WDBI)
* **`read_data(self, dataID, dataLen)`**
  * **GUI Placement**: Data Grid & DID Finder.
  * **Inputs**:
    * `dataID` text input (2-byte hex, e.g. `0xF190` for VIN, `0xF181` for App Version).
    * `dataLen` (number of bytes to read).
  * **`(i)` Tooltip**: *Sends Service 0x22 to read configuration parameters or real-time sensor measurements mapped to specific Data Identifiers (DIDs).*
* **`write_data(self, dataID, dataToWrite)`**
  * **GUI Placement**: Data Editor Modals.
  * **Inputs**:
    * `dataID` text input (2-byte hex).
    * `dataToWrite` text/hex buffer input.
  * **`(i)` Tooltip**: *Sends Service 0x2E to modify saved values (like VIN, options configuration, or calibration parameters) in the ECU.*

---

### 7. Input/Output Control (Actuator Overrides)
* **`io_control(self, ioID, ioType, inputData, outputDataLen)`**
  * **GUI Placement**: Actuator Testing Grid.
  * **Inputs**:
    * `ioID` (2-byte hex actuator code).
    * `ioType` dropdown selection:
      * `0x00` (Return Control to ECU - release override).
      * `0x01` (Reset to Default).
      * `0x02` (Freeze Current State).
      * `0x03` (Short Term Adjustment - manual override value).
    * `inputData` (hex payload for manual adjustment override).
  * **`(i)` Tooltip**: *Sends Service 0x2F to take manual control of hardware outputs. Useful to test fans, pumps, lights, and relays directly. WARNING: Return control to ECU when finished.*

---

### 8. Routine Control
* **`routine_control(self, rcID, rcType, inputData, outputDataLen)`**
  * **GUI Placement**: Routine Controller.
  * **Inputs**:
    * `rcID` (2-byte hex routine ID, e.g. `0xFF01` for Erase Flash).
    * `rcType` dropdown selection:
      * `0x01` (Start Routine).
      * `0x02` (Stop Routine).
      * `0x03` (Request Routine Results).
    * `inputData` (parameters for routine execution).
  * **`(i)` Tooltip**: *Sends Service 0x31 to start or stop execution of complex internal procedures (like erasing memory, self-calibration, or checksum verification) and read status results.*

---

### 9. Memory Examiner (Direct Access)
* **`read_memory(self, memoryAddress, memorySize, outputDataLength)`**
  * **GUI Placement**: Low-level Memory Dump panel.
  * **Inputs**:
    * `memoryAddress` (hex start address, e.g. `0x00018000`).
    * `memorySize` (length of address bytes).
    * `outputDataLength` (bytes to read).
  * **`(i)` Tooltip**: *Sends Service 0x23 to read raw byte sectors directly from the microprocessor's internal/external memory without DID boundaries.*
* **`write_memory(self, memoryAddress, dataToWrite)`**
  * **GUI Placement**: Micro-editor memory writing interface.
  * **Inputs**:
    * `memoryAddress` (hex target address).
    * `dataToWrite` (hex buffer).
  * **`(i)` Tooltip**: *Sends Service 0x3D to write raw binary instructions or bytes directly to an unallocated or unlocked memory block.*

---

### 10. Boot Loader & Flashing (ECU Firmware Reflashing)
* **`wait_for_boot_id(self, periodic=False, bootInApp=False)`**
  * **GUI Placement**: Automatic process running during flashing.
  * **`(i)` Tooltip**: *Listens to the CAN bus for the target ECU's bootloader identifier following a firmware upload or programming session reset.*
* **`request_download_init(self, memoryAddress, dataFormatIdentifier, addressAndLengthFormatIdentifier, uncompressedMemorySize)`**
  * **GUI Placement**: Firmware Flasher.
  * **`(i)` Tooltip**: *Sends Service 0x34 to notify the ECU of incoming firmware data. Establishes target memory location and block sizes.*
* **`transfer_data(self, startAddress, serverBufferSize, memorySize, mau=None)`**
  * **GUI Placement**: Firmware Flasher (Progress loop).
  * **`(i)` Tooltip**: *Sends Service 0x36. Transmits firmware chunks iteratively over the CAN bus to write segments to the ECU's flash memory.*
* **`request_transfer_exit(self)`**
  * **GUI Placement**: Firmware Flasher (Exit/Finalize).
  * **`(i)` Tooltip**: *Sends Service 0x37 to notify the ECU that transmission is complete, triggering final validation.*
* **`parse_data_get_size(self, filename, module)`**
  * **GUI Placement**: Firmware file browser utility.
  * **`(i)` Tooltip**: *Locally parses Intel Hex/S-Record firmware files and returns sector allocations and metadata prior to initiating the download sequence.*
* **`get_data(self, startAddress, endAddress, mau=None)`**
  * **GUI Placement**: Internal memory chunk builder during flashing.
  * **`(i)` Tooltip**: *Extracts raw binaries from hex buffers to arrange block sequences.*

---

## Proposed Changes

We will create the standalone app framework in the active workspace:

### 1. ESP32 Source Code
#### [NEW] [scratch/esp32_can_bridge/esp32_can_bridge.ino](file:///Users/samuel/Desktop/uds-0.0.227-py2.7/scratch/esp32_can_bridge/esp32_can_bridge.ino)
* Core 1: Non-blocking TWAI CAN controller. Core 0: USB Serial, Wi-Fi AP manager, Web portal config, TCP socket, mDNS (`tesladiag.local`), and UDP broadcast listener (discovery).

### 2. UDS Client Bridge
#### [NEW] [uds_bridge.py](file:///Users/samuel/Desktop/uds-0.0.227-py2.7/uds_bridge.py)
* Runs JSON-RPC IPC server in Conda Python 2.7 environment. Coordinates with `uds.client` to execute all 20 listed functions.

#### [NEW] [uds/transport/esp32_transport.py](file:///Users/samuel/Desktop/uds-0.0.227-py2.7/uds/transport/esp32_transport.py)
* Adapts `AbstractTransport` for serial (USB) and TCP socket (Wi-Fi) channels.

### 3. Standalone Desktop GUI
#### [NEW] [gui.py](file:///Users/samuel/Desktop/uds-0.0.227-py2.7/gui.py)
* CustomTkinter app in Python 3. Parses `nodes.json` dynamically and generates dedicated cockpits for each ECU (e.g. BMS, MCU, CHG, GTW) loaded with all 20 UDS functions.

---

## Verification Plan

### Automated Tests
* Create and build Conda:
  ```bash
  CONDA_SUBDIR=osx-64 conda create -y -n uds-py27 python=2.7
  conda run -n uds-py27 pip install pyserial enum34
  ```
* Run a syntax check on all Python components:
  ```bash
  python3 -m py_compile gui.py
  conda run -n uds-py27 python -m py_compile uds_bridge.py
  ```

### Manual Verification
* Upload to ESP32, scan Wi-Fi, run GUI, auto-discover, and verify complete UDS diagnostic suite in simulation and physical loopback mode.
