# CLS OS Phase 1.6 — Task A review

**Scope:** Premium visual system ("Graphite Instrument") + Overview reference implementation ("Operations Deck").
**Sources:** `CLS_OS_PHASE_1_6_ART_DIRECTION.md` (AD), `CLS_OS_PHASE_1_6_REFERENCE_PAGES.md` (RP §1), `CLS_OS_PHASE_1_6_IMPLEMENTATION_PLAN.md` (Task A).
**Verified on:** the authenticated local preview (`http://localhost:3000`, Root owner, test guild `cls-backup`), live bot API.

**Task B and Task C were not started. Phase 2 was not started.** No Welcome, J2C form, Custom Roles, Tickets, Antinuke or other module page was redesigned.

---

## 1. Visual changes

| Area | Before | After |
|---|---|---|
| Overview layout | Status strip + 4 bordered cards (attention, modules table, server, access) in a centred 1680 px column | One instrument rail, then attention queue + grouped module matrix, with a facts column at inline-end. Fluid width (no content max) on Overview only |
| Box count on Overview | 5 bordered boxes, attention items were bordered boxes inside a box | **1 bordered panel** (the readout rail). Everything else is hairline rows and engraved rules on the canvas |
| Page header (all callers) | Title + description | Same API; closes with the engraved rule that starts at the signal tick |
| Purple | Links, "Open" labels | Signal tick, signal edge on the rail, active nav, focus, hovered actions. Resting Overview is graphite first |
| Module state semantics | Tickets "Configured" drawn as *warning*; J2C always "Off"; rows showed "—" | Tickets "Configured" is ok; J2C derived from the real contract; every row states a fact |
| Table primitive | `slate-800/900/400/500` (navy) | Graphite line/surface/fg tokens, `text-start` for RTL |
| Titles | "CLS OS · CLS OS" on dashboard routes | "CLS OS" on dashboard routes, "Overview · CLS OS" on the Overview |

The surface ladder already matched the approved Graphite values (`#040306` stage → `#232030` pressed), so no palette value changed. The approved hierarchy maps to existing tokens: stage `bg-void`/`bg-stage`, chrome `bg-chrome`, canvas `bg-canvas`, panel `surface-1`, raised `surface-2`, hover `surface-3`, pressed `surface-4`.

## 2. Primitives introduced

| Primitive | Where | Notes |
|---|---|---|
| 30° cut | `.cls-cut`, `.cls-cut-sm` (`globals.css`) | clip-path + hairline cut face; RTL-mirrored. One use on the page (rail) |
| Signal edge | `.cls-signal-edge` | 28 × 2 px brand segment on the anchor panel's top border. One per view |
| Signal tick | `.cls-tick` | Starts the page-header rule; cut end face; mirrored in RTL |
| Engraved labelled rule | `components/ui/section-rule.tsx` | The label is the section heading (h2/h3); optional count + action |
| Readout / rail | `components/ui/readout.tsx` (`Readout`), `components/overview/readout-rail.tsx` | `dl` of cells separated by 1 px hairlines (gap-px over `line-subtle`), wraps without broken borders |
| Segment meter | `components/ui/segment-meter.tsx` | 30°-skewed cells, ≤ 12, `role="meter"` with `aria-valuenow/max/text`; always paired with visible text |
| State distribution bar | `components/ui/state-bar.tsx` | Stacked bar + legend with counts; zero parts stay in the legend |
| Mini bars | `components/ui/micro-bar.tsx` | Neutral ink, `dl` with numbers as text |
| Change mark | `ChangeMark` in `readout.tsx` | One brief wash when a watched factual value changes after a re-check; never on first render |
| Page header v2 | `components/dashboard/page-header.tsx` | Backward compatible (same props) |
| Fluid route | `isFluidRoute()` in `lib/shellNav.ts` + `app-shell.tsx` | Overview only; all other routes keep `max-w-content` |
| Activity band | `lib/overviewWidgets.ts`, `components/overview/activity-band.tsx` | Registry with **zero** widgets; renders `null` |
| Tokens | `--cls-dur-data` 400 ms, `--cls-stagger` 30 ms, `--cls-cut-sm/md`, `duration-data`, `text-readout`, `bg-stage` | Reduced motion sets data/stagger to 0 |
| Legacy-token report | `dashboard/scripts/check-legacy-tokens.mjs` | Report-only now; `--strict` for Task C |

`DS` amendments from AD §11 are recorded at the top of `docs/CLS_OS_DESIGN_SYSTEM.md`.

