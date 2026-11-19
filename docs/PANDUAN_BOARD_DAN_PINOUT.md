# Panduan Board & Pinout — All-in-One Trainer Kit ESP32 V4 (38-Pin)

Dokumen ini berisi pemetaan **100% sesuai nomor pin GPIO yang tercetak pada papan PCB Trainer Kit ESP32 V4** Anda, lengkap dengan panduan cara mendemokan setiap komponen untuk project **Smart Mini Greenhouse**.

> **Keunggulan Board Anda:** Seluruh sensor, resistor, LED, tombol, Relay, Buzzer, hingga Servo **sudah tersolder terintegrasi di dalam PCB**. Anda tidak memerlukan breadboard maupun kabel jumper tambahan—cukup colokkan kabel data Micro-USB ke laptop!

---

## 1. Pemetaan Lengkap Pin GPIO pada PCB Anda

| Komponen pada Board | Lokasi di Papan PCB | Pin GPIO | Peran di Smart Greenhouse |
| :--- | :--- | :---: | :--- |
| **Sensor `DHT11`** | Kiri atas (sensor biru) | **`GPIO 32`** | Mengukur **Suhu Udara (`°C`)** & **Kelembapan Udara (`% RH`)** |
| **Sensor `LDR`** | Di atas modul ESP32, sebelah tombol merah | **`GPIO 39`** | Mengukur **Intensitas Cahaya (`%`)** |
| **Knop `Potensiometer`** | Putaran hitam kiri atas | **`GPIO 35`** | **Input/Simulator Kelembapan Tanah (`0–100%`)** saat demo |
| **Modul `Relay` Biru** | Kiri tengah (dekat terminal hijau) | **`GPIO 19`** | Saklar **Pompa Air Irigasi** (berbunyi *"klik"* saat aktif) |
| **Motor `Servo SG90`** | Pojok kanan atas | **`GPIO 23`** | Penggerak **Ventilasi Atap Greenhouse** (`0°` tutup ↔ `90°` buka) |
| **`Buzzer` Hitam** | Pojok kiri bawah | **`GPIO 13`** | **Alarm Peringatan** kondisi kritis |
| **`LED1` (Merah)** | Tengah papan (baris atas) | **`GPIO 4`** | Indikator **Alarm Kondisi Kritis** (selaras dengan Buzzer) |
| **`LED2` (Kuning)** | Tengah papan | **`GPIO 2`** | Lampu **Grow Light** (menyala saat LDR gelap `< 35%`) |
| **`LED3` (Hijau)** | Tengah papan | **`GPIO 26`** | Indikator **Pompa Air Aktif** (selaras dengan Relay `GPIO 19`) |
| **`LED4` (Biru)** | Tengah papan (baris bawah) | **`GPIO 27`** | Indikator **Ventilasi Pendingin** (selaras dengan Servo `GPIO 23`) |
| **`Button1` (Merah)** | Kiri bawah (tombol 1) | **`GPIO 33`** | Ganti Mode **`AUTO` ↔ `MANUAL`** |
| **`Button2` (Kuning)** | Kiri bawah (tombol 2) | **`GPIO 25`** | Kontrol manual **Grow Light (`LED2`)** |
| **`Button3` (Hijau)** | Kiri bawah (tombol 3) | **`GPIO 14`** | Kontrol manual **Pompa Air (`Relay 19` + `LED3`)** |
| **`Button4` (Biru)** | Kiri bawah (tombol 4) | **`GPIO 12`** | Kontrol manual **Ventilasi (`Servo 23` + `LED4`)** |
| **Sensor `PIR HC-SR501`** | Kanan tengah (kubah putih) | `GPIO 34` | Tersedia di board (opsional pengembangan deteksi hama/orang) |
| **Layar `OLED 0.96"` & `BME280`** | Kanan atas & tengah | `SDA 21`, `SCL 22` | Tersedia di jalur `I2C` board |

---

## 2. Pengaturan Penting di Kode Firmware (`.ino`)

Buka file [smart_greenhouse_esp32.ino](../firmware/smart_greenhouse_esp32/smart_greenhouse_esp32.ino). Jika saat diuji ada arah komponen yang terbalik, ubah opsi di bagian atas kode:

1. **Relay menyala terus saat kondisi normal / terbalik:**
   ```cpp
   #define RELAY_ACTIVE_LOW true // Ubah antara true atau false sesuai reaksi Relay papan
   ```
