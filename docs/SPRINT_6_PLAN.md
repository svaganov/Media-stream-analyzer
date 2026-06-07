# Sprint 6: MPEG-TS Transport Analysis

## Overview
Add MPEG-TS (Transport Stream) level analysis for broadcast-grade monitoring.
While Sprint 5 uses FFmpeg for media decode, Sprint 6 adds custom demuxer for transport-level metadata.

## Goals
1. Parse MPEG-TS packets at transport level
2. Extract PCR, PTS, DTS timing information
3. Detect transport errors (CC, TEI, sync loss)
4. Parse PSI/SI tables (PAT, PMT, SDT)
5. Display TS Health dashboard

## Architecture
```
SRT Stream
    │
    ▼
┌─────────────────┐
│  MPEG-TS Packet │  <- 188-byte packets
│  Reader         │
└─────────────────┘
    │
    ├─────────────────────┬─────────────────────┐
    │                     │                     │
    ▼                     ▼                     ▼
┌─────────┐        ┌─────────┐          ┌─────────┐
│ TS Demux│        │ FFmpeg  │          │ PSI     │
│ (Sprint6)│        │ (Sprint5)│          │ Parser  │
│         │        │         │          │ (Sprint6)│
│ • PID   │        │ • Audio │          │ • PAT   │
│ • PCR   │        │ • Video │          │ • PMT   │
│ • CC    │        │ • Decode│          │ • SDT   │
│ • TEI   │        │         │          │ • EIT   │
└─────────┘        └─────────┘          └─────────┘
    │                     │                     │
    └─────────────────────┼─────────────────────┘
                          │
                          ▼
                   ┌─────────────┐
                   │  WebSocket  │
                   │  Broadcast  │
                   └─────────────┘
```

## Implementation Plan

### Phase 1: MPEG-TS Demuxer (Week 1)
- [ ] TS packet parser (188-byte sync)
- [ ] PID filter and demultiplexing
- [ ] Continuity Counter validation
- [ ] Adaptation field parsing (PCR, OPCR)
- [ ] Transport Error Indicator tracking

### Phase 2: PCR Analysis (Week 2)
- [ ] PCR extraction from adaptation field
- [ ] PCR jitter calculation (delta between PCR values)
- [ ] PCR accuracy ( deviation from 27MHz clock)
- [ ] PCR drift rate
- [ ] PTS/DTS extraction and validation

### Phase 3: PSI/SI Parsing (Week 3)
- [ ] PAT parser (Program Association Table)
- [ ] PMT parser (Program Map Table)
- [ ] SDT parser (Service Description Table)
- [ ] EIT parser (Event Information Table)
- [ ] DVB descriptor parsing

### Phase 4: TS Health Dashboard (Week 4)
- [ ] TR 101 290 Priority 1 errors
  - TS sync loss
  - Sync byte error
  - PAT error
  - Continuity count error
  - PMT error
  - PID error
- [ ] TR 101 290 Priority 2 errors
  - Transport error
  - CRC error
  - PCR error
  - PCR accuracy error
  - PTS error
  - CAT error
- [ ] Null packet ratio monitoring
- [ ] Bitrate per PID calculation

## New Files
```
src/
├── analyzers/video/
│   ├── ts_demuxer.py           # Core TS demuxer
│   ├── ts_packet.py             # TS packet structure
│   ├── pcr_analyzer.py          # PCR jitter analysis
│   ├── psi_parser.py            # PSI/SI table parser
│   └── ts_health_monitor.py     # TR 101 290 compliance
└── backend/
    └── ts_stats_broadcaster.py  # TS stats WebSocket broadcast
```

## Metrics to Display

### TS Transport Metrics
| Metric | Description | Unit |
|--------|-------------|------|
| sync_loss_count | TS sync byte errors | count |
| cc_errors | Continuity counter errors | count |
| tei_count | Transport error indicators | count |
| pcr_jitter | PCR jitter | ns |
| pcr_accuracy | PCR accuracy | ns |
| null_ratio | Null packet ratio | % |
| bitrate_total | Total TS bitrate | Mbps |
| bitrate_video | Video PID bitrate | Mbps |
| bitrate_audio | Audio PID bitrate | Mbps |

### PSI/SI Status
| Table | Status | Update Time |
|-------|--------|-------------|
| PAT | Valid/Invalid | ms |
| PMT | Valid/Invalid | ms |
| SDT | Present/Absent | ms |
| EIT | Present/Absent | ms |

### TR 101 290 Compliance
| Priority | Error | Count | Status |
|----------|-------|-------|--------|
| P1 | TS sync loss | 0 | ✅ |
| P1 | Sync byte error | 0 | ✅ |
| P1 | PAT error | 0 | ✅ |
| P1 | CC error | 0 | ✅ |
| P2 | Transport error | 0 | ✅ |
| P2 | PCR error | 0 | ✅ |
| P2 | PCR accuracy | 12ns | ✅ |
| P2 | PTS error | 0 | ✅ |

## UI Mockup
```
┌─────────────────────────────────────────┐
│  📊 MPEG-TS Transport Analysis          │
├─────────────────────────────────────────┤
│  TS Sync:     ✅ Locked (188 bytes)     │
│  PAT/PMT:     ✅ Valid (updated 120ms)  │
│  CC Errors:   0           ✅            │
│  TEI Count:   0           ✅            │
│  PCR Jitter:  12 ns       ✅            │
│  PCR Accuracy: ±2 ns      ✅            │
│  Null Ratio:  2.3%        ⚠️            │
├─────────────────────────────────────────┤
│  PID Bitrates:                          │
│  0x000 (PAT):   0.15 Mbps               │
│  0x100 (Video): 8.50 Mbps               │
│  0x101 (Audio): 0.38 Mbps               │
│  0x1FFF (Null): 0.52 Mbps               │
├─────────────────────────────────────────┤
│  TR 101 290 Compliance:                 │
│  Priority 1: 0 errors     ✅ PASS        │
│  Priority 2: 0 errors     ✅ PASS        │
│  Priority 3: 2 warnings   ⚠️ REVIEW      │
└─────────────────────────────────────────┘
```

## Dependencies
- `python-dvb` or custom TS parser
- `crc32c` for CRC validation
- `bitstruct` for bit-level parsing

## References
- ISO/IEC 13818-1 (MPEG-2 Systems)
- ETSI TR 101 290 (DVB Measurement Guidelines)
- ETSI EN 300 468 (DVB SI Specifications)
