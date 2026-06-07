# Media Stream Analyzer — Технический макет страницы (Layout Specification)

> **Назначение:** Определение именованных зон и разделов страницы.  
> **Правило:** Все зоны имеют фиксированные имена CSS-классов. Содержимое зон меняется в зависимости от `protocol`.  
> **Перед изменением макета — сверяться с DESIGN_SYSTEM.md и этим документом.**
> **GRID Layout (утверждён 2026-06-07):** Применяется для всех видео-протоколов: SRT, NDI, RTMP, MPEG-TS, HLS.

---

## 1. Общая структура страницы (Grid Zones)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ZONE: app-header                  (48px height, 100% width)                │
│  ├── section: app-logo                                                      │
│  ├── section: nav-tabs (horizontal)                                         │
│  ├── section: protocol-selector                                             │
│  └── section: connection-status                                             │
├──────────────────────────────────────────────┬──────────────────────────────┤
│ ZONE: center-panel                            │ ZONE: right-panel            │
│  ├── section: connection-form                 │  ├── section: stream-info    │
│  │   ├── field: url-input                     │  ├── section: alerts       │
│  │   ├── field: latency-input                 │  └── section: quick-settings│
│  │   └── field: action-buttons                 │                              │
│  ├── section: tab-content                     │                              │
│  │   ├── zone: primary-metrics               │                              │
│  │   ├── zone: media-preview                  │                              │
│  │   ├── zone: transport-metrics              │                              │
│  │   ├── zone: audio-metrics                  │                              │
│  │   ├── zone: video-metrics                  │                              │
│  │   ├── zone: network-metrics                │                              │
│  │   └── zone: logs                           │                              │
│  └── section: tab-navigator (vertical)        │                              │
│       ├── tab: overview                       │                              │
│       ├── tab: audio                          │                              │
│       ├── tab: video                          │                              │
│       ├── tab: transport                      │                              │
│       ├── tab: network                        │                              │
│       └── tab: logs                           │                              │
└──────────────────────────────────────────────┴──────────────────────────────┘
```

---

## 1.1 GRID Layout для видео-протоколов (УТВЕРЖДЁНО)

**Статус:** ✅ УТВЕРЖДЕНО (2026-06-07)

**Применимость:** SRT, NDI, RTMP, MPEG-TS, HLS

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ZONE: app-header                  (48px height, 100% width)                │
│  ├── section: app-logo                                                      │
│  ├── section: nav-tabs (horizontal)                                         │
│  ├── section: protocol-selector                                             │
│  └── section: connection-status                                             │
├──────────────────────────────────────────────┬──────────────────────────────┤
│ ZONE: center-panel                            │ ZONE: right-panel            │
│  ├── section: connection-form                 │  ├── section: stream-info    │
│  │   ├── field: url-input                     │  ├── section: alerts         │
│  │   ├── field: latency-input                 │  └── section: quick-settings │
│  │   └── field: action-buttons               │                              │
│  ├── section: tab-content                     │                              │
│  │   ├── zone: primary-metrics               │                              │
│  │   ├── zone: media-preview                  │                              │
│  │   ├── zone: transport-metrics              │                              │
│  │   ├── zone: audio-metrics                  │                              │
│  │   ├── zone: video-metrics                  │                              │
│  │   ├── zone: network-metrics                │                              │
│  │   └── zone: logs                           │                              │
│  └── section: tab-navigator (vertical)        │                              │
│       ├── tab: overview                       │                              │
│       ├── tab: audio                          │                              │
│       ├── tab: video                          │                              │
│       ├── tab: transport                      │                              │
│       ├── tab: network                        │                              │
│       └── tab: logs                           │                              │
└──────────────────────────────────────────────┴──────────────────────────────┘
```

**Особенности видео-протоколов:**
- Вкладка **Video** всегда видима
- Вкладка **Transport** видима для SRT и MPEG-TS
- Вкладка **Network** видима для всех видео-протоколов
- **Latency input** видим только для SRT

---

## 2. Описание зон (Zones)

### 2.1 ZONE: app-header
**Фиксированная высота:** 48px  
**Фон:** `--bg-secondary`  
**Граница:** bottom 1px `--border`  
**Общая для всех протоколов:** ✅ Да

| Section | Назначение | Протокол-специфично |
|---------|-----------|---------------------|
| `app-logo` | Логотип + название | ❌ Нет |
| `protocol-selector` | Dropdown выбора протокола | ❌ Нет (список общий) |
| `connection-status` | WS dot + текст статуса | ❌ Нет |

---

### 2.2 ZONE: sidebar — УДАЛЕНА (перенесена в header и right-panel)
**Статус:** Убрана из GridZone.  
**Причина:** Освобождение горизонтального пространства для content.

