/**
 * ============================================================================
 * SMART MINI GREENHOUSE MONITORING & CONTROL SYSTEM
 * ============================================================================
 * Target Hardware : All-in-One Trainer Kit ESP32 DevKit V4 (38-Pin)
 * Tujuan          : Project Akhir / UAS Internet of Things (IoT)
 *
 * Pemetaan Komponen Terintegrasi pada PCB Board Anda:
 * - DHT11 (Suhu & RH Udara)          -> GPIO 32
 * - LDR (Intensitas Cahaya)          -> GPIO 39 (ADC1)
 * - Potensiometer (Simulasi Tanah)   -> GPIO 35 (ADC1)
 * - Relay Biru (Pompa Air Irigasi)   -> GPIO 19
 * - Motor Servo SG90 (Ventilasi)     -> GPIO 23
 * - Buzzer (Alarm Kondisi Kritis)    -> GPIO 13
 * - LED1 Merah (Alarm Kritis)        -> GPIO 4
 * - LED2 Kuning (Lampu Grow Light)   -> GPIO 2
 * - LED3 Hijau (Indikator Pompa)     -> GPIO 26
 * - LED4 Biru (Indikator Ventilasi)  -> GPIO 27
 * - Button1 Merah (Mode AUTO/MANUAL) -> GPIO 33
 * - Button2 Kuning (Toggle LED2)     -> GPIO 25
 * - Button3 Hijau (Toggle Relay)     -> GPIO 14
 * - Button4 Biru (Toggle Servo/Fan)  -> GPIO 12
 *
 * Library Wajib (Install lewat Arduino Library Manager):
 * - "DHT sensor library" by Adafruit
 * - "Adafruit Unified Sensor" by Adafruit
 * ============================================================================
 */

#include <WiFi.h>
#include <WebServer.h>
#include <DHT.h>

// ============================================================================
// 1. KONFIGURASI WI-FI JARINGAN LOKAL (SESUAIKAN DENGAN HOTSPOT / ROUTER ANDA)
// ============================================================================
const char* WIFI_SSID     = "NAMA_HOTSPOT_ANDA";
const char* WIFI_PASSWORD = "PASSWORD_HOTSPOT_ANDA";

// ============================================================================
// 2. KONFIGURASI PIN GPIO SESUAI PCB TRAINER KIT ESP32 V4
// ============================================================================
#define PIN_DHT           32   // Sensor DHT11 (Suhu & Kelembapan Udara)
#define DHT_TYPE          DHT11

#define PIN_LDR           39   // Sensor Cahaya LDR (ADC1)
#define PIN_POT_SOIL      35   // Knop Potensiometer sebagai Input Kelembapan Tanah (ADC1)

#define PIN_RELAY         19   // Relay Biru Onboard -> Pompa Air Irigasi
#define PIN_SERVO         23   // Motor Servo SG90 -> Ventilasi Atap Greenhouse
#define PIN_BUZZER        13   // Buzzer Onboard -> Alarm Kondisi Kritis

#define PIN_LED1_RED      4    // LED1 (Merah)  -> Indikator Alarm Kritis (bersama Buzzer)
#define PIN_LED2_YELLOW   2    // LED2 (Kuning) -> Lampu Grow Light (LDR gelap)
#define PIN_LED3_GREEN    26   // LED3 (Hijau)  -> Indikator Pompa Air (mengikuti Relay)
#define PIN_LED4_BLUE     27   // LED4 (Biru)   -> Indikator Pendingin/Ventilasi (mengikuti Servo)

#define PIN_BTN1_MODE     33   // Button1 (Merah)  -> Ganti Mode AUTO / MANUAL
#define PIN_BTN2_GROW     25   // Button2 (Kuning) -> Toggle Grow Light (LED2) di Mode MANUAL
#define PIN_BTN3_PUMP     14   // Button3 (Hijau)  -> Toggle Pompa Air (Relay + LED3) di Mode MANUAL
#define PIN_BTN4_FAN      12   // Button4 (Biru)   -> Toggle Ventilasi (Servo + LED4) di Mode MANUAL

