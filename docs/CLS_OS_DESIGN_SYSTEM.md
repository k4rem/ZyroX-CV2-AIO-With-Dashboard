# CLS OS Design System

**Status:** Phase 1.5 design architecture. The primary implementation specification for CLS OS UI.
**Authority:** Implements `cls-os-design-system` (project skill). Where this document and a generic skill disagree, this document wins. Where this document is silent, `cls-os-design-system` rules apply, then `frontend-design` craft.
**Companion documents:** `CLS_OS_UI_AUDIT.md` (current-state findings), `CLS_OS_BRANDING_CLEANUP_MAP.md` (ZyroX removal map), `CLS_OS_PHASE_1_5_IMPLEMENTATION_PLAN.md` (Tasks A/B/C).

Implementation agents: every value here is a decision, not a suggestion. If a value feels wrong in a real screenshot, raise it against the Decision Register (§32) instead of improvising a new value.

---

## 1. Inputs and reference analysis

Five owner references were supplied in the design-architecture conversation. What each contributes and what it does not:

| Reference | Take | Reject |
|---|---|---|
| **CLS website, Home** (sidebar + module grid) | Near-black violet-tinted surfaces (`#060608` page, `#08070C` sidebar, `#0C0B10` panel, `#131218` raised, sampled). Sidebar grouped by small section labels. Active nav item = tinted row + purple bar at the inline-start edge. Breadcrumb `CLS / HOME` with a small icon tile. Small radius (≈3–4 px). Mono uppercase system labels. Thin 1 px borders. | Seven identical module cards in a grid; most of the canvas unused on the right; muted label text ≈3.3:1 contrast (below AA); `LOCKED` chip repeated on every card. |
| **CLS License Admin** | Compact stat strip (number over label). Dense table with mono serials, status chips, an actions dropdown whose destructive items (`Ban`, `Delete`) are red. Filter row directly above the table. Arabic user content inside English table cells (mixed direction is a real requirement, not a hypothetical). | `ACTIVE` status rendered in purple (brand replacing semantics). Full-width purple "Generate key" bar. Everything in uppercase mono, which flattens hierarchy. |
| **Stakent dark dashboard** | Layered surfaces with a distinct raised tier. Sparkline with a glowing live endpoint marker. Large numerals whose fractional part is dimmed. Segmented controls and compact filter chips in panel headers. One accented promo surface per screen, not many. | Large 16–20 px radii, spacious card padding, marketing card inside an app, fintech lavender pastel fills. |
| **Orbital example** (red robot icon in three circles) | Confirms the owner wants a single animated system motif as the landing's focal point. | Orbiting circles and dots. This is literally the ZyroX "architecture" section (`dashboard/app/page.tsx` spinning rings around a `Bot` icon). Not copied. |
| **Official CLS logo** (PNG, 1024², on black) | The brand hue: `#6025E2` (mean of logo pixels; HSL 259°, 77 %, 52 %). The construction: vertical strokes and ≈30° diagonals, i.e. isometric geometry; strokes are *cut* with small gaps where they meet. This geometry drives the landing visual, the loader and the lattice texture. | Nothing is redesigned. The mark is used as supplied. |

**Unavailable reference:** no standalone screenshot of the full ZyroX landing was supplied. Its motion/presentation benchmark was taken from the ZyroX source (`dashboard/app/page.tsx`) plus the orbital fragment above. Take from ZyroX: one orchestrated page-load reveal, confident large display type, frosted fixed nav. Reject: italic uppercase headlines, 40–80 px radii, red gradients, fake dashboard mockup, pulsing blur blobs, invented metrics.

**Logo asset gap:** the owner supplied a raster PNG. CLS OS needs a vector mark for crisp rendering, animation and favicons. Task A must produce a **faithful geometric trace** of the supplied PNG (same paths, same proportions, same `#6025E2`) and get owner sign-off before use. It is a reproduction, not a redesign. No AI-generated logo.

---

## 2. Research principles and their CLS translation

Sources: Linear's 2024 redesign and 2026 UI refresh write-ups ("inverted L" chrome; sidebar dimmed so content leads; compact tabs; fewer, softer separators), current SOC dashboard practice (fixed band order: trust → changes → work queue → history; severity encoded twice; one-click drill-down), and established patterns from Vercel, Raycast, Railway, Supabase and Clerk (quiet chrome, dense tables, keyboard-first, monochrome with one accent).

| Principle | CLS OS translation |
|---|---|
| Chrome recedes, work leads | Sidebar and topbar sit on the darkest level (`bg-chrome`), text at `fg-2`/`fg-3`; the workspace is one step lighter. Purple in chrome is reserved for the single active item. |
| One structural grammar everywhere | Every page uses the same header → toolbar → content → sticky save bar grammar. No page invents its own header card. |
| Density through rows, not tiles | Real data lives in tables and setting rows. Tiles only for 3–6 headline facts. |
| SOC band order | Security Center and Overview follow: *is the data trustworthy / system state* → *what needs attention* → *work queue* → *context/history*. |
| Severity encoded twice | Every status = colour + glyph/shape + text. Never colour alone. |
| Keyboard-first | Visible focus everywhere, `Esc` closes overlays, arrow navigation in menus/tables, `⌘K`/`Ctrl K` reserved for a later command palette. |
| Honest data | If the API does not provide a value, the UI does not display a number. Unknown is shown as "Unknown". (Spec §25, §37.) |

---

## 3. CLS OS design principles

1. **Command, not marketing.** Every surface answers "what is the state and what can I do". Copy is operational, sentence case, factual.
2. **Black first, purple earned.** The system is near-black and neutral. Purple marks identity (logo), intent (primary action), and place (active/selected/focus). It never marks status.
3. **Intensity follows importance.** Depth, glow and motion scale with the importance of the element (§9 glow levels). A settings row never glows.
4. **Geometry from the mark.** The logo's 30° isometric strokes and cut gaps are the only decorative geometry in the system: perimeter visual, lattice texture, loader. No circles-in-orbit, no random blobs.
5. **Dense and calm.** Compact rows, 13 px UI text, small radii, few borders. Calm comes from alignment and restraint, not whitespace.
6. **Direction-agnostic from day one.** Everything is authored in logical properties; RTL is a mode, not a port.

---

## 4. Color

Dark only. `color-scheme: dark`. No light theme, no `prefers-color-scheme` branch.

### 4.1 Background and surface levels

| Token | HEX | RGB | Use |
|---|---|---|---|
| `--cls-bg-void` | `#040306` | 4 3 6 | Landing/auth canvas, behind the logo. Deepest level. |
| `--cls-bg-chrome` | `#070609` | 7 6 9 | Sidebar, topbar, mobile drawer. |
| `--cls-bg-canvas` | `#09080D` | 9 8 13 | Dashboard workspace background. |
| `--cls-surface-1` | `#0E0D13` | 14 13 19 | Panels, tables, setting groups (the default container). |
| `--cls-surface-2` | `#14121B` | 20 18 27 | Raised: panel header strips, KPI tiles, table header row, popover/menu base. |
| `--cls-surface-3` | `#1B1924` | 27 25 36 | Hover on rows, menu items, secondary buttons at rest. |
| `--cls-surface-4` | `#232030` | 35 32 48 | Pressed neutral, selected neutral (non-brand) state. |
| `--cls-surface-well` | `#060508` | 6 5 8 | Inset wells: text inputs, code blocks, ID fields. |
| `--cls-surface-overlay` | `rgba(20,18,27,0.92)` | — | Floating menus, command surfaces; always with `backdrop-filter: blur(12px)`. |
| `--cls-scrim` | `rgba(2,1,4,0.72)` | — | Modal/drawer backdrop. |

Chrome (`#070609`) is darker than the canvas (`#09080D`) on purpose: navigation recedes.

### 4.2 Lines

| Token | HEX | Use |
|---|---|---|
| `--cls-line-subtle` | `#1A1822` | Dividers inside a panel, table row separators. |
| `--cls-line` | `#24212F` | Panel outline, topbar/sidebar edge. |
| `--cls-line-strong` | `#363247` | Hover outline, secondary-button border, separators that must be seen. |
| `--cls-line-input` | `#433D58` | Resting border of text inputs, selects, checkboxes. |

### 4.3 Brand (CLS purple)

Built on the logo hue (259°). The CLS website's `#A855F7` (Tailwind's stock `purple-500`, hue 271°) is **not** used: it drifts from the logo and reads as a framework default.

| Token | HEX | RGB | Contrast | Use |
|---|---|---|---|---|
| `--cls-brand-700` | `#4A1CB5` | 74 28 181 | — | Primary button pressed. |
| `--cls-brand-600` | `#6025E2` | 96 37 226 | white on it 7.34:1 | **Official logo colour.** Primary button fill. Brand fills. |
| `--cls-brand-500` | `#7646F2` | 118 70 242 | white 5.35:1; 3.78:1 vs chrome | Primary hover fill; active-nav indicator bar. |
| `--cls-brand-400` | `#9474FF` | 148 116 255 | 5.75:1 on surface-1 | Purple text, links, active icons, **focus ring**, chart series 1. |
| `--cls-brand-300` | `#B7A2FF` | 183 162 255 | 8.18:1 on brand tint | Text on brand-tinted backgrounds (selected label). |
| `--cls-brand-tint` | `rgba(96,37,226,0.16)` | — | resolves ≈`#1B1134` on surface-1 | Selected nav row, selected table row, selected builder slot. |
| `--cls-brand-tint-strong` | `rgba(96,37,226,0.26)` | — | — | Pressed selected state, drag-over slot. |
| `--cls-brand-line` | `rgba(148,116,255,0.45)` | — | — | Selected outline, builder selection border. |
| `--cls-brand-glow` | `rgba(118,70,242,0.35)` | — | — | Glow colour for levels G1–G3 only (§9). |

**The logo colour on black is 2.76:1.** It is fine for the logo (logos are exempt, and the mark is large), but it must never carry text, thin icons or 1 px strokes. Use `brand-400` for anything that must be read.

#### Purple budget (enforced in review)

Purple may appear only as: the logo; the primary button (max **one** primary per view region); the active nav item; focus rings; selection (rows, builder components, tabs); links and tertiary text buttons; chart series 1; the landing perimeter; G2/G3 glows. Purple must **not** appear on: status indicators, headings, resting icons, resting borders, table chips for categories, KPI numbers, section labels, scrollbars.

Rule of thumb for screenshot review: in a normal dashboard viewport, purple pixels should be a small minority of the screen. If purple is the first thing noticed on a settings page, something is wrong.

### 4.4 Text

| Token | HEX | Contrast (canvas / surface-1 / surface-2) | Use |
|---|---|---|---|
| `--cls-fg-1` | `#ECEAF4` | 17.0 / 16.4 / 15.6 | Primary text, values, titles. |
| `--cls-fg-2` | `#A6A2B6` | 8.2 / 7.9 / 7.5 | Secondary text, descriptions, nav labels at rest. |
| `--cls-fg-3` | `#827E93` | 5.1 / 4.9 / 4.7 | Muted: captions, table headers, timestamps, placeholders. AA on all surfaces up to surface-2. Do not place on surface-3/4. |
| `--cls-fg-4` | `#565265` | 2.7 | Disabled text only (exempt). Never for information. |
| `--cls-fg-on-brand` | `#FFFFFF` | 7.34 on brand-600 | Text on primary buttons. |

### 4.5 Semantic

Semantic colours are independent from brand. Each has a base (text/icon/dot), a tint (background at 12 %), and a line (border at 32 %).

| Meaning | Base | Tint | Line | Base on own tint | Glyph |
|---|---|---|---|---|---|
| **Success / healthy / online** | `#3DD68C` | `rgba(61,214,140,0.12)` | `rgba(61,214,140,0.32)` | 8.5:1 | `CircleCheck` |
| **Warning / degraded** | `#F2B33D` | `rgba(242,179,61,0.12)` | `rgba(242,179,61,0.32)` | 8.5:1 | `TriangleAlert` |
| **Danger / critical / threat** | `#F25A5F` | `rgba(242,90,95,0.12)` | `rgba(242,90,95,0.32)` | 5.2:1 | `OctagonAlert` |
| **Info / pending** | `#4DB3F0` | `rgba(77,179,240,0.12)` | `rgba(77,179,240,0.32)` | 7.0:1 | `Info`, `CircleDashed` |
| **Neutral / unknown / offline** | `#8B879A` | `rgba(139,135,154,0.12)` | `rgba(139,135,154,0.32)` | — | `CircleHelp`, `CircleOff` |

Danger fills (buttons): `--cls-danger-fill: #C9343A` (white 5.2:1), `--cls-danger-fill-hover: #D93A40` (4.54:1), `--cls-danger-fill-active: #B02D33`.

Security severity scale (four levels, never merged with generic status):

| Severity | Token | HEX |
|---|---|---|
| Critical | `--cls-sev-critical` | `#F25A5F` |
| High | `--cls-sev-high` | `#F47C3C` |
| Medium | `--cls-sev-medium` | `#F2B33D` |
| Low | `--cls-sev-low` | `#8B879A` |

