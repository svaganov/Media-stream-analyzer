# Media Stream Analyzer — Design System v1.0

> **Правило для разработки:** Перед изменением любого макета страницы — обязательно сверяться с требованиями, описанными в этом документе. Все компоненты должны соответствовать `theme_main.css`.

---

## 1. Философия дизайна

### Единое приложение
Все страницы анализатора (SRT, IceCast, RTMP, HLS, RTSP, NDI, MPEG-TS, SDI) должны **ощущаться как одно приложение**:
- Одинаковая цветовая палитра
- Одинаковая типографика
- Одинаковая структура layout (header + sidebar + center + right panel)
- Одинаковые компоненты (карточки, метры, графики, формы)

### Протокол-агностичность
Переключение протокола — это **контекстный switch**, а не загрузка другого приложения:
- Header: dropdown с протоколом (всегда виден)
- Sidebar: вкладки адаптируются под протокол (скрываются нерелевантные)
- Center panel: контент меняется, но layout остаётся
- Right panel: всегда Alerts + Settings

### Реальное время
Все анимации и обновления должны быть **плавными и предсказуемы**:
- DBFS метры: 50fps, transition 0.05s
- Графики: обновление 1 раз в секунду, 60fps отрисовка
- Цветовые переходы: плавные, без мерцания

---

## 2. Цветовая палитра

### Основные цвета (CSS Variables)
```css
:root {
  --bg-primary:    #0a0a0f;   /* Фон всего приложения */
  --bg-secondary:  #12121a;   /* Фон header, sidebar, right panel */
  --bg-card:       #1a1a24;   /* Фон карточек, форм, превью */
  --bg-hover:      #222230;   /* Hover состояние */
  --bg-input:      #0d0d15;   /* Фон input полей */

  --border:        #2a2a3a;   /* Границы карточек, разделители */
  --border-focus:  #00d4aa;   /* Фокус input */

  --text-primary:   #e0e0e0;   /* Основной текст */
  --text-secondary: #9090a0;   /* Подписи, метки, неактивные элементы */
  --text-muted:     #606070;   /* Мелкий текст, таймстампы */

  --accent:         #00d4aa;   /* Основной акцент (logo, кнопки, active tab) */
  --accent-dim:     #00d4aa33; /* Полупрозрачный акцент (фон active tab) */
  --accent-glow:    #00d4aa66; /* Glow эффект */

  --safe:           #00cc66;   /* Безопасное значение (green) */
  --safe-dim:       #00cc6633; /* Полупрозрачный green */

  --warning:        #ffaa00;   /* Предупреждение (yellow) */
  --warning-dim:    #ffaa0033; /* Полупрозрачный yellow */

  --danger:         #ff4444;   /* Опасность (red) */
  --danger-dim:     #ff444433; /* Полупрозрачный red */
}
```

### Правила использования цветов
| Элемент | Цвет | Запрещено |
|---------|------|-----------|
| Фон приложения | `--bg-primary` | Использовать чёрный `#000000` |
| Фон карточек | `--bg-card` | Градиенты, тени |
| Границы | `--border` | Толщина > 1px, цвет ярче `--text-secondary` |
| Акцентные элементы | `--accent` | Использовать для текста большого объёма |
| Безопасные значения | `--safe` | Использовать для фона карточек |
| Предупреждения | `--warning` | Только для значений, не для статуса "OK" |
| Опасность | `--danger` | Только для критических значений |

### Цветовые зоны DBFS/LUFS
| Диапазон | Цвет | Применение |
|----------|------|------------|
| -70 … -6 dBFS | `--safe` (green) | Нормальный уровень |
| -6 … -1 dBFS | `--warning` (yellow) | Приближение к clipping |
| -1 … 0 dBFS | `--danger` (red) | Клиппинг |
| LUFS > -23.5 | `--danger` | Превышение EBU R128 |
| LUFS -26 … -23.5 | `--warning` | Близко к порогу |
| LUFS < -26 | `--safe` | В норме EBU R128 |

---

## 3. Типографика

### Шрифты
```css
--font-sans:  -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
--font-mono:  'SF Mono', 'Consolas', 'Courier New', monospace;
```

### Иерархия размеров
| Элемент | Размер | Вес | Шрифт | Цвет |
|---------|--------|-----|-------|------|
| Logo | 15px | 700 | sans-serif | `--accent` |
| Заголовок панели | 10px | 600 | sans-serif | `--text-secondary` |
| Значение метрики | 22-28px | 700 | mono | `--text-primary` / цвет зоны |
| Подпись карточки | 11px | 400 | sans-serif | `--text-secondary` |
| Текст вкладки | 12px | 400 | sans-serif | `--text-secondary` / `--accent` |
| Input | 12px | 400 | mono | `--text-primary` |
| Alert текст | 11px | 400 | sans-serif | `--text-primary` |
| Alert время | 10px | 400 | mono | `--text-secondary` |
| Badge | 10px | 400 | mono | `#fff` |
| Tick label | 9px | 400 | mono | `--text-secondary` |

