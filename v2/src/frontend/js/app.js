/**
 * Stream Media Analyzer v2 — Frontend App
 * Sprint 1.5: Shared logic for audio/video analyzer templates
 */

// ============================================
// State
// ============================================

const state = {
  protocol: 'srt',
  analyzerType: 'audio',
  connected: false,
  metrics: {
    dbfs: { left: -70, right: -70, peak: -70, hold: -70 },
    lufs: { m: -70, s: -70, i: -70 },
    truePeak: { current: -70, max: -70 },
    spectrum: { bands: new Array(31).fill(-70), peakFreq: 0, peakDb: -70 },
    history: new Array(60).fill(-70),
    silence: { active: false, duration: 0 },
    lra: 0,
    network: { rtt: 0, bandwidth: 0, loss: 0, buffer: 0 },
    transport: { sync: true, ccErrors: 0, pcrJitter: 0, nullRatio: 0 },
    video: { codec: '', resolution: '', fps: 0, gop: '', keyframes: 0 },
  },
  animationId: null,
  signalState: {
    baseLevel: -18,
    peakHoldL: -70,
    peakHoldR: -70,
    peakDecay: 0.15,
    lastPeakTimeL: 0,
    lastPeakTimeR: 0,
  },
};

// ============================================
// Initialization
// ============================================

function initAnalyzer(options = {}) {
  state.analyzerType = options.type || 'audio';
  state.protocol = getProtocolFromURL();

  updateProtocolBadge();
  updateStreamInfo();
  setupTabs();
  setupTimeButtons();
  setupConnectButtons();
  setupTransportVisibility();

  // Start demo simulation
  connect();
}

function getProtocolFromURL() {
  const params = new URLSearchParams(window.location.search);
  return params.get('protocol') || (state.analyzerType === 'video' ? 'srt' : 'mp3');
}

function updateProtocolBadge() {
  const badge = document.getElementById('protocol-badge');
  if (badge) badge.textContent = state.protocol.toUpperCase();

  const select = document.getElementById('protocolSelect');
  if (select) select.value = state.protocol;
}

function updateStreamInfo() {
  const defaults = {
    mp3: { bitrate: '128 kbps', codec: 'MP3', samplerate: '44.1 kHz' },
    aac: { bitrate: '256 kbps', codec: 'AAC', samplerate: '48 kHz' },
    srt: { bitrate: '8.5 Mbps', codec: 'H.264', resolution: '1920x1080', fps: '50' },
    rtmp: { bitrate: '6.2 Mbps', codec: 'H.264', resolution: '1280x720', fps: '30' },
    'mpeg-ts': { bitrate: '12 Mbps', codec: 'H.264', resolution: '1920x1080', fps: '25' },
    hls: { bitrate: '4.8 Mbps', codec: 'H.264', resolution: '1280x720', fps: '25' },
  };

  const d = defaults[state.protocol] || {};

  const fields = {
    'info-bitrate': d.bitrate || '—',
    'info-samplerate': d.samplerate || '48 kHz',
    'info-codec': d.codec || '—',
    'info-resolution': d.resolution || '—',
    'info-fps': d.fps || '—',
    'info-vbitrate': d.bitrate || '—',
    'info-abitrate': '192 kbps',
  };

  Object.entries(fields).forEach(([id, value]) => {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
  });
}

function setupTabs() {
  document.querySelectorAll('.nav-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const tabName = tab.dataset.tab;
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      const target = document.getElementById('tab-' + tabName);
      if (target) target.classList.add('active');
    });
  });
}

function setupTimeButtons() {
  document.querySelectorAll('.time-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const parent = btn.closest('.time-window-selector');
      if (parent) {
        parent.querySelectorAll('.time-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
      }
    });
  });
}

