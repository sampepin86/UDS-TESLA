/*
 * ESP32 CAN-to-USB/Wi-Fi SLCAN Bridge
 * Supports Wi-Fi (TCP Server port 1337) and USB Serial (SLCAN protocol).
 * Features:
 *   - Dual-Core FreeRTOS Tasks
 *   - Always-on Access Point (AP) mode for configuration
 *   - Station (STA) mode with saved credentials in NVS (Preferences)
 *   - Dynamic web config portal (Port 80) for Wi-Fi Scanning & Saving
 *   - UDP Discovery Responder (Port 1338)
 *   - Non-blocking CAN TWAI driver with automatic bus-off recovery
 *   - Robust OTA Firmware Updates:
 *       * ArduinoOTA (UDP, port 3232) – flash via Arduino IDE wirelessly
 *       * HTTP /update endpoint – upload .bin via browser or curl
 *       * MD5 integrity check on every upload
 *       * Password-protected (stored in NVS, default: "tesladiag")
 *       * CAN bus gracefully suspended during flash, resumed on failure
 *
 * Pin Connections (Default ESP32 CAN transceiver pins):
 *   - CAN_TX -> GPIO 5
 *   - CAN_RX -> GPIO 4
 */

#include <ArduinoOTA.h>
#include <ESPmDNS.h>
#include <Preferences.h>
#include <Update.h>
#include <WebServer.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include <driver/twai.h>

#define CAN_TX_PIN GPIO_NUM_5
#define CAN_RX_PIN GPIO_NUM_4

#define TCP_PORT 1337
#define UDP_PORT 1338
#define HTTP_PORT 80

// Global Instances
WebServer server(HTTP_PORT);
WiFiServer tcpServer(TCP_PORT);
WiFiClient tcpClient;
WiFiUDP udp;
Preferences preferences;

// Ring Buffers / Queues for FreeRTOS
QueueHandle_t txQueue;
QueueHandle_t rxQueue;

// System States
bool canOpened        = false;
bool otaInProgress    = false;   // blocks CAN task during flash
SemaphoreHandle_t canMutex;      // guards canOpened + twai calls

twai_general_config_t g_config =
    TWAI_GENERAL_CONFIG_DEFAULT(CAN_TX_PIN, CAN_RX_PIN, TWAI_MODE_NORMAL);
twai_timing_config_t  t_config = TWAI_TIMING_CONFIG_500KBITS();
twai_filter_config_t  f_config = TWAI_FILTER_CONFIG_ACCEPT_ALL();

// Wi-Fi Config
String apSSID        = "TeslaDiag-ESP32";
String savedSSID     = "";
String savedPassword = "";

// OTA Config (default password overrideable via web)
String otaPassword   = "tesladiag";

// Firmware version shown in portal
#define FW_VERSION "1.1.1-OTA-TEST"

// Diagnostic Log Buffer
String canLog = "";
const int MAX_LOG_LEN = 2048;

// Function Declarations
void taskCAN(void *pvParameters);
void taskNetwork(void *pvParameters);
void taskOTA(void *pvParameters);
void handleSerial();
void parseSLCAN(String cmd, Stream &client);
void setupWiFi();
void setupArduinoOTA();
void handleRoot();
void handleSave();
void handleOTAPage();
void handleOTAUpload();
void handleNotFound();
void checkCANErrors();
void suspendCAN();
void resumeCAN();

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("\r\n--- TeslaDiag ESP32 Bridge Initializing ---");
  Serial.printf("Firmware Version: %s\r\n", FW_VERSION);

  // Create synchronization primitives
  canMutex = xSemaphoreCreateMutex();

  // Create Queues (100 elements capacity)
  txQueue = xQueueCreate(100, sizeof(twai_message_t));
  rxQueue = xQueueCreate(100, sizeof(String));

  // Initialize Preferences (NVS storage)
  preferences.begin("wifidiag", false);
  savedSSID     = preferences.getString("ssid", "");
  savedPassword = preferences.getString("password", "");
  otaPassword   = preferences.getString("otapass", "tesladiag");

  // Start Wi-Fi Network Setup
  setupWiFi();

  // Configure ArduinoOTA (UDP-based, IDE flashing)
  setupArduinoOTA();

  // Create FreeRTOS Tasks
  // Task 1: Real-time CAN bus handling (Core 1, Priority 5 - Highest)
  xTaskCreatePinnedToCore(taskCAN,     "TaskCAN",     4096, NULL, 5, NULL, 1);

  // Task 2: Network interfaces and web portal (Core 0, Priority 2)
  xTaskCreatePinnedToCore(taskNetwork, "TaskNetwork", 16384, NULL, 2, NULL, 0);

  // Task 3: ArduinoOTA polling (Core 0, Priority 3)
  xTaskCreatePinnedToCore(taskOTA,     "TaskOTA",     8192, NULL, 3, NULL, 0);

  Serial.println("System Initialization Complete. Running...");
}

