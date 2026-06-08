# Media Stream Analyzer v2 — Design System

> **Статус:** ✅ УТВЕРЖДЁНО
>
> **Правило:** При создании новых страниц, секций и элементов ПО **обязано** руководствоваться требованиями этого документа. Любое отклонение требует обновления `DESIGN_SYSTEM.md` **перед** изменением кода.

---

## 1. Цветовая палитра

### 1.1 Фоновые цвета (Background)

| Переменная | Hex | Назначение |
|------------|-----|------------|
| `--bg-primary` | `#0a0a0f` | Корневой фон страницы |
| `--bg-secondary` | `#12121a` | Header, sidebar, карточки |
| `--bg-card` | `#1a1a24` | Внутренние панели, формы |
| `--bg-hover` | `#252532` | Hover-состояние |
| `--bg-active` | `#2d2d3d` | Active-состояние (nav-tab) |
| `--bg-input` | `#0d0d15` | Поля ввода, canvas фон |

### 1.2 Текстовые цвета

| Переменная | Hex | Назначение |
|------------|-----|------------|
| `--text-primary` | `#e8e8f0` | Основной текст |
| `--text-secondary` | `#9090a0` | Вторичный текст, лейблы |
| `--text-muted` | `#606070` | Мелкий текст, заглушки |

### 1.3 Акцентные цвета

| Переменная | Hex | Назначение |
|------------|-----|------------|
| `--accent-primary` | `#4a9eff` | Primary accent (blue) |
| `--accent-secondary` | `#7c5cff` | Secondary accent (purple) |
| `--accent-success` | `#4ade80` | Success / Safe |
| `--accent-warning` | `#fbbf24` | Warning |
| `--accent-danger` | `#f87171` | Danger / Critical |

### 1.4 Цвета метров (Meter Palette)

**DBFS Scale (4 зоны):**

| Диапазон | Цвет | Hex | CSS класс |
|----------|------|-----|-----------|
| -70 .. -18 dBFS | Green | `#4ade80` | `.safe` |
| -18 .. -9 dBFS | Yellow | `#fbbf24` | `.caution` |
| -9 .. -2 dBFS | Orange | `#fb923c` | `.warning` |
| -2 .. 0 dBFS | Red | `#f87171` | `.danger` |

**LUFS Scale (3 зоны, 0..-40):**

| Диапазон | Цвет | Hex | CSS класс |
|----------|------|-----|-----------|
| < -26 LUFS | Green | `#4ade80` | `.safe` |
| -26 .. -23.5 | Yellow | `#fbbf24` | `.warning` |
| > -23.5 | Red | `#f87171` | `.danger` |

**Правило:** Метры используют **только solid colors**, никаких gradients.

---

## 2. Типографика

### 2.1 Шрифты

| Назначение | Стек | Fallback |
|------------|------|----------|
| Основной | `Segoe UI` | `system-ui, -apple-system, sans-serif` |
| Моноширинный | `JetBrains Mono` | `'Fira Code', monospace` |

### 2.2 Размеры

| Размер | Назначение | CSS |
|--------|------------|-----|
| 9px | Мелкие метки, тики шкал | `font-size: 9px` |
| 10px | Заголовки карточек, лейблы | `font-size: 10px; text-transform: uppercase; letter-spacing: 1.5px` |
| 11px | Лейблы каналов, навигация | `font-size: 11px; font-weight: 600` |
| 12px | Кнопки, инпуты, селекты | `font-size: 12px` |
| 13px | Значения technical data | `font-size: 13px; font-weight: 600` |
| 14px | Значения readouts | `font-size: 14px; font-weight: 700` |
| 15px | Заголовок приложения | `font-size: 15px; font-weight: 700` |
| 16px | Метрики SRT | `font-size: 16px; font-weight: 700` |
| 24px | LUFS значения | `font-size: 24px; font-weight: 700` |

---

## 3. Layout Grid

### 3.1 Переменные

