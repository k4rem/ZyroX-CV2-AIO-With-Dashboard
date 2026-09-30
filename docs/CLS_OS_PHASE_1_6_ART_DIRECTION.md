# CLS OS Phase 1.6 — Premium Dashboard Art Direction

Status: **Direction for approval.** No UI source is changed by this document.
Baseline: `a4ff916` (Phase 1.5 closed). Companion docs: `CLS_OS_PHASE_1_6_REFERENCE_PAGES.md`, `CLS_OS_PHASE_1_6_IMPLEMENTATION_PLAN.md`.
Authority: `docs/CLS_OS_DESIGN_SYSTEM.md` (DS) stays the token and component authority. This document **amends** it where noted (§11 amendment register). Where it is silent, the DS wins.

Evidence used: live authenticated captures of baseline `a4ff916` (Overview, Custom Roles, Tickets, Welcome, Join to Create at 390 / 1440 / 2560), the Phase 1.5 final audit captures, and the module source. The owner's screenshots did not arrive with the brief; the captures were taken from the running dashboard instead.

---

## 1. Diagnosis: why the current dashboard reads as generic

Phase 1.5 fixed identity, truth and structure. It did not produce a *look*. Five root causes, in order of impact:

1. **One composition for every job.** Every module page is `Title → description → box of fields → Save`. A Discord message editor, a voice-channel flow, a role roster and a health summary all get the same rectangle. Consistency was achieved by sameness, not by a system.
2. **Two surface worlds.** Rebuilt pages use CLS near-black tokens; six migrated-in-place pages (Custom Roles, J2C, Reaction roles, Auto roles, Vanity/Voice roles, Verification) still render the ZyroX skin: `bg-[#141B2D]` (22 uses), Tailwind stock `slate-900 #0F172A` (97 uses) and `slate-800 #1E293B` (175 uses). Those are **blue-hued** (#0F172A is hue 222°, clearly navy) and are the "navy panels" the owner rejects. `rounded-3xl` (30), `rounded-2xl` (33), `font-black` (49) complete the old look.
3. **Purple is spent on the Save button.** On Custom Roles and J2C the single most saturated element is a 56 px full-width `Save Configuration` bar. Purple therefore means "form submit", not "CLS". Meanwhile rebuilt pages have almost no purple at all, so they read as neutral grey software.
4. **No visual encoding of anything.** The Overview is honest but is 100 % text: a status line that looks like a breadcrumb, a table of "Off / —" rows, three numbers in a box. Ratios that are genuinely discrete (6/6 required modules, 2 of 3 J2C channels set, 5 of 9 log categories routed) are printed as words, never drawn.
5. **Empty canvas at scale.** At 2560 the Overview is a 1680 px island with dead gutters; Welcome at 1440 uses ~30 % of the viewport and leaves the rest black. Density is low not because elements are big but because the page has nothing to say visually.

What is *not* wrong and must be kept: the token ladder (it is already near-black), IBM Plex, the shell/IA, status grammar (glyph + text), truth rules, RTL foundation, snowflake-safe IDs.

---

## 2. Direction: "Graphite Instrument"

**One sentence:** CLS OS looks like a precision instrument machined from graphite: black bodies, engraved hairlines, readouts instead of cards, and a single violet signal line that marks what is live, selected or yours.

| Axis | Direction |
|---|---|
| Material | Graphite, not glass. Layered near-black planes; depth from **tone steps and engraved lines**, not fills, shadows or blur. |
| Geometry | Orthogonal grid + **one** signature angle: the **30° cut** taken from the CLS mark. Used sparingly and always functionally. |
| Colour | Black / graphite / violet. Semantic colours only for state. Blue exists only as `info` and in the Discord preview. |
| Brand energy | Purple as **signal**: a thin line, a tick, a selection rail, a live dot. Never a large fill except the one primary action. |
| Information | Readouts, meters, matrices and flows. Numbers are drawn when the denominator is real. |
| Motion | Mechanical and short: things *arm*, *settle*, *slide into place*. No ambient animation outside live data. |
| Composition | Purpose-built per archetype (§7). Same parts, different assemblies. |

Reference character (not copied): Linear's restraint, Teenage Engineering / avionics readouts for the instrument vocabulary, SOC consoles for the security surfaces, Discord's own client for anything Discord-shaped.

**It must not become:** a black shadcn dashboard with purple buttons; a neon cyberpunk HUD; hexagon wallpaper; glass cards; a poster of diagrams.

---

## 3. Colour and surfaces (revised)

### 3.1 Tokens retired from all surfaced routes

| Legacy token / class | Why | Replacement |
|---|---|---|
| `bg-[#141B2D]`, `#0f172a`, any hex literal in components | Navy (hue ≈ 222°) | `bg-surface-1` or no fill (see §3.3) |
| `bg-slate-900`, `bg-slate-900/40`, `bg-slate-950` | Navy | `bg-canvas`, `bg-surface-1`, `bg-stage` |
| `border-slate-800`, `border-slate-700` | Blue-grey line | `border-line`, `border-line-subtle`, `border-line-strong` |
| `text-slate-300/400/500`, `text-gray-*`, `text-white` | Blue-grey text, off-scale | `text-fg-1/2/3` |
| `bg-{blue,pink,yellow,green,red,purple}-500/20` icon tiles | ZyroX icon tiles, fake semantics | No tile. Icon inherits text colour (DS §11). |
| `bg-gradient-to-br from-primary/10`, `from-blue-500/10` side cards + watermark icons | Decoration | Context rail text (§7) or nothing |
| `rounded-3xl`, `rounded-2xl`, `rounded-[40px]` | Off-scale | `rounded-md` (panels), `rounded-sm` (controls) |
| `shadow-xl` on panels | Panels do not cast shadows (DS §9.1) | none |
| `font-black`, `uppercase tracking-wider` on content | ZyroX voice | DS type scale |
| `data-[state=checked]:bg-emerald-500`, `scale-125` switches | Semantic misuse, off-scale | Standard `Switch` |
| `text-primary` for headings / section labels | Purple budget violation | `text-fg-1`; purple only per §3.4 |

A CI gate (Task C) fails the build if any of these appear under `app/dashboard/**` or `components/**` for surfaced routes.

### 3.2 Neutral hierarchy (black / graphite)

All neutrals keep hue ≈ 255–262° at very low chroma so they read as *graphite*, never navy. Rule: **a neutral surface may not exceed a blue-minus-red channel difference of 8** (e.g. `#14121B`: 27−20 = 7 ✔; `#0F172A`: 42−15 = 27 ✘). This is the objective test for "navy".

| Level | Token | HEX | Role |
|---|---|---|---|
| L0 | `stage` (new alias of `bg-void`) | `#040306` | **Sunk** planes: Discord preview stage, chart plot wells, flow lanes, builder canvas backdrop. The only thing darker than the workspace. |
| L1 | `chrome` | `#070609` | Sidebar, topbar, drawer. Recedes. |
| L2 | `canvas` | `#09080D` | Workspace. Most content sits **directly** on it. |
| L3 | `surface-1` | `#0E0D13` | Contained groups (panels) — used when containment carries meaning. |
| L4 | `surface-2` | `#14121B` | Raised strips: panel header, table header, readout cells, popover base. |
| L5 | `surface-3` | `#1B1924` | Interactive rest (secondary button), hover of rows/nodes. |
| L6 | `surface-4` | `#232030` | Pressed / selected-neutral. |

The workspace therefore has **two directions of depth**: things *rise* (L3–L6) when they are containers or interactive, and things *sink* (L0) when they are a stage for content that is not CLS UI (a Discord message, a chart, a flow). This sink/rise pairing is the main source of "layered" richness without adding colour.

### 3.3 Separation without fill

In order of preference:

1. **Space + hairline**: groups on the canvas separated by a 1 px `line-subtle` rule and 24 px. Default for sections of a page.
2. **Engraved rule** (§4.2): section boundaries that carry a label.
3. **Outline only**: `border-line` on `canvas`, no fill — for lists and tables that sit on the canvas.
4. **Panel**: `surface-1` + `line` + `hl-1` — only when a group must read as one object (a settings group, the attention queue, a readout rail).
5. **Stage**: L0 inset with `line-subtle` frame — only for content that is not CLS UI.

Hard limits: no panel inside a panel (a panel may contain rows, strips and a stage, never another bordered box); at most **two** panel stacks per column; a page never shows more than ~6 bordered objects above the fold at 1440.

### 3.4 Purple system

Purple budget (DS §4.3) stays, but purple gains a *job* beyond buttons:

| Carrier | Recipe | Where |
|---|---|---|
| **Signal tick** | 16 × 2 px `brand-500` segment with a 30° cut end, at inline-start of the page header rule | Every page header. The constant CLS mark inside the dashboard. |
| **Signal edge** | 1 px top-edge gradient `brand-400` 80 % → 0 over the first 40 % of width | At most **one** focal object per view (the Overview status rail, the selected builder component, the Security posture header). |
| **Selection rail** | 2 px `brand-500` inline-start bar + `brand-tint` | Active nav (existing), selected row/node/tab. |
| **Signal path** | 1 px `brand-400` line | J2C flow when armed; chart series 1; timeline brush. |
| **Primary action** | `brand-600` fill | One per region, and on settings pages **only inside the sticky save bar when dirty**. |
| Focus ring, links, live dot | DS unchanged | — |

Consequence: a resting settings page shows purple only as the header tick, the active nav item and focus — the page reads black/graphite with a violet pulse of identity, not purple-with-buttons. When the user edits, the save bar arrives with the only purple fill. Purple appears **because something is yours or live**.

### 3.5 Semantic colour and where blue is allowed

Semantic tokens unchanged (DS §4.5). Clarifications:

- `info #4DB3F0` is the only blue in CLS UI: info notices, *pending* status, and `chart-2` (cyan `#4FC3D9`) as the second categorical series.
- Discord's own palette (`#313338` message bg, `#5865F2` blurple mentions/links, `#2B2D31` embed bg) appears **only inside the Discord preview frame** (§6, reference pages). It is fenced by the stage and labelled "Discord preview".
- Module identity never uses hue. Custom Roles' blue/pink/yellow/green tiles are removed; the only per-row colour on a roles page is the **actual Discord role colour**, as data.
- "Configured" is not a warning. Configured-and-healthy is `ok`; configured-but-incomplete is `warn`; not set up is `neutral`.

---

## 4. CLS-specific visual language

Derived from the CLS mark: a pointy-top hexagonal construction with sliced strokes and 30°/60° geometry. We take **the cut, the segment and the perimeter**, not the hexagon shape.

### 4.1 The 30° cut

A corner chamfer whose diagonal runs at 30° to the horizontal (width `c`, height `c·tan30° ≈ 0.577c`).

| Size | `c` | Use |
|---|---|---|
| `cut-sm` | 8 px | Segment meter ends, selection tags, the signal tick end. |
| `cut-md` | 12 px | Focal panels (status rail, flow nodes, builder frame). |
| `cut-lg` | 20 px | Security posture header; landing/auth frames (existing). |

Rules: always at the **top inline-end** corner (mirrors in RTL); one cut object per region, max **two per viewport** (the signal tick does not count); never on inputs, buttons, chips, table rows, menus, toasts or modals. The cut *frames important instruments*; if everything is cut, nothing is.

Recipe (no SVG, no dependency): `clip-path: polygon(0 0, calc(100% - var(--cut)) 0, 100% calc(var(--cut) * .577), 100% 100%, 0 100%)` on the element; the 1 px border is drawn by a `::before` using the same polygon with a `padding: 1px` + mask-composite ring, and the diagonal is a 1 px `::after` line of length `c / cos30°` rotated 30°. `[dir="rtl"]` mirrors the polygon. Implemented once as `.cls-cut` + `--cut`.

### 4.2 Engraved rule (section separator)

A 1 px `line-subtle` rule with a label cut into it: `overline` label (mono, `fg-3`) at inline-start, a 6 px gap, the rule running to inline-end, optionally a right-aligned mono readout (`2 of 3 set`, `checked 14:02`). It replaces most "card with a title" patterns: a section is announced by a rule, not by a box.

The **page header rule** is the same rule under the title with the signal tick at its start. Every dashboard page therefore carries the CLS mark in the same place without a logo.

### 4.3 Segments

The mark's sliced strokes become the product's native quantity glyph: the **segment meter** — `n` discrete parallelogram segments (6 px tall, 30°-slanted ends, 2 px gaps). Used whenever the denominator is small, discrete and real (≤ 12): required modules 6/6, configuration steps 2/3, routed log categories 5/9, protections armed 4/6. Filled segments take the *meaning* colour (ok/warn/danger for status, `fg-2` for neutral counts, `brand-400` only for "your progress" in a builder). Never used for percentages of continuous quantities (that is a bar or ring).

### 4.4 Perimeter

The landing Perimeter (three nested segmented rings) stays a **system graphic** with two dashboard uses only: the Security posture mark (Phase 7) and the "not configured" module state (static, 3 % opacity lattice + outline). It never decorates ordinary pages.

### 4.5 Readouts instead of cards

A **readout** is a label + value cell on `surface-2`, separated from its neighbours by vertical hairlines, not gaps: `BOT ● Online  158 ms │ MODULES ▰▰▰▰▰▰ 6/6 │ POSTGRES ● │ SCHEDULER ●`. Readout rails replace KPI card grids. They compress 4–6 facts into 56 px and look like an instrument panel rather than a SaaS stat row.

### 4.6 Operational micro-visuals (per-row, inline)

Small, data-true glyphs inside rows so lists stop being "Off — Configure":

| Micro-visual | Encodes | Example |
|---|---|---|
| Segment meter (inline, 40 px) | Discrete completion | Logging `▰▰▰▰▰▱▱▱▱ 5/9 routed` |
| Channel token | A real channel | `# welcome`, `🔊 Join to create` rendered with channel-type glyph |
| Role swatch | Real Discord role colour | `● VIP` with the role's colour dot |
| Flow glyph | J2C chain completeness | `◆─◆─◇─◆` join / temp / control / cleanup |
| Count + delta | Real counts | `1 open` / later `+3 today` |
| Sparkline (Phase 4/5+) | Real time series | ticket opens, events |

### 4.7 What we deliberately do not use

Hexagon grids as backgrounds, hex-shaped buttons or avatars, glowing borders on panels, glass cards, gradient blobs, angled whole-page layouts, scanning lines, radar, globes, fake terminal text, per-module neon hues.

---

## 5. Typography adjustments

Families unchanged (Plex Sans / Plex Sans Arabic / Plex Mono). Changes are in *roles*:

- **Readout value** (new): Plex Sans 600 15/20 tabular; unit in `fg-3` 12 px. Used in readout rails.
- **Readout label**: the existing `overline` (mono uppercase, ≤ 3 words) — one of the four sanctioned roles, now named.
- **Module header**: `page-title` 20/28 stays; description capped at one line at ≥1024 (the header must not grow to three lines of prose).
- Mono is used for **Discord-native tokens** (channel names in tokens, `.staff` commands, `{user}` variables, IDs) — this gives Discord-operations pages their texture.
- No italics, no `font-black`, no uppercase content (DS §5 unchanged).

---

## 6. Data visualization system

Principle: **a chart exists only when a real series exists.** If the data source is not implemented, the widget is not rendered (no placeholder, no "coming soon", no skeleton-forever). A real **zero** is data and is drawn (flat line at 0, empty bars with counts "0"); "not collected" is absence.

### 6.1 Chart frame

- Lives inside a panel (or on the canvas under an engraved rule). The **plot area is a stage** (L0 `#040306`) inset 12 px with a `line-subtle` frame — charts sink, readouts rise.
- Header: `panel-title` + inline-end readout of the headline value and the range selector (segmented control: `24 h · 7 d · 30 d`, only ranges the source supports).
- Heights: sparkline 24–32 px; compact 120 px; default 200 px; timeline track 28 px.

### 6.2 Grid and axes

- Horizontal grid only: 3–4 lines, 1 px `line-subtle`. Baseline 1 px `line`. No vertical grid, no chart border besides the stage frame.
- Axis labels: Plex Mono 11 px `fg-3`, tabular; y-axis at inline-start, max 4 ticks, nice numbers; x-axis time labels at most every 4th tick, 24-hour clock.
- RTL: time axes stay left-to-right (`dir="ltr"` on the plot area) so time always runs left → right; titles, legends, readouts and the y-axis label column mirror. REVISIT with an Arabic-speaking owner review in the RTL phase.

### 6.3 Colour

| Series type | Colour |
|---|---|
| Single neutral quantity (volume, members, events) | `brand-400` line, area fill `brand-400` 20 % → 0 %. This is the **one** place purple carries data, because the series is "the CLS measure". |
| Status series (errors, failures, incidents) | Semantic colour of the state. Never purple. |
| Security severity | `sev-*` scale, stacked critical → low. |
| Categorical (≤ 4) | `chart-1..4` (`#9474FF`, `#4FC3D9`, `#D98AD3`, `#C2BED2`); beyond 4 → "Other" in `fg-4`. |
| Comparison (previous period) | Same hue, 1 px dashed, 50 % opacity. |

Never mix brand and semantic in one plot except a brand series with danger **markers** (incidents on an event line).

### 6.4 Pattern catalogue

| Pattern | Spec | Use when |
|---|---|---|
| **Time-series line/area** | 1.5 px line, round joins, one area max; last point 4 px dot; live series' last point gets G2 | Continuous counts over time (ticket opens, log volume) |
| **Sparkline** | 24–32 px, 1.25 px, no axes; min/max not labelled; tooltip on hover | Trend beside a readout |
| **Categorical bars** | Horizontal preferred (labels fit, RTL-safe); 8 px bars, 2 px `radius-xs` at the value end; value label at bar end, tabular | Channels by type, tickets by category |
| **Stacked state bar** | One 8 px bar split by state, 2 px gaps; legend with counts underneath | Module states On/Partial/Off/Unavailable; protection coverage |
| **Segment meter** | §4.3 | Discrete completion ≤ 12 |
| **Event timeline** | 28 px track on stage; events as 2 × 12 px ticks coloured by severity; clusters (≥ 3 within 6 px) collapse to a count tag; brush = `brand-tint` span | Incidents, config changes |
| **Activity heatmap** | 7 × 24 cells, 10 px, 2 px gap, `radius-xs`; 5-step ramp of `brand-400` alpha (8/20/36/56/80 %) over surface-1; severity heatmaps use `sev` ramp | Hour-of-week activity (log events, ticket opens) |
| **Ring** | 3 px stroke, 40–56 px, value inside in `readout value` | **Only** a true bounded percentage (quota, storage). Max one per view. |
| **Mini trend** | `▲ 12 % vs prev 7 d` caption; neutral `fg-2` unless the metric has an agreed good/bad direction and threshold | Beside readouts |
| **Completeness** | Segment meter labelled "2 of 3 steps"; tooltip lists the missing steps by name. Never "83 % configured". | Only modules with an explicit checklist in code |
| **Severity distribution** | Stacked bar critical → low, counts in legend | Security, automod actions |

### 6.5 Tooltip, hover, keyboard

Tooltip uses the floating recipe (DS §9.1), `small` text, value in `fg-1` tabular, 8 px square swatch, absolute timestamp. Crosshair 1 px `fg-4`. Hovered point 6 px with 2 px stage-coloured ring. Charts are focusable; arrow keys step through points; every chart has a text summary (`aria-describedby`) and "View as table".

### 6.6 States

| State | Visual |
|---|---|
| Loading | Chart-shaped skeleton: stage frame + baseline + 3 grid lines drawn, one shimmer band at `surface-3`. Header/readout labels render immediately. |
| Real zero | Full chart with the zero line / zero bars and the caption "No ticket activity in the last 7 days." |
| Source not available (feature not shipped) | **Not rendered.** |
| Source failed | Stage keeps its size; danger inline banner inside it with Retry. |
| Stale | Readout gets `warn` "Data from 14:02" when older than the source's freshness budget. |

### 6.7 Motion

Draw-in once per mount (DATA tier, §7): line `stroke-dashoffset` 480 ms; bars grow from baseline 320 ms, 20 ms stagger, max 12; segment meters fill sequentially 30 ms per segment (≤ 240 ms total). Updates tween 200 ms. Live insertion: the new bar grows 200 ms; the last-point dot gets G2 for 1.2 s then settles. Reduced motion: final state immediately.

### 6.8 Implementation

Hand-rolled SVG components in `components/viz/` with pure layout helpers (scale, ticks, path) — no chart library in Phase 1.6. Static charts render on the server; only tooltip/brush hydrate. A library is evaluated when Phase 5 needs brushing over large series (see `IMPLEMENTATION_PLAN` §6).

---

## 7. Motion system

Motion answers *what changed, what caused it, what is live*. The dashboard must feel mechanical and responsive, never cinematic.

### 7.1 Tiers

| Tier | Duration | Easing | Covers |
|---|---|---|---|
| **MICRO** | 80–120 ms | `ease-out` (press 80 ms) | Hover tone step, press scale 0.98, focus ring, switch thumb, checkbox, tooltip fade |
| **STATE** | 160–240 ms | `ease-out` enter / `ease-exit` leave (70 %) | Selection rail slide, tab/segmented thumb slide, accordion (`grid-template-rows 0fr→1fr`), status crossfade, save bar in/out, attention item enter/resolve, node selection |
| **DATA** | 240–480 ms (+ ≤ 20 ms stagger) | `ease-out` | Chart draw, bar growth, number tween (400 ms, first mount / changed since last visit only), segment fill, signal-path arm (J2C) |
| **MAJOR** | 280–360 ms | `ease-emphasized` | Drawers, modals, sheets, route entrance of up to 4 regions |

### 7.2 Specific behaviours

- **Route entrance (amends DS §10.2).** On hard navigation only: up to 4 top-level regions fade in with a 4 px rise, 200 ms, 30 ms stagger (total ≤ 290 ms). Tab switches inside a module and revalidations: 120 ms opacity only. Never slide whole pages.
- **Panel/row hover depth.** +1 surface step and `line-strong`, MICRO. No lift, no scale, no glow.
- **Selection.** The 2 px rail *slides* between siblings (STATE 200 ms) rather than blinking — nav, roster rows, flow nodes, tabs.
- **Status change.** Old label fades out 80 ms, new one in 120 ms; the row receives a one-shot tint flash of the new semantic colour (600 ms). Critical-unacknowledged is the only repeating status motion (DS pulse).
- **Number transitions.** Tween only on first mount or when the value changed since the user last saw it (persisted per readout in `sessionStorage`). Live-updating values (latency) swap instantly.
- **Segment movement.** When a ratio changes (e.g. 5/9 → 6/9 routed), only the delta segment animates (fills 120 ms).
- **Signal-path arm (J2C, later Security).** After a successful save that completes the flow, the brand line draws once along the path (DATA 480 ms). This is the dashboard's one "moment" and it confirms a real state change.
- **Live-event insertion.** New row enters via `grid-template-rows 0fr→1fr` 160 ms + semantic tint flash 600 ms; feed pauses on hover/focus with a "Paused · 3 new" pill.
- **Alerts.** New attention item: STATE enter. Resolved item: `ok` flash 600 ms, then collapse 200 ms.
- **Builder / preview.** The Discord preview updates on every keystroke with **no** animation (latency matters more than delight). Structural changes (embed added/removed, format switched) crossfade 120 ms.
- **Save.** Save bar slides up 200 ms when dirty; saving shows the hex loader; success collapses the bar and flashes the changed rows `ok` 600 ms.

### 7.3 Banned

Ambient loops outside live data, spinning decorative graphics, parallax on dashboard pages, fake scanning/typing, staggered card cascades longer than 290 ms, animating layout width/height (except accordion rows and the sidebar grid column), `animate-pulse` on text, bounce/elastic easing.

### 7.4 Reduced motion

DS §10.3 stays: STATE/DATA/MAJOR collapse to 0 ms except 120 ms opacity; no pulses (static ring), no draw-in, no tweens, no signal-path arm (the armed path renders statically), no shimmer. Implemented via the duration tokens plus a `useReducedMotion()` hook for JS-driven tweens.

---

## 8. Density rules

| Element | Rule |
|---|---|
| Page header | Title + one-line description + inline-end state readout / actions; **≤ 72 px** incl. rule. No hero, no icon tile. |
| Readout rail | 56 px; cells ≥ 120 px; wraps into 2 rows < 1024. |
| Setting row | 12 px block padding; switch-only rows 48 px; select rows 52 px; description ≤ 1 line at ≥ 1280, 2 lines max elsewhere. |
| Form controls | 32 px default, 28 px in tables/toolbars; 40 px only on touch and mobile primary. Never `h-12`/`h-14`. |
| Field rhythm | 16 px between fields; 24 px between groups (engraved rule). |
| Tables | 36 px default, 32 px logs/feeds, 44 px with avatars/touch; header 32 px. |
| List rows (roster) | 44 px with swatch + token; secondary line only if it carries data. |
| Panels | 16 px padding (12 px compact); header strip 40 px. |
| Chart cards | Header 40 px + plot; no padding beyond 12 px around the stage; ≥ 1 readout in the header. |
| Builders | Palette rows 32 px; inspector rows 32–40 px; canvas gets every remaining pixel. |
| Gaps | 12 px between panels; 24 px between page sections. `space-12/16` banned. |
| Empty state | 1 line + 1 action, ≤ 96 px tall inside a panel. |

Target: at 1440 × 900 a settings page shows **all** of a typical module's settings above the fold (Custom Roles: 6 rows; J2C: flow + 3 rows; Welcome: composer + full preview).

---

## 9. Page geometry archetypes

No single max-width. Each route is assigned one archetype.

| Archetype | Geometry | Width behaviour | Routes |
|---|---|---|---|
| **A · Operations canvas** | Readout rail + asymmetric 12-col grid; third column at ≥ 1920 | Fluid, no max width; gutters 24/32 px | Overview, Platform, (Security Center, Phase 7) |
| **B · Workspace split** | Composer column (440–560 px) + stage (fluid, L0) | Composer fixed, stage takes the rest; stage content (Discord frame) max 720 px | Welcome (channel + DM), Ticket panel appearance (pre-V2), later embed editors |
| **C · Settings column** | 760 px form + 320 px context rail at ≥ 1440 | Form **start-aligned** (not centred); rail folds under < 1440 | Bot settings, Automod, Antinuke, Auto react |
| **D · Roster / routing table** | Toolbar + compact table/rows | Fluid to 1280, then start-aligned with context rail | Custom Roles, Auto roles, Reaction roles, Voice/Vanity roles, Invites, Access, Logging routes |
| **E · Flow + config** | Flow lane on stage (≤ 1200 px) + settings column below | Lane fluid to 1200; config follows C | Join to Create, (Verification later) |
| **F · Builder** | Palette 240 + canvas fluid + inspector 320 | Full bleed, own header | Tickets V2 (Phase 4) |

All archetypes share: the module header + rule, the gutter scale, the save model, and start-alignment (content never floats in the centre of a 2560 canvas).

---

## 10. Security Center art direction (Phase 7 target; foundation in 1.6)

The Security Center is where the instrument becomes a console. It is the only surface allowed a `cut-lg` frame, a persistent signal edge and live motion — all driven by events.

**Composition (top → bottom), refining DS §17:**

1. **Posture header** (`cut-lg`, signal edge, lattice 3 %): Perimeter mark (static; its affected-domain segment lights in the severity colour during an incident), posture word (Secure / Elevated / Incident), Incident Mode state + countdown, data freshness readout. Height ≤ 120 px.
2. **Readout rail**: open incidents by severity (segment-free counts with severity chips), protections armed `▰▰▰▰▱▱ 4/6`, quarantined accounts, last event age.
3. **Incident rail** (table, 36 px rows): severity chip, title, actor, attribution (Certain / Probable / Unknown as text + confidence glyph), target, age, state, owner. Row → drawer with the incident **timeline** (vertical, events as cut-ended ticks with timestamps in mono).
4. **Event stream (60 %) | Protection coverage matrix (40 %)**. Stream: 32 px rows, mono time, event glyph, actor → action → target; new rows per §7.2. Matrix: rows = protections, columns = State (glyph), Trusted IDs, Last trigger, Missing permissions (count chip), link. Not cards.
5. **Timeline band**: 24 h / 7 d severity-stacked histogram on stage with incident markers; brush filters the stream.
6. **Actor × action matrix**: rows = top actors (24 h), columns = high-risk action types (ban, kick, role change, channel delete, webhook, permission change); cells = counts on the sev heatmap ramp. Click → filtered stream.
7. **Permission change history**: diff rows — role/channel, `+ Administrator` in danger, `− Manage Webhooks` in ok, actor, time, revert link (when Phase 2 supports it).
8. **Quarantine state**: compact roster of quarantined members with reason, since, releaser.

Banned here too: radar sweeps, threat globes, world maps, fake counters, scrolling hex. If the stream is quiet, it says "No security events in the last 24 h" with the freshness readout — a quiet console is a good console.

Phase 1.6 foundation only: severity chip, segment meter, event-timeline track, matrix cell styles, `cut-lg` recipe, and the Antinuke page rebuilt as a protection-coverage matrix + whitelist roster (Task C). No Security Center route.

---

## 11. Amendment register (to DS)

| DS section | Amendment | Reason |
|---|---|---|
| §4.1 | Add `stage` alias (L0 `#040306`) for sunk content planes | Sink/rise layering |
| §4.3 | Purple carriers extended: signal tick, signal edge, signal path | Purple as identity, not only buttons |
| §6.2 | Replace "settings max 760 + rail" as a universal rule with archetypes A–F; content start-aligned | One max-width fits nobody |
| §8 | Add `cut-sm/md/lg` (8/12/20 px) with usage caps | CLS geometry |
| §9.4 | Signal edge is G0-level (no blur) and allowed on one focal object per view | Edge illumination without glow creep |
| §10.2 | Route entrance: ≤ 4 regions, 200 ms, 30 ms stagger, hard navigation only | Owner: too static |
| §10.2 | Add signal-path arm (DATA) and segment delta fill | Purposeful "moments" |
| §15.4 | Page header gains the engraved rule + signal tick and an inline-end state readout slot | Identity on every page |
| §15.5 | Primary save action lives only in the sticky save bar on settings pages | Purple stops being the resting focal point |
| §24 | Superseded by §6 of this doc (patterns, states, stage treatment) | Chart language |

---

## 12. Self-critique (cls-os-ui-review + impeccable pass) and resulting refinements

| Question | Honest answer | Refinement made |
|---|---|---|
| Is it distinctive? | The ingredients (black, purple, hairlines) are common. The distinctiveness comes from three owned devices: the **30° cut**, **segments**, and the **sink/rise stage**. Without them it is another black dashboard. | Made the three devices mandatory in the page header (tick), readouts (segments) and stages (Discord preview, flows, charts), so every page shows at least one. |
| Is it just another black dashboard? | Risk remains on plain settings pages. | Settings pages get the header tick + engraved rules + start-aligned column + context rail; builders/flows carry the richness. A settings page is *allowed* to be quiet; the system is distinctive at product level. |
| Is purple overused? | First draft put signal edges on every panel. Too much. | Capped: one signal edge per view, one primary fill per region, save fill only when dirty. Resting screens should be > 97 % non-purple pixels. |
| Is geometry gimmicky? | Cuts on every card would be. | Max two cut objects per viewport, never on controls/rows/modals; hexagons banned as decoration. |
| Enough data density? | Today the data is thin (no history). | Readout rails, inline micro-visuals and state distributions make *existing* data visible now; time-series slots appear automatically when sources ship. |
| Are charts justified? | Only some. A ring for "6/6 modules" would be fake precision. | Segment meters for discrete ratios; rings only for true bounded percentages; no chart without a real series. |
| Is motion purposeful? | Entrance stagger is the weakest justification. | Limited to hard navigation, ≤ 4 regions, ≤ 290 ms; everything else is state- or data-driven. |
| Does each module feel purpose-built? | Yes for the five reference pages; the remaining modules inherit archetypes rather than bespoke designs. | Archetype table assigns every surfaced route; Task C migrates by archetype, not page-by-page invention. |
| Implementable without a rewrite? | Yes: tokens exist, primitives are small (CSS + SVG), APIs already provide the data. No dependency is required for 1.6 except an optional combobox helper. | Plan limited to three tasks; Tickets gets pre-V2 treatment only; Security gets primitives only. |