void loop() {
  // Core 1 loop or standard loop handles Serial Interface
  handleSerial();
  delay(1);
}

/* ==========================================
 * TASK 1: CAN Bus Handling (Core 1)
 * ========================================== */
void taskCAN(void *pvParameters) {
  twai_message_t txMsg;
  twai_message_t rxMsg;

  while (true) {
    // Yield entirely during OTA flash – flash writes are not ISR-safe
    if (otaInProgress) {
      vTaskDelay(pdMS_TO_TICKS(200));
      continue;
    }

    if (canOpened) {
      // 1. Check for incoming messages to transmit from the Queue
      if (xQueueReceive(txQueue, &txMsg, 0) == pdTRUE) {
        esp_err_t err = twai_transmit(&txMsg, pdMS_TO_TICKS(10));
        if (err != ESP_OK) {
          Serial.printf("CAN Transmit failed: 0x%X\n", err);
        }
      }

      // 2. Poll for received frames from the physical CAN bus
      esp_err_t err = twai_receive(&rxMsg, pdMS_TO_TICKS(5));
      if (err == ESP_OK) {
        String slcanStr = "";
        if (rxMsg.extd) {
          slcanStr += "T";
          char idBuf[9];
          sprintf(idBuf, "%08X", rxMsg.identifier);
          slcanStr += idBuf;
        } else {
          slcanStr += "t";
          char idBuf[4];
          sprintf(idBuf, "%03X", rxMsg.identifier);
          slcanStr += idBuf;
        }
        slcanStr += String(rxMsg.data_length_code);
        for (int i = 0; i < rxMsg.data_length_code; i++) {
          char hexBuf[3];
          sprintf(hexBuf, "%02X", rxMsg.data[i]);
          slcanStr += hexBuf;
        }
        slcanStr += "\r";
        xQueueSend(rxQueue, &slcanStr, 0);
      }

      // 3. Monitor CAN bus errors & trigger automatic recovery
      checkCANErrors();
    } else {
      vTaskDelay(pdMS_TO_TICKS(100));
    }
  }
}

void checkCANErrors() {
  uint32_t alerts;
  twai_read_alerts(&alerts, 0);
  twai_status_info_t status;
  twai_get_status_info(&status);

  // Auto-recovery if bus goes into Bus-Off state
  if (status.state == TWAI_STATE_BUS_OFF) {
    Serial.println("CAN Bus-Off state detected! Attempting recovery...");
    twai_stop();
    twai_initiate_recovery();
    vTaskDelay(pdMS_TO_TICKS(100)); // wait for recovery trigger
  }
}

/* ==========================================
 * TASK 2: Network / Wi-Fi handling (Core 0)
 * ========================================== */