**Что куда перенесено:**
| Было в sidebar | Стало в | Назначение |
|----------------|---------|------------|
| `nav-tabs` | `app-header` → `nav-tabs` | Горизонтальные табы в header |
| `stream-info` | `right-panel` → `stream-info` | Информация о потоке над alerts |

**Новая структура header:**
```
app-header
  ├── app-logo
  ├── nav-tabs (horizontal) ← БЫЛО в sidebar
  ├── protocol-selector
  └── connection-status
```

**Новая структура right-panel:**
```
right-panel
  ├── stream-info ← БЫЛО в sidebar
  ├── alerts
  └── quick-settings
```
| Field | SRT | IceCast | RTMP | HLS | RTSP | NDI | MPEG-TS | SDI |
|-------|-----|---------|------|-----|------|-----|---------|-----|
| `info-protocol` | SRT | IceCast | RTMP | HLS | RTSP | NDI | MPEG-TS | SDI |
| `info-state` | Connected/Disconnected | Connected/Disconnected | — | — | — | — | — | — |
| `info-duration` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `info-packets` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| `info-data` | ✅ MB | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ MB | ❌ |
| `info-bitrate` | ✅ Mbps | ✅ kbps | ✅ Mbps | ✅ Mbps | ✅ Mbps | ✅ Mbps | ✅ Mbps | ✅ Mbps |
| `info-latency` | ✅ ms | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `info-rtt` | ✅ ms | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `info-resolution` | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `info-codec` | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

---

### 2.3 ZONE: center-panel
**Гибкая ширина:** flex: 1  
**Фон:** `--bg-primary`  
**Прокрутка:** vertical auto  
**Общая для всех протоколов:** ✅ Да (содержимое меняется)

| Section | Назначение | Протокол-специфично |
|---------|-----------|---------------------|
| `connection-form` | Форма подключения | Частично (latency поле только SRT) |
| `tab-content` | Контейнер вкладок | Да (содержимое по вкладкам) |
| `tab-navigator` | Переключатель вкладок | Да (видимость табов) |

---

### 2.4 ZONE: right-panel
**Фиксированная ширина:** 280px  
**Фон:** `--bg-secondary`  
**Граница:** left 1px `--border`  
**Общая для всех протоколов:** ✅ Да

| Section | Назначение | Протокол-специфично |
|---------|-----------|---------------------|
| `alerts` | Список алертов | Нет (алерты универсальны) |
| `quick-settings` | Быстрые настройки | Частично (latency только SRT) |

---

## 3. Зоны внутри tab-content (по вкладкам)

### 3.1 Вкладка: overview (Обзор)
**CSS класс:** `.tab-content--overview`  
**Видимость:** Все протоколы ✅

```
zone: overview-layout
  ├── zone: primary-metrics (карточки верхнего ряда)
  │   ├── card: metric-dbfs-peak
  │   ├── card: metric-lufs-momentary
  │   ├── card: metric-true-peak
  │   ├── card: metric-stream-bitrate
  │   └── card: metric-stream-state
  └── zone: secondary-metrics (карточки нижнего ряда)
      ├── card: metric-srt-rtt        [SRT only]
      ├── card: metric-packet-loss    [SRT, MPEG-TS]
      ├── card: metric-bandwidth      [SRT, MPEG-TS]
      ├── card: metric-buffer-health  [SRT only]
      ├── card: metric-video-codec    [Video protocols]
      ├── card: metric-resolution      [Video protocols]
      └── card: metric-frame-rate     [Video protocols]
```

**Карточки по протоколам:**
| Card | SRT | IceCast | RTMP | HLS | RTSP | NDI | MPEG-TS | SDI |
|------|-----|---------|------|-----|------|-----|---------|-----|
| `metric-dbfs-peak` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `metric-lufs-momentary` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `metric-true-peak` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `metric-stream-bitrate` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `metric-stream-state` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `metric-srt-rtt` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `metric-packet-loss` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| `metric-bandwidth` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| `metric-buffer-health` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `metric-video-codec` | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `metric-resolution` | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `metric-frame-rate` | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

---

### 3.2 Вкладка: audio (Аудио)
**CSS класс:** `.tab-content--audio`  
**Видимость:** Все протоколы ✅

```
zone: audio-layout
  ├── zone: dbfs-meters
  │   ├── meter: dbfs-left-channel
  │   └── meter: dbfs-right-channel
  ├── zone: lufs-cards
  │   ├── card: lufs-momentary
  │   ├── card: lufs-shortterm
  │   └── card: lufs-integrated
  ├── zone: lufs-extra
  │   ├── card: true-peak
  │   └── card: loudness-range-lra
  └── zone: loudness-history
      └── chart: lufs-history-chart (60s window)
```

