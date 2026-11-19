(() => {
  "use strict";

  const POLL_INTERVAL_MS = 2000;
  const MAX_HISTORY = 25;

  const PRESETS = {
    ideal: { temperature: 28.0, humidity: 65, light: 75, soil: 62 },
    hot: { temperature: 32.5, humidity: 50, light: 90, soil: 55 },
    dark: { temperature: 24.5, humidity: 78, light: 15, soil: 68 },
    dry: { temperature: 29.5, humidity: 56, light: 70, soil: 25 },
    critical: { temperature: 35.0, humidity: 42, light: 85, soil: 22 },
  };

  // State aplikasi
  const urlParams = new URLSearchParams(window.location.search);
  const presetParam = urlParams.get("preset");
  const demoConnParam = urlParams.get("demoConn");
  const hasUrlPreset = Boolean(presetParam && PRESETS[presetParam]);
  const initialDemoEsp = demoConnParam === "esp";

  const state = {
    source: hasUrlPreset || initialDemoEsp ? "SIM" : localStorage.getItem("gh_source") || "SIM", // "SIM" | "ESP"
    espIp: initialDemoEsp ? "192.168.43.105" : localStorage.getItem("gh_esp_ip") || "192.168.43.100",
    demoConnEsp: initialDemoEsp,
    connected: true,
    mode: "AUTO",
    alertLevel: "NORMAL",
    systemStatus: "NORMAL - Kondisi Greenhouse Ideal",
    soilSource: initialDemoEsp ? "EXTERNAL_ADC" : "SIMULATED",
    servoAngle: 0,
    deviceLabel: initialDemoEsp ? "IP: 192.168.43.105 | RSSI: -54 dBm" : "Virtual ESP32 (Demo)",
    sensors: hasUrlPreset ? { ...PRESETS[presetParam] } : { ...PRESETS.ideal },
    actuators: {
      pump: false,
      fan: false,
      growLight: false,
      buzzer: false,
    },
    thresholds: {
      maxTemp: 31.0,
      minSoil: 40,
      minLight: 35,
    },
    history: [],
  };

  let pollTimer = null;
  let isEditingThreshold = false;

  // Referensi elemen DOM
  const el = {
    connectionBadge: document.getElementById("connectionBadge"),
    connectionText: document.getElementById("connectionText"),
    lastUpdateText: document.getElementById("lastUpdateText"),
    deviceInfoText: document.getElementById("deviceInfoText"),

    btnSourceSim: document.getElementById("btnSourceSim"),
    btnSourceEsp: document.getElementById("btnSourceEsp"),
    espConnectForm: document.getElementById("espConnectForm"),
    espIpInput: document.getElementById("espIpInput"),

    statusBanner: document.getElementById("statusBanner"),
    statusIcon: document.getElementById("statusIcon"),
    systemStatusText: document.getElementById("systemStatusText"),
    currentModeBadge: document.getElementById("currentModeBadge"),

    valTemp: document.getElementById("valTemp"),
    valHum: document.getElementById("valHum"),
    valLight: document.getElementById("valLight"),
    valSoil: document.getElementById("valSoil"),
    barTemp: document.getElementById("barTemp"),
    barHum: document.getElementById("barHum"),
    barLight: document.getElementById("barLight"),
    barSoil: document.getElementById("barSoil"),
    noteTemp: document.getElementById("noteTemp"),
    noteLight: document.getElementById("noteLight"),
    noteSoil: document.getElementById("noteSoil"),
    soilSourceTag: document.getElementById("soilSourceTag"),

    btnModeAuto: document.getElementById("btnModeAuto"),
    btnModeManual: document.getElementById("btnModeManual"),
    modeHint: document.getElementById("modeHint"),

    btnActPump: document.getElementById("btnActPump"),
    btnActFan: document.getElementById("btnActFan"),
    btnActGrow: document.getElementById("btnActGrow"),
    btnActBuzzer: document.getElementById("btnActBuzzer"),
    servoAngleText: document.getElementById("servoAngleText"),
    led4Indicator: document.getElementById("led4Indicator"),

    thresholdForm: document.getElementById("thresholdForm"),
    inpMaxTemp: document.getElementById("inpMaxTemp"),
    inpMinSoil: document.getElementById("inpMinSoil"),
    inpMinLight: document.getElementById("inpMinLight"),

    simulatorPanel: document.getElementById("simulatorPanel"),
    simBadgeState: document.getElementById("simBadgeState"),
    simTemp: document.getElementById("simTemp"),
    simHum: document.getElementById("simHum"),
    simLight: document.getElementById("simLight"),
    simSoil: document.getElementById("simSoil"),
    simTempLabel: document.getElementById("simTempLabel"),
    simHumLabel: document.getElementById("simHumLabel"),
    simLightLabel: document.getElementById("simLightLabel"),
    simSoilLabel: document.getElementById("simSoilLabel"),

    sensorChart: document.getElementById("sensorChart"),
  };

  // =========================================================================
  // LOGIKA EVALUASI SIMULASI (SAMA PERSIS DENGAN FIRMWARE ESP32)
  // =========================================================================
  function evaluateSimulationLogic() {
    const { temperature, light, soil } = state.sensors;
    const { maxTemp, minSoil, minLight } = state.thresholds;

    const highTemp = temperature > maxTemp;
    const drySoil = soil < minSoil;
    const lowLight = light < minLight;
    const severeTemp = temperature >= maxTemp + 2.0;

    if (state.mode === "AUTO") {
      state.actuators.growLight = lowLight;
      state.actuators.fan = highTemp;
      state.actuators.pump = drySoil;
      state.actuators.buzzer = severeTemp || (highTemp && drySoil);
    }
    state.servoAngle = state.actuators.fan ? 90 : 0;

    if (severeTemp || (highTemp && drySoil)) {
      state.alertLevel = "CRITICAL";
      state.systemStatus = "KRITIS - Suhu Panas & Tanah Kering";
    } else if (drySoil && lowLight) {
      state.alertLevel = "ACTIVE";
      state.systemStatus = "MENYIRAM & GROW LIGHT AKTIF - Tanah Kering & Cahaya Kurang";
    } else if (drySoil) {
      state.alertLevel = "ACTIVE";
      state.systemStatus = "MENYIRAM - Tanah Kering";
    } else if (highTemp) {
      state.alertLevel = "ACTIVE";
      state.systemStatus = "PENDINGINAN AKTIF - Suhu Tinggi (Ventilasi Servo Terbuka)";
    } else if (lowLight) {
      state.alertLevel = "ACTIVE";
      state.systemStatus = "GROW LIGHT AKTIF - Cahaya Kurang";
    } else {
      state.alertLevel = "NORMAL";
      state.systemStatus = "NORMAL - Kondisi Greenhouse Ideal";
    }

    const anyActuatorOn =
      state.actuators.pump ||
      state.actuators.fan ||
      state.actuators.growLight ||
      state.actuators.buzzer;

    if (state.mode === "MANUAL" && anyActuatorOn && state.alertLevel === "NORMAL") {
      state.alertLevel = "ACTIVE";
      state.systemStatus = "KONTROL MANUAL AKTIF - Kondisi Lingkungan Ideal";
    }
  }

  // =========================================================================
  // KOMUNIKASI API ESP32 (WI-FI LOKAL)
  // =========================================================================
  function getEspBaseUrl() {
    const cleanIp = state.espIp.trim().replace(/^https?:\/\//i, "").replace(/\/+$/, "");
    return `http://${cleanIp}`;
  }

  async function fetchEspStatus() {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 1700);

    try {
      const response = await fetch(`${getEspBaseUrl()}/api/status`, {
        signal: controller.signal,
        cache: "no-store",
      });
      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      state.connected = true;
      state.mode = data.mode || "AUTO";
      state.alertLevel = data.alertLevel || "NORMAL";
      state.systemStatus = data.systemStatus || "NORMAL - Kondisi Greenhouse Ideal";
      state.soilSource = data.soilSource || "SIMULATED";
      state.deviceLabel = `IP: ${data.ip || state.espIp} | RSSI: ${data.rssi ?? "--"} dBm`;

      if (data.sensors) {
        state.sensors.temperature = Number(data.sensors.temperature ?? 0);
        state.sensors.humidity = Number(data.sensors.humidity ?? 0);
        state.sensors.light = Number(data.sensors.light ?? 0);
        state.sensors.soil = Number(data.sensors.soil ?? 0);
      }

      if (data.actuators) {
        state.actuators.pump = Boolean(data.actuators.pump);
        state.actuators.fan = Boolean(data.actuators.fan);
        state.actuators.growLight = Boolean(data.actuators.growLight);
        state.actuators.buzzer = Boolean(data.actuators.buzzer);
      }
      state.servoAngle = Number(data.servoAngle ?? (state.actuators.fan ? 90 : 0));

      if (data.thresholds && !isEditingThreshold) {
        state.thresholds.maxTemp = Number(data.thresholds.maxTemp ?? 31.0);
        state.thresholds.minSoil = Number(data.thresholds.minSoil ?? 40);
        state.thresholds.minLight = Number(data.thresholds.minLight ?? 35);
      }

      recordHistoryPoint();
      render();
    } catch (_err) {
      clearTimeout(timeoutId);
      state.connected = false;
      state.deviceLabel = `Gagal menjangkau ${state.espIp}`;
      renderConnectionStatusOnly();
    }
  }

  async function sendEspControl(params) {
    const query = new URLSearchParams(params).toString();
    try {
      const response = await fetch(`${getEspBaseUrl()}/api/control?${query}`, {
        method: "POST",
      });
      if (response.ok) {
        await fetchEspStatus();
      }
    } catch (_err) {
      state.connected = false;
      renderConnectionStatusOnly();
    }
  }

  async function sendEspThresholds(params) {
    const query = new URLSearchParams(params).toString();
    try {
      const response = await fetch(`${getEspBaseUrl()}/api/threshold?${query}`, {
        method: "POST",
      });
      if (response.ok) {
        await fetchEspStatus();
      }
    } catch (_err) {
      state.connected = false;
      renderConnectionStatusOnly();
    }
  }

  // =========================================================================
  // RIWAYAT & GRAFIK REAL-TIME (HTML5 CANVAS OFFLINE)
  // =========================================================================
  function formatTimeNow() {
    const now = new Date();
    return now.toLocaleTimeString("id-ID", { hour12: false });
  }

  function recordHistoryPoint() {
    state.history.push({
      time: formatTimeNow(),
      temperature: state.sensors.temperature,
      humidity: state.sensors.humidity,
      light: state.sensors.light,
      soil: state.sensors.soil,
    });
    if (state.history.length > MAX_HISTORY) {
      state.history.shift();
    }
  }

  function seedHistoryPoints() {
    state.history = [];
    const base = state.sensors;
    const nowMs = Date.now();
    const offsets = [
      { t: -0.4, h: 1.5, l: -3, s: 2 },
      { t: -0.3, h: 1.0, l: -2, s: 1 },
      { t: -0.2, h: 0.8, l: -1, s: 2 },
      { t: -0.3, h: 1.2, l: 2, s: 1 },
      { t: -0.1, h: 0.5, l: 1, s: 0 },
      { t: 0.1, h: -0.4, l: -2, s: 1 },
      { t: 0.2, h: -0.6, l: -1, s: -1 },
      { t: 0.1, h: -0.2, l: 2, s: 1 },
      { t: -0.1, h: 0.3, l: 1, s: 0 },
      { t: 0.2, h: -0.5, l: -1, s: -1 },
      { t: 0.1, h: -0.2, l: 1, s: 0 },
      { t: 0.0, h: 0.0, l: 0, s: 0 },
    ];
    offsets.forEach((off, idx) => {
      const ts = new Date(nowMs - (offsets.length - 1 - idx) * POLL_INTERVAL_MS);
      state.history.push({
        time: ts.toLocaleTimeString("id-ID", { hour12: false }),
        temperature: Number(Math.max(0, Math.min(100, base.temperature + off.t)).toFixed(1)),
        humidity: Number(Math.max(0, Math.min(100, base.humidity + off.h)).toFixed(1)),
        light: Math.round(Math.max(0, Math.min(100, base.light + off.l))),
        soil: Math.round(Math.max(0, Math.min(100, base.soil + off.s))),
      });
    });
  }

  function drawChart() {
    const canvas = el.sensorChart;
    if (!canvas) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) return;

    canvas.width = Math.floor(rect.width * dpr);
    canvas.height = Math.floor(rect.height * dpr);

    const ctx = canvas.getContext("2d");
    ctx.scale(dpr, dpr);

    const width = rect.width;
    const height = rect.height;
    const pad = { top: 18, right: 30, bottom: 28, left: 36 };
    const plotW = width - pad.left - pad.right;
    const plotH = height - pad.top - pad.bottom;

    ctx.clearRect(0, 0, width, height);

    // Grid horizontal & label sumbu Y (0 - 100)
    ctx.strokeStyle = "rgba(148, 163, 184, 0.14)";
    ctx.fillStyle = "#94a3b8";
    ctx.font = "11px Segoe UI, sans-serif";
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";

    for (let v = 0; v <= 100; v += 20) {
      const y = pad.top + plotH - (v / 100) * plotH;
      ctx.beginPath();
      ctx.moveTo(pad.left, y);
      ctx.lineTo(width - pad.right, y);
      ctx.stroke();
      ctx.fillText(String(v), pad.left - 8, y);
    }

    const pts = state.history;
    if (pts.length === 0) return;

    // Label waktu sumbu X
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    const stepX = pts.length > 1 ? plotW / (pts.length - 1) : plotW;
    const labelEvery = Math.max(1, Math.ceil(pts.length / 5));

    pts.forEach((p, i) => {
      if (i % labelEvery === 0 || i === pts.length - 1) {
        const x = pts.length === 1 ? pad.left + plotW / 2 : pad.left + i * stepX;
        ctx.fillText(p.time, x, pad.top + plotH + 8);
      }
    });

    const seriesList = [
      { key: "temperature", color: "#fb923c" },
      { key: "humidity", color: "#38bdf8" },
      { key: "light", color: "#facc15" },
      { key: "soil", color: "#4ade80" },
    ];

    seriesList.forEach(({ key, color }) => {
      ctx.strokeStyle = color;
      ctx.lineWidth = 2.4;
      ctx.lineJoin = "round";
      ctx.lineCap = "round";
      ctx.beginPath();

      pts.forEach((p, i) => {
        const val = Math.max(0, Math.min(100, p[key]));
        const x = pts.length === 1 ? pad.left + plotW / 2 : pad.left + i * stepX;
        const y = pad.top + plotH - (val / 100) * plotH;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.stroke();

      // Titik data terbaru
      const last = pts[pts.length - 1];
      const lx = pts.length === 1 ? pad.left + plotW / 2 : pad.left + (pts.length - 1) * stepX;
      const ly = pad.top + plotH - (Math.max(0, Math.min(100, last[key])) / 100) * plotH;
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(lx, ly, 3.8, 0, Math.PI * 2);
      ctx.fill();
    });
  }

  // =========================================================================
  // RENDER ANTARMUKA PENGGUNA
  // =========================================================================
  function renderConnectionStatusOnly() {
    el.connectionBadge.className = "conn-badge";
    if (state.source === "SIM" && !state.demoConnEsp) {
      el.connectionBadge.classList.add("sim");
      el.connectionText.textContent = "MODE SIMULASI";
      el.led4Indicator.className = "act-badge on";
      el.led4Indicator.textContent = "SIMULASI";
    } else if (state.connected) {
      el.connectionBadge.classList.add("online");
      el.connectionText.textContent = "TERHUBUNG KE ESP32";
      el.led4Indicator.className = "act-badge on";
      el.led4Indicator.textContent = "ONLINE";
    } else {
      el.connectionBadge.classList.add("offline");
      el.connectionText.textContent = "TERPUTUS";
      el.led4Indicator.className = "act-badge off";
      el.led4Indicator.textContent = "OFFLINE";
    }

    el.deviceInfoText.textContent = state.deviceLabel;
  }

  function updateActuatorButton(button, isOn, isAlert = false) {
    button.classList.toggle("on", isOn);
    button.classList.toggle("alert", isAlert);
    const label = button.querySelector(".act-state");
    if (label) label.textContent = isOn ? "ON" : "OFF";
  }

  function render() {
    renderConnectionStatusOnly();

    el.lastUpdateText.textContent = formatTimeNow();
    const isEspUi = state.source === "ESP" || state.demoConnEsp;
    el.btnSourceSim.classList.toggle("active", !isEspUi);
    el.btnSourceEsp.classList.toggle("active", isEspUi);

    // Simulator panel visual state
    const isSim = state.source === "SIM" && !state.demoConnEsp;
    el.simulatorPanel.classList.toggle("disabled", !isSim);
    el.simBadgeState.textContent = isSim
      ? "Aktif di Mode Simulasi"
      : "Nonaktif saat Live ESP32 (Gunakan sensor fisik)";

    // Status Banner
    el.statusBanner.className = `status-banner ${state.alertLevel}`;
    el.systemStatusText.textContent = state.systemStatus;
    el.currentModeBadge.textContent = state.mode;
    el.statusIcon.textContent =
      state.alertLevel === "CRITICAL" ? "🚨" : state.alertLevel === "ACTIVE" ? "⚙️" : "✅";

    // Sensor Cards
    const { temperature, humidity, light, soil } = state.sensors;
    el.valTemp.textContent = temperature.toFixed(1);
    el.valHum.textContent = humidity.toFixed(1);
    el.valLight.textContent = Math.round(light);
    el.valSoil.textContent = Math.round(soil);

    el.barTemp.style.width = `${Math.max(0, Math.min(100, (temperature / 50) * 100))}%`;
    el.barHum.style.width = `${Math.max(0, Math.min(100, humidity))}%`;
    el.barLight.style.width = `${Math.max(0, Math.min(100, light))}%`;
    el.barSoil.style.width = `${Math.max(0, Math.min(100, soil))}%`;

    el.noteTemp.innerHTML = `Batas Panas: &gt; ${state.thresholds.maxTemp.toFixed(1)} &deg;C`;
    el.noteLight.textContent = `Batas Gelap: < ${state.thresholds.minLight}%`;
    el.noteSoil.textContent = `Batas Kering: < ${state.thresholds.minSoil}%`;
    el.soilSourceTag.textContent =
      state.soilSource === "EXTERNAL_ADC" || state.demoConnEsp ? "POT / ADC1" : "SIMULASI";

    // Mode Buttons
    el.btnModeAuto.classList.toggle("active", state.mode === "AUTO");
    el.btnModeManual.classList.toggle("active", state.mode === "MANUAL");
    el.modeHint.innerHTML =
      state.mode === "AUTO"
        ? "Mode <strong>AUTO</strong> aktif: aktuator bekerja otomatis berdasarkan pembacaan sensor. Klik tombol aktuator mana saja atau pilih <strong>MANUAL</strong> untuk kendali langsung."
        : "Mode <strong>MANUAL</strong> aktif: Anda mengendalikan Relay Pompa (19), Servo Ventilasi (23), LED2 Grow Light (2), dan Buzzer (13) secara langsung dari Web maupun Button1&ndash;4.";

    // Actuator States
    updateActuatorButton(el.btnActPump, state.actuators.pump);
    updateActuatorButton(el.btnActFan, state.actuators.fan);
    updateActuatorButton(el.btnActGrow, state.actuators.growLight);
    updateActuatorButton(el.btnActBuzzer, state.actuators.buzzer, true);
    if (el.servoAngleText) {
      el.servoAngleText.textContent = `${state.servoAngle}° (${state.actuators.fan ? "Terbuka" : "Tertutup"})`;
    }

    // Threshold inputs (hanya sync jika tidak sedang diketik)
    if (!isEditingThreshold) {
      el.inpMaxTemp.value = state.thresholds.maxTemp.toFixed(1);
      el.inpMinSoil.value = state.thresholds.minSoil;
      el.inpMinLight.value = state.thresholds.minLight;
    }

    // Sync slider simulasi
    el.simTemp.value = temperature;
    el.simHum.value = humidity;
    el.simLight.value = light;
    el.simSoil.value = soil;
    el.simTempLabel.innerHTML = `${temperature.toFixed(1)} &deg;C`;
    el.simHumLabel.textContent = `${Math.round(humidity)} % RH`;
    el.simLightLabel.textContent = `${Math.round(light)} %`;
    el.simSoilLabel.textContent = `${Math.round(soil)} %`;

    drawChart();
  }

  // =========================================================================
  // LOOP POLLING & PERPINDAHAN SUMBER DATA
  // =========================================================================
  function startLoop() {
    if (pollTimer) clearInterval(pollTimer);

    if (state.source === "SIM") {
      state.connected = true;
      state.soilSource = state.demoConnEsp ? "EXTERNAL_ADC" : "SIMULATED";
      state.deviceLabel = state.demoConnEsp
        ? "IP: 192.168.43.105 | RSSI: -54 dBm"
        : "Virtual ESP32 (Demo)";
      evaluateSimulationLogic();
      if (state.history.length === 0) {
        seedHistoryPoints();
      } else {
        recordHistoryPoint();
      }
      render();

      pollTimer = setInterval(() => {
        recordHistoryPoint();
        render();
      }, POLL_INTERVAL_MS);
    } else {
      state.deviceLabel = `Menghubungi ${state.espIp}...`;
      renderConnectionStatusOnly();
      fetchEspStatus();
      pollTimer = setInterval(fetchEspStatus, POLL_INTERVAL_MS);
    }
  }

  function switchSource(nextSource) {
    state.demoConnEsp = false;
    state.source = nextSource;
    localStorage.setItem("gh_source", nextSource);
    state.history = [];
    startLoop();
  }

  // =========================================================================
  // EVENT LISTENERS
  // =========================================================================
  el.btnSourceSim.addEventListener("click", () => switchSource("SIM"));
  el.btnSourceEsp.addEventListener("click", () => switchSource("ESP"));

  el.espConnectForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const ip = el.espIpInput.value.trim();
    if (!ip) return;
    state.espIp = ip;
    localStorage.setItem("gh_esp_ip", ip);
    switchSource("ESP");
  });

  el.btnModeAuto.addEventListener("click", () => {
    if (state.source === "SIM") {
      state.mode = "AUTO";
      evaluateSimulationLogic();
      render();
    } else {
      sendEspControl({ mode: "AUTO" });
    }
  });

  el.btnModeManual.addEventListener("click", () => {
    if (state.source === "SIM") {
      state.mode = "MANUAL";
      evaluateSimulationLogic();
      render();
    } else {
      sendEspControl({ mode: "MANUAL" });
    }
  });

  document.querySelectorAll(".act-toggle").forEach((btn) => {
    btn.addEventListener("click", () => {
      const key = btn.dataset.actuator;
      if (!key) return;
      const nextVal = !state.actuators[key];

      if (state.source === "SIM") {
        state.mode = "MANUAL";
        state.actuators[key] = nextVal;
        evaluateSimulationLogic();
        render();
      } else {
        sendEspControl({ mode: "MANUAL", [key]: String(nextVal) });
      }
    });
  });

  [el.inpMaxTemp, el.inpMinSoil, el.inpMinLight].forEach((input) => {
    input.addEventListener("focus", () => {
      isEditingThreshold = true;
    });
    input.addEventListener("blur", () => {
      isEditingThreshold = false;
    });
  });

  el.thresholdForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const maxTemp = parseFloat(el.inpMaxTemp.value);
    const minSoil = parseInt(el.inpMinSoil.value, 10);
    const minLight = parseInt(el.inpMinLight.value, 10);

    if (Number.isNaN(maxTemp) || Number.isNaN(minSoil) || Number.isNaN(minLight)) return;

    state.thresholds = { maxTemp, minSoil, minLight };
    isEditingThreshold = false;

    if (state.source === "SIM") {
      evaluateSimulationLogic();
      render();
    } else {
      sendEspThresholds({ maxTemp, minSoil, minLight });
    }
  });

  // Preset & Slider Simulator
  document.querySelectorAll(".preset-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      if (state.source !== "SIM" || state.demoConnEsp) switchSource("SIM");
      const preset = PRESETS[btn.dataset.preset];
      if (!preset) return;
      state.sensors = { ...preset };
      state.mode = "AUTO";
      evaluateSimulationLogic();
      seedHistoryPoints();
      render();
    });
  });

  function handleSliderInput() {
    if (state.source !== "SIM" || state.demoConnEsp) switchSource("SIM");
    state.sensors.temperature = parseFloat(el.simTemp.value);
    state.sensors.humidity = parseFloat(el.simHum.value);
    state.sensors.light = parseInt(el.simLight.value, 10);
    state.sensors.soil = parseInt(el.simSoil.value, 10);
    evaluateSimulationLogic();
    render();
  }

  [el.simTemp, el.simHum, el.simLight, el.simSoil].forEach((slider) => {
    slider.addEventListener("input", handleSliderInput);
  });

  window.addEventListener("resize", drawChart);

  // Inisialisasi awal
  el.espIpInput.value = state.espIp;
  startLoop();
})();