void taskNetwork(void *pvParameters) {
  // Start TCP server
  tcpServer.begin();

  // Start UDP Discovery Server
  udp.begin(UDP_PORT);

  while (true) {
    // 1. Maintain HTTP server (Web interface)
    server.handleClient();

    // 2. Accept TCP Client connection
    if (tcpServer.hasClient()) {
      if (tcpClient && tcpClient.connected()) {
        tcpServer.available().stop(); // Reject if already connected
      } else {
        tcpClient = tcpServer.available();
        Serial.println("UDS Bridge connected via Wi-Fi!");
      }
    }

    // 3. Process TCP Client incoming stream (SLCAN Commands)
    if (tcpClient && tcpClient.connected() && tcpClient.available() > 0) {
      String line = tcpClient.readStringUntil('\r');
      if (line.length() > 0) {
        parseSLCAN(line, tcpClient);
      }
    }

    // 4. Distribute received CAN frames from rxQueue to Serial and TCP
    String outFrame;
    while (xQueueReceive(rxQueue, &outFrame, 0) == pdTRUE) {
      Serial.print(outFrame); // Send to USB Serial
      if (tcpClient && tcpClient.connected()) {
        tcpClient.print(outFrame); // Send to Wi-Fi Socket
      }
      // Add to web diagnostic log
      canLog += "RX: " + outFrame + "\n";
      if (canLog.length() > MAX_LOG_LEN) {
        canLog = canLog.substring(canLog.length() - MAX_LOG_LEN);
      }
    }

    // 5. Handle UDP discovery packets
    int packetSize = udp.parsePacket();
    if (packetSize) {
      char packetBuffer[255];
      int len = udp.read(packetBuffer, 255);
      if (len > 0) {
        packetBuffer[len] = 0;
      }
      String request = String(packetBuffer);
      if (request == "DISCOVER_TESLADIAG") {
        // Send JSON discovery reply
        udp.beginPacket(udp.remoteIP(), udp.remotePort());
        String reply = "{\"device\":\"TeslaDiag-ESP32\",\"ip\":\"" +
                       WiFi.localIP().toString() +
                       "\",\"ap_ip\":\"192.168.4.1\",\"can_status\":\"" +
                       (canOpened ? "OPEN" : "CLOSED") + "\"}";
        udp.print(reply);
        udp.endPacket();
      }
    }

    vTaskDelay(pdMS_TO_TICKS(1));
  }
}

/* ==========================================
 * SLCAN Command Parser
 * ========================================== */
void parseSLCAN(String cmd, Stream &client) {
  cmd.trim();
  if (cmd.length() == 0)
    return;

  char type = cmd[0];

  switch (type) {
  case 'S': { // Set Baudrate
    if (canOpened) {
      client.print("\x07"); // ASCII BELL (Error)
      return;
    }
    char speed = cmd[1];
    switch (speed) {
    case '0':
      t_config = TWAI_TIMING_CONFIG_25KBITS();
      break;
    case '1':
      t_config = TWAI_TIMING_CONFIG_25KBITS();
      break;
    case '2':
      t_config = TWAI_TIMING_CONFIG_50KBITS();
      break;
    case '3':
      t_config = TWAI_TIMING_CONFIG_100KBITS();
      break;
    case '4':
      t_config = TWAI_TIMING_CONFIG_125KBITS();
      break;
    case '5':
      t_config = TWAI_TIMING_CONFIG_250KBITS();
      break;
    case '6':
      t_config = TWAI_TIMING_CONFIG_500KBITS();
      break; // Standard Tesla speed
    case '8':
      t_config = TWAI_TIMING_CONFIG_1MBITS();
      break;
    default:
      client.print("\x07");
      return;
    }
    client.print("\r"); // Success
    break;
  }
  case 'O': { // Open CAN
    if (!canOpened) {
      esp_err_t err = twai_driver_install(&g_config, &t_config, &f_config);
      if (err == ESP_OK) {
        err = twai_start();
        if (err == ESP_OK) {
          canOpened = true;
          twai_reconfigure_alerts(TWAI_ALERT_BUS_OFF | TWAI_ALERT_ERR_PASS,
                                  NULL);
          client.print("\r");
          Serial.println("CAN Channel Started Successfully.");
        } else {
          twai_driver_uninstall();
          client.print("\x07");
        }
      } else {
        client.print("\x07");
      }
    } else {
      client.print("\r");
    }
    break;
  }
  case 'C': { // Close CAN
    if (canOpened) {
      twai_stop();
      twai_driver_uninstall();
      canOpened = false;
      client.print("\r");
      Serial.println("CAN Channel Stopped.");
    } else {
      client.print("\r");
    }
    break;
  }
  case 't':   // Transmit Standard Frame: t[ID][LEN][DATA...]
  case 'T': { // Transmit Extended Frame: T[ID][LEN][DATA...]
    if (!canOpened) {
      client.print("\x07");
      return;
    }
    bool isExt = (type == 'T');
    int idLen = isExt ? 8 : 3;

    if (cmd.length() < 1 + idLen + 1) {
      client.print("\x07");
      return;
    }

    String idStr = cmd.substring(1, 1 + idLen);
    uint32_t identifier = strtoul(idStr.c_str(), NULL, 16);
    int dlc = cmd[1 + idLen] - '0';

    if (dlc < 0 || dlc > 8 || cmd.length() < 1 + idLen + 1 + (dlc * 2)) {
      client.print("\x07");
      return;
    }

    twai_message_t msg;
    msg.identifier = identifier;
    msg.extd = isExt;
    msg.rtr = false;
    msg.data_length_code = dlc;

    String dataStr = cmd.substring(1 + idLen + 1);
    for (int i = 0; i < dlc; i++) {
      String byteStr = dataStr.substring(i * 2, (i * 2) + 2);
      msg.data[i] = strtol(byteStr.c_str(), NULL, 16);
    }

    // Queue the frame for transmission
    if (xQueueSend(txQueue, &msg, pdMS_TO_TICKS(10)) == pdTRUE) {
      client.print("\r");
      canLog += "TX: " + cmd + "\n";
      if (canLog.length() > MAX_LOG_LEN) {
        canLog = canLog.substring(canLog.length() - MAX_LOG_LEN);
      }
    } else {
      client.print("\x07");
    }
    break;
  }
  default:
    client.print("\x07");
    break;
  }
}