Not added, on purpose: `useCountUp` / `useReducedMotion` (all motion is CSS and every number on the Overview is small; a tween would be decoration), `cut-lg` and the heatmap ramp (no consumer yet), `components/layout/operations-canvas.tsx` (the Overview grid is the only archetype-A consumer; extract with the second one).

## 3. Real data and each visualization

Every value comes from an existing bot API response. Nothing is estimated. Widgets without a source are not rendered.

| Element | Backing data | Endpoint |
|---|---|---|
| Server name, icon | `name`, `icon` | `GET /guilds/{id}` |
| Bot status + latency | `latency`, request success | `GET /bot/status`, `deriveHealth` |
| Required modules meter (6/6) | `modules.required_ok` + `required_failed` (names in the tooltip) | `GET /system/health?guild_id=` |
| Permissions meter (6/6) | `permissions.module_requirements` keys (total) minus this guild's `missing_by_module` with entries | `GET /system/health?guild_id=` |
| Postgres / Scheduler | `postgres.enabled/connected`, `scheduler.worker_running` | `GET /system/health` |
| Checked hh:mm:ss | server time the loader finished | `loadOverview` |
| Attention queue | `deriveAttention`: failed required modules, permission gaps, Antinuke off, logging categories enabled without a channel, ticket categories without staff; ranked critical → warning → info (stable) | health, antinuke, logging, tickets |
| Tickets meter (3 of 3 steps) | panel channel set; ≥ 1 category; staff roles on every category | `GET /guilds/{id}/tickets` |
| Welcome meter (0 of 2) | `channel_id`; message (text) or embed title/description/message (embed) | `GET /guilds/{id}/welcome` |
| J2C meter (0 of 2) | `join_channel_id`; `control_channel_id` | `GET /guilds/{id}/j2c` |
| Logging meter (routed / enabled) | enabled categories that have a non-zero channel; shown only when ≥ 1 category is enabled | `GET /guilds/{id}/logging` |
| Module state bar | count of matrix rows by bucket (On / Incomplete / Off / Unavailable) | derived from the rows above |
| Members / roles / channels | `member_count`, `role_count`, `channel_count` | `GET /guilds/{id}` |
| Channels by type bars | channel `type` grouped: text (0, 5), voice (2, 13), categories (4), other | `GET /guilds/{id}/channels` (new in the Overview load) |
| Command prefix | `prefix` | `GET /guilds/{id}/prefix` (new in the Overview load) |
| Access | Root owner flag (server-side), grants count (Root only) | session, `listAccessGrants` |

Binary module states (Antinuke, Automod, Auto roles, Reaction roles) have no meter: a single on/off is never drawn as a ratio or percentage.

## 4. Motion

| Tier | What | Duration |
|---|---|---|
| STATE | Page-region entrance (`.cls-enter`): rail, attention, matrix, facts — 4 regions, 4 px rise, staggered by `--cls-stagger` | 200 ms + 30 ms/region |
| DATA | Segment meters fill on mount cell-by-cell; on later renders only the changed cells transition. State bar settles from the inline start (transform only) | 400 ms, 30 ms/cell |
| DATA | Factual change after **Check again** (`router.refresh()`): bot/Postgres/scheduler/module status and ratios wash once when their value differs from the previous read | 400 ms |
| MICRO | Attention and matrix rows: background to `surface-2`, action text to brand-300, chevron nudges 2 px toward its target (direction-aware) | 120 ms |

Verified in the browser: with motion, segments `transition-duration: 0.4s`, entrance `animation-duration: 0.2s`; re-check updated `checkedAt` from 23:25:33Z to 23:25:52Z with no errors. With `prefers-reduced-motion: reduce`: `--cls-dur-data` 0 ms, `--cls-stagger` 0 ms, `.cls-enter` `animation-name: none`, segment transition 0 s, meters render filled. No ambient loops, parallax, scanning or spinners were added (the re-check shows "Checking…" text, not a spinner).

## 5. J2C bug

- **Cause:** `loadOverview` read `j?.enabled ?? j?.status`. The bot's `GET /guilds/{id}/j2c` returns only `guild_id`, `join_channel_id`, `control_channel_id`, `category_id` (confirmed live: all `null` on `cls-backup`). So the Overview always showed "Off".
- **Fix:** `j2cEnabled()` in `lib/overviewModel.ts` returns true when `join_channel_id` is a non-empty string, matching how the J2C form and the bot treat the module (disabling saves all three as `null`). A second checklist step reports the control channel. No `enabled` field was invented.
- **Test:** `overviewModel.test.mjs` — "state comes from join_channel_id (the API has no enabled field)", including an `enabled: true` payload that must still read Off.
- No API contract changed, so backend tests were not required.