### 4.6 Chart categorical palette

Used only for categorical series (not status): `--cls-chart-1 #9474FF`, `--cls-chart-2 #4FC3D9`, `--cls-chart-3 #D98AD3`, `--cls-chart-4 #C2BED2`. Maximum four series per chart; beyond that group into "Other".

### 4.7 Implementation format

Tokens are defined once in `dashboard/app/globals.css` as **RGB channel triplets** so Tailwind opacity modifiers work, and mapped in `tailwind.config.ts`. No raw hex values in components.

```css
:root {
  color-scheme: dark;

  --cls-bg-void: 4 3 6;
  --cls-bg-chrome: 7 6 9;
  --cls-bg-canvas: 9 8 13;
  --cls-surface-1: 14 13 19;
  --cls-surface-2: 20 18 27;
  --cls-surface-3: 27 25 36;
  --cls-surface-4: 35 32 48;
  --cls-surface-well: 6 5 8;

  --cls-line-subtle: 26 24 34;
  --cls-line: 36 33 47;
  --cls-line-strong: 54 50 71;
  --cls-line-input: 67 61 88;

  --cls-brand-700: 74 28 181;
  --cls-brand-600: 96 37 226;
  --cls-brand-500: 118 70 242;
  --cls-brand-400: 148 116 255;
  --cls-brand-300: 183 162 255;

  --cls-fg-1: 236 234 244;
  --cls-fg-2: 166 162 182;
  --cls-fg-3: 130 126 147;
  --cls-fg-4: 86 82 101;

  --cls-ok: 61 214 140;
  --cls-warn: 242 179 61;
  --cls-danger: 242 90 95;
  --cls-danger-fill: 201 52 58;
  --cls-info: 77 179 240;
  --cls-neutral: 139 135 154;
  --cls-sev-high: 244 124 60;

  --cls-chart-2: 79 195 217;
  --cls-chart-3: 217 138 211;
  --cls-chart-4: 194 190 210;
}
```

Tailwind mapping (names implementation must use):

```ts
colors: {
  void: "rgb(var(--cls-bg-void) / <alpha-value>)",
  chrome: "rgb(var(--cls-bg-chrome) / <alpha-value>)",
  canvas: "rgb(var(--cls-bg-canvas) / <alpha-value>)",
  surface: {
    1: "rgb(var(--cls-surface-1) / <alpha-value>)",
    2: "rgb(var(--cls-surface-2) / <alpha-value>)",
    3: "rgb(var(--cls-surface-3) / <alpha-value>)",
    4: "rgb(var(--cls-surface-4) / <alpha-value>)",
    well: "rgb(var(--cls-surface-well) / <alpha-value>)",
  },
  line: {
    subtle: "rgb(var(--cls-line-subtle) / <alpha-value>)",
    DEFAULT: "rgb(var(--cls-line) / <alpha-value>)",
    strong: "rgb(var(--cls-line-strong) / <alpha-value>)",
    input: "rgb(var(--cls-line-input) / <alpha-value>)",
  },
  brand: { 300: …, 400: …, 500: …, 600: …, 700: … },
  fg: { 1: …, 2: …, 3: …, 4: … },
  ok: …, warn: …, danger: { DEFAULT: …, fill: … }, info: …, neutral: …,
  sev: { critical: …, high: …, medium: …, low: … },
  chart: { 1: …, 2: …, 3: …, 4: … },
}
```

The existing `primary` (`#ef4444`), `secondary`, `accent`, `glass`, `glass-red`, `liquid-glass` tokens and utilities are removed in Task A. `slate-*`, `red-*`, `emerald-*` etc. utility colours are banned in CLS OS components after migration.

---

## 5. Typography

### 5.1 Families

| Role | Family | Why | Weights loaded |
|---|---|---|---|
| **UI (dashboard + body everywhere)** | **IBM Plex Sans** | Engineered, slightly industrial grotesk with enterprise/security heritage. Excellent at 12–14 px. Crucially it has a **designed Arabic companion** (IBM Plex Sans Arabic) with matched metrics, so RTL is a first-class pairing, not a fallback. Not the Inter/Geist default that AI dashboards reach for. SIL OFL, on Google Fonts. | 400, 500, 600 |
| **Arabic** | **IBM Plex Sans Arabic** | Same family, same x-height logic, same weights. | 400, 500, 600 |
| **Mono / data** | **IBM Plex Mono** | Justified: Discord IDs (17–20 digits), serial-like values, timestamps in logs, command names, code. Matches the CLS reference's technical labels and shares Plex's skeleton, so mono never looks pasted-in. | 400, 500 |
| **Display (landing + auth only)** | **Chakra Petch** | Chamfered-corner grotesk whose cut geometry echoes the logo's sliced strokes. Gives the gateway gaming-tech character without "gamer font" clichés (Orbitron, Rajdhani). SIL OFL, on Google Fonts. Latin only, so Arabic display falls through to Plex Sans Arabic 600. | 500, 600 |

Loading: `next/font/google`. Plex Sans + Plex Sans Arabic + Plex Mono in the root layout (subsets `latin`, `arabic`). Chakra Petch instantiated **only** in the landing/auth route layout so the dashboard never downloads it. Inter and Outfit are removed.

```css
--cls-font-ui: "IBM Plex Sans", "IBM Plex Sans Arabic", ui-sans-serif, system-ui, sans-serif;
--cls-font-mono: "IBM Plex Mono", "IBM Plex Sans Arabic", ui-monospace, monospace;
--cls-font-display: "Chakra Petch", "IBM Plex Sans Arabic", "IBM Plex Sans", sans-serif;
:lang(ar) { --cls-font-ui: "IBM Plex Sans Arabic", "IBM Plex Sans", system-ui, sans-serif; }
```

Chakra Petch is **never** used in dashboard UI (labels, buttons, data, page titles). Product UI uses one family; display type belongs to the gateway.

### 5.2 Dashboard scale (fixed rem, ratio ≈1.15; no fluid type)

| Style | Family | Size / line | Weight | Tracking | Notes |
|---|---|---|---|---|---|
| `page-title` | Plex Sans | 20 / 28 | 600 | −0.01em | One per page. |
| `section-heading` | Plex Sans | 15 / 22 | 600 | 0 | Groups inside a page. |
| `panel-title` | Plex Sans | 13 / 20 | 600 | 0 | Panel header strip. |
| `body` | Plex Sans | 13 / 20 | 400 | 0 | Default UI text, table cells, controls. |
| `body-prose` | Plex Sans | 14 / 22 | 400 | 0 | Descriptions longer than one line; max 68ch. |
| `small` | Plex Sans | 12 / 16 | 400 | 0 | Help text, secondary cell lines. |
| `caption` | Plex Sans | 11 / 16 | 400 | 0.01em | Timestamps, footnotes. `fg-3`. |
| `overline` | Plex Mono | 11 / 16 | 500 | 0.08em, uppercase | **Restricted role** (below). |
| `table-header` | Plex Mono | 11 / 16 | 500 | 0.06em, uppercase | `fg-3`. |
| `mono-data` | Plex Mono | 12 / 16 | 400 | 0 | IDs, command names, code, serial-like values. |
| `kpi` | Plex Sans | 28 / 32 | 600 | −0.02em, tabular-nums | Fraction/unit part in `fg-3` at 20 px (Stakent DNA). |
| `kpi-sm` | Plex Sans | 20 / 24 | 600 | −0.01em, tabular-nums | Stat strips. |
| `button` | Plex Sans | 13 / 16 | 500 | 0 | Sentence case. Never uppercase. |
| `nav-item` | Plex Sans | 13 / 20 | 500 | 0 | Sidebar. |

**Mono uppercase is restricted to four roles:** sidebar group labels, panel header overlines, table headers, KPI labels. It is never used on buttons, user content, headings, paragraphs, badges, or more than three words. This keeps the CLS "technical label" DNA without the template tell of uppercase-everything.

All numbers in tables, KPIs, counters and timestamps use `font-variant-numeric: tabular-nums`.

### 5.3 Landing/auth scale (expressive)

| Style | Family | Size / line | Weight |
|---|---|---|---|
| `display-hero` | Chakra Petch | `clamp(56px, 6.5vw, 104px)` / 0.95 | 600, −0.02em |
| `display-2` | Chakra Petch | 32 / 36 (mobile 26 / 30) | 600 |
| `auth-title` | Chakra Petch | 28 / 32 | 600 |
| `lead` | Plex Sans | 18 / 28 (mobile 16 / 24) | 400, `fg-2`, max 52ch |
| `wordmark` | Chakra Petch | 15 / 16 | 600, 0.04em |

Fluid sizing is allowed only on `display-hero`.

### 5.4 Arabic rules

- Under `:lang(ar)` / `[dir="rtl"]`: `text-transform: none`, `letter-spacing: 0` for every style (Arabic has no case; tracking breaks joining). Overlines and table headers render in Plex Sans Arabic 500 at 12 px, not mono.
- Arabic line-height +2 px on `body`, `small`, `caption` (e.g. body 13/22). Arabic glyphs need vertical room for diacritics.
- Minimum Arabic text size is 12 px (captions included).
- Never italicise Arabic. CLS OS uses no italics anywhere (removes the ZyroX italic habit).

---

## 6. Layout, grid and density

### 6.1 Shell dimensions

| Element | Value |
|---|---|
| Topbar height | **48 px** |
| Sidebar expanded | **248 px** |
| Sidebar collapsed (icon rail) | **56 px** |
| Mobile drawer | min(320 px, 85vw) |
| Sidebar nav item height | 32 px |
| Sidebar group label row | 24 px, 16 px space above each group |
| Page header block | 56 px minimum (title + one-line description + actions) |
| Sticky save bar | 48 px, bottom of content column |

### 6.2 Content canvas

- **Data pages** (tables, logs, feeds, Overview, Security Center): fluid, no max width. They use the full width of a 27" display.
- **Settings pages**: two columns at ≥1280 px. Form column max **760 px**; a context rail of **320 px** at ≥1440 px (module status, help, "what this changes", danger zone link). Below 1440 the rail folds under the form. Settings forms never stretch to 2000 px.
- **Grid**: 12 columns, 12 px gap at desktop, 16 px at ≥1920.

### 6.3 Gutters and gaps

| Context | Value |
|---|---|
| Page gutter <768 | 16 px |
| Page gutter 768–1919 | 24 px |
| Page gutter ≥1920 | 32 px |
| Gap between page sections | 24 px |
| Gap between panels in a grid | 12 px |
| Panel inner padding | 16 px (compact panels 12 px) |
| Panel header strip | 40 px high, 12 px inline padding |
| Setting row | 12 px block padding, divided by `line-subtle` |

### 6.4 Table rows

| Density | Row height | Use |
|---|---|---|
| Compact | **32 px** | Logs, audit, sessions, event streams. |
| Default | **36 px** | Members, tickets, invites, grants. |
| Comfortable | **44 px** | Touch (`pointer: coarse`) and mobile list rows. Also any row containing a 32 px avatar. |

Header row: 32 px on `surface-2`.

### 6.5 Form density

| Control | Height |
|---|---|
| `sm` (table toolbars, inline edits) | 28 px |
| `md` (default) | 32 px |
| `lg` (landing, auth, mobile primary actions) | 40 px |
| Touch devices | Every interactive target ≥ 40 px visual / 44 px hit area |

Label above field (6 px gap), help text below (4 px gap). Vertical rhythm between fields: 16 px.

### 6.6 Breakpoints

Tailwind defaults plus one: `sm 640`, `md 768`, `lg 1024`, `xl 1280`, `2xl 1536`, **`3xl 1920`**. `4xl 2560` exists only for grid column count changes on the Overview/Security surfaces.

### 6.7 Z-index scale

`base 0 · sticky 10 · topbar 30 · sidebar 40 · scrim 50 · drawer 60 · modal 70 · popover/menu 80 · toast 90 · tooltip 100`. No other values.

---

## 7. Spacing

Base unit 4 px. Nine steps. Nothing outside the scale.

| Token | px | Intended use |
|---|---|---|
| `space-0.5` | 2 | Icon-to-dot offsets, chip inner block padding. |
| `space-1` | 4 | Label ↔ help text, icon ↔ tight text. |
| `space-1.5` | 6 | Icon ↔ label in buttons and nav items; label ↔ field. |
| `space-2` | 8 | Items in a toolbar, chip groups, compact cell padding. |
| `space-3` | 12 | Table cell inline padding, panel gap, setting-row block padding. |
| `space-4` | 16 | Panel padding, field-to-field rhythm, mobile gutter. |
| `space-6` | 24 | Page sections, desktop gutter. |
| `space-8` | 32 | Large-desktop gutter, landing inner gaps. |
| `space-12` | 48 | Landing section breathing room only. |
| `space-16` | 64 | Landing hero vertical rhythm only. |

`space-12` and `space-16` are **banned inside the dashboard**.

---

## 8. Radius