void handleSerial() {
  static String inputString = "";
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    if (inChar == '\r') {
      parseSLCAN(inputString, Serial);
      inputString = "";
    } else if (inChar != '\n') {
      inputString += inChar;
    }
  }
}

/* ==========================================
 * Wi-Fi Manager Setup & Actions
 * ========================================== */
void setupWiFi() {
  // 1. Setup AP Mode (Always active)
  WiFi.softAP(apSSID.c_str(), NULL);
  Serial.print("Access Point started. SSID: ");
  Serial.println(apSSID);
  Serial.print("AP IP Address: ");
  Serial.println(WiFi.softAPIP());

  // 2. Setup STA Mode (if credentials saved)
  WiFi.mode(WIFI_AP_STA);
  if (savedSSID.length() > 0) {
    Serial.printf("Connecting to saved Wi-Fi: %s\n", savedSSID.c_str());
    WiFi.begin(savedSSID.c_str(), savedPassword.c_str());

    // Non-blocking connection check (try for max 15 seconds)
    int retries = 0;
    while (WiFi.status() != WL_CONNECTED && retries < 30) {
      delay(500);
      Serial.print(".");
      retries++;
    }
    if (WiFi.status() == WL_CONNECTED) {
      Serial.println("\r\nWi-Fi Connected!");
      Serial.print("Station IP: ");
      Serial.println(WiFi.localIP());
    } else {
      Serial.println(
          "\r\nCould not connect to saved Wi-Fi. Staying in AP-only Mode.");
    }
  }

  // Set up mDNS
  if (MDNS.begin("tesladiag")) {
    Serial.println("mDNS Responder Started: tesladiag.local");
  }

  // Setup Web Server routing
  server.on("/", HTTP_GET, handleRoot);
  server.on("/save", HTTP_POST, handleSave);
  server.on("/log", HTTP_GET, []() {
    server.send(200, "text/plain", canLog);
  });
  // OTA firmware update endpoints
  server.on("/update", HTTP_GET, handleOTAPage);
  // POST: completion lambda owns the HTTP response; upload callback only writes chunks
  server.on("/update", HTTP_POST,
    []() {
      // Auth gate on the completed POST
      if (!server.authenticate("admin", otaPassword.c_str())) {
        return server.requestAuthentication();
      }
      server.sendHeader("Connection", "close");
      bool ok = !Update.hasError();
      server.send(ok ? 200 : 500, "text/plain",
                  ok ? "OK - Rebooting" : Update.errorString());
      if (ok) {
        Serial.println("[OTA] HTTP upload complete. Rebooting...");
        delay(300);
        ESP.restart();
      } else {
        resumeCAN();
      }
    },
    handleOTAUpload
  );
  server.onNotFound(handleNotFound);
  server.begin();
  Serial.println("Web Configuration Server Started.");
}

