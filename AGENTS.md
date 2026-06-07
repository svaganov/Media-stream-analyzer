# Media Stream Analyzer — Project Documentation

## Project Overview
Real-time media stream analysis application with support for SRT, RTMP, NDI, HLS, RTSP, MPEG-TS protocols.

## Architecture
- **Frontend**: HTML5 + Canvas (real-time meters, charts, video preview)
- **Backend**: Python (FFmpeg, libsrt, WebSocket)
- **Protocols**: SRT, RTMP, NDI, HLS, RTSP, MPEG-TS, SDI (Blackmagic DeckLink)
- **Deployment**: Docker container (local & cloud ready)

## Docker Deployment

### Quick Start
```bash
# Build and run full stack
docker-compose up --build

# Or use helper script
./build-and-run.sh all
```

### Services
| Service | Port | URL |
|---------|------|-----|
| Frontend | 8080 | http://localhost:8080 |
| WebSocket | 8765 | ws://localhost:8765 |
| SRT Test Source | 9000 | srt://localhost:9000 |

### Modes
- `all` — Full stack (backend + frontend + test source)
- `backend` — WebSocket server only
- `frontend` — HTTP static server only
- `test-source` — SRT test generator only
- `test-pipeline` — Run validation test and exit
- `bash` — Interactive shell

See `README-DOCKER.md` for full instructions.

## Unified Frontend Design (NEW)