| Переменная | Значение | Назначение |
|------------|----------|------------|
| `--header-height` | `64px` | Высота шапки |
| `--sidebar-width` | `240px` | Ширина боковой панели |
| `--gap` | `16px` | Отступы между секциями |
| `--radius` | `8px` | Скругление углов |

### 3.2 Grid-структуры

**Audio Analyzer:**
```css
.analyzer-body {
  grid-template-columns: var(--sidebar-width) 1fr;
}
```

**Video Analyzer:**
```css
.main {
  grid-template-columns: 1fr;
}
```

**Sprint Layout (2 колонки внутри center):**
```css
.srt-layout {
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
```

**Audio Meters Row:**
```css
.audio-meters-row {
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
```

### 3.3 Responsive Breakpoints

| Breakpoint | Audio Layout | Video Layout |
|------------|--------------|--------------|
| > 1200px | `240px + 1fr` | `1fr` |
| 900–1200px | `200px + 1fr` | `1fr` |
| < 900px | `1fr` (sidebar hidden) | `1fr` |

---

## 4. Компоненты

### 4.1 Header

```
┌─────────────────────────────────────────────────────────────┐
│  ← Back    Title [Badge]    [Select ▼]     ● Status       │
└─────────────────────────────────────────────────────────────┘
```

- Высота: `64px`
- Фон: `var(--bg-secondary)`
- Border-bottom: `1px solid var(--bg-card)`
- Sticky: `top: 0; z-index: 100`

**Элементы:**
- `.back-btn` — стрелка + текст
- `.header-title` — название страницы + `.protocol-badge`
- `.protocol-select` — `<select>` с темным стилем
- `.connection-status` — точка + текст

**Правило:** Header содержит **только** навигацию назад, заголовок, бейдж протокола, селект протокола и статус подключения. **Никаких nav-tabs в header**.

### 4.2 Sidebar (только audio-analyzer)

- Ширина: `240px`
- Фон: `var(--bg-secondary)`
- Border-radius: `var(--radius)`
- Padding: `16px`

**Nav-tabs:**
- Вертикальный список
- `.nav-tab` — flex row, gap 10px, padding 10px 14px
- Active: `background: var(--bg-active); color: var(--accent-primary)`
- Hover: `background: var(--bg-hover); color: var(--text-primary)`

**Stream Info:**
- Border-top: `1px solid var(--bg-card)`
- `.info-row` — flex space-between, padding 4px 0
- `.label` — `color: var(--text-muted)`
- `.value` — `font-family: var(--font-mono); font-size: 0.8rem`

### 4.3 Panel Section

- Фон: `var(--bg-secondary)`
- Border-radius: `var(--radius)`
- Padding: `20px`
- Margin-bottom: `var(--gap)`

**Заголовок:**
```css
.panel-title {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  color: var(--text-secondary);
  margin-bottom: 10px;
  font-weight: 600;
}
```

### 4.4 Connect Form

```
┌─────────────────────────────────────────────┐
│  [URL input        ] [Latency] [Connect] [X]│
└─────────────────────────────────────────────┘
```

- Фон: `var(--bg-card)`
- Border: `1px solid var(--border)`
- Border-radius: `8px`
- Padding: `12px`
- Flex row, gap `8px`

**Inputs:**
- Фон: `var(--bg-input)`
- Border: `1px solid var(--border)`
- Focus: `border-color: var(--accent-primary)`
- Font-family: `var(--font-mono)`
- Font-size: `12px`

**Buttons:**
- Primary: `background: var(--accent-primary); color: #000`
- Disconnect: `background: var(--accent-danger); color: #fff`
- Padding: `8px 18px`
- Border-radius: `4px`
- Font-size: `12px; font-weight: 700`

### 4.5 Video Preview

```
┌──────────────────────────────┐
│  [image]                     │
│  ┌────┬──────┬─────┬────┐   │
│  │H.264│1920x1080│50fps│IDR│ │
│  └────┴──────┴─────┴────┘   │
└──────────────────────────────┘
```