**Общая для всех протоколов:** ✅ Полностью  
**Все зоны и карточки показываются для любого протокола.**

---

### 3.3 Вкладка: video (Видео)
**CSS класс:** `.tab-content--video`  
**Видимость:** SRT, RTMP, HLS, RTSP, NDI, MPEG-TS, SDI ✅ | IceCast ❌

```
zone: video-layout
  ├── zone: keyframe-preview
  │   ├── element: video-image (16:9)
  │   └── overlay: video-badges
  │       ├── badge: video-codec
  │       ├── badge: video-resolution
  │       ├── badge: video-frame-rate
  │       └── badge: video-frame-type (I/IDR/P/B)
  ├── zone: video-technical-data
  │   ├── card: tech-codec
  │   ├── card: tech-resolution
  │   ├── card: tech-frame-rate
  │   ├── card: tech-bitrate
  │   ├── card: tech-color-space
  │   └── card: tech-profile
  └── zone: gop-structure
    └── element: gop-frame-sequence
```

---

### 3.4 Вкладка: transport (Транспорт)
**CSS класс:** `.tab-content--transport`  
**Видимость:** SRT, MPEG-TS ✅ | Остальные ❌

#### Для SRT:
```
zone: transport-layout--srt
  ├── zone: srt-connection-status
  │   ├── element: status-badge (Connected/Disconnected)
  │   └── zone: srt-metrics-grid
  │       ├── metric: srt-rtt
  │       ├── metric: srt-bandwidth
  │       ├── metric: srt-packet-loss
  │       └── metric: srt-buffer
  └── zone: srt-charts
      ├── chart: srt-rtt-chart
      ├── chart: srt-bandwidth-chart
      ├── chart: srt-packet-loss-chart
      └── chart: srt-buffer-chart
```

#### Для MPEG-TS (Sprint 6):
```
zone: transport-layout--mpegts
  ├── zone: ts-health-monitor
  │   ├── metric: ts-pcr-accuracy
  │   ├── metric: ts-cc-errors
  │   ├── metric: ts-null-packet-ratio
  │   └── metric: ts-bitrate
  ├── zone: ts-tables
  │   ├── table: pat-table
  │   ├── table: pmt-table
  │   └── table: sdt-table
  └── zone: ts-tr101290
      ├── section: priority-1-errors
      ├── section: priority-2-errors
      └── section: priority-3-errors
```

---

### 3.5 Вкладка: network (Сеть)
**CSS класс:** `.tab-content--network`  
**Видимость:** SRT, RTMP, HLS, RTSP, NDI, MPEG-TS ✅ | IceCast, SDI ❌

```
zone: network-layout
  ├── zone: network-metrics
  │   ├── card: net-packets-received
  │   ├── card: net-bytes-received
  │   ├── card: net-retransmissions    [SRT only]
  │   ├── card: net-belated-packets   [SRT only]
  │   └── card: net-jitter            [SRT, MPEG-TS]
  └── zone: network-charts
      ├── chart: network-throughput
      └── chart: network-latency
```

---

### 3.6 Вкладка: logs (Логи)
**CSS класс:** `.tab-content--logs`  
**Видимость:** Все протоколы ✅

```
zone: logs-layout
  └── zone: logs-container
      ├── element: log-entry (timestamp + level + message)
      ├── element: log-entry
      └── ...
```

---

## 4. CSS классы зон (Reference)

### Глобальные зоны
```css
.app                    /* Корневой контейнер */
.app__header            /* ZONE: app-header */
.app__main              /* ZONE: main (grid) — 2 колонки: center + right */
/* .app__sidebar — УДАЛЕНО из grid */
.app__center            /* ZONE: center-panel */
.app__right-panel       /* ZONE: right-panel */
```

### Header секции
```css
.header__logo           /* section: app-logo */
.header__protocol       /* section: protocol-selector */
.header__status         /* section: connection-status */
```

### Header секции (обновлённые)
```css
.header__logo           /* section: app-logo */
.header__nav-tabs       /* section: nav-tabs ← БЫЛО sidebar__nav */
.header__protocol       /* section: protocol-selector */
.header__status         /* section: connection-status */
```

### Right panel секции (обновлённые)
```css
.right-panel            /* ZONE: right-panel */
.right-panel__stream-info /* section: stream-info ← БЫЛО sidebar__info */
.alerts-section         /* section: alerts */
.settings-section       /* section: quick-settings */
```

