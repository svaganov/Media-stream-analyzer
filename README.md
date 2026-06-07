# Media Stream Analyzer - Sprint 5 Backend

## Overview
Python backend for real-time SRT stream analysis with WebSocket API.

## Architecture
```
┌─────────────┐     WebSocket      ┌─────────────────┐
│  Frontend   │◄──────────────────►│  Python Backend │
│  (HTML/JS)  │                    │  (asyncio)      │
└─────────────┘                    └─────────────────┘
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    │                     │                     │
               ┌────▼────┐         ┌────▼────┐         ┌────▼────┐
               │  SRT    │         │ FFmpeg  │         │ Audio   │
               │ Client  │         │ Decoder │         │ Analyzer│
               └─────────┘         └─────────┘         └─────────┘
```

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Install SRT tools
```bash
# Ubuntu/Debian
sudo apt-get install srt-tools

# macOS
brew install srt

# Or build from source: https://github.com/Haivision/srt
```

### 3. Run backend
```bash
cd src/backend
python main.py
```

### 4. Connect frontend
Open `mockups/video_stream_srt_v4.2.html` in browser.
WebSocket will connect to `ws://localhost:8765`

## WebSocket API

### Connect to stream
```json
{
  "action": "connect",
  "protocol": "srt",
  "url": "srt://192.168.1.100:9000",
  "mode": "caller"
}
```

### Server messages
- `srt_stats` - SRT connection metrics (1/sec)
- `audio_analysis` - DBFS/LUFS analysis (50/sec)
- `loudness_history` - Loudness history (1/sec)
- `stream_info` - Stream metadata

## File Structure
```
sprint5_backend/
├── src/
│   ├── backend/
│   │   ├── main.py              # Entry point
│   │   ├── websocket_server.py  # WebSocket server
│   │   ├── srt_client.py        # SRT connection
│   │   └── config.py            # Configuration
│   └── analyzers/
│       ├── audio/
│       │   └── audio_analyzer.py # Audio analysis
│       └── video/
│           └── stream_decoder.py # FFmpeg wrapper
├── tests/
├── requirements.txt
└── README.md
```

## Next Steps
1. Implement real SRT socket connection (replace srt-live-transmit)
2. Add video keyframe extraction
3. Add GOP structure analysis
4. Add alert/event system
5. Add recording functionality


## Native SRT Integration (v5.1)

### Direct libsrt binding
The backend now uses **ctypes** to directly call `libsrt.so` / `srt.dll`:

```python
from backend.libsrt_native import get_srt_lib

# Load library (auto-detects platform)
srt = get_srt_lib()

# Create socket
sock = srt.create_socket()

# Get real-time statistics
stats = srt.get_stats(sock)
print(f"RTT: {stats.rtt_ms}ms, Loss: {stats.loss_rate_percent}%")
```

### High-level connection
```python
from backend.srt_connection import SRTConnection, SRTConnectionConfig

config = SRTConnectionConfig(
    host="192.168.1.100",
    port=9000,
    latency_ms=120
)

conn = SRTConnection(config)
conn.on_stats(lambda s: print(s.to_dict()))
conn.connect()
```

### Supported Platforms
- **Linux**: `libsrt.so` (apt-get install libsrt-dev)
- **macOS**: `libsrt.dylib` (brew install srt)
- **Windows**: `srt.dll` (download from GitHub releases)

### SRT Statistics Available
- RTT, RTT variance
- Bandwidth (estimated, max, received)
- Packet loss (total, current interval, percentage)
- Packet drop (total, current interval, percentage)
- Retransmissions
- Buffer health (available, time span, TSBPD delay)
- Flight size, congestion window
- Belated packets
- Connection state

### Example Usage
```bash
# Run example
python examples/srt_stats_example.py srt://192.168.1.100:9000

# Run backend
python src/backend/main_v2.py
```