function setupConnectButtons() {
  const btnConnect = document.getElementById('btn-connect');
  const btnDisconnect = document.getElementById('btn-disconnect');

  if (btnConnect) {
    btnConnect.addEventListener('click', () => {
      connect();
      addAlert('info', 'Connected to ' + document.getElementById('connect-url')?.value);
    });
  }

  if (btnDisconnect) {
    btnDisconnect.addEventListener('click', () => {
      disconnect();
      addAlert('warning', 'Disconnected');
    });
  }
}

function setupTransportVisibility() {
  const transportCard = document.getElementById('transport-card');
  if (transportCard) {
    transportCard.style.display = state.protocol === 'mpeg-ts' ? 'block' : 'none';
  }
}

// ============================================
// Connection / Simulation
// ============================================

function connect() {
  state.connected = true;
  updateConnectionStatus();
  startSimulation();
}

function disconnect() {
  state.connected = false;
  updateConnectionStatus();
  stopSimulation();
}

function updateConnectionStatus() {
  const dot = document.getElementById('status-dot');
  const text = document.getElementById('status-text');
  if (dot) dot.classList.toggle('disconnected', !state.connected);
  if (text) text.textContent = state.connected ? 'Connected' : 'Disconnected';
}

// ============================================
// Demo Simulation
// ============================================

function startSimulation() {
  let time = 0;

  function tick() {
    time += 0.02;
    simulateMetrics(time);
    updateUI();
    drawSpectrum();
    drawHistory();
    updateSrtCharts();
    state.animationId = requestAnimationFrame(tick);
  }

  tick();
}

function stopSimulation() {
  if (state.animationId) {
    cancelAnimationFrame(state.animationId);
    state.animationId = null;
  }
}

function simulateMetrics(t) {
  const s = state.metrics;

  // Simulate -20 dBFS sine wave with variation
  const baseLevel = -20 + Math.sin(t * 2) * 3;
  const left = baseLevel + Math.random() * 1 - 0.5;
  const right = baseLevel + Math.random() * 1 - 0.5;
  const peak = Math.max(left, right);

  s.dbfs.left = Math.max(-70, Math.min(0, left));
  s.dbfs.right = Math.max(-70, Math.min(0, right));
  s.dbfs.peak = Math.max(-70, Math.min(0, peak));

  // LUFS (slightly lower than dBFS)
  s.lufs.m = s.dbfs.peak - 3 + Math.sin(t) * 1;
  s.lufs.s = s.lufs.m + Math.sin(t * 0.5) * 0.5;
  s.lufs.i = s.lufs.s + Math.sin(t * 0.1) * 0.3;

  // True Peak
  s.truePeak.current = s.dbfs.peak + 1.2;
  s.truePeak.max = Math.max(s.truePeak.max, s.truePeak.current);

  // Spectrum
  for (let i = 0; i < 31; i++) {
    const freq = 20 * Math.pow(2, i / 31 * Math.log2(20000 / 20));
    const dist = Math.abs(freq - 1000) / 1000;
    s.spectrum.bands[i] = baseLevel - dist * 15 + Math.random() * 3;
  }
  s.spectrum.peakFreq = 1000 + Math.sin(t) * 50;
  s.spectrum.peakDb = baseLevel;

  // History
  if (Math.random() > 0.98) {
    s.history.push(s.lufs.s);
    s.history.shift();
  }

  // Silence
  s.silence.active = baseLevel < -58;
  s.silence.duration = s.silence.active ? s.silence.duration + 0.02 : 0;

  // LRA
  s.lra = 8 + Math.sin(t * 0.3) * 2;

  // Network (video only)
  if (state.analyzerType === 'video') {
    s.network.rtt = 20 + Math.sin(t) * 5;
    s.network.bandwidth = 12 + Math.sin(t * 0.7) * 2;
    s.network.loss = Math.max(0, Math.sin(t * 3) * 0.1);
    s.network.buffer = 100 + Math.sin(t * 0.5) * 20;
  }

  // Transport
  if (state.protocol === 'mpeg-ts') {
    s.transport.ccErrors = Math.floor(Math.random() * 0.01);
    s.transport.pcrJitter = 10 + Math.sin(t) * 5;
    s.transport.nullRatio = 2 + Math.sin(t * 0.2) * 1;
  }
}