| Token | px | Components |
|---|---|---|
| `radius-xs` | **2** | Status chips, severity chips, `kbd`, checkboxes, table selection highlight, inline code. |
| `radius-sm` | **4** | Buttons, inputs, selects, nav items, tabs, tooltips, menu items, segmented controls. |
| `radius-md` | **6** | Panels, table containers, popovers, dropdown menus, KPI tiles, toasts. |
| `radius-lg` | **10** | Modals, drawers (the attached edge is 0), landing frames, builder canvas frame. |
| `radius-full` | 9999 | Avatars, status dots, switch track and thumb, guild icons in lists (Discord convention). |

No pill buttons. No pill badges. No 16 px+ radius anywhere in the dashboard. Nested radius rule: inner radius = outer radius − padding (never larger than the parent).

---

## 9. Borders, shadows, depth and glow

### 9.1 Surface recipes

| Surface | Background | Border | Inner highlight | Shadow |
|---|---|---|---|---|
| Panel (default) | `surface-1` | 1 px `line` | `inset 0 1px 0 rgb(255 255 255 / 0.03)` | none |
| Raised (KPI tile, panel header) | `surface-2` | 1 px `line` | `inset 0 1px 0 rgb(255 255 255 / 0.05)` | none |
| Popover / menu | `surface-overlay` + blur 12 px | 1 px `line-strong` | `inset 0 1px 0 rgb(255 255 255 / 0.06)` | `elev-1` |
| Modal / drawer | `surface-1` | 1 px `line-strong` | `inset 0 1px 0 rgb(255 255 255 / 0.06)` | `elev-2` |
| Input well | `surface-well` | 1 px `line-input` | `inset 0 1px 2px rgb(0 0 0 / 0.5)` | none |

`elev-1`: `0 8px 24px -8px rgb(0 0 0 / 0.6)`.
`elev-2`: `0 24px 64px -16px rgb(0 0 0 / 0.75)`.
Shadows on the dashboard canvas are for floating layers only. Panels do not cast shadows: depth comes from the surface ladder + inner highlight.

### 9.2 State borders

| State | Border |
|---|---|
| Hover (interactive container) | `line-strong` |
| Selected | `brand-line` + `brand-tint` background |
| Focus (keyboard) | Focus ring (below), border unchanged |
| Invalid | `danger` line (32 %) + danger help text |
| Disabled | `line-subtle`, content `fg-4` |

### 9.3 Focus ring

`:focus-visible` only: `outline: 2px solid rgb(var(--cls-brand-400)); outline-offset: 2px;`. On inputs the offset is 0 and the border also switches to `brand-400`. Same ring on danger controls (consistency beats colour-matching). Never removed without a replacement.

### 9.4 Glow intensity levels

| Level | Name | Recipe | Allowed on |
|---|---|---|---|
| **G0** | None | — | Everything by default: panels, rows, settings, KPIs, cards, icons. |
| **G1** | Interaction | `0 0 0 1px rgb(var(--cls-brand-400) / 0.35), 0 4px 16px -6px rgb(var(--cls-brand-600) / 0.55)` | Primary button hover; landing CTA at rest. |
| **G2** | Active / selected / live | `0 0 12px rgb(var(--cls-brand-500) / 0.35)` | Active nav indicator bar; selected builder component; the single live endpoint dot on a live chart; "armed" state of Incident Mode toggle. |
| **G3** | Focal visualization | Layered: `drop-shadow(0 0 24px rgb(var(--cls-brand-500) / 0.45))` on SVG core + radial `brand-600` at 8 % behind | Landing Perimeter core; auth transition; Security Center posture mark **only during an active incident**. Max one G3 per viewport. |
| **D2** | Danger glow | `0 0 12px rgb(var(--cls-danger) / 0.40)` | Critical status dot of an unacknowledged incident; critical incident banner's leading edge. Nothing else. |

Glow is never used on: settings rows, form fields, table rows, KPI tiles, ordinary cards, headings, status chips (other than D2 above), hover of non-primary controls.

### 9.5 Background texture

The **isometric lattice** (lines at 30°, 90°, 150°; 24 px cell; 1 px `fg-1` at 3 % opacity, radially masked) is the only background texture. Allowed: landing, auth screens, Security Center posture header, "not configured" module states. Not allowed on normal dashboard pages. No noise textures, no gradient blobs, no external image URLs (the ZyroX `grainy-gradients.vercel.app` noise is removed).

---

## 10. Motion

Motion communicates state, hierarchy and causality. On the dashboard it must never delay a task. The landing may perform.

### 10.1 Tokens

| Token | Duration | Use |
|---|---|---|
| `--cls-dur-instant` | 80 ms | Press feedback, colour changes on active. |
| `--cls-dur-micro` | 120 ms | Hover, focus, tooltip in, checkbox/switch. |
| `--cls-dur-standard` | 200 ms | Dropdowns, popovers, tabs, row expand, sidebar label fade. |
| `--cls-dur-emphasized` | 280 ms | Drawers, modals, sidebar collapse, toasts. |
| `--cls-dur-cinematic` | 600–1400 ms | Landing and auth transitions only. |

| Easing token | Curve | Use |
|---|---|---|
| `--cls-ease-out` | `cubic-bezier(0.2, 0, 0, 1)` | Default entrance. |
| `--cls-ease-in-out` | `cubic-bezier(0.4, 0, 0.2, 1)` | Moves/resizes (sidebar width). |
| `--cls-ease-exit` | `cubic-bezier(0.4, 0, 1, 1)` | Exits (always ≈70 % of the entrance duration). |
| `--cls-ease-emphasized` | `cubic-bezier(0.16, 1, 0.3, 1)` | Drawers, modals, landing reveals. |

Animate `transform` and `opacity` only (plus `stroke-dashoffset` for SVG). Never animate `width`/`height`/`top` of large layouts, except the sidebar width, which uses a CSS grid-template-columns transition.

### 10.2 Component motion

| Interaction | Spec |
|---|---|
| **Sidebar collapse** | Grid column 248→56 px, 280 ms `ease-in-out`. Labels fade out in the first 120 ms and in during the last 120 ms. Group labels become 1 px separators in the rail. |
| **Navigation (route change)** | No page choreography. Content area fades from 0.6→1 opacity in 120 ms. Active nav bar slides to the new item (translateY, 200 ms `ease-out`). |
| **Page entrance** | Only the content region: 120 ms opacity. No staggered cards, no slide-ups. |
| **Card / row hover** | Background to `surface-3` + border to `line-strong`, 120 ms. No scale, no lift, no glow. |
| **Button** | Hover colour 120 ms. Active: `scale(0.98)` 80 ms. Loading: label fades to 0.6, hex loader replaces the leading icon, width locked. |
| **Modal** | Scrim fade 200 ms. Panel: opacity 0→1 + scale 0.98→1, 280 ms `ease-emphasized`. Exit 200 ms. |
| **Drawer** | Slide from inline-end (details) or inline-start (mobile nav): translate 100 %→0, 280 ms `ease-emphasized`. |
| **Dropdown / popover** | Opacity + 4 px translate from the trigger side, 160 ms `ease-out`; exit 100 ms. |
| **Tooltip** | 400 ms delay on first hover, 0 ms on subsequent within 1 s; 120 ms fade. |
| **Chart** | First mount: line draws in (`stroke-dashoffset`) 480 ms `ease-out`; bars grow from baseline 320 ms with 20 ms stagger (max 12). Data updates tween 200 ms. |
| **Counter** | Numbers count only on first mount and only for values that changed since the last visit; 400 ms `ease-out`, tabular-nums. Live-updating values swap without counting. |
| **Status pulse** | Only for **live** and **critical-unacknowledged**: a ring scaling 1→2.2 with opacity 0.5→0, 2.4 s (live) or 1.2 s (critical), infinite. Nothing else pulses. `animate-pulse` on text/buttons is banned. |
| **Drag and drop** | Picked item: `scale(1.02)`, `elev-1`, 120 ms. Drop target: 2 px `brand-400` insertion line, slot `brand-tint-strong`. Drop: settle 200 ms `ease-emphasized`. Invalid target: `not-allowed` cursor + danger insertion line. |
| **Loading** | Skeleton blocks at `surface-3`, shimmer sweep 1.6 s linear. The hex loader (§12.4) for indeterminate action waits > 400 ms. No full-screen spinners inside the dashboard. |
| **Success feedback** | Toast slides in 280 ms; the saved field/row flashes `ok` tint for 600 ms. Save bar collapses 200 ms. |
| **Error feedback** | Field: border to danger, help text replaced, no shake. Toast for server failures; inline banner for page-level failure. |

### 10.3 Reduced motion

Under `prefers-reduced-motion: reduce`: all durations above `micro` become 0 ms except opacity fades (kept at 120 ms). No pulses (static ring instead), no parallax, no chart draw-in, no counters, no shimmer (static skeleton), landing renders its final composed state immediately, auth transition becomes a 120 ms crossfade. Implemented through a single `@media (prefers-reduced-motion: reduce)` block that resets the duration tokens, plus a `useReducedMotion` hook for JS-driven motion.

---

## 11. Iconography

**Primary library: Lucide** (`lucide-react`, already installed). Chosen because it is already in the stack, has consistent 24-grid geometry whose straight terminals sit well with Plex, and supports per-instance stroke width. Phosphor and Tabler are not added.

| Context | Size | Stroke | Colour |
|---|---|---|---|
| Table cells, chips, inline text | 14 px | 1.75 | inherits text colour |
| Nav items, buttons, inputs, menu items | 16 px | 1.75 | `fg-3` at rest, `fg-2` hover, `brand-400` active (nav only), `fg-1` in buttons |
| Page title, panel empty states | 20 px | 1.5 | `fg-2` |
| Full empty/not-configured states | 24 px | 1.5 | `fg-2` |

Rules:
- Icons never sit inside coloured rounded squares (the ZyroX `bg-red-500/10 rounded-2xl` icon tile is banned). Exception: guild/user avatars.
- Icon-only buttons always have `aria-label` and a tooltip.
- Sidebar icons are always visible (expanded and rail). Active icon uses `brand-400`; nothing scales.
- One icon per concept across the product (e.g. Antinuke is always `ShieldAlert`, Automod `ShieldCheck`, Tickets `Ticket`, Logging `ScrollText`, Audit `History`, Access `KeyRound`, J2C `AudioLines`, Welcome `DoorOpen`). The mapping lives in one file (`lib/nav.ts`).
- Official Discord glyph (Discord brand asset) on the Discord sign-in button only.
- The CLS logo is not an icon and never enters the icon set.
- No emoji as UI icons (removes the 🥇🥈🥉 leaderboard medals).

---

## 12. Brand assets and signature elements

### 12.1 Logo usage

- Files (Task A): `dashboard/public/brand/cls-mark.svg` (traced, owner-approved), `cls-mark-512.png`, `app/icon.png` (32/192), `app/apple-icon.png` (180).
- Colour: `#6025E2` on `bg-void`/`bg-chrome` only. Monochrome white variant (`fg-1`) allowed for tiny sizes (< 20 px) where purple-on-black loses definition.
- Minimum size 16 px tall. Clear space = 25 % of mark height on all sides.
- Never recoloured to another hue, never outlined, never placed on purple fills, never rotated, never animated in a way that changes its final geometry.

### 12.2 Wordmark lock-up

Mark (20 px tall in the sidebar, 28 px in landing nav) + 8 px gap + "CLS OS" in `wordmark` style, `fg-1`. "OS" is not coloured differently (single-word accenting is a template tell). The owner tagline "Power. Control. Victory." is **not** used inside the dashboard (see Decision Register).

### 12.3 Perimeter mark

A reduced, static version of the landing Perimeter (§13): three nested pointy-top hexagon outlines, 1 px, cut into six segments each. Used as the Security Center posture glyph and on auth screens. It is a system graphic, not the logo.

### 12.4 Hex loader

Indeterminate loader: a pointy-top hexagon outline made of six segments; segments light `brand-400` in sequence (120 ms step, 720 ms loop), others at `fg-4`. Sizes 14/16/24 px. Replaces every spinning `RefreshCw`/`RefreshCcw` loader. Reduced motion: all six segments at 60 % opacity, static, with "Loading" text for screen readers.

---

## 13. Landing architecture (login gateway)

Mode: Persuade, but the "sale" is only: this is the official, private CLS control system; sign in if you have access.

### 13.1 Structure (≈1.8 desktop viewports)

**Viewport 1: Gateway** (`min-height: 100svh`)

```
┌──────────────────────────────────────────────────────────────┐
│ [mark] CLS OS                                   Sign in ▸   │  48 px bar, transparent → chrome on scroll
│                                                              │
│   CLS OS                              ⬡  perimeter visual   │
│   The private control system for     ⬡⬡  (≈ 560 px square) │
│   the CLS Discord. Security,        ⬡ [CLS] ⬡              │
│   support, recovery and automation,  ⬡⬡  domain labels on  │
│   run from one place.                 ⬡  outer segments     │
│                                                              │
│   [ (Discord) Sign in with Discord ]                         │
│   Access is invite-only. The CLS root owner grants it.       │
│                                                              │
│   ⌄ What runs inside                                         │
└──────────────────────────────────────────────────────────────┘
```

