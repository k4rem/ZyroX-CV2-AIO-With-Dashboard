# CLS OS Phase 1.6 — Implementation Plan

Three tasks. Each ships as one reviewed commit (or a short stack) with owner visual approval before the next starts. Direction: `CLS_OS_PHASE_1_6_ART_DIRECTION.md` (AD). Page concepts: `CLS_OS_PHASE_1_6_REFERENCE_PAGES.md` (RP). Baseline `a4ff916`.

## 0. Global rules (all tasks)

**Do not touch:** auth / NextAuth config, RBAC and policy (`bot/api/auth/**`, `lib/access*`), server-derived Root state, session handling, the bot, database schemas, the API contract (no new endpoints in 1.6), snowflake-safe ID handling (IDs stay strings end to end), the landing and auth pages (closed in Phase 1.5), sidebar IA, the hidden legacy routes (Leveling, Verification, Docs).

**Truth rules:** no fabricated values, no placeholders for future data, no "coming soon". A widget whose source does not exist is not rendered. A real zero is drawn.

**Dependencies:** none are installed in 1.6 except, optionally, `cmdk` in Task B (see §6). Anything else needs an explicit owner decision.

**Verification in every task:**
- `npm run lint`, `npx tsc --noEmit`, `npm run build` (then move the production `.next` aside or restart dev on 3000; never leave a dev server serving a production `.next`).
- Existing unit tests + the tests listed per task.
- Impeccable detector once, over the changed files: `.cursor/skills/impeccable/scripts/impeccable.cmd detect --json <files>`.
- Legacy-token gate (introduced in Task A, enforced from Task C): no `slate-*`, `#141B2D`, `rounded-2xl/3xl`, `font-black`, `shadow-xl` or colour icon tiles in touched files (all surfaced routes by the end of Task C).
- Authenticated screenshots at **2560×1440, 1440×900, 1024×768, 390×844**, plus RTL (`cls_dir=rtl`) at 1440 and 390, plus `prefers-reduced-motion: reduce` at 1440 for any page with motion. Screenshots are stored **outside the repo** (they contain account data).
- A `cls-os-ui-review` pass on the captures before handing to the owner.

---

## Task A — Premium visual system + Overview reference implementation

### Scope

1. **Tokens and CSS primitives** (`app/globals.css`, `tailwind.config.ts`)
   - `stage` colour alias (L0), brand heatmap ramp (5 alpha steps), `--cut-sm/md/lg`, motion tier tokens (`--cls-dur-state`, `--cls-dur-data`, stagger variable), entrance keyframes.
   - `.cls-cut` (clip-path + border ring + diagonal, RTL-mirrored), `.cls-signal-edge`, `.cls-rule` (engraved rule) and `.cls-rule-tick` (signal tick), `.cls-enter` (≤ 4 regions, stagger via `--i`), segment styles.
   - Reduced-motion overrides for every new animation.
2. **Components**
   - `components/ui/readout.tsx`: `ReadoutRail`, `Readout` (label / value / unit / status slot).
   - `components/viz/segment-meter.tsx` (role `meter`, `aria-valuenow/max`, text label), `components/viz/state-bar.tsx` (stacked state distribution + legend), `components/viz/category-bar.tsx` (horizontal categorical bars).
   - `components/dashboard/page-header.tsx` v2: engraved rule + signal tick, one-line description, inline-end state readout slot + actions slot, optional tabs. Must stay backward compatible with current call sites.
   - `components/ui/section-rule.tsx` (engraved rule with label + readout).
   - `lib/useReducedMotion.ts`, `lib/useCountUp.ts` (rAF tween, first mount / changed-since-last-visit only).
   - Layout shells: `components/layout/operations-canvas.tsx` (archetype A grid). Shells for B–E are defined in Task B.
3. **Overview rebuild** (RP §1)
   - `components/overview/*`: readout rail, attention queue, grouped module matrix with micro-visuals, facts column (coverage state bar, server composition with channels-by-type bar, access).
   - `lib/loadOverview.ts`: add `getChannels` to the parallel load (channels-by-type), group modules by nav group, **fix J2C state** (derive from `join_channel_id`, not the non-existent `enabled`/`status`), "Configured" → `ok`, record fetch time for "Checked hh:mm:ss".
   - `lib/moduleChecklist.ts`: explicit per-module completeness checklists (J2C, Welcome, Tickets, Logging only) used by segment meters.
   - Activity band slot registry (`lib/overviewWidgets.ts`) with **zero registered widgets** in 1.6; only the mechanism and its "render nothing" test.
4. **DS amendments**: apply AD §11 to `docs/CLS_OS_DESIGN_SYSTEM.md` (the only doc edit allowed in Task A).
5. **Legacy-token gate script**: `dashboard/scripts/check-legacy-tokens.mjs` (report-only in Task A).