// ============================================
// UI Updates
// ============================================

function updateUI() {
  const s = state.metrics;

  // Legacy audio-analyzer elements
  setHeight('dbfs-left', dbfsToPercent(s.dbfs.left));
  setHeight('dbfs-right', dbfsToPercent(s.dbfs.right));
  setColor('dbfs-left', dbfsToColor(s.dbfs.left));
  setColor('dbfs-right', dbfsToColor(s.dbfs.right));
  setText('dbfs-peak-value', s.dbfs.peak.toFixed(1) + ' dBFS');
  setText('dbfs-hold-value', s.dbfs.hold.toFixed(1) + ' dBFS');

  setWidth('lufs-m-bar', lufsToPercent(s.lufs.m));
  setWidth('lufs-s-bar', lufsToPercent(s.lufs.s));
  setWidth('lufs-i-bar', lufsToPercent(s.lufs.i));
  setColor('lufs-m-bar', lufsToColor(s.lufs.m));
  setColor('lufs-s-bar', lufsToColor(s.lufs.s));
  setColor('lufs-i-bar', lufsToColor(s.lufs.i));
  setText('lufs-m', s.lufs.m.toFixed(1));
  setText('lufs-s', s.lufs.s.toFixed(1));
  setText('lufs-i', s.lufs.i.toFixed(1));

  setWidth('true-peak-bar', dbfsToPercent(s.truePeak.current));
  setWidth('true-peak-max-bar', dbfsToPercent(s.truePeak.max));
  setText('true-peak', s.truePeak.current.toFixed(1));
  setText('true-peak-max', s.truePeak.max.toFixed(1));

  setText('silence-status', s.silence.active ? 'ACTIVE' : 'Inactive');
  setText('silence-duration', s.silence.duration.toFixed(1) + ' s');

  setWidth('lra-bar', Math.min(100, s.lra * 5));
  setText('lra-value', s.lra.toFixed(1) + ' LU');

  setText('net-rtt', s.network.rtt.toFixed(1) + ' ms');
  setText('net-bandwidth', s.network.bandwidth.toFixed(1) + ' Mbps');
  setText('net-loss', s.network.loss.toFixed(2) + '%');
  setText('net-buffer', s.network.buffer.toFixed(0) + ' ms');

  setText('ts-sync', s.transport.sync ? 'Locked' : 'Lost');
  setText('ts-cc', s.transport.ccErrors.toString());
  setText('ts-pcr', s.transport.pcrJitter.toFixed(0) + ' ns');
  setText('ts-null', s.transport.nullRatio.toFixed(1) + '%');

  // Duration counter
  const dur = document.getElementById('info-duration');
  if (dur && state.connected) {
    const sec = Math.floor(performance.now() / 1000);
    const m = Math.floor(sec / 60).toString().padStart(2, '0');
    const s_ = (sec % 60).toString().padStart(2, '0');
    dur.textContent = `${m}:${s_}`;
  }

  // Segmented DBFS meters (video analyzer)
  updateSegmentedDbfs();

  // LUFS 3-scale meters (video analyzer)
  updateLufsMeters();
}

// ============================================
// Segmented DBFS Meter Animation
// ============================================