Documented for Task B, not fixed here: Custom Roles `parseInt()` on role IDs (`customroles-form.tsx` L85, L117); Welcome default template colour without `#` (ignored by `greet2`); J2C "off" silently clears all three channels.

## 6. Responsive, RTL, reduced motion

- **2560:** rail in 7 cells; main column + 24 rem facts column; the module matrix flows into two balanced columns (Security, Moderation, Tickets | Engagement). Start-aligned, no centred island.
- **1440:** rail, attention, the full matrix and the facts column are above the fold.
- **1024:** single column; rail wraps into a 3-column grid with intact hairlines; facts become a 3-up strip under the matrix.
- **390:** rail as a 2-column grid, then attention, module rows (name + state, then detail + meter, then Configure), then facts. No horizontal overflow. Every link and button ≥ 40 px tall.
- **RTL (1440, 390):** cut, signal edge, tick, meters, bars and chevrons mirror; English strings with numbers are isolated with `dir="auto"`; latency is `dir="ltr"` (also fixed in the topbar health indicator).
- **Reduced motion (1440):** as §4.

## 7. Accessibility

- Segment meters: `role="meter"` + `aria-valuenow/min/max/valuetext` + label; visible "6/6" / "2 of 3 steps" text beside every meter.
- State bar: `role="img"` with a full text summary, plus a visible legend with counts.
- Status is always glyph/dot shape + text. Attention rows prefix a screen-reader severity ("Critical:", "Warning:", "Notice:").
- Headings: page h1, section h2 (engraved rule labels), domain h3. Rail is a `dl`.
- Focus: global `:focus-visible` ring on rows, links, the re-check button, and the tooltip triggers (meters with checklist detail).

## 8. Self-review (cls-os-ui-review + impeccable)

Impeccable detector run once over the changed UI files: 1 finding — **layout-property animation** (`.cls-fill` transitioned `width`/`flex-grow`). Fixed: fills scale with `transform` from the inline start.

| Severity | Finding | Resolution |
|---|---|---|
| HIGH | J2C always Off; Tickets "Configured" rendered as warning | Fixed (§5, Tickets → ok) |
| HIGH | Old Overview used undefined utilities (`text-section-title`, `text-brand`, `duration-row`), so headings and links rendered unstyled | Removed with the rebuild |
| HIGH | RTL bidi reordering ("of 3 steps 3", "ms 159") | Fixed with `dir="auto"` / `dir="ltr"` |
| HIGH | Touch targets < 40 px at 390 (Configure, re-check) | Fixed |
| MEDIUM | "Required modules" label truncated at 1440; server name truncated | Rail column rebalanced; duplicate member count removed from the rail (it is in the facts column) |
| MEDIUM | Row hover on `surface-1` barely visible | Hover is `surface-2` |
| MEDIUM | 2560 two-column matrix left a gap under Security | Balanced CSS columns |
| MEDIUM (open) | Guild `loading.tsx` skeleton is still three generic bars; it is shared by every guild route | Task C (route skeletons per archetype) |
| MEDIUM (open) | `cn()` uses plain `tailwind-merge`, which treats custom font sizes (`text-body`, `text-small`, …) as colours and drops one of them when both are passed. New code avoids the collision; fixing it globally changes sizes on legacy pages | Task C, with visual re-check |
| POLISH (open) | Entrance plays on client navigation to the Overview, not only on hard loads | Acceptable (≤ 290 ms, 4 regions) |

## 9. Tests

- `npm run build` — pass. Built in an isolated temporary copy (outside the repo, `node_modules` junctioned) so the shared `.next` of the running dev server was not overwritten; the copy was deleted afterwards. Overview route 2.42 kB / 129 kB first load.
- `npm run lint` — pass (0 errors; existing `exhaustive-deps` warnings on legacy pages only).
- `npx tsc --noEmit` — pass.
- `node --test lib/*.test.mjs` — 47 / 47 pass (new: `overviewModel.test.mjs` 9 tests, `isFluidRoute`, attention `origin`).
- `git diff --check` — clean.
- Client bundle scan — none of the 7 secret `.env.local` values (NextAuth secret, Discord client secret/ID, internal service and identity keys, audience, Root owner ID) appear in any of the 102 `.next/static` files.
- Unchanged: auth (`lib/auth`, `app/api`, `app/auth`), Root gating (`isRootOwner`, server-side only), guild authorization, API client, snowflake helpers, Task B landing (`app/page.tsx`, landing components). `git diff` on these paths is empty.

## 10. Legacy tokens