- Aspect-ratio: `16/9`
- Фон: `var(--bg-card)`
- Border: `1px solid var(--border)`
- Border-radius: `8px`
- Overflow: `hidden`

**Overlay badges:**
- `background: rgba(0,0,0,0.75)`
- `backdrop-filter: blur(4px)`
- Padding: `3px 8px`
- Border-radius: `4px`
- Font: `10px var(--font-mono)`

### 4.6 Technical Data Grid

```css
.tech-data {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}
```

**Item:**
- Фон: `var(--bg-card)`
- Border: `1px solid var(--border)`
- Border-radius: `6px`
- Padding: `10px`
- Text-align: `center`

**Label:** `font-size: 9px; text-transform: uppercase; color: var(--text-secondary)`
**Value:** `font-family: var(--font-mono); font-size: 13px; font-weight: 600`

### 4.7 GOP Bar

```
┌────────────────────────────────────────┐
│  I  B  B  P  B  B  P  B  B  P  ...    │
└────────────────────────────────────────┘
```

- Flex row, gap `3px`
- Фон: `var(--bg-card)`
- Border: `1px solid var(--border)`
- Border-radius: `8px`
- Padding: `10px`
- Flex-wrap: `wrap`

**Frame types:**

| Тип | Background | Border | Color |
|-----|------------|--------|-------|
| I / IDR | `rgba(74,222,128,0.15)` | `1px solid #4ade80` | `#4ade80` |
| IDR (bold) | `rgba(74,222,128,0.15)` | `2px solid #4ade80` | `#4ade80` |
| P | `rgba(74,158,255,0.15)` | `1px solid #4a9eff` | `#4a9eff` |
| B | `rgba(251,191,36,0.15)` | `1px solid #fbbf24` | `#fbbf24` |

**Frame size:** `22px × 22px`, border-radius `3px`

### 4.8 SRT Status Card

- Фон: `var(--bg-card)`
- Border: `1px solid var(--border)`
- Border-radius: `8px`
- Padding: `14px`

**Metrics Grid:**
```css
.srt-metrics-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}
```

**Metric:**
- Фон: `var(--bg-primary)`
- Border-radius: `6px`
- Padding: `10px`
- Label: `font-size: 9px; text-transform: uppercase`
- Value: `font-size: 16px; font-weight: 700`

**Status Badge:**
- Connected: `background: rgba(74,222,128,0.15); color: #4ade80`
- Disconnected: `background: rgba(248,113,113,0.15); color: #f87171`

### 4.9 SRT Chart Card

- Фон: `var(--bg-card)`
- Border: `1px solid var(--border)`
- Border-radius: `8px`
- Padding: `12px`
- Margin-bottom: `10px`

**Header:** flex space-between
- Title: `font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px`
- Time buttons: flex row, gap `4px`

**Canvas:**
- Width: `100%`
- Height: `100px`
- Фон: `var(--bg-input)`
- Border-radius: `4px`

**Time Button:**
- Active: `background: rgba(74,158,255,0.15); color: #4a9eff; border-color: #4a9eff`
- Inactive: `background: var(--bg-input); color: var(--text-secondary)`

### 4.10 Segmented Meter (DBFS / LUFS)

**Общая структура:**

```
┌────────────────────────────────┐
│  0 ──┐  ┌──┐  ┌─── 0          │
│  9 ──┘  │██│  │███             │
│ 18 ──   │██│  │███  9          │
│ 20 ──   │██│  │███  18         │
│ 30 ──   │██│  │███  20         │
│ 40 ──   │██│  │███  30         │
│ 50 ──   │██│  │███  40         │
│ 60 ──   │██│  │███  50         │
│ 70 ──   └──┘  └─── 60         │
│            70                  │
│  ┌──────┐    ┌──────┐          │
│  │ L    │    │ R    │          │
│  │ -1.0 │    │ -1.5 │          │
│  │ dBFS │    │ dBFS │          │
│  └──────┘    └──────┘          │
└────────────────────────────────┘
```