function updateSegmentedDbfs() {
  const s = state.metrics;
  const sig = state.signalState;
  const t = Date.now() / 1000;

  // Generate realistic audio signal
  const dbfsL = generateAudioSignal(t, 'L');
  const dbfsR = generateAudioSignal(t, 'R');

  // Update peak holds
  const phL = updatePeakHold(dbfsL, sig.peakHoldL, sig.lastPeakTimeL, t);
  sig.peakHoldL = phL.val;
  sig.lastPeakTimeL = phL.time;

  const phR = updatePeakHold(dbfsR, sig.peakHoldR, sig.lastPeakTimeR, t);
  sig.peakHoldR = phR.val;
  sig.lastPeakTimeR = phR.time;

  // Bar height in px (max 252px)
  const maxPx = 252;
  const pxL = maxPx - (Math.abs(dbfsL) / 70) * maxPx;
  const pxR = maxPx - (Math.abs(dbfsR) / 70) * maxPx;

  const containerL = document.getElementById('dbfsBarContainerL');
  const containerR = document.getElementById('dbfsBarContainerR');
  if (containerL) containerL.style.height = pxL + 'px';
  if (containerR) containerR.style.height = pxR + 'px';

  // Color
  function getColorHex(dbfs) {
    if (dbfs >= -2) return '#f87171';
    if (dbfs >= -9) return '#fb923c';
    if (dbfs >= -18) return '#fbbf24';
    return '#4ade80';
  }

  const cL = getColorHex(dbfsL);
  const cR = getColorHex(dbfsR);

  const valL = document.getElementById('dbfsValL');
  const valR = document.getElementById('dbfsValR');
  if (valL) {
    valL.textContent = dbfsL.toFixed(1);
    valL.style.color = cL;
    const labels = valL.parentNode?.querySelectorAll('.dbfs-readout__value');
    if (labels && labels[1]) labels[1].style.color = cL;
  }
  if (valR) {
    valR.textContent = dbfsR.toFixed(1);
    valR.style.color = cR;
    const labels = valR.parentNode?.querySelectorAll('.dbfs-readout__value');
    if (labels && labels[1]) labels[1].style.color = cR;
  }

  // Peak hold lines
  const peakL = document.getElementById('dbfsPeakL');
  const peakR = document.getElementById('dbfsPeakR');
  const holdPxL = maxPx - (Math.abs(sig.peakHoldL) / 70) * maxPx;
  const holdPxR = maxPx - (Math.abs(sig.peakHoldR) / 70) * maxPx;
  if (peakL) peakL.style.bottom = (4 + holdPxL) + 'px';
  if (peakR) peakR.style.bottom = (4 + holdPxR) + 'px';

  const holdL = document.getElementById('peakHoldL');
  const holdR = document.getElementById('peakHoldR');
  if (holdL) {
    holdL.textContent = sig.peakHoldL.toFixed(1);
    holdL.style.color = getColorHex(sig.peakHoldL);
    const labels = holdL.parentNode?.querySelectorAll('.dbfs-readout__value');
    if (labels && labels[1]) labels[1].style.color = getColorHex(sig.peakHoldL);
  }
  if (holdR) {
    holdR.textContent = sig.peakHoldR.toFixed(1);
    holdR.style.color = getColorHex(sig.peakHoldR);
    const labels = holdR.parentNode?.querySelectorAll('.dbfs-readout__value');
    if (labels && labels[1]) labels[1].style.color = getColorHex(sig.peakHoldR);
  }
}

function generateAudioSignal(t, channel) {
  const phase = channel === 'L' ? 0 : 0.7;
  const slow = Math.sin(t * 0.5 + phase) * 8;
  const fast = Math.sin(t * 3 + phase * 2) * 4;
  const noise = (Math.random() - 0.5) * 3;
  let dbfs = -18 + slow + fast + noise;
  if (Math.sin(t * 2.1 + phase) > 0.92) {
    dbfs += 8 + Math.random() * 6;
  }
  return Math.max(-70, Math.min(0, dbfs));
}

function updatePeakHold(current, hold, lastTime, t) {
  if (current > hold) {
    return { val: current, time: t };
  }
  const elapsed = t - lastTime;
  const decay = state.signalState.peakDecay * elapsed * 60;
  return { val: Math.max(current, hold - decay), time: lastTime };
}