Report (`node scripts/check-legacy-tokens.mjs`, report-only): 23 files — `slate-*` 471, `#141B2D` 22, `rounded-2xl/3xl` 63, `font-black` 49, `shadow-xl` 17. All in legacy module forms and hidden pages (Tickets, Verification, Leveling, J2C, Reaction roles, Vanity roles, Custom roles, Auto role, Auto react, `server-card`, `guild-tabs`, `metric-card`, `form-elements`). The Overview, shell, page header and the `ui/` primitives report **zero** after the table fix. Module migration is Task B/C.

## 11. Screenshots (outside Git — contain account data)

`%TEMP%\cls-p16-taskA\` (`C:\Users\aero\AppData\Local\Temp\cls-p16-taskA\`):

- `before-1440x900.png` (Phase 1.6 direction capture of the old Overview)
- `final-2560x1440.png`, `final-1440x900.png`, `final-1024x768.png`, `final-1024-fullpage.png`, `final-390x844.png`, `final-390-fullpage.png`
- `final-rtl-1440x900.png`, `final-rtl-390-fullpage.png`
- `final-reduced-motion-1440x900.png`
- `state-attention-hover.png`

## 12. Unresolved concerns

1. The test guild is sparse (1 of 8 modules on, no activity history), so the 2560 view has empty lower space. That is correct under "real data only"; the activity band fills it when a source ships.
2. The "module source failed" row state is not covered by a unit test: `loadOverview` imports the server API client through path aliases that `node --test` cannot resolve. The failure path is one shared helper (`unavailableRow`).
3. The ticket panel channel name contains an emoji that renders as a colour glyph in the row detail; it is real Discord data and left as-is.
4. `health.permissions.top_role_position` already exists in the API; RP §4.2 calls it "future". Worth using in Task C (Bot settings / Security).

---

## 13. ANALYTICS / INSTRUMENT REFINEMENT (Task A.1)

Owner feedback on Task A: the Graphite direction is approved, but the Overview read as text-heavy and lacked a focal point. Task A.1 adds an **instrument deck** directly under the readout rail. Hierarchy is now: page header → readout rail → instrument deck (focal) → needs attention → module matrix + facts. Future activity slots stay unrendered.

### 13.1 Deck composition

One dark stage (`bg-void`, the `#040306` L0 token), hairline-separated regions (`gap-px` over `line-subtle`), not a card per chart. The deck now carries the page's signal edge (moved off the rail) and one CLS cut; the rail keeps its cut — two cuts per viewport, the AD maximum.

| Width | Layout |
|---|---|
| < 768 | One column, priority order: System Core → Live latency → Module state → Server composition |
| 768–1279 | System Core full width; Module state + Composition side by side; Live latency full width |
| 1280–1919 | System Core left spanning two rows (`1.35fr`); Module state and Composition stacked right; Live latency full width |
| ≥ 1920 | Three columns: System Core spanning two rows; Module state + Composition side by side; Live latency under them |

Future Security / Tickets / Logging instruments get a region in this grid only when their sources exist (`overviewWidgets`); none is rendered.

### 13.2 Real-data mapping

| Instrument | Encodes | Source |
|---|---|---|
| **System Core — outer ring** | One segment per required bot module. `ok` = success, `failed` = danger. | `/system/health` → `modules.required_ok` / `required_failed` (`requiredModuleItems`) |
| **System Core — inner ring** | One segment per module that declares permission requirements, for **this** guild. `ok` = success (less ink), `missing` = warning. | `permissions.module_requirements` + `permissions.guilds[guild].missing_by_module` (`permissionItems`) |
| **System Core — centre** | Live bot state (Online / Degraded / Offline / Unknown) and gateway latency in ms. | Shared shell poll (`/bot/status` + `/system/health`), SSR reading until the first poll lands |
| **Module state** | One segment per module row in the matrix, ordered On → Incomplete → Off → Unavailable; centre = On count / total. | The matrix's own `ModuleRow.bucket` values — the same numbers as the matrix, never a score |
| **Server composition** | One slanted tick per real channel grouped by Discord type (Text, Voice, Categories, Other); proportional runs above 96 channels. | `getChannels` → `channelComposition` |
| **Live latency** | Gateway latency samples collected during this browser session. | The shared shell poll — see 13.3 |

Not reported ≠ healthy: a ring whose source did not report is drawn as a dashed **neutral** track with "Not reported by the bot." No health percentage, security score, trend or history is computed anywhere.

Bot module names are mapped to dashboard names for display only (`Welcomer` → Welcome, `TicketCog` → Tickets, `JoinToCreate` → Join to Create).

### 13.3 Latency sampling