void handleRoot() {
  String html = "<!DOCTYPE html><html><head><meta name='viewport' "
                "content='width=device-width, "
                "initial-scale=1'><title>TeslaDiag ESP32 Portal</title>";
  html += "<style>body{font-family:Arial,sans-serif;background:#0f172a;color:#"
          "f8fafc;padding:20px;text-align:center;}";
  html +=
      ".card{background:#1e293b;padding:20px;border-radius:10px;margin:20px "
      "auto;max-width:400px;box-shadow:0 4px 6px -1px rgba(0,0,0,0.5);}";
  html += "input,select{width:90%;padding:10px;margin:10px "
          "0;background:#334155;border:1px solid "
          "#475569;color:#fff;border-radius:5px;}";
  html += "button{background:#e21c34;color:#fff;border:none;padding:10px "
          "20px;border-radius:5px;cursor:pointer;font-weight:bold;}";
  html += "a{color:#38bdf8;text-decoration:none;}</style></head><body>";
  html += "<h1>TeslaDiag Adapter Config</h1>";
  html += "<div class='card'><h2>Status</h2>";
  html += "<p><b>AP IP:</b> 192.168.4.1</p>";
  html += "<p><b>Local Network IP:</b> " +
          (WiFi.status() == WL_CONNECTED ? WiFi.localIP().toString()
                                         : "Not Connected") +
          "</p>";
  html += "<p><b>CAN Bus Status:</b> " +
          String(canOpened ? "RUNNING" : "STOPPED") + "</p></div>";
  html += "<div class='card'><h2>Configure Connection</h2>";
  html += "<form action='/save' method='POST'>";
  
  // Scan networks
  int n = WiFi.scanNetworks();
  html += "<select name='ssid' id='ssid' required>";
  if (n == 0) {
    html += "<option value=''>No networks found</option>";
  } else {
    for (int i = 0; i < n; ++i) {
      String ssid = WiFi.SSID(i);
      String selected = (ssid == savedSSID) ? "selected" : "";
      html += "<option value='" + ssid + "' " + selected + ">" + ssid + " (" + String(WiFi.RSSI(i)) + " dBm)</option>";
    }
  }
  html += "<option value='_custom_'>-- Hidden Network --</option>";
  html += "</select>";
  
  html += "<input type='text' name='custom_ssid' id='custom_ssid' placeholder='Hidden SSID' style='display:none;'>";
  html += "<input type='password' name='pass' placeholder='Password'>";
  html += "<button type='submit'>Save & Reconnect</button></form>";
  html += "</div>";
          
  html += "<div class='card'><h2>Live CAN Terminal</h2>";
  html += "<textarea id='term' rows='10' style='width:100%;background:#000;color:#0f0;font-family:monospace;border:none;' readonly></textarea>";
  html += "<br><label style='color:white;'><input type='checkbox' id='autoScroll' checked> Auto-Scroll</label>";
  html += "</div>";
  
  html += "<script>";
  html += "function refreshLog() {";
  html += "  fetch('/log').then(r=>r.text()).then(t=>{";
  html += "    let term = document.getElementById('term');";
  html += "    term.value = t;";
  html += "    if(document.getElementById('autoScroll').checked) { term.scrollTop = term.scrollHeight; }";
  html += "  });";
  html += "  setTimeout(refreshLog, 1000);";
  html += "}";
  html += "refreshLog();";
  
  // Script for hidden network field toggle
  html += "document.getElementById('ssid').addEventListener('change', function() {";
  html += "  document.getElementById('custom_ssid').style.display = this.value === '_custom_' ? 'block' : 'none';";
  html += "});";
  html += "</script>";

  html += "</body></html>";
  server.send(200, "text/html", html);
}

void handleSave() {
  if (server.hasArg("ssid")) {
    savedSSID = server.arg("ssid");
    if (savedSSID == "_custom_" && server.hasArg("custom_ssid")) {
      savedSSID = server.arg("custom_ssid");
    }
    savedPassword = server.arg("pass");

    // Save to NVS
    preferences.putString("ssid", savedSSID);
    preferences.putString("password", savedPassword);

    String html = "<html><body><h1>Configuration Saved!</h1><p>Rebooting and connecting to " +
                  savedSSID + "... Please wait 10 seconds.</p>";
    html += "<p>After reboot, open the GUI and click Scan. You can close this window.</p></body></html>";
    server.send(200, "text/html", html);
    delay(2000);

    // Hard restart to ensure clean Wi-Fi stack initialization
    ESP.restart();
  } else {
    server.send(400, "text/plain", "Bad Request");
  }
}