### Must not touch

Module pages other than Overview; shell/sidebar behaviour (only the page header component changes); API client behaviour; access/admin pages beyond inheriting the new page header.

### Visual acceptance criteria

- Overview at 1440 shows rail, attention, full module matrix and facts column **above the fold** with current data.
- Exactly one signal edge and one cut object on the page (the rail). Header tick present.
- Non-purple pixels dominate: purple only on the tick, active nav, focus, links and the signal edge.
- Every module row has a factual detail or micro-visual; no row shows only "—" when data exists.
- J2C shows its real state. Tickets "Configured" shows `ok`.
- 2560: three columns, start-aligned, no dead centre island; the module matrix is not stretched beyond ~1200 px rows.
- No new bordered-box-in-bordered-box nesting (attention items are rows, not boxes).
- Nothing renders for the activity band.

### Screenshots required

Overview at the four viewports; RTL 1440 + 390; reduced motion 1440; a before/after pair at 1440. The "module source failed" state is verified by a unit test with a rejected loader promise, not by breaking the live bot.

### Responsive criteria

Per RP §1.4. 1024 single column with the 2-up facts strip; 390 rail collapses to one line + disclosure; no horizontal overflow at any width; touch targets ≥ 40 px at 390.

### Testing

- Unit: `deriveAttention` (existing), `moduleChecklist`, J2C state derivation, coverage counts, channels-by-type grouping, `SegmentMeter` aria output, widget registry renders nothing with no sources, `useCountUp` respects reduced motion.
- Build, lint, typecheck, detector, legacy-token report.

### Model recommendation

**Claude Opus 5 (thinking, high)**: this task sets the system everyone else copies; judgement on restraint matters more than speed. Review by a separate `cls-os-ui-review` pass.

---

## Task B — Module-specific layouts: Welcome + J2C + Custom Roles + shared settings patterns

### Scope

1. **Shared settings patterns**
   - `components/settings/setting-row.tsx`, `setting-group.tsx` (panel of rows with engraved-rule title and readout).
   - `components/settings/save-bar.tsx`: sticky save bar with dirty tracking, Discard, `Ctrl/⌘ S`, navigation guard, saving / error / success states (DS §15.5, AD §7.2).
   - `lib/useDraft.ts`: draft state + dirty diff + reset.
   - `components/ui/combobox.tsx` with `ChannelCombobox` and `RoleCombobox` (type glyph / colour dot, category or position meta, search, full keyboard support; resolves pasted IDs). Fixes the deferred Select keyboard item for these controls.
   - `components/ui/segmented.tsx` (sliding thumb, STATE tier).
   - Layout shells: `workspace-split.tsx` (B), `settings-column.tsx` (C, start-aligned + context rail), `roster.tsx` (D), `flow-lane.tsx` (E).
2. **Discord preview** (`components/discord/`)
   - `DiscordFrame` (fenced Discord palette, overline "Discord preview", desktop/mobile width), `DiscordMessage`, `DiscordEmbed`, `DiscordMention`.
   - `lib/discordMarkdown.ts`: tested subset (bold, italic, underline, strikethrough, inline code, code block, headers `#/##/###`, lists, masked links, spoilers render as plain), no HTML injection (render React nodes, never `dangerouslySetInnerHTML`).
   - `lib/welcomeVariables.ts`: the 13 bot variables resolved from real guild + viewer data; unknown-token detection.
   - Colour normalisation matching `greet2` (`#RRGGBB` or default grey).
3. **Welcome + Join DM** rebuilt per RP §2 (all fields the API and bot already support: embed message/title/description/colour/author/footer/thumbnail/image, auto-delete).
4. **Join to Create** rebuilt per RP §3 (flow lane, three setting rows, enable switch with the "clears channels" confirmation, signal-path arm on completing save).
5. **Custom Roles** rebuilt per RP §4 (gate, roster, real prefix, role position, role ladder rail) — role IDs kept as strings (removes `parseInt`). The Voice role and Vanity roles tabs adopt the roster/settings shells without new features.

### Must not touch

API payload shapes (the forms send exactly the fields they send today, plus the already-supported Welcome fields); Tickets, Antinuke, Automod, Logging (Task C); Overview (Task A); Discord preview must not be reused for Tickets until Task C.

### Visual acceptance criteria

- Welcome at 1440: composer and full preview visible together; preview matches what `greet2` sends for text and embed (compare against a real test send done manually by the owner on the test guild).
- J2C at 1440: flow lane + all settings above the fold; off state legible (≥ 4.5:1 text); no red for off.
- Custom Roles at 1440: gate + 5 rows ≤ 360 px tall; real role colours and positions; no decorative icons or hue tiles.
- No resting purple fill on any of the three pages; purple fill appears only in the save bar when dirty.
- Zero legacy tokens in touched files.

