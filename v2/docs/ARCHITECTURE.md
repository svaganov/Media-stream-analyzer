# Media Stream Analyzer v2 — Architecture

## Overview
Clean rewrite starting from Sprint 1 (Audio Analysis) with future-proof architecture.

## Principles
1. **Protocol-agnostic**: Input layer abstracts SRT/RTMP/NDI/File
2. **Single entry point**: `uvicorn v2.src.main:app`
3. **Plugin architecture**: Analyzers and inputs register via factories
4. **Immutable contracts**: All data models in `core/models.py`
5. **Test-driven**: Every module has tests from day one

## Layer Diagram

```
Frontend (Browser)
    │ WS / HTTP
    ▼
FastAPI (REST + WebSocket)
    │
    ▼
SessionManager → Pipeline → Broadcaster
    │
    ├── InputLayer (SRT/RTMP/File)
    ├── DecodeLayer (FFmpeg)
    ├── AnalyzeLayer (Audio/Video/Transport)
    ├── AggregateLayer (Metrics + History + Alerts)
    └── OutputLayer (WebSocket / SSE / File)
```

## Sprint Roadmap

| Sprint | Focus | Deliverables |
|--------|-------|--------------|
| 1 | Audio Foundation | DBFS, LUFS, True Peak, FFT, Silence, History |
| 2 | Audio Enhancement | EBU R128 compliance, calibration, multi-channel |
| 3 | Video UI | Keyframe preview, metadata, GOP structure |
| 4 | SRT Protocol | Native libsrt, real-time stats, charts |
| 5 | Pipeline + Backend | FFmpeg integration, WebSocket, alerts |
| 6 | MPEG-TS Transport | PCR, PSI/SI, TR 101 290 |
| 7 | Multi-Protocol | RTMP, NDI, HLS support |
| 8 | Enterprise | Recording, REST API, auth |