2. **Arah putaran Potensiometer (Kelembapan Tanah) terbalik:**
   ```cpp
   #define POT_INVERTED true
   ```
3. **Nilai cahaya LDR terbalik (saat ditutup tangan malah naik ke `100%`):**
   ```cpp
   #define LDR_INVERTED true
   ```
4. **Tombol `Button1–Button4` tidak merespons atau tertekan terus:**
   ```cpp
   #define BUTTON_ACTIVE_LOW false
   ```

> **Catatan Penting saat Upload (`GPIO 12` & `GPIO 2`):**
> Jangan menekan tombol **`Button4` (Biru / `GPIO 12`)** saat proses *Upload* program atau saat menyalakan ulang ESP32, karena `GPIO 12` merupakan salah satu pin *strapping/boot* ESP32. Dalam kondisi tidak ditekan, `GPIO 12` aman digunakan sebagai tombol input.

---

## 3. Cara Instalasi & Upload di Arduino IDE

1. Buka **Arduino IDE** dan pastikan **Board Package ESP32** (*esp32 by Espressif Systems*) sudah terpasang.
2. Pilih menu **Tools → Board → ESP32 Arduino → ESP32 Dev Module**.
3. Install 2 library wajib melalui **Sketch → Include Library → Manage Libraries...**:
   * **`DHT sensor library`** (oleh *Adafruit*)
   * **`Adafruit Unified Sensor`** (oleh *Adafruit*)
4. Buka [smart_greenhouse_esp32.ino](../firmware/smart_greenhouse_esp32/smart_greenhouse_esp32.ino), lalu ubah `WIFI_SSID` dan `WIFI_PASSWORD` sesuai dengan **Hotspot HP / Wi-Fi Lokal** Anda.
5. Colokkan kabel Micro-USB ke port ESP32, pilih **Port COM** yang muncul, lalu klik **Upload**.
6. Buka **Serial Monitor** (kecepatan **`115200` baud**). Jika muncul pesan `[OK] Wi-Fi Terhubung!`, catat **IP Address ESP32** yang tampil (contoh: `192.168.43.105`).
7. Buka [index.html](../web-dashboard/index.html) di browser laptop/HP yang tersambung ke Hotspot yang sama, klik **Live ESP32 (Wi-Fi Lokal)**, masukkan IP tersebut, lalu klik **Hubungkan**.

---

## 4. Skenario Demo di Depan Dosen (Tinggal Putar & Tutup!)

Saat presentasi UAS, Anda cukup melakukan gerakan sederhana berikut di papan **Trainer Kit ESP32 V4**:

1. **Demo Pencahayaan Otomatis (`LDR 39` → `LED2 Kuning`):**
   * Tutup sensor **LDR** dengan jari → persentase cahaya di Web Dashboard turun (`< 35%`), **`LED2` Kuning (Grow Light)** langsung menyala, dan status web berubah menjadi **`GROW LIGHT AKTIF - Cahaya Kurang`**.
2. **Demo Irigasi Otomatis (`Potensiometer 35` → `Relay 19` + `LED3 Hijau`):**
   * Putar knop **Potensiometer** hingga nilai Kelembapan Tanah di bawah `40%` → **Relay Biru** berbunyi *"KLIK"*, **`LED3` Hijau** menyala, dan status web berubah menjadi **`MENYIRAM - Tanah Kering`**.
3. **Demo Ventilasi Suhu Panas (`DHT11 32` → `Servo 23` + `LED4 Biru`):**
   * Hembuskan udara hangat ke sensor biru **DHT11** hingga suhu melewati `31.0 °C` → **Motor Servo (`GPIO 23`)** langsung berputar `90°` membuka ventilasi, **`LED4` Biru** menyala, dan status web menjadi **`PENDINGINAN AKTIF - Suhu Tinggi`**.
4. **Demo Alarm Kritis (`Buzzer 13` + `LED1 Merah`):**
   * Naikkan suhu `> 31 °C` sambil memutar Potensiometer ke kondisi kering (`< 40%`) → banner Web Dashboard berubah **Merah (`KRITIS`)**, **`LED1` Merah** menyala, dan **`Buzzer`** berbunyi peringatan.
5. **Demo Kontrol Manual (Web & Tombol Fisik):**
   * Klik mode **`MANUAL`** di Web Dashboard (atau tekan **`Button1` Merah**), lalu nyalakan/matikan Relay, Servo, Grow Light, atau Buzzer langsung dari layar Web atau memakai **`Button2`**, **`Button3`**, dan **`Button4`**.