### Design System v2.0
- **Single-page application** with tab-based navigation
- **Consistent color palette**: Dark theme (#0a0a0f, #12121a, #1a1a24)
- **Unified components**: DBFS meters, LUFS cards, stat cards, charts
- **Protocol-agnostic header**: Quick switch between SRT/RTMP/NDI/HLS/RTSP/MPEG-TS/SDI/Audio
- **Adaptive center panel**: Content changes based on selected tab (Overview/Audio/Video/Transport/Network/Logs)
- **Persistent sidebar**: Navigation + stream info + system status
- **Persistent right panel**: Alerts + quick settings

### Key UX Principles
1. **Same app feel**: All analysis types share identical layout, colors, typography
2. **Quick context switching**: Protocol selector in header (one click)
3. **Tab navigation**: Overview/Audio/Video/Transport/Network/Logs (left sidebar)
4. **Real-time feedback**: Animated meters, color-coded status, pulse indicators
5. **Responsive**: Grid layouts adapt to available space

### Files
- `src/frontend/unified_analyzer.html` — Main unified dashboard (54.9 KB)
- `src/frontend/audio_analyzer_final.html` — Sprint 2 audio-only (legacy)
- `src/frontend/video_stream_icecast.html` — Sprint 3 video (legacy)
- `src/frontend/video_stream_srt_smooth.html` — Sprint 4 SRT video (legacy)
- `src/frontend/live_stream_analyzer.html` — Sprint 5 live frontend (legacy)

## Sprint History

### Sprint 1: Project Setup & Audio Analysis (COMPLETED)
- IceCast stream analyzer
- DBFS meter (0 top, -70 bottom, solid colors)
- EBU R128 LUFS meter (M, S, I)
- True Peak detector
- FFT Spectrum analyzer
- Silence Detector
- Loudness History Graph (Youlean-style)

### Sprint 2: Audio Analyzers Enhancement (COMPLETED)
- EBU R128 Calculator
- DBFS meter with correct scale
- True Peak detector
- FFT Spectrum
- Silence Detector
- All analyzers in `src/analyzers/audio/`

### Sprint 3: Video Stream Analysis — IceCast Style (COMPLETED)
- Video stream mockup with keyframe preview
- Stream metadata display
- Technical specifications panel
- GOP structure visualization
- Two-column layout (video left, audio right)

### Sprint 4: SRT Video Stream Analysis (COMPLETED)
- SRT-specific metrics: RTT, Bandwidth, Packet Loss, Buffer Health
- SRT real-time charts with time windows (1m/5m/15m/30m/60m)
- SRT Connection status panel
- **Smooth Loudness History Graph** (Catmull-Rom spline, 60fps)
- Video keyframe with metadata overlay
- Technical specs: Codec, Resolution, Frame Rate, Bitrate, Color Space
- GOP structure: I/IDR/P/B frame visualization
- DBFS + LUFS meters (EBU R128 compliant)
- Layout: Left column (Video + SRT), Right column (Audio)

### Sprint 5: SRT Backend with FFmpeg Audio Integration (COMPLETED ✅ TESTED)
- **Native libsrt integration** via ctypes (direct C API binding)
- **FFmpeg audio decoder** for real-time PCM extraction from SRT
- **Stream Pipeline** orchestration (SRT → FFmpeg → AudioAnalyzer)
- **WebSocket Server v3** with full pipeline integration
- **Frontend WebSocket client** with real-time data binding
- **Video Keyframe + GOP Analysis**
- **Docker Container** for local deployment
- **Unified Frontend Design** — single app feel for all stream types

#### Sprint 5 Test Results (2026-06-06)
**Status: ALL TESTS PASSED ✅**

| Metric | Expected | Actual | Status |
|--------|----------|--------|--------|
| SRT Connection | Stable | 12,529 packets, 102 MB | ✅ |
| DBFS | 0.0 dBFS | -0.4 dBFS | ✅ |
| LUFS M/S/I | -3.7 LUFS | -4.1 LUFS | ✅ |
| True Peak | 0.0 dBTP | -0.4 dBTP | ✅ |
| Pipeline Stability | 8+ seconds | 668 audio blocks | ✅ |
| Data Rate | High | 102 Mbps | ✅ |

**Test Environment:** Linux (Debian 12), FFmpeg 5.1.8, Python 3.11
**Test Signal:** aevalsrc sin(2*PI*1000*t), amplitude 1.0, 48kHz stereo
**SRT Pipeline:** FFmpeg listener (port 9000) → FFmpeg caller → PCM f32le → AudioAnalyzer

**Test Artifacts:** `tests/sprint5_validation/`
- `test_srt_source.py` — SRT test source generator
- `test_srt_pipeline.py` — CLI dashboard test
- `test_srt_integration.py` — WebSocket + SRT integration
- `test_ws_client.html` — Frontend WebSocket client
- `SRT_TEST_README.md` — Test instructions
- `SPRINT5_TEST_REPORT.md` — Full test report

### Sprint 6: MPEG-TS Transport Analysis (PLANNED)
- **MPEG-TS Demuxer** for transport-level analysis
- **PSI/SI Tables parsing** (PAT, PMT, SDT, EIT)
- **TS Health Dashboard** (PCR accuracy, null packet ratio)
- **Broadcast compliance checks** (TR 101 290)

## File Structure
```
media-stream-analyzer/
├── Dockerfile                         # Docker image definition
├── docker-compose.yml                 # Docker Compose orchestration
├── entrypoint.sh                      # Container entrypoint script
├── build-and-run.sh                   # Helper build script
├── .dockerignore                      # Docker ignore rules
├── README-DOCKER.md                   # Docker deployment guide
├── AGENTS.md                          # Main project documentation
├── PROJECT_STRUCTURE.md               # Complete file structure
├── PROJECT_SUMMARY.md                 # Executive summary
├── README.md                          # Quick start guide
├── requirements.txt                   # Python dependencies
│
├── src/
│   ├── backend/
│   │   ├── main.py, main_v2.py, main_v3.py
│   │   ├── websocket_server.py, websocket_server_v2.py, websocket_server_v3.py
│   │   ├── stream_pipeline.py, srt_client.py, srt_connection.py
│   │   ├── libsrt_native.py, alert_manager.py, config.py
│   ├── analyzers/
│   │   ├── audio/audio_analyzer.py, ffmpeg_audio_decoder.py
│   │   └── video/stream_decoder.py, keyframe_extractor.py, stream_metadata.py, ts_demuxer.py
│   └── frontend/
│       ├── unified_analyzer.html      # ⭐ NEW: Unified dashboard (all protocols)
│       ├── audio_analyzer_final.html  # Sprint 2 audio-only
│       ├── video_stream_icecast.html  # Sprint 3 video
│       ├── video_stream_srt_smooth.html # Sprint 4 SRT
│       └── live_stream_analyzer.html  # Sprint 5 live
│
├── docs/
│   ├── EBU_R128_Guide.md, SRT_Protocol.md, API_Reference.md
│   ├── FULL_DOCUMENTATION.md, SPRINT_5_PLAN.md, SPRINT_6_PLAN.md
│   └── MPEG_TS_Transport.md
│
├── tests/
│   ├── test_audio_analyzer.py, test_srt_backend.py, test_libsrt_native.py
│   ├── test_ffmpeg_audio_decoder.py, test_stream_pipeline.py
│   ├── test_keyframe_extractor.py, test_alert_manager.py
│   ├── test_stream_metadata.py, test_websocket.py, test_ts_demuxer.py
│   └── sprint5_validation/
│       ├── test_srt_source.py, test_srt_pipeline.py
│       ├── test_srt_integration.py, test_ws_client.html
│       ├── SRT_TEST_README.md, SPRINT5_TEST_REPORT.md
│
└── examples/
    ├── srt_stats_example.py, pipeline_example.py
```

## Design System Governance (NEW)

### Обязательное правило
**Перед изменением любого макета страницы — обязательно сверяться с `DESIGN_SYSTEM.md`.**

### Правило утверждения дизайна (CRITICAL)
**Любое изменение в дизайне утверждённых элементов, стилей или общего макета требует подтверждения от пользователя.**

- Элементы со статусом **"УТВЕРЖДЕНО"** изменять запрещено без явного разрешения.
- Перед изменением таких элементов необходимо сформулировать вопрос и ждать ответа.
- Список утверждённых файлов:
  - `theme_main.css` — ✅ УТВЕРЖДЕНО
  - `LAYOUT_SPECIFICATION.md` — ✅ УТВЕРЖДЕНО
  - `DESIGN_SYSTEM.md` — ✅ УТВЕРЖДЕНО
- Новые элементы можно добавлять свободно, если они следуют утверждённой дизайн-системе.
- Если новый элемент конфликтует с утверждённым — требуется подтверждение.

- Все CSS переменные определены в `src/frontend/theme_main.css`
- Все компоненты, цвета, типографика, layout описаны в `DESIGN_SYSTEM.md`
- Любое отклонение от Design System требует обновления DESIGN_SYSTEM.md **перед** изменением кода
- Новые компоненты должны следовать BEM-нотации и использовать CSS variables из theme_main.css

### Файлы дизайн-системы
| Файл | Назначение | Статус |
|------|-----------|--------|
| `DESIGN_SYSTEM.md` | Требования, правила, спецификации компонентов | ✅ УТВЕРЖДЕНО |
| `LAYOUT_SPECIFICATION.md` | Технический макет: имена зон, видимость по протоколам, CSS классы | ✅ УТВЕРЖДЕНО |
| `src/frontend/theme_main.css` | CSS variables, базовые стили, компоненты | ✅ УТВЕРЖДЕНО |
| `src/frontend/unified_analyzer.html` | Эталонный макет (референс) | 🔄 В разработке |
| `PAGE_STRUCTURE_ASCII.md` | ASCII структура одной страницы с вкладками | ✅ УТВЕРЖДЕНО |

### История изменений утверждённых файлов
| Дата | Изменение | Инициатор |
|------|-----------|-----------|
| 2026-06-07 | Удалена зона `sidebar` из GridZone. Nav-tabs перенесены в header (horizontal). Stream-info перенесён в right-panel. | Пользователь (явная команда) |

### Порядок сверки при изменении макета
1. Открыть `LAYOUT_SPECIFICATION.md` — проверить имена зон и их видимость
2. Открыть `DESIGN_SYSTEM.md` — проверить требования к компонентам
3. Открыть `theme_main.css` — проверить CSS классы и переменные
4. Только после этого вносить изменения в HTML/CSS

### Design System v1.0 включает
- Цветовую палитру (тёмная тема, 3 статуса)
- Типографику (sans + mono, 12 размеров)
- Layout grid (header 48px + sidebar 200px + center + right 280px)
- 15+ компонентов (card, meter, chart, alert, badge, form, etc.)
- Протокол-специфичные адаптации (8 протоколов)
- Анимации (50fps DBFS, 1s charts)
- Accessibility (контраст, focus states)

## Key Design Decisions
- DBFS scale: 0 dBFS at top, -70 dBFS at bottom (solid colors, no gradients)
- LUFS target: -23 LUFS (EBU R128)
- Loudness History: 60-second window, 1-second update, 60fps smooth animation
- SRT charts: 1-second update, configurable time windows
- Color coding: Green (safe), Yellow (warning), Red (danger)
- **Sprint 5 architecture**: FFmpeg for media decode + libsrt for statistics
- **Sprint 6 architecture**: Hybrid — FFmpeg for media + custom demuxer for TS metadata
- **Deployment**: Docker container with Debian 12, FFmpeg 5.1.8, Python 3.11
- **Unified UX**: Single-page app with protocol-agnostic design system

## Docker Network Modes

### Host Network (Linux — рекомендуется)
- **Все порты доступны без ограничений**
- Контейнер использует сетевые интерфейсы хоста напрямую
- Подходит для тестирования потоков из интернета на любых портах
- Запуск: `docker-compose up` или `./build-and-run.sh all host`

### Bridge Network (macOS/Windows)
- Проброс конкретных портов через NAT
- Добавьте нужные порты в `docker-compose.yml` → `ports:`
- Запуск: `./build-and-run.sh all bridge`

### Поддерживаемые протоколы и порты
| Протокол | Порт | Описание |
|----------|------|----------|
| SRT | 9000+ | Настраиваемый, любой порт |
| RTMP | 1935 | Стандартный RTMP порт |
| RTSP | 554 | Стандартный RTSP порт |
| HLS | 80/443 | HTTP/HTTPS streaming |
| NDI | 49952-49959 | NDI discovery ports |
| MPEG-TS | 5000-5010 | UDP multicast/unicast |

## Next Steps
1. ✅ Sprint 5: Complete, tested, Dockerized, unified frontend
2. Sprint 6: Implement MPEG-TS transport-level analysis
3. Expand to RTMP, NDI, HLS protocols
4. Add recording and logging functionality

---
*Last updated: 2026-06-06*
*Version: 5.3*
*Status: Sprint 5 Complete, Tested, Dockerized & Unified — Sprint 6 Planning*
