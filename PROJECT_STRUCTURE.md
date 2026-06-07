# Media Stream Analyzer — Project Structure

## Directory Layout

```
media-stream-analyzer/
├── AGENTS.md                          # Main project documentation
├── PROJECT_STRUCTURE.md               # This file
├── PROJECT_SUMMARY.md                 # Executive summary
├── README.md                          # Quick start guide
├── requirements.txt                   # Python dependencies
│
├── src/
│   ├── backend/
│   │   ├── __init__.py
│   │   ├── main.py                    # Entry point (Sprint 1-3)
│   │   ├── main_v2.py                 # SRT native entry (Sprint 4)
│   │   ├── main_v3.py                 # Full pipeline entry (Sprint 5)
│   │   ├── websocket_server.py        # Basic WS (Sprint 3)
│   │   ├── websocket_server_v2.py     # Native SRT WS (Sprint 4)
│   │   ├── websocket_server_v3.py     # Full pipeline WS (Sprint 5)
│   │   ├── stream_pipeline.py         # Pipeline orchestration (Sprint 5)
│   │   ├── srt_client.py              # srt-live-transmit wrapper (Sprint 4)
│   │   ├── srt_connection.py          # Native SRT connection (Sprint 5)
│   │   ├── libsrt_native.py          # ctypes binding (Sprint 5)
│   │   ├── alert_manager.py           # Alert system (Sprint 5)
│   │   └── config.py                  # Configuration
│   │
│   ├── analyzers/
│   │   ├── __init__.py
│   │   ├── audio/
│   │   │   ├── __init__.py
│   │   │   ├── audio_analyzer.py      # DBFS/LUFS/True Peak/LRA
│   │   │   └── ffmpeg_audio_decoder.py # FFmpeg PCM extraction (Sprint 5)
│   │   └── video/
│   │       ├── __init__.py
│   │       ├── stream_decoder.py      # FFmpeg video decoder
│   │       ├── keyframe_extractor.py  # Keyframe extraction (Sprint 5)
│   │       ├── stream_metadata.py     # Metadata parser (Sprint 5)
│   │       └── ts_demuxer.py          # MPEG-TS demuxer (Sprint 6)
│   │
│   └── frontend/
│       ├── audio_analyzer_final.html      # Sprint 2 mockup
│       ├── video_stream_icecast.html      # Sprint 3 mockup
│       ├── video_stream_srt_smooth.html   # Sprint 4 mockup
│       └── live_stream_analyzer.html      # Sprint 5 live frontend
│
├── docs/
│   ├── EBU_R128_Guide.md              # EBU R128 standard guide
│   ├── SRT_Protocol.md                # SRT protocol documentation
│   ├── API_Reference.md               # WebSocket/REST API specs
│   ├── FULL_DOCUMENTATION.md          # Complete documentation
│   ├── SPRINT_5_PLAN.md               # Sprint 5 plan
│   ├── SPRINT_6_PLAN.md               # Sprint 6 plan
│   ├── MPEG_TS_Transport.md           # MPEG-TS documentation (Sprint 6)
│   ├── DESIGN_SYSTEM.md               # Design System v1.0 (colors, typography, components)
│   └── LAYOUT_SPECIFICATION.md        # Technical layout: zones, sections, CSS classes
│
├── tests/
│   ├── test_audio_analyzer.py         # Audio analysis tests
│   ├── test_srt_backend.py            # SRT backend tests
│   ├── test_libsrt_native.py          # Native SRT tests
│   ├── test_ffmpeg_audio_decoder.py    # FFmpeg decoder tests
│   ├── test_stream_pipeline.py         # Pipeline tests
│   ├── test_keyframe_extractor.py     # Keyframe tests
│   ├── test_alert_manager.py          # Alert system tests
│   ├── test_stream_metadata.py         # Metadata parser tests
│   └── test_websocket.py              # WebSocket tests
│
├── examples/
│   ├── srt_stats_example.py           # SRT stats CLI example
│   └── pipeline_example.py            # Full pipeline CLI example
│
└── mockups/
    ├── audio_analyzer_final.html      # Sprint 2 final mockup
    ├── video_stream_icecast.html      # Sprint 3 mockup
    ├── video_stream_srt_v4.2.html     # Sprint 4 mockup
    └── video_stream_srt_smooth.html   # Sprint 4 smooth loudness
```