// ============================================
// LUFS 3-Scale Meter Animation
// ============================================

function updateLufsMeters() {
  const time = Date.now() / 1000;

  const baseSignal = -24 + Math.sin(time * 0.8) * 4;
  const modulation = Math.sin(time * 2.5) * 3 + Math.sin(time * 5.2) * 1.5;
  const peaks = Math.max(0, Math.sin(time * 8) * 5 - 3) * Math.random();
  const noise = (Math.random() - 0.5) * 1.5;

  const m = baseSignal + modulation + peaks + noise;
  const s = m * 0.6 + (-24) * 0.4 + Math.sin(time * 1.2) * 2;
  const i = s * 0.4 + (-25) * 0.6 + Math.sin(time * 0.5) * 1;
  const tp = Math.max(m, -1.5) + 2.5 + Math.random() * 0.5;
  const lra = 4 + Math.sin(time * 0.3) * 2 + Math.random() * 0.5;

  const clampM = Math.max(-40, Math.min(0, m));
  const clampS = Math.max(-40, Math.min(0, s));
  const clampI = Math.max(-40, Math.min(0, i));
  const clampTP = Math.max(-6, Math.min(0, tp));

  // Bar heights (0..-40 scale, max 252px)
  const maxPx = 252;
  const pxM = maxPx - (Math.abs(clampM) / 40) * maxPx;
  const pxS = maxPx - (Math.abs(clampS) / 40) * maxPx;
  const pxI = maxPx - (Math.abs(clampI) / 40) * maxPx;

  const containerM = document.getElementById('lufsBarContainerM');
  const containerS = document.getElementById('lufsBarContainerS');
  const containerI = document.getElementById('lufsBarContainerI');
  if (containerM) containerM.style.height = pxM + 'px';
  if (containerS) containerS.style.height = pxS + 'px';
  if (containerI) containerI.style.height = pxI + 'px';

  // Color by zone
  function getColorClass(val) {
    if (val > -23.5) return 'lufs-readout__value--danger';
    if (val > -26) return 'lufs-readout__value--warning';
    return 'lufs-readout__value--safe';
  }
  function getColorHex(val) {
    if (val > -23.5) return '#f87171';
    if (val > -26) return '#fbbf24';
    return '#4ade80';
  }

  // Update M readout + TP
  const valM = document.getElementById('lufsValM');
  const tpValM = document.getElementById('tpValM');
  if (valM) {
    valM.textContent = clampM.toFixed(1);
    valM.className = 'lufs-readout__value ' + getColorClass(clampM);
    valM.style.color = getColorHex(clampM);
    const labels = valM.parentNode?.querySelectorAll('.lufs-readout__value');
    if (labels && labels[1]) labels[1].style.color = getColorHex(clampM);
  }
  if (tpValM) {
    tpValM.textContent = clampTP.toFixed(1);
    tpValM.className = 'lufs-readout__value ' + (clampTP > -1 ? 'lufs-readout__value--danger' : 'lufs-readout__value--safe');
    tpValM.style.color = clampTP > -1 ? '#f87171' : '#4ade80';
    const labels = tpValM.parentNode?.querySelectorAll('.lufs-readout__value');
    if (labels && labels[1]) labels[1].style.color = clampTP > -1 ? '#f87171' : '#4ade80';
  }

  // Update S readout
  const valS = document.getElementById('lufsValS');
  if (valS) {
    valS.textContent = clampS.toFixed(1);
    valS.className = 'lufs-readout__value ' + getColorClass(clampS);
    valS.style.color = getColorHex(clampS);
    const labels = valS.parentNode?.querySelectorAll('.lufs-readout__value');
    if (labels && labels[1]) labels[1].style.color = getColorHex(clampS);
  }

  // Update I readout
  const valI = document.getElementById('lufsValI');
  if (valI) {
    valI.textContent = clampI.toFixed(1);
    valI.className = 'lufs-readout__value ' + getColorClass(clampI);
    valI.style.color = getColorHex(clampI);
    const labels = valI.parentNode?.querySelectorAll('.lufs-readout__value');
    if (labels && labels[1]) labels[1].style.color = getColorHex(clampI);
  }

  // Update LRA
  const lraVal = document.getElementById('lraVal');
  if (lraVal) lraVal.textContent = lra.toFixed(1);

  // Peak hold lines
  const peakM = document.getElementById('lufsPeakM');
  const peakS = document.getElementById('lufsPeakS');
  const peakI = document.getElementById('lufsPeakI');
  const holdM = Math.max(clampM, -20 + Math.sin(time * 0.5) * 3);
  const holdS = Math.max(clampS, -22 + Math.sin(time * 0.3) * 2);
  const holdI = Math.max(clampI, -24 + Math.sin(time * 0.2) * 1);
  if (peakM) peakM.style.bottom = (4 + maxPx - (Math.abs(holdM) / 40) * maxPx) + 'px';
  if (peakS) peakS.style.bottom = (4 + maxPx - (Math.abs(holdS) / 40) * maxPx) + 'px';
  if (peakI) peakI.style.bottom = (4 + maxPx - (Math.abs(holdI) / 40) * maxPx) + 'px';

  // TP line on M scale
  const tpLineM = document.getElementById('lufsTpLineM');
  if (tpLineM) {
    const tpPx = maxPx - (Math.abs(clampTP) / 6) * maxPx;
    tpLineM.style.bottom = (4 + tpPx) + 'px';
  }
}