- The topbar indicator already polled `/bot/status` + `/system/health` every 30 s while the tab is visible. That poll moved into one `HealthReadingProvider` in the shell; the topbar, the rail's bot latency, System Core and the sparkline all read it. **No new interval, no new endpoint.** Measured on the preview: 2 status + 2 health requests in 65 s.
- Each successful status reading appends `{at, ms}` to an in-memory buffer bounded to **20 samples** (`appendLatencySample`; ≈ 10 minutes at 30 s). Non-finite or negative values are rejected.
- The buffer lives for the tab session (the provider sits in the dashboard shell), so navigating away from the Overview and back keeps the series; a reload starts a new one. It is labelled "This session · N samples · every 30 s". No backend persistence, no DB table.
- "Check again" also triggers the shared probe (guarded by an in-flight flag, so it never overlaps the scheduled one) and therefore adds a real sample.
- The value is Discord's gateway heartbeat latency, which updates roughly every 40 s, so consecutive samples are often identical; a flat line is the honest reading. The range readout is hidden while min = max.

### 13.4 Accessibility

- Every instrument has a text equivalent next to it (legends with counts and states) and an `aria-label` summary on the graphic.
- System Core and Module state legend items are focusable; focus or hover highlights the matching segment(s) and dims the rest, and an `aria-live` caption names the item ("Logging — loaded"). Segments carry `<title>` tooltips.
- The sparkline is focusable; ←/→ step through samples ("158 ms · 03:12:43"), Esc clears.
- States are never colour-only: non-OK items show "Failed" / "Missing" in text; OK items carry an sr-only state.

### 13.5 Motion (DATA tier, 400 ms)

Ring segments fade in once, staggered (30 ms); a changed state transitions its fill; live numbers settle in when they change; the newest sparkline segment draws in. Hover dimming uses the micro tier. No spinning, pulsing, scanning or ambient loops. Under `prefers-reduced-motion` every one of these is `animation: none` (verified in the browser: `.cls-arc`, `.cls-num`, `.cls-enter` all `none`).

### 13.6 RTL

The page mirrors. Rings stay clockwise from 12 o'clock (a gauge is not text); the sparkline keeps a left-to-right time axis (`dir="ltr"`); the channel strip follows the page direction so it reads in the same order as its legend.

### 13.7 Rail and facts changes

- Rail: segment meters for Required modules and Permissions removed (System Core now draws them); the `6/6` ratio stays with a status dot and the per-module tooltip. Bot latency is live from the shared poll.
- Facts: the "Module state" bar and the "Channels by type" bars are removed — both moved into the deck. Server facts (members, roles, channels, prefix) and access remain.

### 13.8 Self-review (cls-os-ui-review + impeccable)

- First render: rings read as a solid green donut and the core legends were twelve text rows. Fixed: thinner bands with wider gaps so the slanted 30° segment ends show, inner ring at reduced ink, legends compacted to wrapping items with state text only when not OK.
- Rail latency rendered unrounded (`157.93…`) and broke the cell. Fixed (rounded).
- RTL: channel strip was forced LTR while its legend mirrored. Fixed.
- Mobile ring capped at 14 rem so System Core does not consume the first screen.
- Impeccable detector on the changed UI: 0 findings. Legacy-token report: no Overview / instrument / shell file listed.
- No BLOCKER or HIGH remains. POLISH: legend items are ~24 px tall on mobile (informational, not actions).

### 13.9 Tests

`node --test lib/*.test.mjs` — 62 / 62 pass. New: `instruments.test.mjs` (bounded buffer, no mutation, invalid readings, stats, sparkline sizes/flat series/extension, ring segments for 0 / negative / NaN / huge counts, numeric-only paths, invalid segment/tick input, 30° slant, polar origin) and System Core aggregation in `overviewModel.test.mjs`. `tsc --noEmit`, `npm run lint` (pre-existing warnings only), `git diff --check` clean. `npm run build` passes in an isolated copy; `.next/static` contains no env secret value.

Note: the port-3000 dev server is running with a Tailwind config loaded before Task A, so config-only utilities from Task A (e.g. `text-readout`) do not render there; the production build includes them.

### 13.10 Screenshots (outside Git — contain account data)

`C:\Users\aero\AppData\Local\Temp\cls-p16-taskA1\`:

- `taskA1-2560.png`, `taskA1-1440.png` (full page), `taskA1-1024.png`, `taskA1-390.png`
- `taskA1-1440-rtl.png`, `taskA1-1440-reduced-motion.png`
- `taskA1-latency-samples-hover.png` (15 real samples, hover tooltip)
- `taskA1-core-hover.png` (System Core focus state: "Logging — loaded")

**Status: READY FOR OWNER VISUAL APPROVAL.** Task A is not marked owner-approved.