- Text column start-aligned (mirrors in RTL), occupies 5 of 12 columns; visual 7 of 12, vertically centred.
- One CTA. No secondary CTA. No "Add to Server". No nav links other than "Sign in".

**Viewport 2 (≈0.8 vh): Inside CLS OS + footer**

A 3 × 2 matrix of **rows, not cards**: each item is icon (20 px) + name (`section-heading`) + one factual sentence + availability line in `fg-3` ("Available now" / "In development"). Separated by `line-subtle` hairlines. Content:

| Domain | Line | Availability (Phase 1.5 truth) |
|---|---|---|
| Security | Antinuke and automod protect the server from destructive changes and spam. | Available now |
| Support | Ticket categories and panels configured from the dashboard; tickets run in Discord. | Available now (V2 builder in development) |
| Recovery | Encrypted backups of bot and platform data. Restore tooling is being built and tested. | In development |
| Automation | Welcome messages, auto roles, reaction roles and Join to Create voice channels. | Available now |
| Moderation | Automod rules and event logging to channels you choose. | Available now |
| Audit | Every dashboard change is recorded with who made it and when. | Available now (viewer in development) |

Footer (48 px): mark + "CLS OS", `Privacy`, `Terms`, `CLS Discord` (external), "Private system. Access by grant only." No copyright "Development // Neural Infrastructure", no status claims.

No FAQ, no stats, no testimonials, no dashboard mockup, no pricing.

### 13.2 Hero visual concepts

**Concept A: Command Lattice.** An isometric lattice fills the hero; six domain nodes sit on lattice vertices and route PCB-like traces into the logo core; pulses run along the traces.
Strengths: directly uses the logo's 30° grid; shows "modules connected to one core".
Weaknesses: circuit-board imagery is a crypto/AI cliché; reads busy at small sizes; labels on a lattice are hard to reflow for RTL and mobile; no natural "entering a gate" moment.