## Sprint Deliverables

### Sprint 1: Audio Analysis
- `src/analyzers/audio/audio_analyzer.py` (initial)
- `frontend/audio_analyzer_final.html`

### Sprint 2: Audio Enhancement
- `src/analyzers/audio/audio_analyzer.py` (updated)
- `tests/test_audio_analyzer.py`

### Sprint 3: Video Stream UI
- `frontend/video_stream_icecast.html`
- `src/backend/websocket_server.py`

### Sprint 4: SRT Stream Analysis
- `frontend/video_stream_srt_smooth.html`
- `src/backend/srt_client.py`
- `src/backend/websocket_server_v2.py`
- `src/backend/libsrt_native.py` (initial)

### Sprint 5: Complete Backend
- `src/backend/main_v3.py`
- `src/backend/websocket_server_v3.py`
- `src/backend/stream_pipeline.py`
- `src/backend/srt_connection.py`
- `src/backend/libsrt_native.py` (complete)
- `src/backend/alert_manager.py`
- `src/analyzers/audio/ffmpeg_audio_decoder.py`
- `src/analyzers/video/keyframe_extractor.py`
- `src/analyzers/video/stream_metadata.py`
- `frontend/live_stream_analyzer.html`
- `examples/srt_stats_example.py`
- `examples/pipeline_example.py`

### Sprint 6: MPEG-TS Transport (Planned)
- `src/analyzers/video/ts_demuxer.py`
- `src/analyzers/video/ts_packet.py`
- `src/analyzers/video/pcr_analyzer.py`
- `src/analyzers/video/psi_parser.py`
- `src/analyzers/video/ts_health_monitor.py`
- `tests/test_ts_demuxer.py`

## File Size Summary

| Component | Files | Approx. Size |
|-----------|-------|-------------|
| Backend | 12 | ~85 KB |
| Analyzers | 7 | ~65 KB |
| Frontend | 4 | ~120 KB |
| Tests | 9 | ~35 KB |
| Documentation | 8 | ~45 KB |
| Examples | 2 | ~8 KB |
| **Total** | **42** | **~358 KB** |

## Key Design Patterns

### Pipeline Pattern
```python
StreamPipeline:
  SRTConnection → FFmpegAudioDecoder → AudioAnalyzer
              ↓
  VideoKeyframeExtractor → GOPStructure
              ↓
  AlertManager → WebSocket Broadcast
```

### Observer Pattern
All components use callbacks for loose coupling:
```python
component.on_event(callback)
component._notify_callbacks(data)
```

### Factory Pattern
```python
get_srt_lib() → LibSRTNative singleton
```

## Dependencies

### Python Packages
```
asyncio
websockets>=11.0
numpy>=1.24.0
scipy>=1.10.0
Pillow>=10.0.0
pydantic>=2.0.0
pytest>=7.3.0
pytest-asyncio>=0.21.0
```

### System Dependencies
```
ffmpeg
libsrt (libsrt.so / srt.dll / libsrt.dylib)
```

## Configuration Hierarchy

1. **Environment variables** (highest priority)
2. **Config file** (`config.py`)
3. **Default values** (lowest priority)

## Testing Strategy

| Test Type | Tool | Coverage |
|-----------|------|----------|
| Unit tests | pytest | Individual components |
| Integration tests | pytest-asyncio | Pipeline workflows |
| End-to-end | Manual | Frontend + Backend |
| Performance | pytest-benchmark | Real-time constraints |
