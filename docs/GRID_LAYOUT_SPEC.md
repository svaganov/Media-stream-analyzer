# Media Stream Analyzer — Детальный Grid макет (Grid Layout Specification)

> **Назначение:** Единый язык для описания всех зон, элементов и окон страницы.  
> **Версия:** 1.1 (sidebar удалена, nav-tabs в header, stream-info в right-panel)

---

## 1. Глобальная структура страницы

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ZONE: app-header              height: 48px, width: 100%                   │
│                                                                             │
│  ┌──────────┐ ┌────────────────────────────┐ ┌──────────┐ ┌──────────────┐  │
│  │app-logo  │ │nav-tabs (horizontal)       │ │protocol  │ │connection    │  │
│  │          │ │                            │ │selector  │ │status        │  │
│  └──────────┘ └────────────────────────────┘ └──────────┘ └──────────────┘  │
│                                                                             │
├──────────────────────────────────────────────────────┬────────────────────┤
│                                                      │                    │
│  ZONE: center-panel                                  │  ZONE: right-panel │
│  width: flex (1)                                     │  width: 280px      │
│                                                      │                    │
│  ┌────────────────────────────────────────────────┐  │  ┌────────────────┐  │
│  │ section: connection-form                       │  │  │section:        │  │
│  │  ┌─────────────────┐ ┌─────┐ ┌──────────────┐│  │  │stream-info     │  │
│  │  │field: url-input │ │field│ │field:        ││  │  │                │  │
│  │  │                 │ │laten│ │action-buttons││  │  │  info-protocol │  │
│  │  └─────────────────┘ └─────┘ └──────────────┘│  │  │  info-state    │  │
│  └────────────────────────────────────────────────┘  │  │  info-duration │  │
│                                                      │  │  info-packets  │  │
│  ┌────────────────────────────────────────────────┐  │  │  info-data     │  │
│  │ section: tab-content                             │  │  │  info-bitrate  │  │
│  │                                                  │  │  └────────────────┘  │
│  │  ┌──────────────────────────────────────────┐  │  │                      │
│  │  │ zone: primary-metrics (overview tab)     │  │  │  ┌────────────────┐  │
│  │  │  ┌────────┐┌────────┐┌────────┐┌────────┐│  │  │  │section:        │  │
│  │  │  │card:   ││card:   ││card:   ││card:   ││  │  │  │alerts          │  │
│  │  │  │dbfs    ││lufs-m  ││true-   ││stream  ││  │  │  │                │  │
│  │  │  │peak    ││omentary││peak    ││bitrate ││  │  │  │  alert-item    │  │
│  │  │  └────────┘└────────┘└────────┘└────────┘│  │  │  │  alert-item    │  │
│  │  └──────────────────────────────────────────┘  │  │  │  alert-item    │  │
│  │                                                  │  │  └────────────────┘  │
│  │  ┌──────────────────────────────────────────┐  │  │                      │
│  │  │ zone: media-preview (video tab)          │  │  │  ┌────────────────┐  │
│  │  │  ┌────────────────────────────────────┐    │  │  │  │section:        │  │
│  │  │  │ element: video-image (16:9)       │    │  │  │  │quick-settings  │  │
│  │  │  │  overlay: video-badges            │    │  │  │  │                │  │
│  │  │  │   ┌────┐┌────┐┌────┐┌────┐        │    │  │  │  │  setting-row   │  │
│  │  │  │   │H.26││1920││50  ││IDR │        │    │  │  │  │  setting-row   │  │
│  │  │  │   └────┘└────┘└────┘└────┘        │    │  │  │  │  setting-row   │  │
│  │  │  └────────────────────────────────────┘    │  │  │  │  setting-row   │  │
│  │  └──────────────────────────────────────────┘  │  │  │  └────────────────┘  │
│  │                                                  │  │                      │
│  │  ┌──────────────────────────────────────────┐  │  │                      │
│  │  │ zone: transport-metrics (transport tab)  │  │  │                      │
│  │  │  ┌──────────────────────────────────┐      │  │  │                      │
│  │  │  │ section: srt-connection-status  │      │  │  │                      │
│  │  │  │  ┌────────┐┌────────┐┌────────┐  │      │  │  │                      │
│  │  │  │  │metric: ││metric: ││metric: │  │      │  │  │                      │
│  │  │  │  │rtt     ││bandwid ││pkt-loss│  │      │  │  │                      │
│  │  │  │  └────────┘└────────┘└────────┘  │      │  │  │                      │
│  │  │  └──────────────────────────────────┘      │  │  │                      │
│  │  │  ┌──────────────────────────────────┐      │  │  │                      │
│  │  │  │ zone: srt-charts                │      │  │  │                      │
│  │  │  │  ┌────────┐┌────────┐┌────────┐  │      │  │  │                      │
│  │  │  │  │chart:  ││chart:  ││chart:  │  │      │  │  │                      │
│  │  │  │  │rtt     ││bandwid ││pkt-loss│  │      │  │  │                      │
│  │  │  │  └────────┘└────────┘└────────┘  │      │  │  │                      │
│  │  │  └──────────────────────────────────┘      │  │  │                      │
│  │  └──────────────────────────────────────────┘  │  │                      │
│  │                                                  │  │                      │
│  │  ┌──────────────────────────────────────────┐  │  │                      │
│  │  │ zone: audio-metrics (audio tab)          │  │  │                      │
│  │  │  ┌────────────────┐┌────────────────┐      │  │  │                      │
│  │  │  │ meter: dbfs-L  ││ meter: dbfs-R  │      │  │  │                      │
│  │  │  │  ┌──────────┐  │  ┌──────────┐  │      │  │  │                      │
│  │  │  │  │ scale    │  │  │ scale    │  │      │  │  │                      │
│  │  │  │  │ ┌──────┐ │  │  │ ┌──────┐ │  │      │  │  │                      │
│  │  │  │  │ │ bar  │ │  │  │ │ bar  │ │  │      │  │  │                      │
│  │  │  │  │ └──────┘ │  │  │ └──────┘ │  │      │  │  │                      │
│  │  │  │  └──────────┘  │  └──────────┘  │      │  │  │                      │
│  │  │  └────────────────┘└────────────────┘      │  │  │                      │
│  │  │  ┌────────┐┌────────┐┌────────┐             │  │  │                      │
│  │  │  │card:   ││card:   ││card:   │             │  │  │                      │
│  │  │  │lufs-m  ││lufs-s  ││lufs-i  │             │  │  │                      │
│  │  │  └────────┘└────────┘└────────┘             │  │  │                      │
│  │  │  ┌────────┐┌────────┐                        │  │  │                      │
│  │  │  │card:   ││card:   │                        │  │  │                      │
│  │  │  │true-   ││lra     │                        │  │  │                      │
│  │  │  │peak    ││        │                        │  │  │                      │
│  │  │  └────────┘└────────┘                        │  │  │                      │
│  │  │  ┌────────────────────────────────────┐      │  │  │                      │
│  │  │  │ chart: loudness-history (60s)     │      │  │  │                      │
│  │  │  └────────────────────────────────────┘      │  │  │                      │
│  │  └──────────────────────────────────────────┘  │  │                      │
│  │                                                  │  │                      │
│  │  ┌──────────────────────────────────────────┐  │  │                      │
│  │  │ zone: network-metrics (network tab)      │  │  │                      │
│  │  │  ┌────────┐┌────────┐┌────────┐┌────────┐│  │  │                      │
│  │  │  │card:   ││card:   ││card:   ││card:   ││  │  │                      │
│  │  │  │packets ││bytes   ││retrans ││jitter  ││  │  │                      │
│  │  │  └────────┘└────────┘└────────┘└────────┘│  │  │                      │
│  │  └──────────────────────────────────────────┘  │  │                      │
│  │                                                  │  │                      │
│  │  ┌──────────────────────────────────────────┐  │  │                      │
│  │  │ zone: logs (logs tab)                    │  │  │                      │
│  │  │  ┌────────────────────────────────────┐    │  │  │                      │
│  │  │  │ element: logs-container           │    │  │  │                      │
│  │  │  │  ┌────────────────────────────┐    │    │  │  │                      │
│  │  │  │  │ log-entry: timestamp       │    │    │  │  │                      │
│  │  │  │  │ log-entry: timestamp       │    │    │  │  │                      │
│  │  │  │  └────────────────────────────┘    │    │  │  │                      │
│  │  │  └────────────────────────────────────┘    │  │  │                      │
│  │  └──────────────────────────────────────────┘  │  │                      │
│  └────────────────────────────────────────────────┘  │                      │
│                                                      │                    │
└──────────────────────────────────────────────────────┴────────────────────┘
```

---

## 2. Имена зон (Zones) — Полный список

### 2.1 Глобальные зоны (Grid-level)

| # | Имя зоны | CSS класс | Размер | Родитель |
|---|----------|-----------|--------|----------|
| 1 | **app** | `.app` | 100vw × 100vh | `<body>` |
| 2 | **app-header** | `.app__header` | 100% × 48px | `.app` |
| 3 | **app-main** | `.app__main` | 100% × calc(100% - 48px) | `.app` |
| 4 | **center-panel** | `.app__center` | flex: 1 × 100% | `.app__main` |
| 5 | **right-panel** | `.app__right-panel` | 280px × 100% | `.app__main` |

### 2.2 Зоны внутри app-header

| # | Имя зоны | CSS класс | Размер | Родитель | Протокол-специфично |
|---|----------|-----------|--------|----------|---------------------|
| 6 | **app-logo** | `.header__logo` | auto × 100% | `.app__header` | ❌ Нет |
| 7 | **nav-tabs** | `.header__nav` | auto × 100% | `.app__header` | Да (видимость табов) |
| 8 | **protocol-selector** | `.header__protocol` | auto × 100% | `.app__header` | ❌ Нет |
| 9 | **connection-status** | `.header__status` | auto × 100% | `.app__header` | ❌ Нет |

### 2.3 Зоны внутри center-panel

| # | Имя зоны | CSS класс | Размер | Родитель | Протокол-специфично |
|---|----------|-----------|--------|----------|---------------------|
| 10 | **connection-form** | `.connection-form` | 100% × auto | `.app__center` | Частично (latency) |
| 11 | **tab-content** | `.tab-content` | 100% × auto | `.app__center` | Да (по вкладкам) |
| 12 | **tab-navigator** | `.tab-navigator` | 100% × auto | `.app__center` | Да (видимость) |

### 2.4 Зоны внутри tab-content (по вкладкам)

| # | Имя зоны | CSS класс | Родитель | Видимость |
|---|----------|-----------|----------|-----------|
| 13 | **primary-metrics** | `.primary-metrics` | `.tab-content--overview` | Все протоколы |
| 14 | **secondary-metrics** | `.secondary-metrics` | `.tab-content--overview` | По протоколу |
| 15 | **media-preview** | `.media-preview` | `.tab-content--video` | Video protocols |
| 16 | **video-technical-data** | `.video-technical-data` | `.tab-content--video` | Video protocols |
| 17 | **gop-structure** | `.gop-structure` | `.tab-content--video` | Video protocols |
| 18 | **transport-metrics** | `.transport-metrics` | `.tab-content--transport` | SRT, MPEG-TS |
| 19 | **srt-charts** | `.srt-charts` | `.tab-content--transport` | SRT |
| 20 | **ts-health-monitor** | `.ts-health-monitor` | `.tab-content--transport` | MPEG-TS |
| 21 | **audio-metrics** | `.audio-metrics` | `.tab-content--audio` | Все протоколы |
| 22 | **network-metrics** | `.network-metrics` | `.tab-content--network` | По протоколу |
| 23 | **logs** | `.logs` | `.tab-content--logs` | Все протоколы |

### 2.5 Зоны внутри right-panel

| # | Имя зоны | CSS класс | Размер | Родитель | Протокол-специфично |
|---|----------|-----------|--------|----------|---------------------|
| 24 | **stream-info** | `.right-panel__stream-info` | 100% × auto | `.app__right-panel` | Да (поля) |
| 25 | **alerts** | `.alerts-section` | 100% × auto | `.app__right-panel` | ❌ Нет |
| 26 | **quick-settings** | `.settings-section` | 100% × auto | `.app__right-panel` | Частично |

---

## 3. Элементы (Elements) — Полный список

### 3.1 app-header элементы

| Элемент | CSS класс | Родитель | Описание |
|---------|-----------|----------|----------|
| logo-text | `.header__logo-text` | `.header__logo` | Текст "◆ MEDIA STREAM ANALYZER" |
| protocol-dropdown | `.header__protocol-select` | `.header__protocol` | `<select>` протокола |
| ws-dot | `.header__status-dot` | `.header__status` | Индикатор WS статуса |
| ws-text | `.header__status-text` | `.header__status` | Текст статуса |
| nav-tab | `.nav-tab` | `.header__nav` | Кнопка вкладки |
| nav-tab-icon | `.nav-tab__icon` | `.nav-tab` | SVG иконка |
| nav-tab-label | `.nav-tab__label` | `.nav-tab` | Текст вкладки |

### 3.2 connection-form элементы

| Элемент | CSS класс | Родитель | Описание |
|---------|-----------|----------|----------|
| url-input | `.connection-form__url` | `.connection-form` | Поле URL |
| latency-input | `.connection-form__latency` | `.connection-form` | Поле latency (SRT only) |
| connect-btn | `.connection-form__connect` | `.connection-form` | Кнопка Connect |
| disconnect-btn | `.connection-form__disconnect` | `.connection-form` | Кнопка Disconnect |

### 3.3 primary-metrics элементы (overview tab)

**Назначение:** Сводные карточки с ключевыми метриками. Только числовые значения, без графиков и шкал.

**Важно:** В primary-metrics НЕТ полных аудио измерений (нет DBFS метров, нет LUFS графика). 
Для полных аудио измерений — перейти во вкладку **Audio**.

| Элемент | CSS класс | Родитель | Описание |
|---------|-----------|----------|----------|
| metric-card | `.metric-card` | `.primary-metrics` | Карточка метрики |
| metric-label | `.metric-card__label` | `.metric-card` | Подпись метрики |
| metric-value | `.metric-card__value` | `.metric-card` | Значение метрики |
| metric-unit | `.metric-card__unit` | `.metric-card` | Единица измерения |

**Конкретные карточки (4 шт. в ряд):**
| Имя | CSS класс | Доступность |
|-----|-----------|-------------|
| dbfs-peak | `.metric-card--dbfs` | Все |
| lufs-momentary | `.metric-card--lufs-m` | Все |
| true-peak | `.metric-card--true-peak` | Все |
| stream-bitrate | `.metric-card--bitrate` | Все |
| stream-state | `.metric-card--state` | Все |
| srt-rtt | `.metric-card--srt-rtt` | SRT |
| packet-loss | `.metric-card--pkt-loss` | SRT, MPEG-TS |
| bandwidth | `.metric-card--bandwidth` | SRT, MPEG-TS |
| buffer-health | `.metric-card--buffer` | SRT |
| video-codec | `.metric-card--codec` | Video protocols |
| resolution | `.metric-card--resolution` | Video protocols |
| frame-rate | `.metric-card--fps` | Video protocols |

### 3.4 media-preview элементы (video tab)

| Элемент | CSS класс | Родитель | Описание |
|---------|-----------|----------|----------|
| video-image | `.media-preview__image` | `.media-preview` | `<img>` или `<video>` |
| video-overlay | `.media-preview__overlay` | `.media-preview` | Контейнер бейджей |
| video-badge | `.badge` | `.media-preview__overlay` | Бейдж (H.264, 1920x1080, etc.) |

### 3.5 video-technical-data элементы

| Элемент | CSS класс | Родитель | Описание |
|---------|-----------|----------|----------|
| tech-item | `.tech-item` | `.video-technical-data` | Карточка параметра |
| tech-label | `.tech-item__label` | `.tech-item` | Название параметра |
| tech-value | `.tech-item__value` | `.tech-item` | Значение параметра |

**Конкретные параметры:**
| Имя | CSS класс |
|-----|-----------|
| tech-codec | `.tech-item--codec` |
| tech-resolution | `.tech-item--resolution` |
| tech-frame-rate | `.tech-item--fps` |
| tech-bitrate | `.tech-item--bitrate` |
| tech-color-space | `.tech-item--color` |
| tech-profile | `.tech-item--profile` |

### 3.6 gop-structure элементы

| Элемент | CSS класс | Родитель | Описание |
|---------|-----------|----------|----------|
| gop-frame | `.gop-frame` | `.gop-structure` | Фрейм GOP |
| gop-frame-I | `.gop-frame--I` | `.gop-structure` | I-frame |
| gop-frame-IDR | `.gop-frame--IDR` | `.gop-structure` | IDR-frame |
| gop-frame-P | `.gop-frame--P` | `.gop-structure` | P-frame |
| gop-frame-B | `.gop-frame--B` | `.gop-structure` | B-frame |

### 3.7 transport-metrics элементы (SRT)

| Элемент | CSS класс | Родитель | Описание |
|---------|-----------|----------|----------|
| srt-status-card | `.srt-status` | `.transport-metrics` | Карточка статуса |
| srt-status-badge | `.srt-status__badge` | `.srt-status` | Badge Connected/Disconnected |
| srt-metric | `.srt-metric` | `.srt-metrics` | Метрика SRT |
| srt-metric-label | `.srt-metric__label` | `.srt-metric` | Подпись |
| srt-metric-value | `.srt-metric__value` | `.srt-metric` | Значение |

**Конкретные метрики:**
| Имя | CSS класс |
|-----|-----------|
| srt-rtt | `.srt-metric--rtt` |
| srt-bandwidth | `.srt-metric--bandwidth` |
| srt-packet-loss | `.srt-metric--loss` |
| srt-buffer | `.srt-metric--buffer` |

### 3.8 srt-charts элементы

| Элемент | CSS класс | Родитель | Описание |
|---------|-----------|----------|----------|
| chart-card | `.chart-card` | `.srt-charts` | Контейнер графика |
| chart-title | `.chart-card__title` | `.chart-card` | Заголовок |
| chart-canvas | `.chart-card__canvas` | `.chart-card` | `<canvas>` |
| time-window | `.time-window` | `.chart-card` | Селектор окна времени |
| time-btn | `.time-window__btn` | `.time-window` | Кнопка 1m/5m/15m/30m/60m |

**Конкретные графики:**
| Имя | CSS класс |
|-----|-----------|
| rtt-chart | `.chart-card--rtt` |
| bandwidth-chart | `.chart-card--bandwidth` |
| packet-loss-chart | `.chart-card--loss` |
| buffer-chart | `.chart-card--buffer` |

### 3.9 audio-metrics элементы (Вкладка Audio)

**Назначение:** ПОЛНЫЕ аудио измерения с визуализацией. 
Включает DBFS метры, LUFS карточки и Loudness History график.

**Структура зоны audio-metrics:**
```
audio-metrics
  ├── zone: dbfs-meters (2 вертикальные шкалы)
  │   ├── meter: dbfs-left-channel (шкала 0 → -70 dBFS, бар, значение)
  │   └── meter: dbfs-right-channel (шкала 0 → -70 dBFS, бар, значение)
  ├── zone: lufs-cards (5 карточек в ряд)
  │   ├── card: lufs-momentary (M)
  │   ├── card: lufs-shortterm (S)
  │   ├── card: lufs-integrated (I)
  │   ├── card: true-peak (TP)
  │   └── card: loudness-range (LRA)
  └── zone: loudness-history (график 60-секундного окна)
      └── chart: lufs-history-canvas