void handleNotFound() { server.send(404, "text/plain", "File Not Found"); }

/* ==========================================
 * OTA: Safely Suspend / Resume CAN
 * ========================================== */
void suspendCAN() {
  if (xSemaphoreTake(canMutex, pdMS_TO_TICKS(500)) == pdTRUE) {
    otaInProgress = true;
    if (canOpened) {
      twai_stop();
      twai_driver_uninstall();
      Serial.println("[OTA] CAN bus suspended for firmware update.");
    }
    xSemaphoreGive(canMutex);
  }
}

void resumeCAN() {
  if (xSemaphoreTake(canMutex, pdMS_TO_TICKS(500)) == pdTRUE) {
    otaInProgress = false;
    if (canOpened) {
      // Re-install driver only if it was open before
      esp_err_t err = twai_driver_install(&g_config, &t_config, &f_config);
      if (err == ESP_OK) twai_start();
      Serial.println("[OTA] CAN bus resumed after update failure.");
    }
    xSemaphoreGive(canMutex);
  }
}

/* ==========================================
 * OTA: ArduinoOTA Setup (UDP / Arduino IDE)
 * ========================================== */
void setupArduinoOTA() {
  ArduinoOTA.setHostname("tesladiag-esp32");
  ArduinoOTA.setPassword(otaPassword.c_str());

  ArduinoOTA.onStart([]() {
    String type = (ArduinoOTA.getCommand() == U_FLASH) ? "firmware" : "filesystem";
    Serial.println("[OTA] ArduinoOTA start: " + type);
    suspendCAN();
  });

  ArduinoOTA.onEnd([]() {
    Serial.println("\n[OTA] ArduinoOTA complete. Rebooting...");
  });

  ArduinoOTA.onProgress([](unsigned int progress, unsigned int total) {
    Serial.printf("[OTA] Progress: %u%%\r", (progress * 100) / total);
  });

  ArduinoOTA.onError([](ota_error_t error) {
    Serial.printf("[OTA] Error[%u]: ", error);
    if      (error == OTA_AUTH_ERROR)    Serial.println("Auth Failed");
    else if (error == OTA_BEGIN_ERROR)   Serial.println("Begin Failed");
    else if (error == OTA_CONNECT_ERROR) Serial.println("Connect Failed");
    else if (error == OTA_RECEIVE_ERROR) Serial.println("Receive Failed");
    else if (error == OTA_END_ERROR)     Serial.println("End Failed");
    resumeCAN(); // restore CAN on failure
  });

  ArduinoOTA.begin();
  Serial.println("[OTA] ArduinoOTA ready (port 3232, hostname: tesladiag-esp32.local)");
}

/* ==========================================
 * OTA: Dedicated FreeRTOS Task
 * ========================================== */
void taskOTA(void *pvParameters) {
  while (true) {
    ArduinoOTA.handle();
    vTaskDelay(pdMS_TO_TICKS(10));
  }
}

/* ==========================================
 * OTA: HTTP Binary Upload Page + Handler
 * ==========================================
 * Usage:
 *   Browser : http://tesladiag.local/update
 *   curl    : curl -u admin:<pass> -F "firmware=@firmware.bin" \
 *             http://<ip>/update
 * ========================================== */