// ============================================================================
// 3. OPSI POLARITAS & KALIBRASI SENSOR BOARD
// ============================================================================
// Ubah ke false jika modul relay aktif pada logika HIGH
#define RELAY_ACTIVE_LOW        false

// Ubah ke true jika LED onboard menyala saat diberi logika LOW
#define LED_ACTIVE_LOW          false

// Ubah ke false jika tombol fisik aktif saat ditekan ke 3.3V (bukan ke GND)
#define BUTTON_ACTIVE_LOW       true

// Ubah ke true jika nilai LDR terbalik (saat ditutup tangan angka justru naik)
#define LDR_INVERTED            false

// Ubah ke true jika putaran Potensiometer (kelembapan tanah) arahnya terbalik
#define POT_INVERTED            false

// true = gunakan Knop Potensiometer (GPIO 35) untuk demo kelembapan tanah real-time
// false = gunakan simulasi penguapan otomatis di firmware
#define USE_POT_AS_SOIL_SENSOR  true

// Sudut Servo SG90 untuk jendela ventilasi greenhouse
#define SERVO_ANGLE_CLOSED      0
#define SERVO_ANGLE_OPEN        90

// ============================================================================
// 4. OBJEK & VARIABEL GLOBAL SISTEM
// ============================================================================
DHT dht(PIN_DHT, DHT_TYPE);
WebServer server(80);

// Data pembacaan sensor terkini
float temperatureC = 28.0;
float humidityAir  = 65.0;
int   lightPercent = 70;
int   soilMoisture = 60;
int   rawLdrAdc    = 0;
int   rawSoilAdc   = 0;
bool  dhtValid     = false;

// Nilai internal simulasi (dipakai hanya jika USE_POT_AS_SOIL_SENSOR == false)
float simulatedSoil = 62.0;

// Ambang batas otomatis (Threshold) - bisa diubah dari Web Dashboard
float threshMaxTemp  = 31.0; // °C
int   threshMinSoil  = 40;   // %
int   threshMinLight = 35;   // %

// Mode Operasi & Status Aktuator
bool isAutoMode     = true;
bool pumpState      = false; // Relay (19) + LED3 Hijau (26)
bool fanState       = false; // Servo (23) + LED4 Biru (27)
bool growLightState = false; // LED2 Kuning (2)
bool buzzerState    = false; // Buzzer (13) + LED1 Merah (4)

int currentServoAngle = -1;

// Status Kondisi Sistem (Poin B.5)
String systemStatus = "NORMAL - Kondisi Greenhouse Ideal";
String alertLevel   = "NORMAL"; // "NORMAL", "ACTIVE", "CRITICAL"

// Pewaktu non-blocking (millis)
unsigned long lastSensorReadMs = 0;
unsigned long lastBuzzerToggleMs = 0;
unsigned long lastSoilSimMs = 0;
bool buzzerTonePhase = false;

// Struktur debounce untuk 4 tombol fisik (Button1 - Button4)
struct DebouncedButton {
  uint8_t pin;
  int lastReading;
  int stableState;
  unsigned long lastChangeMs;
};

const unsigned long DEBOUNCE_DELAY_MS = 60;
DebouncedButton btnMode = { PIN_BTN1_MODE, HIGH, HIGH, 0 };
DebouncedButton btnGrow = { PIN_BTN2_GROW, HIGH, HIGH, 0 };
DebouncedButton btnPump = { PIN_BTN3_PUMP, HIGH, HIGH, 0 };
DebouncedButton btnFan  = { PIN_BTN4_FAN,  HIGH, HIGH, 0 };

// ============================================================================
// 5. HELPER OUTPUT PERANGKAT KERAS (RELAY, LED, BUZZER, SERVO)
// ============================================================================
void writeRelay(bool on) {
  int level = RELAY_ACTIVE_LOW ? (on ? LOW : HIGH) : (on ? HIGH : LOW);
  digitalWrite(PIN_RELAY, level);
}

void writeLed(uint8_t pin, bool on) {
  int level = LED_ACTIVE_LOW ? (on ? LOW : HIGH) : (on ? HIGH : LOW);
  digitalWrite(pin, level);
}