```

| Элемент | CSS класс | Родитель | Описание |
|---------|-----------|----------|----------|
| dbfs-meter | `.dbfs-meter` | `.audio-metrics` | DBFS meter |
| dbfs-scale | `.dbfs-meter__scale` | `.dbfs-meter` | Шкала 0 → -70 dBFS |
| dbfs-bar | `.dbfs-meter__bar` | `.dbfs-meter__scale` | Бар (green/yellow/red) |
| dbfs-tick | `.dbfs-meter__tick` | `.dbfs-meter__scale` | Деление шкалы |
| dbfs-value | `.dbfs-meter__value` | `.dbfs-meter` | Значение dBFS |
| lufs-card | `.lufs-card` | `.audio-metrics` | LUFS карточка |
| lufs-label | `.lufs-card__label` | `.lufs-card` | Подпись (Momentary/Short-term/Integrated) |
| lufs-value | `.lufs-card__value` | `.lufs-card` | Значение LUFS |
| loudness-history | `.loudness-history` | `.audio-metrics` | График истории |
| history-canvas | `.loudness-history__canvas` | `.loudness-history` | Canvas 60s window |

**Конкретные LUFS карточки (5 шт.):**
| Имя | CSS класс |
|-----|-----------|
| lufs-momentary | `.lufs-card--m` |
| lufs-shortterm | `.lufs-card--s` |
| lufs-integrated | `.lufs-card--i` |
| true-peak | `.lufs-card--tp` |
| loudness-range | `.lufs-card--lra` |

### 3.10 network-metrics элементы

| Элемент | CSS класс | Родитель | Описание |
|---------|-----------|----------|----------|
| network-card | `.metric-card` | `.network-metrics` | Карточка метрики |
| net-packets | `.metric-card--packets` | `.network-metrics` | Packets received |
| net-bytes | `.metric-card--bytes` | `.network-metrics` | Bytes received |
| net-retrans | `.metric-card--retrans` | `.network-metrics` | Retransmissions (SRT) |
| net-belated | `.metric-card--belated` | `.network-metrics` | Belated packets (SRT) |
| net-jitter | `.metric-card--jitter` | `.network-metrics` | Jitter |

### 3.11 logs элементы

| Элемент | CSS класс | Родитель | Описание |
|---------|-----------|----------|----------|
| logs-container | `.logs-container` | `.logs` | Скроллируемый контейнер |
| log-entry | `.log-entry` | `.logs-container` | Запись лога |
| log-timestamp | `.log-entry__time` | `.log-entry` | Время |
| log-level | `.log-entry__level` | `.log-entry` | Уровень (INFO/WARN/ERROR) |
| log-message | `.log-entry__msg` | `.log-entry` | Сообщение |

### 3.12 stream-info элементы (right-panel)

| Элемент | CSS класс | Родитель | Описание |
|---------|-----------|----------|----------|
| info-row | `.stream-info__row` | `.right-panel__stream-info` | Строка |
| info-label | `.stream-info__label` | `.stream-info__row` | Метка |
| info-value | `.stream-info__value` | `.stream-info__row` | Значение |

**Конкретные поля:**
| Имя | CSS класс | SRT | IceCast | RTMP | HLS | RTSP | NDI | MPEG-TS | SDI |
|-----|-----------|-----|---------|------|-----|------|-----|---------|-----|
| info-protocol | `.stream-info__protocol` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| info-state | `.stream-info__state` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| info-duration | `.stream-info__duration` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| info-packets | `.stream-info__packets` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| info-data | `.stream-info__data` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| info-bitrate | `.stream-info__bitrate` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| info-latency | `.stream-info__latency` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| info-rtt | `.stream-info__rtt` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| info-resolution | `.stream-info__resolution` | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| info-codec | `.stream-info__codec` | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

### 3.13 alerts элементы

| Элемент | CSS класс | Родитель | Описание |
|---------|-----------|----------|----------|
| alert-item | `.alert-item` | `.alerts-section` | Алерт |
| alert-time | `.alert-item__time` | `.alert-item` | Время |
| alert-msg | `.alert-item__msg` | `.alert-item` | Сообщение |

**Модификаторы:**
| Имя | CSS класс |
|-----|-----------|
| alert-info | `.alert-item--info` |
| alert-warning | `.alert-item--warning` |
| alert-critical | `.alert-item--critical` |

### 3.14 quick-settings элементы

| Элемент | CSS класс | Родитель | Описание |
|---------|-----------|----------|----------|
| setting-row | `.setting-row` | `.settings-section` | Строка настройки |
| setting-label | `.setting-row__label` | `.setting-row` | Метка |
| setting-value | `.setting-row__value` | `.setting-row` | Значение |

**Конкретные настройки:**
| Имя | CSS класс | Протокол-специфично |
|-----|-----------|---------------------|
| setting-lufs-target | `.setting-row--lufs` | ❌ Нет |
| setting-true-peak | `.setting-row--tp` | ❌ Нет |
| setting-silence | `.setting-row--silence` | ❌ Нет |
| setting-latency | `.setting-row--latency` | ✅ SRT only |
| setting-update-rate | `.setting-row--rate` | ❌ Нет |
| setting-history | `.setting-row--history` | ❌ Нет |

---

## 4. Вкладки (Tabs) — Видимость по протоколам

| Вкладка | CSS класс | SRT | IceCast | RTMP | HLS | RTSP | NDI | MPEG-TS | SDI |
|---------|-----------|-----|---------|------|-----|------|-----|---------|-----|
| Overview | `.tab-content--overview` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Audio | `.tab-content--audio` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Video | `.tab-content--video` | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Transport | `.tab-content--transport` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Network | `.tab-content--network` | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| Logs | `.tab-content--logs` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## 5. Протокол-специфичные адаптации

### 5.1 SRT
```
header:      nav-tabs [overview, audio, video, transport, network, logs]
             protocol-selector [SRT]