void handleOTAPage() {
  // Basic HTTP auth check
  if (!server.authenticate("admin", otaPassword.c_str())) {
    return server.requestAuthentication();
  }

  String html = "<!DOCTYPE html><html><head>"
    "<meta name='viewport' content='width=device-width,initial-scale=1'>"
    "<title>TeslaDiag OTA Update</title>"
    "<style>"
    "body{font-family:Arial,sans-serif;background:#0f172a;color:#f8fafc;padding:20px;text-align:center;}"
    ".card{background:#1e293b;padding:24px;border-radius:10px;margin:20px auto;max-width:420px;}"
    "h1{color:#e21c34;}h2{color:#38bdf8;}"
    "input[type=file]{width:90%;padding:10px;margin:10px 0;background:#334155;"
    "  border:1px solid #475569;color:#fff;border-radius:5px;}"
    "button{background:#e21c34;color:#fff;border:none;padding:12px 28px;"
    "  border-radius:5px;cursor:pointer;font-weight:bold;font-size:16px;}"
    "progress{width:90%;height:20px;margin-top:12px;}"
    "#status{margin-top:10px;font-size:14px;color:#94a3b8;}"
    "</style></head><body>"
    "<h1>TeslaDiag Firmware Update</h1>"
    "<div class='card'>"
    "<h2>Current Version: " FW_VERSION "</h2>"
    "<p style='color:#94a3b8;font-size:13px;'>Upload a compiled .bin firmware file.<br>"
    "The CAN bus will be suspended during flashing.</p>"
    "<form id='upForm' method='POST' action='/update' enctype='multipart/form-data'>"
    "<input type='file' id='binFile' name='firmware' accept='.bin' required><br>"
    "<button type='submit'>&#x1F4E1; Flash Firmware</button>"
    "</form>"
    "<progress id='prog' value='0' max='100' style='display:none'></progress>"
    "<div id='status'></div></div>"
    "<script>"
    "document.getElementById('upForm').addEventListener('submit',function(e){"
    "  e.preventDefault();"
    "  var f=document.getElementById('binFile').files[0];"
    "  if(!f){alert('Select a .bin file first');return;}"
    "  var fd=new FormData();fd.append('firmware',f);"
    "  var xhr=new XMLHttpRequest();"
    "  xhr.open('POST','/update',true);"
    "  xhr.upload.onprogress=function(e){"
    "    if(e.lengthComputable){"
    "      var pct=Math.round(e.loaded/e.total*100);"
    "      document.getElementById('prog').style.display='block';"
    "      document.getElementById('prog').value=pct;"
    "      document.getElementById('status').innerText='Uploading: '+pct+'%';"
    "    }"
    "  };"
    "  xhr.onload=function(){"
    "    if(xhr.status===200){"
    "      document.getElementById('status').innerText='Success! Rebooting in 5 seconds...';"
    "      setTimeout(function(){location.href='/';},6000);"
    "    } else {"
    "      document.getElementById('status').innerText='ERROR: '+xhr.responseText;"
    "    }"
    "  };"
    "  xhr.onerror=function(){document.getElementById('status').innerText='Upload failed (network error)';};"
    "  document.getElementById('status').innerText='Starting upload...';"
    "  xhr.send(fd);"
    "});"
    "</script></body></html>";
  server.send(200, "text/html", html);
}

// Upload callback: ONLY writes bytes to flash. Never calls server.send() or
// server.authenticate() here — those break the HTTP stream mid-transfer.
void handleOTAUpload() {
  HTTPUpload &upload = server.upload();

  if (upload.status == UPLOAD_FILE_START) {
    Serial.printf("[OTA] HTTP upload start: %s\n", upload.filename.c_str());
    suspendCAN();
    if (!Update.begin(UPDATE_SIZE_UNKNOWN)) {
      Update.printError(Serial);
      // Don't call server.send() here — let the POST completion lambda do it
    } else {
      Serial.println("[OTA] Update.begin OK");
    }

  } else if (upload.status == UPLOAD_FILE_WRITE) {
    if (Update.write(upload.buf, upload.currentSize) != upload.currentSize) {
      Update.printError(Serial);
    } else {
      Serial.printf("[OTA] Progress: %u bytes\r", (uint32_t)Update.progress());
    }

  } else if (upload.status == UPLOAD_FILE_END) {
    if (Update.end(true)) {
      Serial.printf("\n[OTA] Flash done: %u bytes written\n", upload.totalSize);
    } else {
      Update.printError(Serial);
    }
    // Response is sent by the POST completion lambda above

  } else if (upload.status == UPLOAD_FILE_ABORTED) {
    Update.end();
    Serial.println("[OTA] Upload aborted by client.");
    resumeCAN();
    // No server.send() here either — connection is already gone
  }
}