// Menggerakkan Motor Servo SG90 menggunakan pulsa PWM 50 Hz standar (tanpa library tambahan)
// Hanya mengirim pulsa ketika sudut berubah agar tidak bergetar dan tidak menghambat WebServer
void moveServoAngle(int targetAngle) {
  targetAngle = constrain(targetAngle, 0, 180);
  if (targetAngle == currentServoAngle) return;

  currentServoAngle = targetAngle;
  int pulseUs = map(targetAngle, 0, 180, 500, 2400);

  for (int cycle = 0; cycle < 25; cycle++) {
    digitalWrite(PIN_SERVO, HIGH);
    delayMicroseconds(pulseUs);
    digitalWrite(PIN_SERVO, LOW);
    delayMicroseconds(20000 - pulseUs);
    if (cycle % 5 == 0) {
      server.handleClient();
    }
  }
}

void applyHardwareOutputs() {
  writeRelay(pumpState);
  writeLed(PIN_LED3_GREEN, pumpState);      // LED3 (Hijau) mengikuti Relay Pompa
  writeLed(PIN_LED2_YELLOW, growLightState); // LED2 (Kuning) sebagai Grow Light
  writeLed(PIN_LED4_BLUE, fanState);        // LED4 (Biru) mengikuti Ventilasi Servo
  writeLed(PIN_LED1_RED, buzzerState);      // LED1 (Merah) menyala saat Alarm/Kritis

  moveServoAngle(fanState ? SERVO_ANGLE_OPEN : SERVO_ANGLE_CLOSED);

  if (!buzzerState) {
    buzzerTonePhase = false;
    digitalWrite(PIN_BUZZER, LOW);
  }
}

void updateBuzzerPattern() {
  if (!buzzerState) {
    digitalWrite(PIN_BUZZER, LOW);
    return;
  }
  unsigned long now = millis();
  if (now - lastBuzzerToggleMs >= 450) {
    lastBuzzerToggleMs = now;
    buzzerTonePhase = !buzzerTonePhase;
    digitalWrite(PIN_BUZZER, buzzerTonePhase ? HIGH : LOW);
  }
}

// ============================================================================
// 6. PEMBACAAN SENSOR & EVALUASI LOGIKA GREENHOUSE
// ============================================================================
void readSensors() {
  // 1) Baca DHT11 (Suhu & Kelembapan Udara) pada GPIO 32
  float t = dht.readTemperature();
  float h = dht.readHumidity();

  if (!isnan(t) && !isnan(h)) {
    temperatureC = t;
    humidityAir  = h;
    dhtValid     = true;
  } else {
    dhtValid = false;
  }

  // 2) Baca LDR (Intensitas Cahaya 0 - 100%) pada GPIO 39
  long ldrSum = 0;
  for (int i = 0; i < 5; i++) {
    ldrSum += analogRead(PIN_LDR);
    delay(2);
  }
  rawLdrAdc = ldrSum / 5;

  int mappedLight = LDR_INVERTED
                      ? map(rawLdrAdc, 4095, 0, 0, 100)
                      : map(rawLdrAdc, 0, 4095, 0, 100);
  lightPercent = constrain(mappedLight, 0, 100);

  // 3) Baca Potensiometer sebagai Sensor Kelembapan Tanah (GPIO 35) atau Simulasi
  if (USE_POT_AS_SOIL_SENSOR) {
    long soilSum = 0;
    for (int i = 0; i < 5; i++) {
      soilSum += analogRead(PIN_POT_SOIL);
      delay(2);
    }
    rawSoilAdc = soilSum / 5;
    int mappedSoil = POT_INVERTED
                        ? map(rawSoilAdc, 4095, 0, 0, 100)
                        : map(rawSoilAdc, 0, 4095, 0, 100);
    soilMoisture = constrain(mappedSoil, 0, 100);
  } else {
    unsigned long now = millis();
    if (lastSoilSimMs == 0) lastSoilSimMs = now;
    float dtSec = (now - lastSoilSimMs) / 1000.0;
    lastSoilSimMs = now;

    if (pumpState) {
      simulatedSoil += 4.5 * dtSec;
    } else {
      float dryRate = (temperatureC > threshMaxTemp) ? 0.65 : 0.25;
      simulatedSoil -= dryRate * dtSec;
    }
    simulatedSoil = constrain(simulatedSoil, 15.0, 95.0);
    soilMoisture = (int)round(simulatedSoil);
    rawSoilAdc = map(soilMoisture, 0, 100, 0, 4095);
  }
}