**Размеры:**
- Scale: `width: 72px; height: 260px`
- Ticks panel: `width: 28px`
- Bar container: `width: 44px`
- Segments позиционируются absolute от bottom

**Peak hold line:**
- `width: 44px; height: 2px`
- `background: #fff; box-shadow: 0 0 4px rgba(255,255,255,0.8)`

**LUFS TP line (только M scale):**
- `background: #00d4aa; box-shadow: 0 0 4px rgba(0,212,170,0.6)`

**Readouts:**
- Фон: `var(--bg-card)`
- Border: `1px solid var(--border)`
- Border-radius: `6px`
- Padding: `6px 10px`
- Label: `font-size: 10px; text-transform: uppercase; letter-spacing: 1px`
- Value: `font-family: var(--font-mono); font-size: 14px; font-weight: 700`

### 4.11 Alert Item

```css
.alert-item {
  border-left: 3px solid; /* цвет по severity */
  background: rgba(color, 0.1);
  border-radius: 6px;
  padding: 10px;
  margin-bottom: 8px;
  font-size: 11px;
}
```

| Severity | Border | Background |
|----------|--------|------------|
| Info | `#4a9eff` | `rgba(74,158,255,0.1)` |
| Warning | `#fbbf24` | `rgba(251,191,36,0.1)` |
| Critical | `#f87171` | `rgba(248,113,113,0.1)` |

### 4.12 History Canvas

- Width: `100%`
- Height: `160px`
- Фон: `var(--bg-card)`
- Border: `1px solid var(--border)`
- Border-radius: `8px`

**Элементы:**
- Grid lines: `#252532`
- Target line (-23 LUFS): `#4a9eff`, dashed
- Data line: `#4ade80`, width `2px`
- Fill: `rgba(74,222,128,0.1)`

---

## 5. Анимации

| Элемент | Animation | Duration |
|---------|-----------|----------|
| Status dot | Pulse | `2s infinite` |
| Meter fill | Height/width transition | `0.05s linear` |
| Peak hold line | Bottom transition | `0.1s linear` |
| Card hover | Transform translateY | `0.2s ease` |
| Nav-tab hover | Background + color | `0.15s` |
| Protocol card hover | Border + transform | `0.2s ease` |

---

## 6. Принципы именования

### 6.1 CSS Variables
- Все цвета, размеры, шрифты — через `var(--name)`
- Определены в `:root` в `styles.css`

### 6.2 CSS Классы
- Использовать **kebab-case**: `.audio-meter-col`
- Блоки: `.meter-container`, `.srt-chart-card`
- Элементы: `.meter-label`, `.meter-value`
- Модификаторы: `.alert-item.warning`, `.dbfs-readout__value--danger`

### 6.3 ID-атрибуты
- Только для JS-binding: `#dbfsValL`, `#lufsPeakM`
- Формат: `camelCase` или `kebab-case`

---

## 7. Обязательные правила

1. **Тёмная тема единственная.** Никаких light-mode стилей.
2. **Метры — solid colors.** Никаких gradients на шкалах.
3. **Шрифт mono для значений.** Все числовые readouts — `var(--font-mono)`.
4. **BEM-нотация для новых компонентов.**
5. **CSS variables вместо хардкода.**
6. **Проверять DESIGN_SYSTEM.md перед созданием новых элементов.**

---

## 8. История изменений

| Дата | Изменение | Автор |
|------|-----------|-------|
| 2026-06-08 | Удалён right-panel из всех шаблонов | User |
| 2026-06-08 | DBFS + LUFS расположены рядом (audio-meters-row) | User |
| 2026-06-08 | Nav-tabs убраны из header video-analyzer | User |
| 2026-06-08 | Создан Design System v1.0 | Kimi |
