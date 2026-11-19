# Smart Mini Greenhouse Monitoring & Control System (ESP32)

Project Akhir UAS Internet of Things (IoT) berbasis **Development Board IoT ESP32 DevKitC V4 (Starter IoT)** dengan antarmuka **Web Dashboard** lokal (berjalan tanpa memerlukan koneksi internet).

---

## Struktur Project

```text
Project_IoT_2/
├── firmware/
│   └── smart_greenhouse_esp32/
│       └── smart_greenhouse_esp32.ino                # Program ESP32 + HTTP Web Server + REST API
├── web-dashboard/
│   ├── index.html                                    # Antarmuka Web Dashboard (Monitoring, Kontrol & Simulator)
│   ├── style.css                                     # Desain UI responsif tema Greenhouse
│   └── app.js                                        # Logika polling API ESP32, grafik Canvas offline, & Mode Simulasi
├── docs/
│   ├── assets/                                       # Foto board, diagram blok, flowchart, & screenshot UI
│   ├── PANDUAN_BOARD_DAN_PINOUT.md                   # Cara cek GPIO board Trainer Kit ESP32 V4 & setup Arduino IDE
│   ├── PRD_SMART_GREENHOUSE.md                       # Product Requirements Document (PRD)
│   ├── DRAFT_LAPORAN_UAS.md                          # Draft laporan lengkap sesuai syarat tugas UAS
│   ├── generate_report_docx.py                       # Script generator diagram & laporan Word (.docx)
│   └── Laporan_Project_Akhir_IoT_Smart_Greenhouse.docx # Dokumen laporan akhir siap kumpul
└── README.md
```

---

## Cara Menggunakan

### 1. Uji Coba Antarmuka Web Dashboard (Langsung di Browser)
Anda dapat langsung melihat dan menguji seluruh fungsi antarmuka **sebelum** mengunggah program ke ESP32:
1. Buka file [web-dashboard/index.html](web-dashboard/index.html) langsung di browser (Chrome / Edge).
2. Pastikan berada di **Mode Simulasi (Tanpa Alat)**.
3. Coba tombol skenario preset (*Kondisi Ideal*, *Siang Terik*, *Malam Hari*, *Tanah Kering*, *Kondisi Kritis*) atau geser slider sensor untuk melihat perubahan status banner, grafik *real-time*, dan respons aktuator otomatis/manual.

### 2. Upload Program ke Board ESP32 DevKitC V4
1. Ikuti panduan instalasi library (`DHT sensor library` & `Adafruit Unified Sensor`) serta verifikasi label GPIO PCB di [docs/PANDUAN_BOARD_DAN_PINOUT.md](docs/PANDUAN_BOARD_DAN_PINOUT.md).
2. Buka [firmware/smart_greenhouse_esp32/smart_greenhouse_esp32.ino](firmware/smart_greenhouse_esp32/smart_greenhouse_esp32.ino).
3. Ganti `WIFI_SSID` dan `WIFI_PASSWORD` dengan nama dan sandi **Hotspot HP / Wi-Fi Lokal** Anda.
4. Upload ke board ESP32, lalu buka **Serial Monitor (`115200` baud)** untuk mencatat **IP Address ESP32** (misal `192.168.43.105`).

### 3. Hubungkan Web Dashboard ke ESP32 Asli
1. Hubungkan laptop/HP ke jaringan Hotspot/Wi-Fi yang **sama** dengan ESP32.
2. Buka [web-dashboard/index.html](web-dashboard/index.html), klik **Live ESP32 (Wi-Fi Lokal)**, masukkan IP Address ESP32, lalu klik **Hubungkan**.
3. *(Alternatif)* Anda juga bisa membuka langsung `http://<IP_ESP32>/` dari browser HP untuk mengakses halaman web ringan yang tersimpan di dalam memori ESP32.

---

## Checklist Demonstrasi UAS (Sesuai Soal Project Akhir)

- [ ] **Koneksi Jaringan:** ESP32 terhubung ke Hotspot/Wi-Fi lokal (`LED4 Biru` berkedip saat mencari Wi-Fi, `LED3 Hijau` berkedip 2x saat siap) dan badge web menunjukkan `TERHUBUNG KE ESP32`.
- [ ] **Pembacaan Sensor Berubah:**
  - Tutup sensor **LDR (`GPIO 39`)** dengan jari → persentase cahaya turun (`< 35%`) → **`LED2` Kuning (`GPIO 2` - Grow Light)** menyala.
  - Putar knop **Potensiometer (`GPIO 35`)** ke nilai `< 40%` → **`Relay` (`GPIO 19` - Pompa Air)** berbunyi *"klik"* + **`LED3` Hijau (`GPIO 26`)** menyala.
  - Dekatkan sumber hangat / hembuskan napas ke **DHT11 (`GPIO 32`)** → suhu naik `> 31.0 °C` → **Motor `Servo SG90` (`GPIO 23`)** membuka ventilasi ke `90°` + **`LED4` Biru (`GPIO 27`)** menyala.
  - Buat suhu `>= 33.0 °C` (atau suhu `> 31.0 °C` & tanah `< 40%`) → **`Buzzer` (`GPIO 13`)** berbunyi *beep* + **`LED1` Merah (`GPIO 4`)** menyala dan status web menjadi `KRITIS`.
- [ ] **Data Terkirim & Status Sesuai:** Nilai sensor + satuan, banner *Status Kondisi Sistem*, posisi sudut Servo (`0°`/`90°`), serta *Waktu Pembaruan Terakhir* diperbarui otomatis tiap 2 detik.
- [ ] **Kendali Aktuator:** Mode `AUTO` merespons sensor secara otomatis, dan Mode `MANUAL` dapat menyalakan/mematikan **Relay Pompa (`19`)**, **Servo Ventilasi (`23`)**, **LED2 Grow Light (`2`)**, dan **Buzzer (`13`)** dari Web Dashboard maupun 4 tombol fisik **`Button1` (`33`)**, **`Button2` (`25`)**, **`Button3` (`14`)**, dan **`Button4` (`12`)**.