void evaluateSystemLogic() {
  bool highTemp   = (temperatureC > threshMaxTemp);
  bool drySoil    = (soilMoisture < threshMinSoil);
  bool lowLight   = (lightPercent < threshMinLight);
  bool severeTemp = (temperatureC >= (threshMaxTemp + 2.0));

  // Pada mode AUTO, seluruh aktuator dikendalikan otomatis oleh pembacaan sensor
  if (isAutoMode) {
    growLightState = lowLight;
    fanState       = highTemp;
    pumpState      = drySoil;
    buzzerState    = (severeTemp || (highTemp && drySoil));
  }

  // Penentuan Status Kondisi Sistem & Alert Level (Poin B.5)
  if (severeTemp || (highTemp && drySoil)) {
    alertLevel = "CRITICAL";
    systemStatus = "KRITIS - Suhu Panas & Tanah Kering";
  } else if (drySoil && lowLight) {
    alertLevel = "ACTIVE";
    systemStatus = "MENYIRAM & GROW LIGHT AKTIF - Tanah Kering & Cahaya Kurang";
  } else if (drySoil) {
    alertLevel = "ACTIVE";
    systemStatus = "MENYIRAM - Tanah Kering";
  } else if (highTemp) {
    alertLevel = "ACTIVE";
    systemStatus = "PENDINGINAN AKTIF - Suhu Tinggi (Ventilasi Servo Terbuka)";
  } else if (lowLight) {
    alertLevel = "ACTIVE";
    systemStatus = "GROW LIGHT AKTIF - Cahaya Kurang";
  } else {
    alertLevel = "NORMAL";
    systemStatus = "NORMAL - Kondisi Greenhouse Ideal";
  }

  if (!isAutoMode && (pumpState || fanState || growLightState || buzzerState) && alertLevel == "NORMAL") {
    alertLevel = "ACTIVE";
    systemStatus = "KONTROL MANUAL AKTIF - Kondisi Lingkungan Ideal";
  }

  applyHardwareOutputs();
}

// ============================================================================
// 7. PENANGANAN 4 TOMBOL FISIK ONBOARD (BUTTON 1 - BUTTON 4)
// ============================================================================
bool isButtonPressedEdge(DebouncedButton& btn) {
  unsigned long now = millis();
  int reading = digitalRead(btn.pin);

  if (reading != btn.lastReading) {
    btn.lastChangeMs = now;
  }
  btn.lastReading = reading;

  if ((now - btn.lastChangeMs) > DEBOUNCE_DELAY_MS) {
    if (reading != btn.stableState) {
      btn.stableState = reading;
      int activeState = BUTTON_ACTIVE_LOW ? LOW : HIGH;
      if (btn.stableState == activeState) {
        return true;
      }
    }
  }
  return false;
}

void handlePhysicalButtons() {
  // Button1 (GPIO 33 - Merah): Ganti Mode AUTO <-> MANUAL
  if (isButtonPressedEdge(btnMode)) {
    isAutoMode = !isAutoMode;
    Serial.printf("[BTN1-33] Mode diubah ke: %s\n", isAutoMode ? "AUTO" : "MANUAL");
    evaluateSystemLogic();
  }

  // Button2 (GPIO 25 - Kuning): Toggle Grow Light (LED2)
  if (isButtonPressedEdge(btnGrow)) {
    isAutoMode = false;
    growLightState = !growLightState;
    Serial.printf("[BTN2-25] Grow Light manual -> %s\n", growLightState ? "ON" : "OFF");
    evaluateSystemLogic();
  }

  // Button3 (GPIO 14 - Hijau): Toggle Pompa Air (Relay + LED3)
  if (isButtonPressedEdge(btnPump)) {
    isAutoMode = false;
    pumpState = !pumpState;
    Serial.printf("[BTN3-14] Pompa Relay manual -> %s\n", pumpState ? "ON" : "OFF");
    evaluateSystemLogic();
  }

  // Button4 (GPIO 12 - Biru): Toggle Ventilasi (Servo + LED4)
  if (isButtonPressedEdge(btnFan)) {
    isAutoMode = false;
    fanState = !fanState;
    Serial.printf("[BTN4-12] Ventilasi Servo manual -> %s\n", fanState ? "OPEN" : "CLOSED");
    evaluateSystemLogic();
  }
}