center:      connection-form [url + latency + connect/disconnect]
             tab-content:
               overview:  primary-metrics [dbfs, lufs, tp, bitrate, state]
                          secondary-metrics [rtt, loss, bandwidth, buffer, codec, res, fps]
               audio:     dbfs-meters + lufs-cards + loudness-history
               video:     keyframe-preview + tech-data + gop-structure
               transport: srt-connection-status + srt-charts (rtt, bw, loss, buffer)
               network:   packets + bytes + retrans + belated + jitter
               logs:      logs-container
right-panel: stream-info [protocol, state, duration, packets, data, bitrate, latency, rtt]
             alerts
             quick-settings [lufs-target, tp-max, silence, latency, rate, history]
```

### 5.2 IceCast
```
header:      nav-tabs [overview, audio, logs]
             protocol-selector [IceCast]
center:      connection-form [url + connect/disconnect (no latency)]
             tab-content:
               overview:  primary-metrics [dbfs, lufs, tp, bitrate, state]
               audio:     dbfs-meters + lufs-cards + loudness-history
               logs:      logs-container
right-panel: stream-info [protocol, state, duration, bitrate]
             alerts
             quick-settings [lufs-target, tp-max, silence, rate, history (no latency)]
```

### 5.3 RTMP / HLS / RTSP / NDI
```
header:      nav-tabs [overview, audio, video, network, logs]
             protocol-selector [RTMP/HLS/RTSP/NDI]