**Concept B: CLS Perimeter.** Three nested pointy-top hexagons around the official mark. A pointy-top hexagon is built from vertical edges and ±30° edges, exactly the angles of the CLS mark, so the rings look *derived from the logo* rather than generic. Each ring is cut into six segments with small gaps (the logo's cut strokes). The outer ring's six segments are the six real domains (Security, Support, Recovery, Automation, Moderation, Audit), labelled outside the ring. Middle ring = controls (short tick marks). Inner ring = the access boundary.
Strengths: security/control/entry metaphor is literal and truthful (a private perimeter); it gives the sign-in flow a real choreography (the perimeter locks, then opens); it reduces cleanly to a mobile size, a loader (§12.4) and a Security Center glyph (§12.3), so it is a system, not a one-off decoration.
Weaknesses: nested shapes could echo the orbital reference. Mitigated: straight segments, fixed orientation (no rotation), no orbiting dots.

**Concept C: Live Operations Stream.** A horizontal stream of event rows ("member verified", "ticket opened") flowing past the logo.
Strengths: feels "alive".
Weaknesses: a public page cannot show real events (privacy), so it would be fake data, and it slides into fake-terminal/hacker UI. Rejected on the brief's own rules.

**Selected: Concept B, CLS Perimeter**, with Concept A's lattice used only as the faint background texture (§9.5), never as nodes or traces.

### 13.3 Perimeter construction

- SVG, one file, < 8 KB, inline in the page. Pure SVG + CSS transforms/opacity + `stroke-dashoffset`. No canvas, no WebGL, no motion library.
- Ring sizes (desktop 560 px square): outer 100 %, middle 74 %, inner 50 %; logo at 26 % height, centred, official geometry.
- Strokes: outer 1.5 px `fg-3` at 40 %; middle 1 px `fg-3` at 30 %; inner 1.5 px `brand-500` at 60 %. Segment gaps = 3 % of edge length.
- Domain labels: `overline` style outside each outer segment (Arabic: Plex Sans Arabic 12 px, no uppercase).
- Background: lattice texture masked to a 70 % radial fade; a single radial `brand-600` at 8 % behind the core (G3).

### 13.4 Landing motion choreography

| t (ms) | Event |
|---|---|
| 0 | `bg-void`. Lattice fades 0 → 1 over 600 ms. |
| 150 | Logo strokes draw in via `stroke-dashoffset` (600 ms `ease-emphasized`). Final frame is the exact official mark. |
| 600 | Inner ring segments arm one by one, 60 ms stagger (six segments), each 240 ms. |
| 850 | Middle ring ticks fade in together, 300 ms. |
| 1000 | Outer segments arm, 60 ms stagger; each domain label fades in with its segment. |
| 700 | Text column: title, lead, CTA reveal together as one group, opacity + 8 px translate, 500 ms `ease-emphasized` (one orchestrated moment, not per-element staggers). |
| 1600 | Composition complete. Core glow settles to G3 resting intensity. |
| Idle | Every 7 s a single highlight (12 % of an edge) travels once around the outer ring (1.8 s). Hovering or focusing a domain label (or its row below) brightens that outer segment to `brand-400` and pauses the sweep. |
| Pointer | Rings parallax by depth: 2 / 4 / 6 px maximum toward the pointer, 200 ms smoothing. No rotation, no 3D tilt. Disabled on touch. |
| Scroll | Header bar gains `bg-chrome` at 80 % + blur after 24 px of scroll. The perimeter moves at 0.85× scroll speed until off-screen. |

Performance: animations paused when the tab is hidden or the visual is off-screen (IntersectionObserver). Target: no layout shift, LCP element is the H1 text, not the SVG.

Reduced motion: the final composed state renders immediately; no sweep, no parallax.

Mobile (< 768): the perimeter renders at 280 px above the title, labels hidden (domains appear in the list below), idle sweep kept, no parallax.

### 13.5 Metadata

`title`: "CLS OS". Dashboard pages: "{Page} · {Guild} · CLS OS" (the middle dot is standard title-bar convention, not UI copy). `description`: "The private control system for the CLS Discord." `robots`: `noindex` for everything except `/`, `/privacy` and `/terms` (REVISIT, see §32). `themeColor`: `#040306`. Icons from the traced mark.

---

## 14. Authentication experience

Entering CLS OS should feel like passing a controlled gate, not signing up for a product.

| State | Surface | Content and behaviour |
|---|---|---|
| **Logged out** | Landing (§13) | One CTA: `lg` primary button with the official Discord glyph, "Sign in with Discord". |
| **Sign-in pending** | Landing, in place | On click: button enters loading ("Connecting to Discord…", hex loader, width locked). The perimeter "locks": segment gaps close and the inner ring brightens to G3 over 500 ms, then the browser navigates to Discord. Reduced motion: loading button only. |
| **OAuth callback / session establishment** | `/auth/continue` (new route, Task B), full-screen `bg-void` + lattice + static Perimeter mark | NextAuth's callback redirects here, not straight into the shell. Shows the user's Discord avatar and name with "Checking your access" (hex loader). The server resolves the session and authorized guilds, then routes (below). The Perimeter mark's inner ring opens (segments move outward 8 px and fade, 400 ms) as the shell mounts. Typical duration < 1 s; never an artificial delay. |
| **Routing after sign-in** | — | 0 authorized guilds and not root → **No access** screen. Exactly 1 guild → that guild's Overview. >1 → guild picker. Root with 0 guilds → Platform page. A `callbackUrl` inside `/dashboard` is honoured if authorized. |
| **No access (authenticated, no grant)** | Auth screen layout | Title "No access yet". Body: "You're signed in as {name}. Access to CLS OS is granted by the CLS root owner." Discord ID shown in `mono-data` with a Copy button. Actions: "Sign out" (secondary). No alarming red: this is a normal state. |
| **Auth error** | `/auth/error` (NextAuth `pages.error`) | Error-specific copy, no raw codes as headlines (code shown small as "Reference: OAuthCallback"): cancelled on Discord ("Sign-in was cancelled on Discord."), callback failure ("Discord sign-in didn't complete. Try again."), service unreachable ("CLS OS can't reach the bot service right now. Try again in a minute."), configuration ("Sign-in isn't configured correctly on this server. Tell the root owner."). Primary "Try again" (restarts sign-in), secondary "Back to CLS OS". |
| **Session ended / revoked** | Redirect to `/` with a notice bar | Bar above the gateway: "Your session ended. Sign in again to continue." (info tone). Replaces the current behaviour of silently re-triggering Discord sign-in from the dashboard layout. |
| **Already authenticated** | Server-side redirect | Visiting `/` with a valid session redirects to `/dashboard` before render (no flash of the landing). `/dashboard` applies the routing rules above. |
| **Sign out** | User menu | "Sign out" → confirmation not required → returns to `/` with notice "Signed out." |

Auth screens share one layout: centred 400 px column on `bg-void` with lattice texture, Perimeter mark 96 px above the title, `auth-title` (Chakra Petch), body `body-prose`, actions `lg`.

Task B may add `pages.error` and the `/auth/continue` callback target to NextAuth configuration. It must not change session creation, token minting, the proxy or grant logic.

---

## 15. Dashboard app shell

Inverted-L chrome: sidebar at inline-start plus topbar across the content column.

```
┌────────────┬─────────────────────────────────────────────────────────┐
│ [mark] CLS OS │ ☰  CLS Main / Security / Antinuke      ● Bot online 42 ms  (avatar) │ 48
│ ┌────────┐ ├─────────────────────────────────────────────────────────┤
│ │ CLS Main ⌄│ │ Antinuke                                    [Save] │
│ └────────┘ │ │ Destructive-action protection for this server.       │
│ OVERVIEW   │ │─────────────────────────────────────────────────────│
│  Overview  │ │ content                                              │
│ MANAGEMENT │ │                                                      │
│  Roles     │ │                                                      │
│ …          │ │                                                      │
│            │ │                                                      │
│ ────────── │ │                                                      │
│ ⟨ Collapse │ │                              [Discard] [Save changes] │ sticky bar
└────────────┴─────────────────────────────────────────────────────────┘
```

### 15.1 Sidebar

- Background `bg-chrome`, inline-end border 1 px `line`. Full height, not floating, no radius (removes the ZyroX floating rounded glass sidebar).
- **Header (48 px):** mark + "CLS OS" wordmark; in rail mode the mark only.
- **Guild switcher (40 px):** guild icon 20 px (`radius-full`) + guild name (truncate) + `ChevronsUpDown`. Opens a popover listing authorized guilds (icon, name, access template) with search when > 6. In rail mode: guild icon only, same popover. Replaces the large guild header card.
- **Groups:** label in `overline`, `fg-3`, 24 px row, 16 px above. Groups have no collapse toggles in Phase 1.5 (the tree is short enough). In rail mode group labels become 1 px `line-subtle` separators with 8 px margins.
- **Items (32 px):** 16 px icon + label (`nav-item`), 8 px inline padding, `radius-sm`.
  - Rest: icon `fg-3`, label `fg-2`.
  - Hover: background `surface-3`, label `fg-1`, 120 ms.
  - Active: background `brand-tint`, label `fg-1`, icon `brand-400`, **2 × 16 px `brand-500` bar at the inline-start edge with G2**. `aria-current="page"`.
  - Focus: focus ring inset (offset −2 px).
  - Rail mode: 40 × 32 px hit area centred, label in a tooltip (inline-end side), `aria-label` = label.
- **Badges:** only real counts that require action (e.g. Tickets open count once Tickets V2 exists; Security open incidents). Style: 18 px high, `radius-xs`, `surface-4` background, `fg-2` 11 px tabular; critical incidents use danger tint. No "New", "Beta" or promotional badges. Legacy pages show nothing in the sidebar (the "Legacy" notice lives on the page).
- **Footer:** "Collapse" toggle (`PanelLeftClose`/`PanelLeftOpen`, mirrored in RTL) with `aria-expanded`. Collapse state persists in `localStorage` (`cls.sidebar`).
- **Future items:** hidden. A route that does not exist does not appear. There is no "Coming soon" section (decision: LOCKED).

### 15.2 Phase 1.5 navigation tree

Target IA from the project skill, filtered to what exists. Existing routes are kept; grouped pages use in-page tabs that link to the existing routes.

| Group | Item | Route(s) | Notes |
|---|---|---|---|
| OVERVIEW | Overview | `/guild/[id]` | Rebuilt (§16). |
| MANAGEMENT | Roles | `/customroles`, `/invcrole`, `/vanityroles` | One nav item; tabs "Custom roles", "Voice role", "Vanity roles". Commands and Members hidden (no API). |
| TICKETS | Ticket setup | `/tickets` | Legacy config. Page header notice: "Panels are published from Discord with the ticket command." |
| ENGAGEMENT | Welcome | `/welcome`, `/joindm` | Tabs "Channel message", "Direct message". |
| | Auto roles | `/autorole` | |
| | Reaction roles | `/reactionroles` | |
| | Auto react | `/autoreact` | |
| | Invites | `/tracking`, `/invites` | Tabs "Tracking", "Leaderboard (legacy counts)". |
| | Join to Create | `/j2c` | Required module (spec §19). Not in the skill IA; placed here (REVISIT). |
| MODERATION | Automod | `/automod` | |
| | Logging | `/logging` | Currently only in the tab bar; now in the sidebar. |
| SECURITY | Antinuke | `/antinuke` | Whitelist lives inside. Security Overview, Bot Protection, Bot Trap, Disaster Recovery hidden until their phases. |
| SYSTEM | Bot settings | `/settings` | Prefix. |
| | Access | `/dashboard/access` | Root only. |
| | Platform | `/dashboard/admin` | Root only. Renamed from "Admin Panel". |

Hidden in Phase 1.5 (routes stay, not linked): Leveling and Leaderboard (module disabled by default, spec §18.3), Verification (legacy engine, rebuilt in Phase 3; REVISIT with owner), Docs.

Root visibility must be computed on the server (the dashboard layout becomes a server component wrapper that passes `isRoot` into the client shell). The current client-side `isAdmin()` check reads a server-only env var and can never be true in the browser.

### 15.3 Topbar

48 px, `bg-chrome`, bottom border `line`. Sticky. Contents in order (logical, so RTL mirrors):

1. **Sidebar toggle** (`<1024` opens drawer; ≥1024 toggles rail).
2. **Breadcrumbs**: `CLS Main / Security / Antinuke`. Separator `/` in `fg-4` (direction-neutral). Last crumb `fg-1`, others `fg-3` links. Guild name crumb is `dir="auto"`. Truncates middle crumbs first. At < 768 only the last crumb shows.
3. Flexible space.
4. **System status indicator**: dot + "Bot online" + latency in `fg-3` tabular ("42 ms"), from `GET /api/v1/bot/status` polled every 30 s. States: online (ok, live pulse), degraded (latency > 400 ms or required-module failure → warn "Degraded"), offline/unreachable (danger "Bot unreachable"). Click opens a popover with the real `/api/v1/system/health` summary (required modules, Postgres, scheduler, permission health for the current guild). This is the one place global health is always visible.
5. **User menu**: 28 px avatar. Menu: name + Discord ID (mono, copy), access level ("Root owner" or template name), divider, "Sign out". No "Support Matrix", no "Deauthorize".

Removed from the topbar: the fake "Query neural network…" search (the command palette is deferred), and the notifications bell (the broadcast endpoint is root-only; see audit). A real notifications surface returns with Security/Tickets phases.

### 15.4 Page header grammar

Every dashboard page:

1. `page-title` + optional one-line description (`body`, `fg-2`, max 80ch).
2. Inline-end: at most one primary action and two secondary actions; overflow into a `MoreHorizontal` menu.
3. Optional tab row (32 px, underline indicator 2 px `brand-500`, labels `fg-2`/`fg-1` active) for grouped pages.
4. Optional page-level notice (legacy, degraded, read-only) as a single-line banner.

No hero cards, icon tiles, gradients or glows in headers.

### 15.5 Save model

Settings pages keep local draft state and show a **sticky save bar** when dirty: `surface-2`, top border `line-strong`, text "Unsaved changes" (`fg-2`), buttons "Discard" (ghost) and "Save changes" (primary). `Ctrl/⌘ S` saves. Navigating away while dirty asks for confirmation. Replaces the 56 px full-width "Save Configuration" buttons.

### 15.6 Mobile drawer

< 1024: the sidebar becomes a drawer from inline-start, `bg-chrome`, full height, `min(320px, 85vw)`, scrim `--cls-scrim`, focus trapped, `Esc`/scrim/route change closes. Same tree and states as desktop, 40 px item height for touch.

---

## 16. Dashboard Overview (guild)

Not a KPI card grid. Hierarchy follows the SOC band order.

```
┌ System line ───────────────────────────────────────────────────────────────┐
│ ● Bot online 42 ms │ Required modules 7/7 │ Permissions 1 module missing │ Postgres ● │ Scheduler ● │
└────────────────────────────────────────────────────────────────────────────┘
┌ Needs attention (list) ─────────────────────┐ ┌ Server ─────────────────────┐
│ ▲ Logging: bot lacks View Audit Log  [Fix ▸] │ │ 412 members  38 roles  61 ch │
│ ● Antinuke is off                  [Open ▸]  │ │ Your access: Admin           │
│   (empty: "Nothing needs attention.")        │ └──────────────────────────────┘
└──────────────────────────────────────────────┘ ┌ Access ─────────────────────┐
┌ Modules (table) ─────────────────────────────────────────────┐ (root: grants count)
│ Module        State        Detail                       Last change │
│ Antinuke      ● On         3 whitelisted users                     │
│ Automod       ● On         4 of 6 rules                            │
│ Tickets       ● Configured 2 categories · 3 open                   │
│ Welcome       ○ Off        —                                       │
│ Join to Create● On         Trigger: Create VC                      │
│ Logging       ▲ Partial    5 of 9 categories routed                │
└──────────────────────────────────────────────────────────────┘
```

### 16.1 Available now (Phase 1.5 may display)

| Widget | Source | Notes |
|---|---|---|
| System line | `GET /api/v1/bot/status`, `GET /api/v1/system/health` | Bot online + latency; required modules ok/failed (names on hover/popover); permission health for this guild (`missing_by_module`); Postgres; scheduler worker. |
| Needs attention | Derived client/server-side from the same responses + module configs | Only real, checkable conditions: required module failed; bot missing permissions for a module (from `permission_health_summary`); antinuke disabled; logging categories enabled without a channel; ticket categories without staff roles. Each item: severity glyph, one sentence, link to the fixing page. Empty state "Nothing needs attention." |
| Modules table | Existing GET endpoints: antinuke, automod, tickets (`open_ticket_count`, categories), welcome, j2c, logging, autorole, reaction roles | Columns: Module, State (status label), Detail (one factual line), link. "Last change" column is **hidden** until the audit read API exists. |
| Server facts | `GET /api/v1/guilds/{id}` | Member, role, channel counts as a compact stat strip (`kpi-sm`). |
| Your access | Session/grant | Template name; root sees "Root owner". |

### 16.2 Future widgets (must NOT be shown or faked in Phase 1.5)

| Widget | Arrives with | Requirement |
|---|---|---|
| Open incidents / security posture | Phase 7 | Incident store. |
| Recent audit activity feed + "Last change" column | Audit read API (not yet built) | `GET` audit endpoint with guild scope. |
| Open tickets list, first-response metrics | Phase 4 | Tickets V2. |
| Verification / recovery coverage | Phase 3 / 2S | Must use spec §25 wording: "grants on file", never "recoverable". |
| Backup health (last successful off-host backup) | Deployment + backup status API | Real backup job status. |
| Snapshot status (last known-good) | Phase 2 | Snapshot metadata. |
| Activity charts | Phase 5 | Event history. |

Implementation agents must not render placeholders, skeleton-forever panels or "coming soon" tiles for future widgets. They simply do not exist yet.

### 16.3 Global home `/dashboard`

Not a page of its own: it applies the routing rules in §14. Root with no guild context sees **Platform** (`/dashboard/admin`), redesigned as a compact system page: host stats strip (CPU, RAM, database size, loaded modules, all real), required-module table, maintenance mode setting row, broadcast message setting row.

---

## 17. Security Center design language (Phase 7 target; foundation now)

The one page where the system may be visibly "alive". It must feel like an operations console because it *is* one: every element is backed by an event, incident or check.

### 17.1 Bands (fixed order)

1. **Posture header** (lattice texture allowed). Perimeter mark (§12.3) + posture state word:
   - **Secure** (ok): no open incidents, protections armed.
   - **Elevated** (warn): open medium/high incidents or a protection disabled/misconfigured.
   - **Incident** (danger): critical incident open or Incident Mode active. Perimeter mark gets G3 in danger tint, outer ring segment of the affected domain pulses (1.2 s) until acknowledged.
   Also here: Incident Mode state + remaining time (countdown, `kpi-sm` tabular), Dashboard Lock state, **data freshness** ("Events current to 14:02:31", turns warn if the feed is > 60 s stale). Band 1 answers "can I trust this screen and what is the posture".
2. **Since you last looked**: one line of deltas ("2 new incidents, 1 resolved, Bot Trap triggered 3 times").
3. **Incident rail** (work queue): table, sorted by severity then age. Columns: severity chip, title, actor, **attribution** (Certain / Probable / Unknown per spec §37, rendered as text + confidence glyph, never guessed), target, age, state (Open / Contained / Resolved), owner. Row click → incident drawer (timeline, evidence, actions).
4. **Two columns below**:
   - **Live feed** (inline-start, 60 %): virtualized compact rows (32 px): time (mono), event type glyph, actor, action, target. New rows insert at top with a 200 ms `ok`/`warn`/`danger` tint flash, no sliding. "Pause feed" toggle for reading. Filters: severity, module, actor.
   - **Protected surface map** (inline-end, 40 %): a matrix, not cards. Rows = protections (Antinuke, Bot Trap, Phishing, Automod, Verification, Permissions); columns = State, Trusted IDs count, Last trigger, Config link. Permission health appears here with missing permissions listed.
5. **Timeline** (below the fold): 24 h / 7 d event histogram (bars by severity) with incident markers; brush to filter the feed.
6. **Actor activity**: top actors by high-risk actions (24 h), each linking to a filtered feed.

### 17.2 Motion and glow budget on Security

Allowed: live pulse on the feed's "Live" indicator; D2 on unacknowledged critical items; G3 on the posture mark during Incident; tint flash for new rows; countdown ticking. Not allowed: radar sweeps, rotating globes, scrolling hex dumps, fake "scanning" bars, map of the world, anything animated without an underlying event.

### 17.3 Available in Phase 1.5

Only the Antinuke page (legacy config) and permission health (in Overview and topbar health popover). The Security Center route is not created in Phase 1.5.

---

## 18. Tickets V2 builder design language (Phase 4 target)

Locked direction: Canva / Discord-builder editing. Design the shell now so the rest of the system accommodates it.

### 18.1 Panel builder layout (≥1280)

```
┌ Topbar: Tickets / Panels / "Support panel"   Draft ●  [Preview: Desktop | Mobile]  [Publish to #support] ┐
├ Palette 240 ┬───────────────── Canvas (fluid) ──────────────────┬ Inspector 320 ┤
│ Layout      │  ┌ Discord preview frame ────────────────────────┐ │ Button        │
│  Container  │  │ (CLS Bot)  APP  Today at 14:02                │ │ Label  [Open…]│
│  Section    │  │ ┌ container ─────────────────────────────────┐│ │ Style  [Prim.]│
│  Separator  │  │ │ ## Need help?                              ││ │ Emoji  [📩  ] │
│ Content     │  │ │ Pick a category below.                     ││ │ Opens category│
│  Text       │  │ │ [Open ticket] [Report a user]  ← selected  ││ │  [Support ⌄]  │
│  Media      │  │ └────────────────────────────────────────────┘│ │ ⚠ 1 issue     │
│ Interactive │  └───────────────────────────────────────────────┘ │               │
│  Button     │   Outline ▸ (collapsible tree of components)       │               │
│  Select     │                                                    │               │
└─────────────┴────────────────────────────────────────────────────┴───────────────┘
```

- **Canvas = the live preview.** Editing happens directly on a faithful Discord message render. The Discord frame is the *only* place Discord's own palette is used (its dark theme), fenced by a 1 px `line` frame and a small "Discord preview" overline so it is never confused with CLS UI.
- **Palette** (240 px): grouped components (Layout, Content, Interactive) as 32 px rows with icon + name; drag or press Enter to insert after the current selection.
- **Inspector** (320 px): properties of the selected component; validation issues listed at the top with jump-to.
- **Outline**: collapsible tree under the canvas for precise selection and keyboard reordering.
- **Status**: Draft / Published / Out of sync (published message differs from draft) as a status label; Publish is the single primary action and names its target channel.

### 18.2 Form builder layout

Same three-column shell. Canvas shows the **Discord modal preview** (title, fields). Palette: Short text, Paragraph, (select, when Discord supports it in modals at build time; verify against current Discord docs in Phase 4). Inspector: label, placeholder, required, min/max length. Discord's modal component limits are enforced in the palette (disabled with a tooltip when the limit is reached).

### 18.3 Interaction states

| State | Visual |
|---|---|
| Hover component | 1 px dashed `line-strong` outline. |
| Selected | 1 px `brand-line` outline + G2 + name tag (11 px overline on `brand-600`, top inline-start). Inspector shows it. |
| Multi-select | Shift/Ctrl click; same outline, tag shows count. |
| Dragging | Ghost at 0.9 opacity, `elev-1`; origin slot shows `surface-3` placeholder. |
| Drop target | 2 px `brand-400` insertion line; container slot `brand-tint-strong`. |
| Invalid drop | Danger insertion line + tooltip naming the Discord limit ("A row holds up to 5 buttons"). |
| Invalid component | Danger outline + issue badge; inspector lists the issue. |

Keyboard: Tab into canvas, arrow keys move selection through the outline order, `Alt+↑/↓` reorders, `Enter` inserts the focused palette item after selection, `Delete` removes (undo toast, 6 s), `Ctrl/⌘ Z` / `Shift+Ctrl/⌘ Z` undo/redo, `Ctrl/⌘ D` duplicates. All drag operations have a keyboard equivalent (required for accessibility).

### 18.4 Preview modes

Desktop Discord (canvas width 520 px message column) and Mobile Discord (360 px). Toggle in the builder topbar (segmented control). Optional "Show as member" (hides staff-only controls).

### 18.5 Responsive behaviour

- 1024–1279: palette collapses to a 48 px icon strip with tooltips; inspector 288 px.
- 768–1023: canvas full width; inspector becomes a bottom sheet (50 vh) when a component is selected; palette via an "Add component" button popover.
- < 768: **no drag and drop**. The builder shows the preview plus the outline list; tapping a component opens a full-screen inspector sheet; reordering uses Move up/Move down actions. A notice says "Rearranging works best on a larger screen." Publishing is allowed.

---

## 19. Table / data grid system

One component family for Members, Tickets, Audit, Logs, Sessions, Invites, Grants.

| Part | Spec |
|---|---|
| Container | Panel recipe (§9.1), `radius-md`, no inner padding; toolbar and table share the container. |
| Toolbar (44 px) | Search input (`sm`, 240–320 px, `Search` icon, `/` focuses it), filter buttons, then flexible space, then column control (`Columns3` icon button), density toggle (only on Logs/Audit), export (where valid). |
| Filters | Each filter is a `sm` secondary button showing "Status: Open" when set; opens a popover with checkboxes or a date range. Active filters get a `line-strong` border and a clear (×) affordance. "Clear filters" tertiary button when any are set. |
| Header | 32 px, `surface-2`, `table-header` style. Sortable headers show `ArrowUpDown` on hover, `ArrowUp`/`ArrowDown` when active (icon at inline-end of label). Sticky within the scroll container. |
| Rows | Density per §6.4. Separator 1 px `line-subtle`. Hover `surface-3`. Selected `brand-tint` + inline-start 2 px `brand-500` bar. Focused row (keyboard): focus ring inset. |
| Cells | Text `body` `fg-1`; secondary line `small` `fg-3`. Numbers inline-end aligned + tabular. IDs `mono-data` with copy-on-hover button. Timestamps relative ("4 min ago") with absolute in a tooltip, `caption` style. User content `dir="auto"`. |
| Status cells | Status label (dot + text) by default; status chip only for severity and ticket state columns. |
| Row actions | Single `MoreHorizontal` icon button at inline-end, visible on hover/focus and always on touch. Menu items: icon + label; destructive items at the bottom, danger text, separated by a divider. |
| Selection & bulk | Checkbox column (40 px). When ≥1 row selected the toolbar swaps to a bulk bar: "3 selected", bulk actions, "Clear selection". Destructive bulk actions confirm (§22). |
| Pagination | Footer 40 px: "1–50 of 412" (`fg-3` tabular), page-size select (25/50/100), previous/next icon buttons (mirrored in RTL). Logs and feeds use cursor-based "Load older" instead of page numbers. |
| Column control | Popover with checkboxes to show/hide columns; required columns disabled. Persisted per table in `localStorage`. |
| Empty | In-table: 20 px icon + one sentence + optional action, centred in a 160 px tall row area. Distinguish "No results for these filters" (with Clear filters) from "Nothing here yet" (with the creating action or an explanation). |
| Loading | 8 skeleton rows at the current density; header stays real. |
| Error | Replaces rows: danger inline banner "Couldn't load members. {reason}" + Retry. Toolbar stays usable. |
| Mobile (< 768) | Rows become list items (44 px min): primary field + status on the first line, two secondary fields on the second. Tap opens a detail sheet. Bulk selection via long-press is not offered in Phase 1.5; filters move into a filter sheet. |
| Tablet (768–1023) | Columns have priority tiers (1 always, 2 ≥ 768, 3 ≥ 1280). First column sticky; horizontal scroll with an inline-end fade. |

Virtualization is required once a table can exceed 500 rendered rows (Logs, Audit). Phase 1.5 tables (grants, invite leaderboard) do not need it.

---

## 20. Form system

No control is wrapped in its own card. Settings are grouped into panels of **setting rows**.

### 20.1 Setting row

Label (`body` 500, `fg-1`) + description (`small`, `fg-3`, max 60ch) at inline-start; control at inline-end, vertically centred. Rows separated by `line-subtle`. Switch-only rows are 52 px; rows with a select or input stack on < 768 (control goes below the text).

### 20.2 Controls

| Control | Spec |
|---|---|
| Text input | `md` 32 px, `surface-well`, 1 px `line-input`, `radius-sm`, 10 px inline padding, `body` text, placeholder `fg-3`. Hover: `line-strong`→ lighter. Focus: border `brand-400` + ring. Leading icon optional (16 px, `fg-3`). |
| Textarea | Same recipe, min 3 rows, vertical resize only, character counter at inline-end below when a limit exists (Discord limits: 2000 message, 4096 embed description). |
| Select | Radix Select. Trigger like an input + `ChevronDown` at inline-end. Content = popover recipe, items 32 px, selected item shows `Check` and `fg-1` (no purple fill on the selected option). Full keyboard support. |
| Combobox (Discord channels/roles/users) | Replaces raw ID inputs. Search field + list: channels show type icon (`Hash`, `Volume2`, `Folder`) + name + category in `fg-3`; roles show a 8 px colour dot (the role's own colour) + name + position; users show avatar + name + ID. Multi-select renders selected values as removable tokens (`radius-xs`, `surface-3`). Paste of a raw ID resolves to the entity. |
| Checkbox | 14 px, `radius-xs`, `line-input` border; checked `brand-600` fill + white check. Indeterminate supported. Label click toggles. |
| Radio | 14 px circle; checked 6 px `brand-400` dot inside `brand-400` ring. Group uses `fieldset`/`legend`. |
| Switch | Track 28 × 16 px, thumb 12 px; off `surface-4` track + `fg-3` thumb; on `brand-600` track + white thumb. 120 ms. Always paired with a visible label. Uses existing `@radix-ui/react-switch`. |
| Slider | Only for bounded values with live visual feedback (none in Phase 1.5). Otherwise number input with steppers and unit suffix ("seconds"). |
| Number input | Input with unit suffix inside the field (`fg-3`), steppers as 24 px icon buttons at inline-end. |
| Date / time | Phase 1.5 has none. Later: text-entry + popover calendar, 24-hour times, locale-aware formatting, time zone always shown. |
| Search | Input with `Search` icon, `Esc` clears, results announced via `aria-live="polite"` count. |
| Colour (embeds) | Swatch 24 px + hex input (mono). |
| Discord message fields | Monospace-free `body`, with a small "Supports Discord markdown" help line and variable tokens (`{user}`) inserted from a menu, rendered as `radius-xs` tokens in preview. |

### 20.3 Validation and help

- Validate on blur and on submit; never on each keystroke for format errors (length counters update live).
- Error: border `danger`, help text replaced by error text (`small`, `danger`, leading `CircleAlert` 14 px), `aria-invalid`, `aria-describedby`. Error text says what is wrong and how to fix it ("Pick a text channel. Voice channels can't receive welcome messages.").
- Server errors after save: toast + the save bar stays open with "Couldn't save. {reason}" and Retry.

### 20.4 Danger settings

Placed last on the page in a **Danger zone** panel: `surface-1` with a 1 px `danger` line at 32 %, overline "Danger zone" in `danger`. Each row: label + consequence sentence + `danger-secondary` button. Confirmation per §22.3. Never mixed with ordinary settings.

---

## 21. Button system

Five variants plus icon buttons. Nothing else.

| Variant | Rest | Hover | Active | Use |
|---|---|---|---|---|
| **Primary** | `brand-600` fill, white text | `brand-500` + G1 | `brand-700`, scale 0.98 | The single main action of a region. |
| **Secondary** | `surface-3` fill, 1 px `line-strong`, `fg-1` | `surface-4` | `surface-4`, scale 0.98 | Other actions. |
| **Ghost** | transparent, `fg-2` | `surface-3`, `fg-1` | `surface-4` | Toolbars, low-emphasis actions, Discard. |
| **Tertiary (text)** | transparent, `brand-400`, no padding change | underline | `brand-300` | Inline actions inside text ("Clear filters", "Copy ID"). |
| **Danger** | `danger-fill`, white | `danger-fill-hover` | `danger-fill-active` | Only inside confirmation dialogs. |
| **Danger secondary** | transparent, 1 px danger line 32 %, `danger` text | danger tint background | tint 20 % | Destructive entry points on pages (Revoke, Delete, Reset). |
| **Icon button** | Ghost recipe, square (28/32/40), 16 px icon | as ghost | as ghost | Must have `aria-label` + tooltip. |

Common: `radius-sm`, `button` type style, 6 px icon gap, heights `sm 28`, `md 32`, `lg 40`, inline padding 10/12/16 px. Focus: focus ring. Disabled: `surface-2` fill, `fg-4` text, no border change, `cursor: not-allowed`, no hover; disabled buttons that block a task must have a visible reason nearby (not only a tooltip). Loading: `aria-busy="true"`, width locked, leading icon replaced by the hex loader, label kept (e.g. "Saving…"), click ignored. Sentence-case labels naming the result: "Save changes", "Grant access", "Revoke access". No `→` appended to labels, no uppercase labels.

---

## 22. Modals, drawers, popovers, dropdowns, full pages

### 22.1 Choosing the container

| Container | Use when | Examples |
|---|---|---|
| **Inline** (default) | The action fits in the page flow. Exhaust this first. | Editing a setting, adding a whitelist entry, inline row edit. |
| **Popover** | Small, non-destructive choice anchored to a control; no scrolling content. | Filters, column control, guild switcher, health summary, date range. |
| **Dropdown menu** | A list of actions on one object. | Row actions, user menu, "More" overflow. |
| **Drawer** (inline-end, 480 px; 640 px wide variant) | Inspect or edit one record while keeping the list visible. | Incident details, ticket details, grant details, log event JSON. |
| **Modal** (480 px; 640 px wide) | Blocking decision or short focused task that must complete or cancel. | Confirmations, create grant, create category. Max one modal at a time; never a modal on a modal. |
| **Full page** | Multi-step or large work surfaces; anything with its own navigation. | Tickets builder, restore wizard, transcript viewer. |

All overlays: rendered in a portal (never clipped by `overflow`), focus moves in and is trapped, `Esc` closes (except typed-confirmation in progress, where `Esc` still closes but never confirms), focus returns to the trigger, `aria-modal` for modal/drawer, `role="dialog"` with a labelled title.

### 22.2 Modal anatomy

Header (title `section-heading` + optional description + close icon button), body (16 px padding, scrolls), footer (actions at inline-end: Cancel ghost, primary/danger last). Mobile: modals become bottom sheets (full width, `radius-lg` top corners, drag handle, max 90 vh); drawers become full-screen sheets.

### 22.3 Dangerous action confirmation tiers

Aligned with the command risk model (spec §45).

| Tier | Pattern |
|---|---|
| **Low** (reversible, e.g. remove a reaction-role row) | No dialog. Perform, then toast with Undo (6 s). |
| **Medium** (revoke a grant, delete a category) | Confirmation modal: title names the action and object ("Revoke access for aero?"), body states the consequence in one sentence, danger button repeats the verb ("Revoke access"). Cancel is focused by default. |
| **High** (bulk revoke, reset a module, disable antinuke) | As Medium, plus an explicit checkbox acknowledging the consequence, plus a 2 s arming delay on the danger button (shows a filling underline). Audit notice: "This will be recorded in the audit log." |
| **Critical** (Incident Mode actions, restore, root operations; later phases) | Full modal with typed confirmation (type the guild name or the action keyword), recent-auth check if required by the backend, danger button disabled until the text matches exactly, notice "This action is mirrored to CLS Ops." |

---

## 23. Status system

Colour + glyph + text, always. Pills are not the default.

| Status | Colour | Glyph (Lucide) | Dot shape | Motion | Label |
|---|---|---|---|---|---|
| Healthy | `ok` | `CircleCheck` | solid | none | "Healthy" |
| Online | `ok` | — (dot) | solid | live pulse only on the global bot indicator and live feeds | "Online" |
| Offline | `neutral` | `CircleOff` | hollow ring | none | "Offline" |
| Warning | `warn` | `TriangleAlert` | solid | none | "Warning" |
| Degraded | `warn` | `CircleAlert` | half-filled | none | "Degraded" |
| Critical | `danger` | `OctagonAlert` | solid | 1.2 s pulse + D2 until acknowledged, then static | "Critical" |
| Pending | `info` | `CircleDashed` | dashed ring | slow rotation (1.6 s) of the dashed ring; static under reduced motion | "Pending" |
| Disabled | `fg-4` | `CircleMinus` | hollow ring | none | "Disabled" |
| Unknown | `neutral` | `CircleHelp` | dashed ring | none | "Unknown" |

Rendering forms:

1. **Status label** (default everywhere): 6 px dot + 6 px gap + `small` text in `fg-2`. No background.
2. **Status chip** (tables with severity/state columns, incident rail): 20 px high, `radius-xs`, semantic tint background, semantic line border, 11 px 500 semantic-colour text, optional 12 px glyph. Never purple.
3. **Status glyph** (dense matrices, rail mode): glyph only with `aria-label` and tooltip.

Legacy/Beta/Root markers are **not statuses**: "Legacy" is a neutral outline tag (`line-strong`, `fg-2`, `radius-xs`), shown only in page headers. "Root" is shown as text in the user menu, not as a badge on nav items.

---

## 24. Chart system

No chart is needed in Phase 1.5 (no time-series data exists). This section fixes the language for later phases.

| Element | Spec |
|---|---|
| Canvas | Inside a panel; chart area padding 12 px; height 160 px (compact) / 240 px (default). |
| Grid | Horizontal lines only, 1 px `line-subtle`; 3–5 lines. No vertical grid. No chart borders. |
| Axes | Labels `caption` in Plex Mono `fg-3`, tabular. Y axis at inline-start; X axis time labels at most every 4th tick. No axis lines except the baseline (`line`). |
| Line | 1.5 px, `chart-1` (or semantic colour for semantic series), `stroke-linejoin: round`. |
| Area | Line + fill gradient from series colour at 24 % to 0 %. Only one area per chart. |
| Bar | Rounded top 2 px (`radius-xs`), 60 % band width, 2 px gap in stacked bars; severity histograms use `sev-*`. |
| Timeline | Horizontal track, events as 8 px markers coloured by severity, clusters collapse into a count bubble; brush selection `brand-tint`. |
| Sparkline | 24–32 px tall, 1.25 px line, no axes; last point 4 px dot; if the series is live, the last point gets G2 (Stakent DNA, used sparingly). |
| Markers | Hover crosshair 1 px `fg-4` vertical; point 6 px with 2 px `surface-1` ring. |
| Tooltip | Popover recipe, `small` text, value tabular in `fg-1`, series swatch 8 px square, timestamp absolute. Follows pointer, flips at edges. Keyboard: arrow keys move between points when the chart is focused. |
| Legend | Above the chart at inline-start, `small`, swatch + name; click toggles series. |
| Empty | "No events in this range." centred, grid still drawn. |
| Animation | §10.2. |
| Accessibility | Every chart has a text summary (`aria-describedby`) and a "View as table" toggle. |

Library decision is deferred to the first phase that needs charts (Phase 5). Sparklines and simple bars should be hand-rolled SVG; a chart library is justified only for interactive time-series with brushing.

---

## 25. Loading, empty and error states

Each state has its own visual so users can tell them apart at a glance.

| State | Where | Visual | Copy pattern |
|---|---|---|---|
| **Loading (content)** | Any panel/table | Skeleton blocks matching the final layout (`surface-3`, shimmer). Headers/labels render immediately. | — |
| **Loading (action)** | Buttons, save bar | Hex loader in the button. | "Saving…" |
| **Loading (route)** | `loading.tsx` | Page header skeleton + content skeleton. No full-screen spinner, no "Initializing System / edge cortex" text. | — |
| **Empty (no data yet)** | Inside a panel/table | 20 px `fg-3` icon + one sentence + optional primary/secondary action. No illustration. | "No reaction roles yet. Add one to let members pick roles with a reaction." |
| **Empty (filtered)** | Tables | Same size, `SearchX` icon + "No results for these filters." + Clear filters. | — |
| **Not configured** | A module page whose core setting is unset | Panel with the lattice texture at 3 %, 24 px module icon, title "Set up {Module}", one sentence on what it does, primary "Set up" that scrolls/opens the first required setting. | "Logging sends server events to channels you choose. Pick a channel to start." |
| **No permission** | Page or panel | `Lock` 24 px `fg-3`, title "You can't view this", body naming the missing capability and who grants it. No danger colour. | "This page needs the logging.view capability. The CLS root owner can grant it." |
| **Error (recoverable)** | In place of the failed region | Danger inline banner: `OctagonAlert`, specific message, "Try again" button, reference id (`digest`) in `caption`. The rest of the page keeps working. | "Couldn't load automod settings. The bot API timed out. Try again." |
| **Error (route boundary)** | `error.tsx` | Page-level version of the above inside the shell (sidebar/topbar stay). No "neural link" copy. | "This page failed to load." + reason + "Try again" / "Go to Overview" |
| **Offline / degraded** | Global | Topbar status turns warn/danger; a 36 px banner under the topbar: "Bot API unreachable. Showing data loaded at 14:02. Changes can't be saved." Save bars disable with that reason. | — |
| **Disabled module** | Module page | Page renders normally with a notice row at the top: "{Module} is turned off. Settings are kept." + the enable switch (if permitted). No grayscale filters on content. | — |
| **Legacy surface** | Legacy pages | Neutral notice row in the header: "Legacy settings. This module is being rebuilt in a later phase." | — |

---

## 26. RTL foundation

Arabic UI is not shipped in Phase 1.5, but every component must render correctly with `dir="rtl"`.

| Area | Rule |
|---|---|
| Document | `<html lang dir>` driven by a locale setting (default `en`/`ltr`). Radix `DirectionProvider` wraps the app with the same value. A development-only override (cookie `cls_dir=rtl`) enables RTL screenshot QA. |
| CSS properties | Logical only: `margin-inline-*`, `padding-inline-*`, `inset-inline-*`, `border-inline-*`, `text-align: start/end`, `border-start-*-radius`. Tailwind: `ms-/me-/ps-/pe-/start-/end-/text-start/text-end/border-s/border-e/rounded-s/rounded-e`. **Banned** in CLS OS components: `ml-/mr-/pl-/pr-/left-/right-/text-left/text-right/border-l/border-r/rounded-l/rounded-r`, and `space-x-*` (use `gap-*`). Enforced by a grep check in acceptance. |
| Icon mirroring | Mirror (`rtl:-scale-x-100` via a `.cls-mirror` utility): chevrons and arrows used for direction/navigation, Back, pagination prev/next, sidebar collapse (`PanelLeft*`), undo/redo, "external link" arrow, reply. Do not mirror: check, search, clock, play/media, charts/trend icons, logos, Discord glyph, the CLS mark, the Perimeter, text-bearing icons. |
| Sidebar | At inline-start (right in RTL). Drawer slides from inline-start. Active bar on the inline-start edge. Tooltips in rail mode open to inline-end. |
| Breadcrumbs | `/` separator (direction-neutral). Order follows reading direction automatically. |
| Tables | Column order follows direction (first column at inline-start). Numeric columns align to inline-end in both directions. Sticky first column uses `inset-inline-start`. Row actions at inline-end. |
| Forms | Labels and help at inline-start; setting-row controls at inline-end. Switch thumb moves toward inline-end when on (Radix handles with `dir`). Input text aligns start; IDs, URLs, emails and numbers inside inputs use `dir="ltr"` and `text-align: start`. |
| Numbers and IDs | Western digits (0–9) in both locales (REVISIT with Arabic content review). Discord IDs, hex, URLs, commands, code: wrapped in `<bdi dir="ltr">` + mono. Percentages and units via `Intl.NumberFormat(locale)`. Dates via `Intl.DateTimeFormat(locale)` with explicit 24-hour time. |
| Mixed text | All user-generated or Discord-sourced strings (guild names, channel names, notes, message content, usernames) render with `dir="auto"` so Arabic notes inside English tables display correctly (seen in the CLS license admin reference). |
| Charts | Time axis origin at inline-start (time flows right-to-left in RTL); Y axis at inline-start. REVISIT with Arabic users. |
| Motion | Direction-dependent motion (drawer slide, dropdown offset, active bar slide) uses logical direction tokens. |
| Typography | §5.4. |
| Text expansion | Components tolerate +30 % label length; no fixed-width buttons; nav labels truncate with tooltip. |

---

## 27. Responsive foundation

Desktop first. Mobile is usable administration, not the full command center.

| Range | Sidebar | Grid | Tables | Builders | Topbar | Modals / drawers | Charts |
|---|---|---|---|---|---|---|---|
| **Large desktop ≥1920** | Expanded 248 | 12 col, 16 gap, 32 gutter; Overview adds a 360 px inline-end rail; Security feed 60/40 | All columns | Full 3-panel (palette 260, inspector 340) | Full breadcrumbs + health + user | Modal 480/640; drawer 640 | Default 240 px |
| **Desktop 1280–1919** | Expanded by default | 12 col, 12 gap, 24 gutter; settings 760 + 320 rail (≥1440) | All columns | 3-panel (240 / 320) | Full | Modal 480/640; drawer 480 | 240 px |
| **Laptop 1024–1279** | Rail 56 by default; expand overlays (no content reflow) | 8 effective columns; settings single column 760 | Priority tiers 1–2 visible, rest via column control | Palette icon strip 48, inspector 288 | Breadcrumbs truncate middle | Same | 200 px |
| **Tablet 768–1023** | Drawer | 1–2 columns | Tiers 1–2; sticky first column; horizontal scroll | Canvas + inspector bottom sheet; palette popover; drag supported | Menu button + last 2 crumbs + health dot | Modal 480; drawer 100 % width at < 900 | Full width, 200 px |
| **Mobile < 768** | Drawer (min(320, 85vw)) | Single column, 16 gutter | List rows + detail sheet | Preview + outline; no drag; full-screen inspector | Menu, last crumb, health dot, avatar | Bottom sheets; drawers full-screen | Full width, 160 px, simplified ticks |

Save bars stay at the bottom (thumb zone) on mobile. Touch targets ≥ 44 px under `pointer: coarse`. Hover-only affordances (row actions) are always visible on touch.

---

## 28. Accessibility

| Area | Requirement |
|---|---|
| Contrast | Text ≥ 4.5:1 (all `fg-1..3` tokens pass on their allowed surfaces; see §4.4). Large text/icons and focus indicators ≥ 3:1. `fg-4` for disabled only. Brand text uses `brand-400`/`brand-300`, never `brand-600`. Input borders (`line-input` ≈ 2:1) rely on the well fill + visible label for identification (REVISIT). |
| Focus | `:focus-visible` ring on every interactive element (§9.3). Focus never lost on route change: focus moves to the page title (`tabIndex=-1`). Skip link "Skip to content" as the first focusable element. |
| Keyboard | Everything reachable by Tab; menus/selects/tabs use arrow keys (Radix); `Esc` closes overlays; tables support row focus with arrow keys where rows are actionable; `Ctrl/⌘ S` saves; builder has full keyboard equivalents (§18.3). |
| Semantics | Landmarks: `header`, `nav[aria-label="Primary"]`, `main`. One `h1` per page (page title). Tables are real `<table>` with `<th scope>`. Setting groups use `fieldset`/`legend` where they are forms. |
| Screen-reader labels | Icon buttons `aria-label`; rail nav items `aria-label`; status glyphs `aria-label` (e.g. "Critical"); loaders `role="status"` with text; toasts `aria-live="polite"` (critical security events `assertive`); save bar announces "Unsaved changes" once. |
| Colour redundancy | Status = colour + glyph/shape + text (§23). Charts include patterns/labels and a table view. Validation errors include text and icon. |
| Motion | §10.3. No content flashes more than 3 times per second. Auto-updating feeds can be paused. |
| Drag and drop | Every drag has a keyboard and a menu alternative (Move up/down, Move to…). Drop results announced ("Button moved to position 2"). |
| Zoom | Usable at 200 % zoom (layout collapses to the tablet/mobile patterns). No horizontal page scroll at 320 CSS px except inside tables. |
| Language | `lang` attribute per locale; user content in other languages gets `dir="auto"` (and `lang` when known). |

---

## 29. Implementation primitives and dependencies

### 29.1 Current stack (audited)

Next.js 14.2.3 (App Router), React 18, TypeScript 5.9, Tailwind 3.4 (no plugins), `lucide-react` 0.378, `class-variance-authority`, `clsx`, `tailwind-merge`, `sonner` 2, `@radix-ui/react-slot`, `@radix-ui/react-switch`, `next-auth` 4, `jsonwebtoken`.

Finding: 30 files use `animate-in fade-in slide-in-*` classes, but `tailwindcss-animate` is not installed, so none of those animations run. They are dead classes.

### 29.2 Keep

All of the above. `lucide-react` is the icon library. `sonner` remains the toast system (restyled). `cva` + `cn()` remain the component variant pattern.

### 29.3 Proposed additions for Phase 1.5 (Task A only)

| Package | Purpose | Why the existing stack is insufficient | Cost / risk |
|---|---|---|---|
| `@radix-ui/react-dropdown-menu` | Row actions, user menu, overflow menus | Current menus are hand-rolled `div`s with click-outside handlers: no roles, no arrow keys, no focus return, clipped by overflow. | Small, same vendor as existing Radix packages, headless (no styles to fight). Low risk. |
| `@radix-ui/react-popover` | Guild switcher, health popover, filters | Same as above. | Low. |
| `@radix-ui/react-dialog` | Modals, drawers, confirmation tiers, mobile nav drawer | Focus trap, scroll lock, `aria-modal`, `Esc` handling are easy to get wrong by hand. | Low. |
| `@radix-ui/react-tooltip` | Rail nav labels, icon buttons | Needs delay groups and keyboard/focus triggers. | Low. |
| `@radix-ui/react-select` | Select control | Current `components/ui/select.tsx` has no keyboard support or ARIA roles. | Low. |
| `@radix-ui/react-direction` | RTL `DirectionProvider` for all Radix primitives | Radix components need the direction context to mirror keyboard behaviour. | Tiny. |

Pin exact versions compatible with React 18 at install time and commit the lockfile.

### 29.4 Explicitly not added in Phase 1.5

| Need | Decision | Reason |
|---|---|---|
| Motion library (framer-motion / motion) | **Not added.** | Every dashboard motion in §10 is CSS transitions/keyframes. The landing Perimeter is SVG + CSS + a small `requestAnimationFrame` parallax hook. Revisit only if the landing prototype cannot hit the choreography with CSS. |
| `tailwindcss-animate` | **Not added.** | CLS OS defines its own small keyframe set (fade, scale-in, slide-inline, shimmer, pulse-ring, hex-step) in `tailwind.config.ts`. Dead `animate-in` classes are removed. |
| Chart library | **Not added.** | No time-series data in Phase 1.5. |
| Drag and drop (`@dnd-kit`) | **Deferred to Phase 4** (Tickets builder). | Chosen then for keyboard sensors and accessibility announcements. |
| Command palette (`cmdk`) | **Deferred.** | Needs a real command/search index first; the fake search box is removed rather than replaced. |
| Table engine (TanStack Table) | **Deferred to Phase 5** (Logs/Audit). | Phase 1.5 tables are small; the CLS Table primitive handles sort/select client-side. |
| Component kit (shadcn CLI, MUI, etc.) | **Not added.** | Primitives are built in-repo on Radix + tokens so they look like CLS, not like a kit. |

### 29.5 Primitive inventory Task A must build

`Button`, `IconButton`, `Input`, `Textarea`, `Select`, `Combobox` (channel/role/user), `Checkbox`, `Radio`, `Switch`, `SettingRow`, `SettingGroup` (panel), `Panel` (+ header strip), `PageHeader`, `Tabs` (link tabs), `StatusLabel`, `StatusChip`, `Tag`, `KpiStrip`, `Table` family (+ toolbar, pagination, empty, skeleton), `Skeleton`, `HexLoader`, `EmptyState`, `NoticeRow`, `InlineBanner`, `SaveBar`, `Dialog` (+ `ConfirmDialog` tiers), `Drawer`, `Popover`, `DropdownMenu`, `Tooltip`, `Toast` (sonner theme), `Kbd`, `Avatar`, `GuildIcon`, `CopyId`, shell (`AppShell`, `Sidebar`, `Topbar`, `Breadcrumbs`, `GuildSwitcher`, `HealthIndicator`, `UserMenu`), brand (`ClsMark`, `Wordmark`, `PerimeterMark`, `LatticeBackground`).

---

## 30. Copy and voice

- Product name: always "CLS OS". Never "ZyroX", "Zyrox", "CLS Dashboard", "CLS System", "Engine", "Console" as a product name.
- Sentence case everywhere, including buttons and headings. Uppercase only through the four `overline`/`table-header` roles.
- Plain verbs; a button says what happens ("Save changes", "Revoke access", "Publish panel"); the toast repeats the verb ("Changes saved", "Access revoked").
- No invented tech vocabulary: banned words include neural, cortex, matrix, uplink, shard (unless referring to real Discord shards), edge network, cluster (unless real), cinematic, hyper, quantum, AI (unless the AI module itself).
- No unverifiable numbers or claims (uptime, latency promises, community counts, encryption claims that are not implemented).
- Errors say what happened and what to do, without apology. Empty states invite the next action.
- Discord terminology follows Discord's own names ("Server", "Channel", "Role", "Member"); "Guild" appears only in IDs and developer contexts.

---

## 31. Self-critique and revisions

Using `cls-os-ui-review` (severity lens, CLS rules) and Impeccable (`critique` heuristics, cognitive-load checklist, product slop test, `operate` constraints) against this specification before finalising.

| Question | Finding | Revision made |
|---|---|---|
| Does this feel like CLS or a template? | The first draft used the CLS website's `#A855F7` as primary; that is Tailwind's stock purple and made the system read as "any purple dashboard". | Palette rebuilt on the logo's own hue (259°); primary fill is the literal logo colour. Geometry (Perimeter, loader, lattice) derived from the mark's 30° strokes, so identity comes from CLS itself. |
| Is purple overused? | The CLS license admin reference uses purple for statuses and plan tags. Carrying that over would repeat a semantic misuse. | Added the purple budget (§4.3): no purple statuses, chips, headings or resting icons. Selected option in selects is `fg-1` + check, not a purple fill. |
| Is glow overused? | Draft allowed glow on KPI tiles and hover of cards (Stakent-style). | Glow restricted to G1–G3 + D2 with named components; KPIs, cards and rows are G0. Only one G3 per viewport. |
| Is density actually compact? | Draft table default was 40 px rows and 14 px body. | Body 13 px; rows 32/36/44; topbar 48; sidebar items 32; 24 px gutters; `space-12/16` banned in the dashboard. Settings are capped at 760 px so wide screens gain a context rail instead of stretched forms. |
| Are we creating generic dashboard cards? | Overview draft was a row of four KPI tiles plus module cards. | Overview rebuilt as system line → needs-attention list → modules table (§16). Tiles are limited to the server facts strip. Module lists are tables. |
| Is motion purposeful? | Draft had staggered page entrances in the dashboard. | Removed: product loads into the task (Impeccable `operate`). Page entrance is a 120 ms fade; the only orchestrated sequence is the landing. Pulses limited to live and critical-unacknowledged. |
| Is the command-center concept functional or decorative? | The Perimeter risked being decoration. | Its segments are the six real domains with honest availability; it drives the real sign-in state change; it reappears as the Security posture glyph bound to real incident state. Radar/scanning/world-map visuals explicitly banned. |
| Is the landing too long? | Draft had a third section (FAQ + security explainer). | Cut to gateway + one compact domain list + footer (≈1.8 viewports). |
| Is the dashboard too visually noisy? | Mono uppercase labels (CLS DNA) everywhere would flatten hierarchy and read as template chrome (`frontend-design` tells). | Mono uppercase limited to four roles. Chakra Petch removed from dashboard UI entirely (display fonts in product UI are "strangeness without purpose"). No icon tiles. |
| Does the system scale to Tickets / Security / Logs? | Needed explicit density modes and a builder shell before those phases. | Compact 32 px rows for logs/audit, virtualization rule, drawer-first inspection, builder shell with keyboard equivalents, Security band order, severity scale separate from status. |
| Is RTL truly accounted for? | Draft only said "use logical properties". | Added the banned-class list with a grep gate, icon mirroring list, `dir="auto"` for user content (the reference shows Arabic notes in tables), `<bdi>` for IDs, Arabic typography rules (no uppercase/tracking, +2 px leading, 12 px minimum), Radix `DirectionProvider`, a dev RTL override for screenshot QA. |
| Are mobile compromises realistic? | Draft promised drag and drop on mobile. | Mobile builder is preview + outline + move actions; tables become list rows; bulk selection not offered on mobile in Phase 1.5; save bar in thumb zone. |
| Accessibility vs premium look | Logo purple fails as text; input borders are low contrast. | `brand-400` for all readable purple; `fg-3` tuned to pass on surface-2; input border compromise recorded as REVISIT rather than hidden. |

Residual risks (tracked in §32 as REVISIT): Chakra Petch's personality on the real gateway; the exact input border contrast; J2C and Verification placement; RTL chart direction.

---

## 32. Design decision register

| # | Decision | Status |
|---|---|---|
| D1 | Dark only; no light theme | **LOCKED** |
| D2 | Brand hue = logo hue 259°; primary fill `#6025E2` (logo); readable purple `#9474FF`; website `#A855F7` not used | **LOCKED** |
| D3 | Surface ladder values (§4.1) and chrome darker than canvas | **REVISIT AFTER VISUAL PROTOTYPE** (fine-tune ±1–2 steps of lightness only) |
| D4 | Semantic colours independent of brand; purple budget (§4.3) | **LOCKED** |
| D5 | Severity scale (critical/high/medium/low) separate from status | **LOCKED** |
| D6 | IBM Plex Sans + Plex Sans Arabic + Plex Mono for all UI | **LOCKED** |
| D7 | Chakra Petch as landing/auth display face | **REVISIT AFTER VISUAL PROTOTYPE** (fallback candidate: Plex Sans 600 condensed tracking) |
| D8 | No display font in dashboard UI (incl. page titles) | **LOCKED** |
| D9 | Mono uppercase restricted to four roles | **LOCKED** |
| D10 | Dashboard body 13 px; fixed rem scale | **LOCKED** |
| D11 | Topbar 48, sidebar 248/56, row heights 32/36/44, controls 28/32/40 | **LOCKED** |
| D12 | Settings column max 760 + 320 context rail | **REVISIT AFTER VISUAL PROTOTYPE** |
| D13 | Spacing scale (§7) with 48/64 banned in dashboard | **LOCKED** |
| D14 | Radius 2/4/6/10/full; no pills | **LOCKED** |
| D15 | Glow levels G0–G3 + D2 with named allowances | **LOCKED** |
| D16 | Motion tokens and reduced-motion behaviour | **LOCKED** |
| D17 | Lucide as the only icon library; stroke 1.75/1.5 | **LOCKED** |
| D18 | Logo used as supplied; vector trace requires owner approval | **LOCKED** (owner action: approve trace) |
| D19 | Landing = gateway + domain list + footer, ≈1.8 viewports, single Discord CTA | **LOCKED** |
| D20 | Hero concept B, CLS Perimeter | **LOCKED** |
| D21 | Perimeter choreography timings (§13.4) | **REVISIT AFTER VISUAL PROTOTYPE** |
| D22 | Owner tagline "Power. Control. Victory." not used in dashboard; landing use optional | **REVISIT AFTER VISUAL PROTOTYPE** (owner preference) |
| D23 | Auth flow with `/auth/continue`, `/auth/error`, server redirect for signed-in users, no auto Discord redirect from the dashboard | **LOCKED** |
| D24 | Sidebar IA per §15.2; future items hidden, no "Coming soon" | **LOCKED** |
| D25 | Join to Create placed under Engagement | **REVISIT AFTER VISUAL PROTOTYPE** (owner) |
| D26 | Verification and Leveling hidden from nav in Phase 1.5 | **REVISIT AFTER VISUAL PROTOTYPE** (owner confirmation) |
| D27 | Horizontal guild tab bar and large guild header card removed | **LOCKED** |
| D28 | Topbar search and notification bell removed until real features exist | **LOCKED** |
| D29 | Overview = system line + needs attention + modules table; no fake widgets | **LOCKED** |
| D30 | Security Center band order and motion budget (§17) | **LOCKED** |
| D31 | Tickets builder: canvas = live Discord preview; 240/fluid/320 layout; no mobile DnD | **LOCKED** |
| D32 | Table system (§19) and density modes | **LOCKED** |
| D33 | Setting-row form pattern, sticky save bar, danger zone | **LOCKED** |
| D34 | Button variants (§21) | **LOCKED** |
| D35 | Confirmation tiers (§22.3) | **LOCKED** |
| D36 | Status system (§23); status label default, chips only for severity/state | **LOCKED** |
| D37 | Chart language (§24); library chosen in Phase 5 | **LOCKED** (library: deferred) |
| D38 | Logical properties only; banned physical classes; `dir="auto"` for user content | **LOCKED** |
| D39 | Western digits in Arabic UI | **REVISIT AFTER VISUAL PROTOTYPE** (with Arabic reviewers) |
| D40 | RTL chart time axis flows right-to-left | **REVISIT AFTER VISUAL PROTOTYPE** |
| D41 | Input border `#433D58` (≈2:1) with well fill | **REVISIT AFTER VISUAL PROTOTYPE** |
| D42 | Radix primitives added (dropdown, popover, dialog, tooltip, select, direction); no motion/chart/DnD/cmdk libraries in 1.5 | **LOCKED** |
| D43 | `noindex` on all routes except `/`, `/privacy`, `/terms` | **REVISIT AFTER VISUAL PROTOTYPE** (owner: should the gateway be indexed at all?) |
| D44 | Product name constant "CLS OS" in code; `NEXT_PUBLIC_BRAND_NAME` removed | **LOCKED** |