// ============================================================================
// 8. HELPER PARSING REQUEST & PEMBUAT JSON RESPONSE
// ============================================================================
void sendCorsHeaders() {
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.sendHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  server.sendHeader("Access-Control-Allow-Headers", "Content-Type");
}

bool extractParamValue(const String& key, String& outValue) {
  if (server.hasArg(key)) {
    outValue = server.arg(key);
    return true;
  }
  if (server.hasArg("plain")) {
    String body = server.arg("plain");
    String searchKey = "\"" + key + "\"";
    int idx = body.indexOf(searchKey);
    if (idx < 0) return false;

    int colonIdx = body.indexOf(':', idx + searchKey.length());
    if (colonIdx < 0) return false;

    int start = colonIdx + 1;
    while (start < (int)body.length() && (body[start] == ' ' || body[start] == '\t')) {
      start++;
    }
    if (start >= (int)body.length()) return false;

    if (body[start] == '"') {
      int endQuote = body.indexOf('"', start + 1);
      if (endQuote > start) {
        outValue = body.substring(start + 1, endQuote);
        return true;
      }
    } else {
      int endIdx = start;
      while (endIdx < (int)body.length() && body[endIdx] != ',' && body[endIdx] != '}' && body[endIdx] != ' ') {
        endIdx++;
      }
      outValue = body.substring(start, endIdx);
      outValue.trim();
      return true;
    }
  }
  return false;
}

bool parseBoolStr(const String& val) {
  String v = val;
  v.toLowerCase();
  return (v == "true" || v == "1" || v == "on");
}

String buildStatusJson() {
  String json = "{";
  json += "\"project\":\"Smart Mini Greenhouse Monitoring & Control System\",";
  json += "\"device\":\"Trainer Kit ESP32 DevKit V4 (38-Pin)\",";
  json += "\"connected\":true,";
  json += "\"ip\":\"" + WiFi.localIP().toString() + "\",";
  json += "\"rssi\":" + String(WiFi.RSSI()) + ",";
  json += "\"uptimeSeconds\":" + String(millis() / 1000) + ",";
  json += "\"mode\":\"" + String(isAutoMode ? "AUTO" : "MANUAL") + "\",";
  json += "\"alertLevel\":\"" + alertLevel + "\",";
  json += "\"systemStatus\":\"" + systemStatus + "\",";
  json += "\"dhtValid\":" + String(dhtValid ? "true" : "false") + ",";
  json += "\"soilSource\":\"" + String(USE_POT_AS_SOIL_SENSOR ? "EXTERNAL_ADC" : "SIMULATED") + "\",";
  json += "\"servoAngle\":" + String(currentServoAngle < 0 ? 0 : currentServoAngle) + ",";
  json += "\"sensors\":{";
    json += "\"temperature\":" + String(temperatureC, 1) + ",";
    json += "\"humidity\":" + String(humidityAir, 1) + ",";
    json += "\"light\":" + String(lightPercent) + ",";
    json += "\"soil\":" + String(soilMoisture) + ",";
    json += "\"rawLdr\":" + String(rawLdrAdc) + ",";
    json += "\"rawSoil\":" + String(rawSoilAdc);
  json += "},";
  json += "\"actuators\":{";
    json += "\"pump\":" + String(pumpState ? "true" : "false") + ",";
    json += "\"fan\":" + String(fanState ? "true" : "false") + ",";
    json += "\"growLight\":" + String(growLightState ? "true" : "false") + ",";
    json += "\"buzzer\":" + String(buzzerState ? "true" : "false");
  json += "},";
  json += "\"thresholds\":{";
    json += "\"maxTemp\":" + String(threshMaxTemp, 1) + ",";
    json += "\"minSoil\":" + String(threshMinSoil) + ",";
    json += "\"minLight\":" + String(threshMinLight);
  json += "}";
  json += "}";
  return json;
}