### Правила типографики
- Заголовки панелей: **ВСЕ ЗАГЛАВНЫЕ**, letter-spacing 1.5px
- Значения метрик: **monospace**, жирный, без единиц измерения внутри числа
- Единицы измерения: отдельным `<span>` меньшего размера, `--text-secondary`
- Подписи: sentence case, без точки в конце

---

## 4. Layout

### Grid структура
```
┌─────────────────────────────────────────────────────────────┐
│ HEADER (48px)                                               │
├──────────┬──────────────────────────────────────┬───────────┤
│ SIDEBAR  │  CENTER PANEL                        │ RIGHT     │
│ (200px)  │  (flex: 1)                           │ PANEL     │
│          │                                      │ (280px)   │
│ Nav tabs │  Tab content                         │ Alerts    │
│ Stream   │  Cards / Meters / Charts / Video     │ Settings  │
│ info     │                                      │           │
└──────────┴──────────────────────────────────────┴───────────┘
```

### Размеры
| Элемент | Ширина/Высота | Примечание |
|---------|---------------|------------|
| Header | 100% × 48px | Фиксированная высота |
| Sidebar | 200px × 100% | Фиксированная ширина |
| Right panel | 280px × 100% | Фиксированная ширина |
| Center panel | flex: 1 | Занимает оставшееся пространство |
| Gap между карточками | 12px | Всегда |
| Padding карточки | 14px | Всегда |
| Border radius карточки | 8px | Всегда |
| Border radius кнопки | 4px | Всегда |
| Border radius badge | 4px | Всегда |
| Border radius input | 4px | Всегда |

### Адаптивность
- **Минимальная ширина:** 1200px (sidebar + center 500px + right panel)
- При ширине < 1200px: center panel получает горизонтальный скролл
- **Никакого responsive collapse** — приложение для профессионального использования на мониторах

---

## 5. Компоненты

### 5.1 Карточка (Card)
```
background: var(--bg-card)
border: 1px solid var(--border)
border-radius: 8px
padding: 14px
```
- Заголовок: `.card-title` — uppercase, 11px, `--text-secondary`
- Значение: `.card-value` — 22px, bold, mono, цвет по зоне
- Подпись: `.card-sub` — 10px, `--text-secondary`

### 5.2 DBFS Meter
```
Контейнер: background: var(--bg-card), border: 1px solid var(--border)
Шкала: height: 240px, background: var(--bg-input)
Шкала делений: 8 линий (0, -10, -20, -30, -40, -50, -60, -70)
Бар: position: absolute, bottom: 0, width: 70%, centered
  transition: height 0.05s linear
  Цвет: green / yellow / red по зоне
Значение: text-align: center, 14px, mono, bold
```

### 5.3 LUFS Card
```
Контейнер: background: var(--bg-card), border: 1px solid var(--border)
Значение: 24px, bold, mono, цвет по зоне
Метка: 10px, uppercase, --text-secondary
```

### 5.4 График (Chart)
```
Контейнер: background: var(--bg-card), border: 1px solid var(--border)
Canvas: background: var(--bg-input), border-radius: 4px
Линия: 2px, цвет метрики
Заливка: цвет метрики + 22 hex (15% opacity)
Grid: 1px, --border
```

### 5.5 Video Preview
```
Контейнер: background: var(--bg-card), border: 1px solid var(--border)
Aspect ratio: 16:9
Overlay badges: position: absolute, top-left
  background: rgba(0,0,0,0.75), backdrop-filter: blur(4px)
  padding: 3px 8px, border-radius: 4px
  font: 10px mono, color: #fff
```

### 5.6 Alert Item
```
Контейнер: background: var(--bg-card), border: 1px solid var(--border)
Left border: 3px solid (color по уровню)
Padding: 10px
Время: 10px, mono, --text-secondary
Сообщение: 11px, --text-primary
```

### 5.7 Connection Form
```
Контейнер: background: var(--bg-card), border: 1px solid var(--border)
Flex: row, gap: 8px
URL input: flex: 2, font: mono
Latency input: flex: 1, max-width: 90px, font: mono
Connect button: background: var(--accent), color: #000, bold
Disconnect button: background: var(--danger), color: #fff
```

### 5.8 Nav Tab
```
Padding: 10px 12px, border-radius: 6px
Gap: 10px (icon + text)
Inactive: color: --text-secondary
Hover: background: --bg-hover, color: --text-primary
Active: background: --accent-dim, color: --accent
Icon: 16×16px, stroke-width: 2
```

