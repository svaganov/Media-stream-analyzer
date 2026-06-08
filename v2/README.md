# Media Stream Analyzer v2 — Sprint 1

## Overview
Clean rewrite of the audio analysis foundation.

## Sprint Deliverables

### Sprint 1: Audio Analysis Foundation

| Module | Description | Tests |
|--------|-------------|-------|
| `core/models.py` | Data contracts (DBFS, LUFS, TruePeak, Spectrum, Silence) | ✅ |
| `core/constants.py` | EBU R128 constants, thresholds | ✅ |
| `core/config.py` | Pydantic Settings configuration | ✅ |
| `analyzers/audio/dbfs_meter.py` | Peak meter with hold | ✅ |
| `analyzers/audio/ebu_r128.py` | LUFS M/S/I calculator | ✅ |
| `analyzers/audio/true_peak.py` | 4x oversampling peak detector | ✅ |
| `analyzers/audio/fft_spectrum.py` | 31-band spectrum analyzer | ✅ |
| `analyzers/audio/silence_detector.py` | Threshold-based silence detection | ✅ |
| `analyzers/audio/audio_analyzer.py` | Orchestrator combining all analyzers | ✅ |

### Sprint 1.5: Frontend Structure

| File | Description |
|------|-------------|
| `frontend/index.html` | Landing page with protocol selector |
| `frontend/audio-analyzer.html` | Audio analyzer template (MP3, AAC) |
| `frontend/video-analyzer.html` | Video analyzer template (SRT, RTMP, MPEG-TS, HLS) |
| `frontend/css/styles.css` | Unified dark theme, meters, layout grid |
| `frontend/js/app.js` | Demo simulation, canvas rendering, UI updates |

**Features:**
- 2 templates × 6 protocols = unified UX
- Real-time demo simulation (50 fps)
- DBFS vertical meters, LUFS horizontal bars
- FFT spectrum canvas, Loudness history graph
- Responsive layout (sidebar + center + right panel)

## Architecture Principles
1. **Protocol-agnostic** — Input layer abstracts protocols
2. **Plugin architecture** — Analyzers inherit from `AudioAnalyzerBase`
3. **Immutable contracts** — All output via `to_dict()` dataclasses
4. **Unified UX** — Audio/Video templates share CSS and JS
5. **Test-driven** — Every backend module has tests

## Quick Start

### Backend
```bash
cd v2
pip install -e ".[dev]"
pytest tests/ -v
```

### Frontend
Open `v2/src/frontend/index.html` in a browser.
No build step required — pure HTML/CSS/JS.

### API Usage
```python
from v2.src.analyzers.audio.audio_analyzer import AudioAnalyzer
import numpy as np

analyzer = AudioAnalyzer(sample_rate=48000, channels=2)

sr = 48000
t = np.linspace(0, 1, sr, endpoint=False)
samples = np.stack([
    0.5 * np.sin(2 * np.pi * 1000 * t),
    0.5 * np.sin(2 * np.pi * 1000 * t)
]).astype(np.float32)

result = analyzer.process(samples)
print(result.to_dict())
```

## Next: Sprint 2
- FastAPI backend with WebSocket broadcast
- Real audio input (Icecast/HTTP stream)
- Connect frontend to backend via WebSocket