### Center panel секции
```css
.center-panel           /* ZONE: center-panel */
.connection-form        /* section: connection-form */
.connection-form__url   /* field: url-input */
.connection-form__latency /* field: latency-input */
.connection-form__actions /* field: action-buttons */
.tab-content            /* section: tab-content */
.tab-content--active     /* активная вкладка */
.tab-content--overview   /* вкладка overview */
.tab-content--audio      /* вкладка audio */
.tab-content--video      /* вкладка video */
.tab-content--transport  /* вкладка transport */
.tab-content--network    /* вкладка network */
.tab-content--logs       /* вкладка logs */
```

### Зоны внутри вкладок
```css
/* Overview */
.overview-layout        /* zone: overview-layout */
.primary-metrics        /* zone: primary-metrics */
.secondary-metrics      /* zone: secondary-metrics */
.metric-card            /* card: любая метрика */
.metric-card--dbfs      /* card: metric-dbfs-peak */
.metric-card--lufs      /* card: metric-lufs-momentary */
.metric-card--srt-rtt   /* card: metric-srt-rtt */

/* Audio */
.audio-layout           /* zone: audio-layout */
.dbfs-meters            /* zone: dbfs-meters */
.dbfs-meter             /* meter: dbfs-left/right */
.lufs-cards             /* zone: lufs-cards */
.lufs-card              /* card: lufs-m/s/i */
.lufs-extra             /* zone: lufs-extra */
.loudness-history       /* zone: loudness-history */

/* Video */
.video-layout           /* zone: video-layout */
.keyframe-preview       /* zone: keyframe-preview */
.video-badges           /* overlay: video-badges */
.video-technical-data   /* zone: video-technical-data */
.gop-structure          /* zone: gop-structure */
.gop-frame              /* element: gop-frame-sequence */
.gop-frame--I           /* I-frame */
.gop-frame--IDR         /* IDR-frame */
.gop-frame--P           /* P-frame */
.gop-frame--B           /* B-frame */

/* Transport */
.transport-layout       /* zone: transport-layout */
.transport-layout--srt  /* zone для SRT */
.transport-layout--mpegts /* zone для MPEG-TS */
.srt-connection-status  /* zone: srt-connection-status */
.srt-metrics-grid       /* zone: srt-metrics-grid */
.srt-charts             /* zone: srt-charts */

/* Network */
.network-layout         /* zone: network-layout */
.network-metrics        /* zone: network-metrics */
.network-charts         /* zone: network-charts */

/* Logs */
.logs-layout            /* zone: logs-layout */
.logs-container         /* zone: logs-container */
.log-entry              /* element: log-entry */
```

### Right panel секции
```css
.right-panel            /* ZONE: right-panel */
.alerts-section         /* section: alerts */
.alert-item             /* элемент алерта */
.alert-item--info       /* info алерт */
.alert-item--warning    /* warning алерт */
.alert-item--critical   /* critical алерт */
.settings-section       /* section: quick-settings */
.setting-row            /* строка настройки */
.setting-row__label     /* метка настройки */
.setting-row__value     /* значение настройки */
```

---

## 5. Таблица видимости зон по протоколам

| Zone / Section | SRT | IceCast | RTMP | HLS | RTSP | NDI | MPEG-TS | SDI |
|----------------|-----|---------|------|-----|------|-----|---------|-----|
| **app-header** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **right-panel** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **connection-form** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **tab: overview** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **tab: audio** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **tab: video** | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **tab: transport** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| **tab: network** | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| **tab: logs** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **latency-input** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **srt-metrics** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **srt-charts** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **video-preview** | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **gop-structure** | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **ts-health-monitor** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| **ts-tr101290** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |

---

## 6. Правила именования

### 6.1 Имена зон (Zones)
- Всегда в `kebab-case`
- Формат: `{area}-{purpose}`
- Примеры: `audio-layout`, `srt-metrics-grid`, `keyframe-preview`

### 6.2 Имена секций (Sections)
- Всегда в `kebab-case`
- Формат: `{area}__{subsection}` (BEM)
- Примеры: `sidebar__nav`, `header__logo`, `stream-info__row`

### 6.3 Имена элементов (Elements)
- Всегда в `kebab-case`
- Формат: `{parent}__{element}` (BEM)
- Примеры: `video-badges`, `gop-frame`, `log-entry`

### 6.4 Модификаторы (Modifiers)
- Формат: `{block}--{modifier}` или `{block}__{element}--{modifier}`
- Примеры: `tab-content--active`, `gop-frame--IDR`, `alert-item--critical`

---

## 7. Версионирование

| Версия | Дата | Изменения |
|--------|------|-----------|
| 1.0 | 2026-06-07 | Базовый Layout Specification для 8 протоколов |

---

*Перед изменением макета — проверить соответствие имен зон этому документу.*
*Все CSS классы должны быть взяты из этого справочника.*