### Screenshots required

Each page at four viewports; Welcome in Text and Embed format; Welcome with an unknown variable and an invalid colour; J2C enabled-complete, enabled-incomplete, off, and the off-confirmation dialog; Custom Roles with none / some / all assigned; save bar dirty, saving, error; RTL 1440 + 390; reduced motion 1440 for J2C (signal path must render statically).

### Responsive criteria

Welcome ≤ 1023 content width switches to Edit | Preview segmented; J2C lane becomes a vertical stepper < 768; roster rows become list items < 768; save bar pinned bottom with 40 px controls on touch.

### Testing

- Unit: markdown subset (including injection attempts), variable resolution + unknown-token detection, colour normalisation (matches `greet2`), `useDraft` dirty/reset, save bar keyboard shortcut and navigation guard, J2C payload when disabling (all three `null`), Custom Roles payload keeps full-precision string IDs (19-digit fixture), combobox keyboard navigation.
- Manual: one real Welcome test (owner joins with an alt or uses the bot's existing test command) compared with the preview.
- Build, lint, typecheck, detector, legacy-token gate on touched files.

### Model recommendation

**Claude Opus 5 (thinking, high)** for the Discord preview, combobox and save-bar primitives (correctness and accessibility). The three page assemblies can be done by **Claude Sonnet 5.5 (high)** once the primitives are merged. Independent visual review after.

---

## Task C — Remaining surfaced module migration + motion / data-viz foundation

### Scope

1. **Migrate by archetype** (no new features):
   - C · Settings column: Bot settings, Automod (rules as setting rows with legible disabled state + "Turn on Automod to change these" line), Auto react.
   - Security foundation: **Antinuke** as a protection-coverage matrix (per-event rows with state glyph, punishment) + whitelist roster; master switch with a high-tier confirmation when disabling (DS §22.3).
   - D · Roster / routing: Logging (category × channel routing table with segment meter in the header), Auto roles, Reaction roles, Invites (tracking + leaderboard table), Access and Platform aligned to the new header/readout.
   - **Tickets pre-V2** per RP §5.1 (setting rows with channel comboboxes, categories table, panel appearance with the Discord preview).
   - Route `loading.tsx` / `error.tsx` skeletons matched to each archetype.
2. **Data-viz foundation** (`components/viz/`): `Sparkline`, `LineArea` (single series), `EventTimeline` track, `Heatmap` (7×24), `SeverityBar`, `Ring`, `ChartFrame` (stage, header readout, loading skeleton, real-zero, error states, "View as table"). Pure SVG, server-renderable, tooltip hydration only.
3. **Motion foundation**: live-row insertion utility (grid-rows + tint flash), status-change crossfade, accordion utility, selection-rail slide helper; all reduced-motion-safe.
4. **Legacy-token gate** switched from report to **fail** for all surfaced routes.
5. Fixtures for viz components live **only** in unit tests (and an optional dev-only preview route guarded by `NODE_ENV !== "production"`, not linked, clearly labelled "Fixture data"). No fixture ever reaches a user-facing route.

### Must not touch

Tickets V2 features (builder, forms, transcripts, analytics); Security Center route; hidden legacy routes; API contracts; Overview and Task B pages except to consume new primitives.

### Visual acceptance criteria

- Every surfaced route matches its archetype; no page uses the old `Title → box → giant Save` composition.
- Zero legacy tokens repository-wide in surfaced routes (gate passes).
- Antinuke and Automod disabled states legible; red appears only for danger.
- Tickets: no raw ID inputs; open count readout in the header; categories as a table.
- Viz components render correctly with fixtures at compact/default heights, in RTL (time axis LTR), and with reduced motion.

### Screenshots required

Every migrated route at 1440 and 390; Antinuke, Logging, Tickets at all four viewports; RTL 1440 for Antinuke, Logging, Tickets; the dev-only viz preview (fixture-labelled) at 1440 including loading, zero, and error states; reduced motion 1440 for the viz preview.

### Responsive criteria

As per archetype; tables become list rows < 768 (DS §19); no horizontal page overflow; matrix views scroll within their panel with a sticky first column at 768–1023.

### Testing

- Unit: viz scales/ticks/paths, heatmap binning, timeline clustering, `ChartFrame` state selection (loading / zero / error / not rendered), live insertion respects reduced motion, Antinuke disable confirmation, Logging routed counts.
- Build, lint, typecheck, detector over all changed files, legacy-token gate (fail mode).
- Final `cls-os-ui-review` over the full surfaced product at four viewports.

### Model recommendation

**Composer 2.5** for the archetype migrations (mechanical, pattern-following, many files), with the viz foundation and Antinuke matrix by **Claude Opus 5 (thinking, high)**, and a final independent Opus review pass before closing Phase 1.6.

---

## 5. Sequencing and gates

1. Task A → owner visual approval of Overview + primitives (this is where the direction is proven or corrected).
2. Task B → owner approval of Welcome, J2C, Custom Roles.
3. Task C → final Phase 1.6 audit (four viewports, RTL, reduced motion) → close.

If the owner rejects Task A's look, stop and revise the AD before Task B; Tasks B and C depend on its primitives.

## 6. Dependency recommendations (none installed now)

| Need | Recommendation | Why | Alternatives considered |
|---|---|---|---|
| Charts (1.6) | **None — hand-rolled SVG** | Patterns in AD §6 are simple; SVG takes tokens directly, renders on the server, zero bundle cost, full visual control | — |
| Charts (Phase 5+, brushing over large series) | **visx** (only the modules used: scale, shape, axis, brush, tooltip) | Unstyled primitives render our SVG language; tree-shakeable; React-native | Recharts (opinionated look, heavier, harder to make "native"); Chart.js (canvas, styling via config, weak accessibility); ECharts (very large); uPlot (tiny, fast canvas time series, awkward React/styling — keep as fallback if series exceed ~10k points); Tremor / Nivo (template look) |
| Motion | **None — CSS + small hooks** | All tiers are transform/opacity/stroke; rAF tween hook for numbers | Framer Motion / `motion` (defer to Tickets V2 if drag/layout animation needs it; evaluate `@dnd-kit` separately for DnD) |
| Combobox (Task B) | **`cmdk`** (optional) | Small, accessible, keyboard-complete command/list primitive that composes with the existing Radix Popover; avoids rebuilding listbox keyboard logic | Hand-rolled on Radix Popover (acceptable if the owner prefers zero deps; costs more testing) |
| Discord markdown | **None — tested subset parser** | Only a subset is needed; must never emit raw HTML | Evaluate a maintained parser in Tickets V2 when Components V2 fidelity matters |

Version and bundle sizes must be measured at install time (`next build` output) before any dependency is accepted.

## 7. Known issues to fix inside the tasks (found during this direction pass)

| Issue | Where | Task |
|---|---|---|
| Join to Create always shows "Off" on Overview (reads non-existent `enabled`/`status`) | `lib/loadOverview.ts` | A |
| Tickets "Configured" semantics (must be `ok`, never warning) | `lib/loadOverview.ts` / status mapping | A |
| Role IDs `parseInt()`ed (precision loss for 19-digit snowflakes) | `components/dashboard/customroles-form.tsx` L85, L117 | B |
| Welcome default template writes a colour without `#`, which the bot ignores | `components/dashboard/welcome-form.tsx` | B |
| J2C "off" silently clears all three channels | `components/dashboard/j2c-form.tsx` | B (confirmation + copy) |
| Duplicate document title "CLS OS · CLS OS" | route metadata | A (page header work) |

## 8. Final refinement (Phase 1.6 closed)

The authenticated visual QA verdict on Task C was **REFINEMENT REQUIRED**. This pass closed that gap. Phase 2 was not started. Overview, Welcome, and Join to Create were not redesigned.

Pages changed:

- Logging is an event routing table: category, enabled, destination, routing. The readout is the real routed count (`0 of 6` on the preview guild). Enabled with no destination is incomplete. Disabled is off. Toggles and channel changes still save immediately.
- Antinuke is a protection status strip, the existing master switch, and a whitelist table. No score, incidents, or coverage percentage. Save uses the shared dirty bar and stays hidden while the switch is clean. Whitelist add and remove still apply immediately and send the saved switch, not an unsaved draft.
- Bot settings, auto roles, reaction roles, vanity roles, voice role, and auto react sit in a compact settings instrument. Empty lists name the real add action. Voice role still saves `role_id` and `enabled` together.
- Custom roles heading is "Custom roles".
- English help copy uses `dir="auto"`. Technical tokens stay `dir="ltr"`. The page direction is unchanged.

Safe deferrals:

- Welcome and Join to Create keep their approved layouts. The unused area under a short form at wide resolutions is the real content height, not missing panels.
- Antinuke still has no per-action coverage in the API.
- Hidden Verification and Leveling, and unused legacy components, stay outside the strict surfaced-page gate.
- No reduced-motion screenshot: this pass added no motion.

Screenshots: `C:\Users\aero\Desktop\CLS-OS-PHASE-1-6-QA\refinement`.

Phase 1.6 status: **CLOSED**.
