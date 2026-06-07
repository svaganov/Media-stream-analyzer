# Testing Guide — Sprint 3: FFT Spectrum + Time Windows

## Overview

Sprint 3 добавляет:
- **FFT Spectrum Analyzer** — 1024-point real-time FFT с peak detection
- **Time Window Manager** — управление окнами 1m/5m/15m/30m/60m
- **History Buffers** — кольцевые буферы для графиков с downsampling
- **Metrics Aggregator** — объединение всех анализаторов
- **Updated API** — новые endpoints для спектра и истории

## Test Script

```bash
cd media-stream-analyzer
python scripts/test-sprint3.py
```

## Manual Testing Checklist

### 1. Time Windows
- [ ] Выбрать окно 1m — график показывает последнюю минуту
- [ ] Выбрать окно 5m — график масштабируется
- [ ] Выбрать окно 15m — default window
- [ ] Выбрать окно 30m — данные downsampling
- [ ] Выбрать окно 60m — максимальное окно
- [ ] Нажать Reset — все буферы очищаются, графики сбрасываются

### 2. FFT Spectrum
- [ ] Спектр обновляется 50fps (плавная анимация)
- [ ] Peak frequency отображается корректно
- [ ] 64 frequency bands отображаются
- [ ] Цвета меняются по частоте (rainbow gradient)
- [ ] При тишине спектр пустой (все столбики низкие)

### 3. Bitrate Chart
- [ ] Area chart отображается корректно
- [ ] Min/Max/Avg обновляются в реальном времени
- [ ] При смене окна график перезагружается
- [ ] Threshold lines (warning/danger) видны

### 4. Jitter Chart
- [ ] Line chart отображается корректно
- [ ] Min/Max/Avg обновляются
- [ ] Warning threshold (50ms) виден

### 5. API Endpoints
```bash
# Health check
curl http://localhost:8000/api/health

# Get current spectrum
curl http://localhost:8000/api/metrics/spectrum

# Get bitrate history (15m window, 200 points)
curl "http://localhost:8000/api/metrics/history/bitrate?window=15m&points=200"

# Get stats for jitter (5m window)
curl "http://localhost:8000/api/metrics/stats/jitter?window=5m"

# Change time window
curl -X POST http://localhost:8000/api/session/window   -H "Content-Type: application/json"   -d '{"window": "30m"}'

# Get chart configs
curl http://localhost:8000/api/charts/config
```

### 6. WebSocket
```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/metrics');

// Subscribe to spectrum updates (50fps)
ws.send(JSON.stringify({
    action: 'subscribe_spectrum',
    enabled: true
}));

// Change time window
ws.send(JSON.stringify({
    action: 'set_window',
    window: '5m'
}));
```

## Expected Behavior

### Time Windows
| Window | Max Points | Resolution | Use Case |
|--------|-----------|------------|----------|
| 1m | 60 | 1 second | Short-term monitoring |
| 5m | 300 | 1 second | Medium-term |
| 15m | 900 | 1 second | Default, detailed |
| 30m | 900 | 2 seconds | Long-term, downsampled |
| 60m | 900 | 4 seconds | Maximum, downsampled |

### FFT Spectrum
- **FFT Size**: 1024 points
- **Sample Rate**: 48 kHz
- **Frequency Range**: 0 - 24 kHz (Nyquist)
- **Display Bands**: 64 (logarithmic scale)
- **Update Rate**: 50fps (WebSocket)
- **Window**: Hann window
- **Overlap**: 50%

### Chart Data Format
```json
{
    "metric": "bitrate",
    "window": "15m",
    "points": 200,
    "data": [
        {"timestamp": 1717520400.123, "value": 256.0},
        {"timestamp": 1717520401.123, "value": 258.5}
    ]
}
```

## Performance Requirements

- **FFT Processing**: < 5ms per frame (1024 samples)
- **Buffer Updates**: < 1ms per metric
- **WebSocket Broadcast**: < 10ms for all clients
- **Chart Rendering**: 50fps smooth (Canvas 2D)
- **Memory Usage**: < 50MB for 60m window (all metrics)

## Troubleshooting

### Spectrum not updating
1. Check WebSocket connection
2. Verify `subscribe_spectrum` message sent
3. Check browser console for errors

### Charts empty after window change
1. Wait 1-2 seconds for data to populate
2. Check API response: `curl /api/metrics/history/bitrate?window=15m`
3. Verify Reset didn't clear buffers

### High memory usage
1. Check buffer sizes in `TimeWindowManager`
2. Verify downsampling for 30m/60m windows
3. Monitor `get_registered_metrics()` count

## Files Added/Modified

### New Files
- `src/core/time_window.py` — Time Window Manager
- `src/analyzers/audio/fft_spectrum.py` — FFT Analyzer
- `src/metrics/aggregator.py` — Metrics Aggregator
- `src/metrics/history_buffer.py` — History Buffers
- `src/api/main.py` — Updated API (v3.0)
- `src/web/assets/js/app.js` — Frontend JS
- `scripts/test-sprint3.py` — Test script
- `docs/testing-sprint3.md` — This file

### Modified Files
- `AGENTS.md` — Sprint status updated
- `PROJECT_STRUCTURE.md` — New modules added