// ============================================================================
// 9. HANDLER ENDPOINT WEB SERVER
// ============================================================================
void handleOptions() {
  sendCorsHeaders();
  server.send(204);
}

void handleRoot() {
  sendCorsHeaders();
  String html = R"rawliteral(
<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Smart Mini Greenhouse - ESP32</title>
  <style>
    body { font-family: system-ui, sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding: 20px; }
    .wrap { max-width: 720px; margin: 0 auto; }
    .card { background: #1e293b; border-radius: 12px; padding: 16px; margin-bottom: 14px; border: 1px solid #334155; }
    h1 { margin: 0 0 6px; font-size: 1.35rem; color: #4ade80; }
    .status { padding: 10px 14px; border-radius: 8px; font-weight: 600; margin: 12px 0; background: #064e3b; color: #a7f3d0; }
    .status.ACTIVE { background: #78350f; color: #fde68a; }
    .status.CRITICAL { background: #7f1d1d; color: #fecaca; }
    .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
    .metric { background: #0f172a; padding: 12px; border-radius: 8px; }
    .label { font-size: 0.85rem; color: #94a3b8; }
    .val { font-size: 1.5rem; font-weight: 700; margin-top: 4px; }
    .btns { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
    button { cursor: pointer; border: none; border-radius: 8px; padding: 10px 14px; font-weight: 600; background: #334155; color: #fff; }
    button.on { background: #16a34a; }
    small { color: #94a3b8; }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <h1>Smart Mini Greenhouse (ESP32 V4)</h1>
      <small id="meta">Memuat status perangkat...</small>
      <div id="sysStatus" class="status">Menunggu data...</div>
      <div class="grid">
        <div class="metric"><div class="label">Suhu Udara (DHT11)</div><div class="val" id="t">-- &deg;C</div></div>
        <div class="metric"><div class="label">Kelembapan Udara (DHT11)</div><div class="val" id="h">-- % RH</div></div>
        <div class="metric"><div class="label">Cahaya (LDR)</div><div class="val" id="l">-- %</div></div>
        <div class="metric"><div class="label">Kelembapan Tanah (Pot)</div><div class="val" id="s">-- %</div></div>
      </div>
    </div>
    <div class="card">
      <div><strong>Kontrol Aktuator</strong> &mdash; Mode: <span id="mode">AUTO</span></div>
      <div class="btns">
        <button onclick="toggleMode()">Ganti Mode (AUTO/MANUAL)</button>
        <button id="bPump" onclick="toggleAct('pump')">Pompa (Relay 19 + LED3)</button>
        <button id="bFan" onclick="toggleAct('fan')">Ventilasi (Servo 23 + LED4)</button>
        <button id="bGrow" onclick="toggleAct('growLight')">Grow Light (LED2)</button>
        <button id="bBuzz" onclick="toggleAct('buzzer')">Buzzer (13 + LED1)</button>
      </div>
      <p><small>Tip: Buka <code>web-dashboard/index.html</code> di laptop Anda dan masukkan IP ESP32 ini untuk tampilan grafik lengkap.</small></p>
    </div>
  </div>
  <script>
    let state = null;
    async function load() {
      const r = await fetch('/api/status');
      state = await r.json();
      document.getElementById('t').innerHTML = state.sensors.temperature + ' &deg;C';
      document.getElementById('h').textContent = state.sensors.humidity + ' % RH';
      document.getElementById('l').textContent = state.sensors.light + ' %';
      document.getElementById('s').textContent = state.sensors.soil + ' %';
      const st = document.getElementById('sysStatus');
      st.textContent = state.systemStatus;
      st.className = 'status ' + state.alertLevel;
      document.getElementById('mode').textContent = state.mode;
      document.getElementById('meta').textContent = 'Terhubung (' + state.ip + ') | Pembaruan: ' + new Date().toLocaleTimeString();
      document.getElementById('bPump').className = state.actuators.pump ? 'on' : '';
      document.getElementById('bFan').className = state.actuators.fan ? 'on' : '';
      document.getElementById('bGrow').className = state.actuators.growLight ? 'on' : '';
      document.getElementById('bBuzz').className = state.actuators.buzzer ? 'on' : '';
    }
    async function toggleMode() {
      if (!state) return;
      const next = state.mode === 'AUTO' ? 'MANUAL' : 'AUTO';
      await fetch('/api/control?mode=' + next, { method: 'POST' });
      load();
    }
    async function toggleAct(key) {
      if (!state) return;
      const val = !state.actuators[key];
      await fetch('/api/control?mode=MANUAL&' + key + '=' + val, { method: 'POST' });
      load();
    }
    load();
    setInterval(load, 2000);
  </script>
</body>
</html>
)rawliteral";
  server.send(200, "text/html", html);
}

void handleApiStatus() {
  sendCorsHeaders();
  server.send(200, "application/json", buildStatusJson());
}

void handleApiControl() {
  sendCorsHeaders();
  String val;

  if (extractParamValue("mode", val)) {
    val.toUpperCase();
    isAutoMode = (val == "AUTO");
  }

  if (extractParamValue("pump", val)) {
    isAutoMode = false;
    pumpState = parseBoolStr(val);
  }
  if (extractParamValue("fan", val)) {
    isAutoMode = false;
    fanState = parseBoolStr(val);
  }
  if (extractParamValue("growLight", val)) {
    isAutoMode = false;
    growLightState = parseBoolStr(val);
  }
  if (extractParamValue("buzzer", val)) {
    isAutoMode = false;
    buzzerState = parseBoolStr(val);
  }

  evaluateSystemLogic();
  server.send(200, "application/json", buildStatusJson());
}

void handleApiThreshold() {
  sendCorsHeaders();
  String val;

  if (extractParamValue("maxTemp", val)) {
    float parsed = val.toFloat();
    if (parsed >= 15.0 && parsed <= 50.0) threshMaxTemp = parsed;
  }
  if (extractParamValue("minSoil", val)) {
    int parsed = val.toInt();
    if (parsed >= 5 && parsed <= 95) threshMinSoil = parsed;
  }
  if (extractParamValue("minLight", val)) {
    int parsed = val.toInt();
    if (parsed >= 5 && parsed <= 95) threshMinLight = parsed;
  }

  evaluateSystemLogic();
  server.send(200, "application/json", buildStatusJson());
}

// ============================================================================
// 10. SETUP & LOOP UTAMA
// ============================================================================
void connectToWiFi() {
  Serial.println();
  Serial.print("Menghubungkan ke Wi-Fi: ");
  Serial.println(WIFI_SSID);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  bool blinkPhase = false;
  unsigned long startAttempt = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - startAttempt < 20000) {
    blinkPhase = !blinkPhase;
    writeLed(PIN_LED4_BLUE, blinkPhase); // LED4 biru berkedip saat mencari Wi-Fi
    delay(300);
    Serial.print(".");
  }

  writeLed(PIN_LED4_BLUE, false);

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[OK] Wi-Fi Terhubung!");
    Serial.print("[OK] IP Address ESP32 : ");
    Serial.println(WiFi.localIP());
    // Kedip cepat 2x pada LED3 Hijau tanda Wi-Fi siap
    for (int i = 0; i < 2; i++) {
      writeLed(PIN_LED3_GREEN, true); delay(120);
      writeLed(PIN_LED3_GREEN, false); delay(120);
    }
  } else {
    Serial.println("\n[PERINGATAN] Gagal terhubung ke Wi-Fi. Akan mencoba ulang otomatis di loop.");
  }
}

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("\n=== SMART MINI GREENHOUSE ESP32 V4 STARTING ===");

  // Konfigurasi pin output aktuator
  pinMode(PIN_RELAY, OUTPUT);
  pinMode(PIN_SERVO, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  pinMode(PIN_LED1_RED, OUTPUT);
  pinMode(PIN_LED2_YELLOW, OUTPUT);
  pinMode(PIN_LED3_GREEN, OUTPUT);
  pinMode(PIN_LED4_BLUE, OUTPUT);

  // Pastikan seluruh aktuator mati & servo tertutup saat startup awal
  writeRelay(false);
  writeLed(PIN_LED1_RED, false);
  writeLed(PIN_LED2_YELLOW, false);
  writeLed(PIN_LED3_GREEN, false);
  writeLed(PIN_LED4_BLUE, false);
  digitalWrite(PIN_BUZZER, LOW);
  digitalWrite(PIN_SERVO, LOW);

  // Konfigurasi 4 tombol fisik onboard
  uint8_t btnModeType = BUTTON_ACTIVE_LOW ? INPUT_PULLUP : INPUT;
  int idleState = BUTTON_ACTIVE_LOW ? HIGH : LOW;

  pinMode(PIN_BTN1_MODE, btnModeType);
  pinMode(PIN_BTN2_GROW, btnModeType);
  pinMode(PIN_BTN3_PUMP, btnModeType);
  pinMode(PIN_BTN4_FAN,  btnModeType);

  btnMode.lastReading = idleState; btnMode.stableState = idleState;
  btnGrow.lastReading = idleState; btnGrow.stableState = idleState;
  btnPump.lastReading = idleState; btnPump.stableState = idleState;
  btnFan.lastReading  = idleState; btnFan.stableState  = idleState;

  // Resolusi ADC ESP32 (0 - 4095)
  analogReadResolution(12);

  // Inisialisasi sensor DHT11
  dht.begin();

  // Posisi awal servo tertutup (0 derajat)
  moveServoAngle(SERVO_ANGLE_CLOSED);

  // Koneksi ke Wi-Fi lokal
  connectToWiFi();

  // Daftarkan routing Web Server & API
  server.on("/", HTTP_GET, handleRoot);
  server.on("/api/status", HTTP_GET, handleApiStatus);
  server.on("/api/status", HTTP_OPTIONS, handleOptions);
  server.on("/api/control", HTTP_POST, handleApiControl);
  server.on("/api/control", HTTP_GET, handleApiControl);
  server.on("/api/control", HTTP_OPTIONS, handleOptions);
  server.on("/api/threshold", HTTP_POST, handleApiThreshold);
  server.on("/api/threshold", HTTP_GET, handleApiThreshold);
  server.on("/api/threshold", HTTP_OPTIONS, handleOptions);
  server.onNotFound([]() {
    if (server.method() == HTTP_OPTIONS) {
      handleOptions();
    } else {
      sendCorsHeaders();
      server.send(404, "application/json", "{\"error\":\"Endpoint tidak ditemukan\"}");
    }
  });

  server.begin();
  Serial.println("[OK] HTTP Web Server berjalan di Port 80.");

  // Pembacaan sensor awal
  readSensors();
  evaluateSystemLogic();
}

void loop() {
  server.handleClient();
  handlePhysicalButtons();
  updateBuzzerPattern();

  unsigned long now = millis();

  // Pantau koneksi Wi-Fi
  if (WiFi.status() != WL_CONNECTED) {
    static unsigned long lastReconnectMs = 0;
    if (now - lastReconnectMs > 10000) {
      lastReconnectMs = now;
      connectToWiFi();
    }
  }

  // Baca sensor & perbarui logika tiap 2 detik (2000 ms)
  if (now - lastSensorReadMs >= 2000) {
    lastSensorReadMs = now;
    readSensors();
    evaluateSystemLogic();

    Serial.printf(
      "[SENSOR] Suhu: %.1f C | RH: %.1f%% | Cahaya(LDR39): %d%% (ADC:%d) | Tanah(Pot35): %d%% | Servo: %d deg | Mode: %s | Status: %s\n",
      temperatureC, humidityAir, lightPercent, rawLdrAdc, soilMoisture,
      currentServoAngle, isAutoMode ? "AUTO" : "MANUAL", systemStatus.c_str()
    );
  }
}