center:      connection-form [url + connect/disconnect (no latency)]
             tab-content:
               overview:  primary-metrics [dbfs, lufs, tp, bitrate, state]
                          secondary-metrics [codec, res, fps]
               audio:     dbfs-meters + lufs-cards + loudness-history
               video:     keyframe-preview + tech-data + gop-structure
               network:   packets + bytes + jitter
               logs:      logs-container
right-panel: stream-info [protocol, duration, bitrate, resolution, codec]
             alerts
             quick-settings [lufs-target, tp-max, silence, rate, history]
```

### 5.4 MPEG-TS
```
header:      nav-tabs [overview, audio, video, transport, network, logs]
             protocol-selector [MPEG-TS]
center:      connection-form [url + connect/disconnect (no latency)]
             tab-content:
               overview:  primary-metrics [dbfs, lufs, tp, bitrate, state]
                          secondary-metrics [loss, bandwidth, codec, res, fps]
               audio:     dbfs-meters + lufs-cards + loudness-history
               video:     keyframe-preview + tech-data + gop-structure
               transport: ts-health-monitor + ts-tr101290
               network:   packets + bytes + jitter
               logs:      logs-container
right-panel: stream-info [protocol, duration, packets, data, bitrate, resolution, codec]
             alerts
             quick-settings [lufs-target, tp-max, silence, rate, history]
```

### 5.5 SDI
```
header:      nav-tabs [overview, audio, video, logs]
             protocol-selector [SDI]
center:      connection-form [url + connect/disconnect (no latency)]
             tab-content:
               overview:  primary-metrics [dbfs, lufs, tp, bitrate, state]
                          secondary-metrics [codec, res, fps]
               audio:     dbfs-meters + lufs-cards + loudness-history
               video:     keyframe-preview + tech-data + gop-structure
               logs:      logs-container
right-panel: stream-info [protocol, duration, bitrate, resolution, codec]
             alerts
             quick-settings [lufs-target, tp-max, silence, rate, history]
```

---

## 6. Версионирование

| Версия | Дата | Изменения |
|--------|------|-----------|
| 1.0 | 2026-06-07 | Базовый Grid с sidebar |
| 1.1 | 2026-06-07 | Удалена sidebar, nav-tabs → header, stream-info → right-panel |

---

*Перед изменением макета — сверяться с этим документом для проверки имён зон и элементов.*