// ============================================
// SRT Charts
// ============================================

function updateSrtCharts() {
  const time = Date.now() / 1000;
  drawChart('rttChart', '#00d4aa', i => 40 + Math.sin(i * 0.3 + time) * 15 + Math.random() * 5, 100);
  drawChart('bwChart', '#4ade80', i => 7 + Math.sin(i * 0.2 + time * 0.5) * 2 + Math.random() * 0.5, 12);
  drawChart('lossChart', '#f87171', i => Math.max(0, Math.sin(i * 0.5 + time) * 0.5 + Math.random() * 0.3), 2);
  drawChart('bufChart', '#fbbf24', i => 100 + Math.sin(i * 0.15 + time * 0.3) * 30 + Math.random() * 10, 200);
}

function drawChart(canvasId, color, dataFn, maxVal) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width;
  const h = canvas.height;
  const pad = 10;

  ctx.clearRect(0, 0, w, h);

  const data = [];
  for (let i = 0; i < 50; i++) {
    data.push(dataFn(i));
  }

  const stepX = (w - 2 * pad) / (data.length - 1);

  // Fill
  ctx.beginPath();
  for (let i = 0; i < data.length; i++) {
    const x = pad + i * stepX;
    const y = h - pad - (data[i] / maxVal) * (h - 2 * pad);
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.lineTo(pad + (data.length - 1) * stepX, h - pad);
  ctx.lineTo(pad, h - pad);
  ctx.closePath();
  ctx.fillStyle = color + '22';
  ctx.fill();

  // Line
  ctx.beginPath();
  for (let i = 0; i < data.length; i++) {
    const x = pad + i * stepX;
    const y = h - pad - (data[i] / maxVal) * (h - 2 * pad);
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.strokeStyle = color;
  ctx.lineWidth = 2;
  ctx.stroke();
}

// ============================================
// Canvas Drawing (Legacy + New)
// ============================================

function drawSpectrum() {
  const canvas = document.getElementById('spectrum-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width;
  const h = canvas.height;
  const bands = state.metrics.spectrum.bands;

  ctx.clearRect(0, 0, w, h);

  ctx.strokeStyle = '#252532';
  ctx.lineWidth = 1;
  for (let i = 0; i < 5; i++) {
    const y = (h / 4) * i;
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(w, y);
    ctx.stroke();
  }

  const barW = (w - 20) / bands.length;
  const colors = { safe: '#4ade80', caution: '#fbbf24', warning: '#fb923c', danger: '#f87171' };
  bands.forEach((db, i) => {
    const pct = dbfsToPercent(db) / 100;
    const barH = pct * (h - 20);
    const x = 10 + i * barW;
    const y = h - 10 - barH;
    ctx.fillStyle = colors[dbfsToColor(db)] || '#4ade80';
    ctx.fillRect(x + 1, y, barW - 2, barH);
  });
}

function drawHistory() {
  const canvas = document.getElementById('history-canvas') || document.getElementById('historyCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width;
  const h = canvas.height;
  const values = state.metrics.history;

  ctx.clearRect(0, 0, w, h);

  ctx.strokeStyle = '#252532';
  ctx.lineWidth = 1;
  [-23, -30, -40, -50, -60].forEach(db => {
    const y = h - (dbfsToPercent(db) / 100) * (h - 20) - 10;
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(w, y);
    ctx.stroke();
  });

  const targetY = h - (dbfsToPercent(-23) / 100) * (h - 20) - 10;
  ctx.strokeStyle = '#4a9eff';
  ctx.setLineDash([5, 5]);
  ctx.beginPath();
  ctx.moveTo(0, targetY);
  ctx.lineTo(w, targetY);
  ctx.stroke();
  ctx.setLineDash([]);

  if (values.length < 2) return;
  ctx.strokeStyle = '#4ade80';
  ctx.lineWidth = 2;
  ctx.beginPath();
  values.forEach((db, i) => {
    const x = (i / (values.length - 1)) * w;
    const y = h - (dbfsToPercent(db) / 100) * (h - 20) - 10;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  ctx.fillStyle = 'rgba(74, 222, 128, 0.1)';
  ctx.lineTo(w, h);
  ctx.lineTo(0, h);
  ctx.closePath();
  ctx.fill();
}

// ============================================
// Alerts
// ============================================

function addAlert(severity, message) {
  const container = document.getElementById('alerts-container');
  if (!container) return;

  const now = new Date();
  const time = now.getHours().toString().padStart(2, '0') + ':' +
               now.getMinutes().toString().padStart(2, '0') + ':' +
               now.getSeconds().toString().padStart(2, '0');

  const item = document.createElement('div');
  item.className = 'alert-item ' + severity;
  item.innerHTML = `
    <div>
      <div class="alert-time">${time}</div>
      <div class="alert-msg">${message}</div>
    </div>
  `;
  container.insertBefore(item, container.firstChild);
}

// ============================================
// Helpers
// ============================================

function dbfsToPercent(db) {
  return Math.max(0, Math.min(100, (db + 70) / 70 * 100));
}

function lufsToPercent(lufs) {
  return Math.max(0, Math.min(100, (lufs + 70) / 70 * 100));
}

function dbfsToColor(db) {
  if (db >= -6) return 'danger';
  if (db >= -9) return 'warning';
  if (db >= -18) return 'caution';
  return 'safe';
}

function lufsToColor(lufs) {
  if (lufs > -14) return 'danger';
  if (lufs >= -24 && lufs <= -22) return 'safe';
  if (lufs < -40) return 'safe';
  return 'caution';
}

function setHeight(id, pct) {
  const el = document.getElementById(id);
  if (el) el.style.height = pct + '%';
}

function setWidth(id, pct) {
  const el = document.getElementById(id);
  if (el) el.style.width = pct + '%';
}

function setColor(id, colorClass) {
  const el = document.getElementById(id);
  if (el) {
    el.className = el.className.replace(/\b(safe|caution|warning|danger)\b/g, '');
    el.classList.add(colorClass);
  }
}

function setText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

// Expose for inline scripts
window.initAnalyzer = initAnalyzer;