### 5.9 GOP Frame
```
Width: 22px, height: 22px, border-radius: 3px
Font: 10px, mono, bold, centered
I/IDR: background: --safe-dim, border: 1px solid --safe, color: --safe
P: background: --accent-dim, border: 1px solid --accent, color: --accent
B: background: --warning-dim, border: 1px solid --warning, color: --warning
IDR: border-width: 2px
```

---

## 6. Анимации и переходы

### DBFS Meter
- `transition: height 0.05s linear` — 50fps обновление
- Без `ease` — только linear для точности

### Цветовые переходы
- `transition: color 0.3s, background-color 0.3s` — для статусов
- `transition: border-color 0.2s` — для input focus

### Chart redraw
- Canvas: полный clear + redraw каждые 1000ms
- Анимация: отсутствует (данные меняются дискретно)

### Hover эффекты
- Nav tab: `background` 0.2s
- Button: `opacity: 0.8` при hover
- Card: без hover эффекта (статичный)

---

## 7. Протокол-специфичные адаптации

### При переключении протокола:

| Протокол | Видимые вкладки | Latency input | SRT Charts | Video |
|----------|-----------------|---------------|------------|-------|
| **SRT** | All 6 | ✅ Visible | ✅ Visible | ✅ Visible |
| **IceCast** | Overview, Audio, Logs | ❌ Hidden | ❌ Hidden | ❌ Hidden |
| **RTMP** | Overview, Audio, Video, Network, Logs | ❌ Hidden | ❌ Hidden | ✅ Visible |
| **HLS** | Overview, Audio, Video, Network, Logs | ❌ Hidden | ❌ Hidden | ✅ Visible |
| **RTSP** | Overview, Audio, Video, Network, Logs | ❌ Hidden | ❌ Hidden | ✅ Visible |
| **NDI** | Overview, Audio, Video, Network, Logs | ❌ Hidden | ❌ Hidden | ✅ Visible |
| **MPEG-TS** | Overview, Audio, Video, Transport, Network, Logs | ❌ Hidden | ✅ Visible (TS) | ✅ Visible |
| **SDI** | Overview, Audio, Video, Logs | ❌ Hidden | ❌ Hidden | ✅ Visible |

---

## 8. Именование CSS классов

### BEM-подобная нотация
```
.block__element--modifier

Примеры:
.dbfs-meter__scale
.dbfs-meter__bar--green
.lufs-card__value--danger
.srt-chart__canvas
.alert-item--critical
.nav-tab--active
```

### Запрещено
- Использовать `id` для стилизации (только для JS)
- Inline styles в HTML (кроме динамических значений JS)
- `!important` без крайней необходимости
- Глубокая вложенность (> 3 уровня)

---

## 9. Иконки

### Требования
- Формат: inline SVG
- Stroke: `currentColor`
- Stroke-width: 2
- Размер: 16×16px (nav), 18×18px (header)
- Без fill (только outline)

### Набор иконок
| Иконка | SVG пример |
|--------|-----------|
| Overview | 4 квадрата 2×2 |
| Audio | Волны/крест |
| Video | Прямоугольник + play |
| Transport | Молния |
| Network | Цель/сеть |
| Logs | Документ |

---

## 10. Accessibility

### Контраст
- `--text-primary` на `--bg-primary`: WCAG AA ✅
- `--accent` на `--bg-primary`: WCAG AA ✅
- `--text-secondary` на `--bg-primary`: WCAG AA (для крупного текста) ✅

### Focus states
- Input focus: `border-color: var(--accent)`
- Button focus: `outline: 2px solid var(--accent)`, `outline-offset: 2px`
- Tab focus: `box-shadow: 0 0 0 2px var(--accent-dim)`

---

## 12. Layout Specification (NEW)

### Технический макет страницы
Подробная схема зон, разделов и CSS-классов описана в отдельном документе:
**`LAYOUT_SPECIFICATION.md`** — имена всех зон, видимость по протоколам, CSS классы.

### Ключевые зоны страницы
```
app-header      → sidebar → center-panel → right-panel
  ├── logo          ├── nav-tabs    ├── connection-form   ├── alerts
  ├── protocol      ├── stream-info ├── tab-content       ├── quick-settings
  └── status                        ├── tab-navigator
```

### Видимость вкладок по протоколам
| Протокол | Overview | Audio | Video | Transport | Network | Logs |
|----------|----------|-------|-------|-----------|---------|------|
| SRT      | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| IceCast  | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ |
| RTMP     | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| HLS      | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| RTSP     | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| NDI      | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| MPEG-TS  | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| SDI      | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |

## 11. Версионирование

| Версия | Дата | Изменения |
|--------|------|-----------|
| 1.0 | 2026-06-07 | Базовый Design System для Sprint 5 |

---

*Перед любыми изменениями макета — сверяться с этим документом.*
*Все CSS переменные определены в `theme_main.css`.*
