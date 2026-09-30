# CLS OS Phase 1.6 — Reference Pages

Visual concepts for five reference pages plus the Security direction. Language, tokens and motion come from `CLS_OS_PHASE_1_6_ART_DIRECTION.md` (AD). Every element listed as **Now** is backed by an existing API field; **Future** items are named with the phase/endpoint that unlocks them and are **not** rendered until then (no placeholders, no "coming soon").

Captured baseline (`a4ff916`, 1440 unless noted): Overview (also 390, 2560), Custom Roles, Tickets, Welcome (also 390, 2560), Join to Create (also 390, 2560). Captures are stored outside the repo (owner/avatar data).

Legend used in the diagrams: `▰▱` segment meter · `◆◇` configured / missing flow node · `●○` status dot · `⟋` 30° cut corner · `░` stage (L0 `#040306`) · `━` signal (brand).

---

## 0. Screenshot critique

### 0.1 Overview (captured 390 / 1440 / 2560)

| Question | Finding |
|---|---|
| Generic | Title + paragraph + table + two small boxes: the default admin template. The status line is styled like a breadcrumb and is easy to miss. |
| Legacy | None (rebuilt in 1.5). |
| Blue/navy | None. The problem is monotony, not hue. |
| Hierarchy | "Needs attention" (the most important thing) has the same weight as the Server box; the page has no focal element. |
| Should be denser | Modules table: 40 px rows of "Off · — · Configure" × 8; the Detail column is empty for 7 of 8 rows. "Configure" repeated 8 times. |
| Should be more visual | 6/6 required modules, the module state distribution, channel composition, attention severity: all real, all printed as text. |
| Keep simple | Needs-attention wording, truthful empty states, no fake KPIs. |
| Module-specific | Per-module rows need a factual micro-visual (routed categories, channel tokens, flow completeness) instead of "—". |
| 2560 | Content is a 1680 px island with wide dead gutters; right column 280 px; the page looks unfinished. |
| Bug found | `loadOverview` reads `j2c.enabled ?? j2c.status`, fields the J2C API does not return, so **Join to Create always shows "Off"** even when configured. Fix in Task A (derive from `join_channel_id`). |

### 0.2 Custom Roles

| Question | Finding |
|---|---|
| Generic | Five identical cards in a 2-column grid + a lone fifth card: the "card grid everywhere" pattern. |
| Legacy | Full ZyroX skin: `#141B2D` rounded-3xl container, `slate-900/40` cards, `font-black` title, gradient side card with watermark crown. |
| Blue/navy | The whole container and every card; the "Command Usage" card is blue-tinted with a blue heading. |
| Hierarchy | The permission gate ("Required Permission Role") looks like a sixth preset; it is actually the rule that governs all of them. |
| Should be denser | ~680 px of height for 6 selects that all say "none". Target: 6 rows ≈ 300 px. |
| Should be more visual | The real role colour and hierarchy position are available (`roles` API returns `color`, `position`) and not shown. |
| Keep simple | One role per preset; no drag and drop. |
| Module-specific | This is a **roster** of command → role bindings; it should look like Discord role management (swatch, name, position), with the command token as the identity. |
| Semantics | Decorative icons with hue (blue shield, pink heart, yellow crown, green star) imply meaning that does not exist. |
| Bug found | `customroles-form.tsx` still `parseInt()`s role IDs (lines 85, 117); 19-digit snowflakes lose precision. Must be fixed when Task B rebuilds the page (keep IDs as strings end to end). |

### 0.3 Tickets (pre-V2)

| Question | Finding |
|---|---|
| Generic | "Global Configuration" section with an icon tile header; a form of raw inputs. |
| Legacy | Icon tile, uppercase tracked field labels, large H2. Colours already migrated. |
| Blue/navy | None. |
| Hierarchy | The one operational fact (1 open ticket) sits in an unlabeled footer strip below everything, next to an orphan "CLS TICKETS" caption. |
| Should be denser | Category cards (2 × full-width halves for two rows of data) → table rows. |
| Should be more visual | Panel appearance exists in config (title, description, colour, image) but is only reachable through a dialog; no preview. |
| Keep simple | Do not start the V2 builder here. |
| Module-specific | Channel/category fields are raw ID text inputs while the channels API exists: replace with channel comboboxes. |

### 0.4 Welcome (captured 390 / 1440 / 2560)

| Question | Finding |
|---|---|
| Generic | Two selects and a Save button in a box; at 1440 about 70 % of the viewport is empty. |
| Legacy | None visually; functionally the page exposes 3 of the 12 fields the bot renders. |
| Blue/navy | None. |
| Hierarchy | The thing being configured (a Discord message) is never shown. |
| Should be denser | The variables list uses a whole column for five lines; it should be an insert menu with resolved values. |
| Should be more visual | This page is *about* a message: it needs a live Discord preview. |
| Keep simple | Two formats only (text, embed), as the bot supports. |
| Module-specific | Discord message workspace (composer + stage). |
| Capability gap (real) | The bot's `greet2` renders embed `message`, `title`, `description`, `color`, `author_name/icon`, `footer_text/icon`, `thumbnail`, `image`, plus `auto_delete_duration`, and supports 13 variables. The API schema accepts all of them. The UI exposes title, description and colour only. |
| Fidelity trap | `greet2` only honours colours that start with `#` (or ints); the current "Apply default template" writes `2f3136` (no `#`), which the bot silently ignores. The preview must replicate this and the composer must normalise/validate it. |

### 0.5 Join to Create (captured 390 / 1440 / 2560)

| Question | Finding |
|---|---|
| Generic | Status card + three equal cards + a giant Save: an infographic of a form. |
| Legacy | Full ZyroX skin (navy container, icon tiles, pill status, oversized switch recoloured green, gradient "How it works" card). |
| Blue/navy | Container and all three cards; blue icon tile on "Control Panel Channel". |
| Hierarchy | Disabled state greys the three cards to near-illegibility (≈1.5:1), so an off module hides its own explanation. |
| Semantics | "Inactive" uses a **red** power icon and red dot: off is not danger. |
| Should be denser | At 390 "System Status" wraps to four lines beside a pill and a scaled switch; ~1430 px tall for three selects. |
| Should be more visual | The module *is* a flow (join → temporary VC → control panel → cleanup); the page never shows it. |
| Keep simple | Three settings. |
| Behaviour to surface honestly | Turning the switch off saves all three channel IDs as `null`; the configuration is **cleared**, not paused. The new design must say so and confirm. |

---

## 1. Overview (Archetype A · Operations canvas)

### 1.1 Concept

An **operations deck**: a readout rail on top (the page's single focal instrument), a ranked attention queue, a module matrix with factual micro-visuals, and a narrow facts column. A reserved **activity band** below grows automatically as later phases ship data sources.

### 1.2 Regions and data

| Region | Now (real source) | Future (renders only when the source exists) |
|---|---|---|
| **Readout rail** (`cut-md`, signal edge; the only one on the page) | Server identity (icon, name), Bot status + latency (`/bot/status`), Required modules `▰▰▰▰▰▰ 6/6` (`/system/health.modules`), Permissions (ok / "2 modules missing" warn, from `permissions.missing_by_module`), Postgres, Scheduler, "Checked 14:02:31" (fetch time) | Incident posture (Phase 7), Backup health (backup status API) |
| **Needs attention** (panel) | `deriveAttention` items, ranked critical → warning → info; each row: severity glyph, sentence, module token, action button naming the destination ("Open Antinuke") | Security incidents (Phase 7), ticket SLA breaches (Phase 4) |
| **Module matrix** (outline table on canvas, grouped by nav group) | Per module: state glyph + label, factual micro-visual (see 1.3), configure link on row hover/focus (always visible on touch) | "Last change" column (audit read API) |
| **Coverage** (facts column) | Stacked state bar of the surfaced modules: On / Partial / Off / Unavailable with counts | — |
| **Server composition** (facts column) | Members, roles, channels (`/guilds/{id}`) + channels-by-type bar (text / voice / category / other) from `/guilds/{id}/channels` | Member growth sparkline (needs member history, Phase 5) |
| **Access** (facts column) | Your access label; root: active grants on this server | Recent dashboard sessions (Phase 1 session store read API) |
| **Activity band** | Not rendered | Tickets opened/closed 7 d area + open queue count (Phase 4); Security events severity timeline (Phase 2/7); Log volume heatmap 7×24 (Phase 5); Recent events feed (audit read API) |

Activity-band rule: each widget is registered with a `source` key. The loader asks the API which sources exist (capability flags already implied by the endpoints returning 200 vs 404). Absent source → widget not rendered, and the band collapses to nothing. No empty frames.

### 1.3 Module matrix micro-visuals (all from existing endpoints)

| Module | State rule | Micro-visual / detail |
|---|---|---|
| Antinuke | `status` on/off | `N whitelisted` + protections armed segments when per-event flags exist in config |
| Automod | `enabled` | `N rules` + punishment summary (e.g. "timeout ×3") |
| Tickets | configured = panel channel or ≥ 1 category; `warn` when a category lacks staff | `# panel-channel` token · `2 categories` · `1 open` |
| Welcome | configured = channel + content | `# welcome` token · `Embed` / `Text` |
| Join to Create | configured = `join_channel_id` set (**fixes the always-Off bug**) | flow glyph `◆─◆─◇─◆` (join / temp / control / cleanup) |
| Logging | on / partial / off (existing) | `▰▰▰▰▰▱▱▱▱ 5/9 routed` |
| Auto role | humans + bots > 0 | `2 human · 1 bot` role swatches (role colours) |
| Reaction roles | panels > 0 | `N panels` |

"Configured" renders `ok`, "Partial" `warn`, "Off / not set up" `neutral`, "Unavailable" `neutral` + reason on hover.

### 1.4 Composition by width

**2560 × 1440** (content ≈ 2248 px; three columns; fluid, start-aligned, no max width)

```
Overview                                                         Checked 14:02:31
━━─────────────────────────────────────────────────────────────────────────────────────
┌ READOUT RAIL ─────────────────────────────────────────────────────────────────────⟋┐
│ (C) cls-backup │ BOT ● Online 158 ms │ MODULES ▰▰▰▰▰▰ 6/6 │ PERMISSIONS ● OK │ POSTGRES ● │ SCHEDULER ● │
└──────────────────────────────────────────────────────────────────────────────────────┘
┌ Needs attention ─────────── (640) ┐ ┌ Modules ─────────────────────────── (fluid) ┐ ┌ Coverage ──── (400) ┐
│ ▲ Antinuke is off  [Open Antinuke]│ │ SECURITY                                       │ │ ████▒▒░░░░░ 8        │
│                                    │ │  Antinuke    ○ Off      0 whitelisted          │ │ 1 on · 0 partial ·   │
│ (activity band widgets stack here  │ │ MODERATION                                     │ │ 7 off · 0 unavailable│
│  in this column when they exist)   │ │  Automod     ○ Off      —                      │ ├ Server ──────────────┤
│                                    │ │  Logging     ○ Off      ▱▱▱▱▱▱▱▱▱ 0/9 routed   │ │ 2 members 12 roles   │
│                                    │ │ TICKETS                                        │ │ 58 channels          │
│                                    │ │  Tickets     ● Configured # panel · 2 cat · 1 open│ │ text ███████ 41      │
│                                    │ │ ENGAGEMENT                                     │ │ voice ██ 9 · cat █ 8 │
│                                    │ │  Welcome · J2C · Auto role · Reaction roles …  │ ├ Your access ─────────┤
└────────────────────────────────────┘ └────────────────────────────────────────────────┘ │ Root owner · 0 grants│
                                                                                         └──────────────────────┘
[Activity band — only when sources exist: 3-up row of chart panels (Tickets 7 d · Security timeline · Log heatmap)]
```

**1440 × 900** (content ≈ 1144 px; two columns `1fr 340px`)

```
Overview ━━──────────────────────────────────────────────── Checked 14:02:31
┌ READOUT RAIL (2 lines max) ───────────────────────────────────────────⟋┐
└────────────────────────────────────────────────────────────────────────┘
┌ Needs attention ─────────────────────────┐ ┌ Coverage ────────── 340 ┐
│ ▲ Antinuke is off          [Open Antinuke]│ │ stacked state bar       │
└───────────────────────────────────────────┘ ├ Server ─────────────────┤
┌ Modules (grouped matrix, 36 px rows) ────┐ │ counts + channel bar     │
│ …                                          │ ├ Your access ────────────┤
└───────────────────────────────────────────┘ └─────────────────────────┘
[Activity band: 2-up chart panels when present]
```

Everything above fits in 900 px for the current data.

**1024 × 768** (sidebar expanded: content ≈ 728 px; single column; rail mode: ≈ 920 px, same layout)

```
Overview ━━───────────────────────
┌ READOUT RAIL (wraps to 2 rows) ⟋┐
└──────────────────────────────────┘
┌ Needs attention ─────────────────┐
┌ Coverage ───────┐┌ Server ───────┐   ← 2-up strip; Access joins Server panel
┌ Modules matrix (Detail column kept; micro-visual shrinks to text) ┐
[Activity band: 1-up]
```

**390 × 844** (single column; 16 px gutter)

```
Overview
┌ cls-backup ● Online 158 ms   ⌄ ┐   ← rail collapses to 1 line + disclosure for the rest
┌ Needs attention (list, 44 px) ─┐
┌ Modules: list rows             ┐   name + state on line 1; micro-visual/detail on line 2
┌ Coverage bar + Server 2×2 grid ┐
```

### 1.5 Motion

Hard navigation: rail → attention → matrix → facts enter (≤ 4 regions, AD §7.2). Segment meter fills once (DATA). Latency value swaps live (no tween). Resolved attention item flashes `ok` and collapses. Nothing loops except the live bot dot (existing).

---

## 2. Welcome (Archetype B · Workspace split)

### 2.1 Concept

A **Discord message workspace**: composer on the inline-start, a live Discord preview on a sunk stage on the inline-end. The page immediately reads as "I am writing the message my server sends". Tabs "Channel message | Direct message" (existing routes `/welcome`, `/joindm`) share the composition.

### 2.2 Composer (now, all fields supported by API + bot)

1. **Delivery strip** (readout, top of composer): `Sends to # welcome when a member joins` · state (`ok` Active / `neutral` Not sending: pick a channel and write a message) · `Deletes after 30 s` when set.
2. **Channel** — channel combobox (text + announcement channels, `#` glyph, category in `fg-3`).
3. **Format** — segmented control `Text | Embed` (replaces the select).
4. **Text format**: message textarea with a 2000-character counter and an "Insert variable" menu.
5. **Embed format**, grouped under engraved rules and collapsed by default except Content:
   - Content: message above embed (`embed_data.message`), title, description (4096 counter)
   - Appearance: colour swatch + hex (normalised to `#RRGGBB`; invalid → field error "Use a # colour, e.g. #6025E2 — Discord will otherwise use the default grey")
   - Author: name, icon URL / `{user_avatar}` / `{server_icon}`
   - Media: thumbnail, image (URL or the two image variables)
   - Footer: text, icon
6. **Auto-delete** — number input with "seconds" suffix, empty = keep.
7. Template action: "Start from default" (secondary, ghost row at the end; applies the CLS default with a **valid** `#` colour).

Variables menu: all 13 bot variables (`{user}`, `{user_avatar}`, `{user_name}`, `{user_id}`, `{user_nick}`, `{user_joindate}`, `{user_createdate}`, `{server_name}`, `{server_id}`, `{server_membercount}`, `{server_icon}`, `{timestamp}`), each shown with its **resolved preview value** (mono). Unknown `{tokens}` in text get a dashed `warn` underline in the preview and a composer hint.

Save: sticky save bar when dirty (the page's only purple fill).

### 2.3 Stage (preview)

- L0 stage fills the remaining width; a Discord frame (Discord dark palette, fenced, overline "Discord preview") max 720 px, centred **within the stage**.
- Frame content: channel header `# welcome`; a message by the bot (real bot name and avatar from `/bot/status`), `APP` tag, "Today at 14:02"; the rendered text/embed.
- **Variables resolve with real data**: server name, icon, member count from the guild; the member is **the signed-in viewer** ("Previewing as you" caption), so no fake user appears.
- Embed rendered faithfully: 4 px left colour bar (actual colour; default grey when invalid, matching the bot), author row, title, description with Discord markdown subset, thumbnail, image, footer + timestamp (bot always sets a timestamp).
- Width toggle `Desktop | Mobile` (520 / 360 px message column).
- Updates on every keystroke with no animation (AD §7.2).

### 2.4 Future (planned, **not** built in 1.6)

"Send test message" (needs a test-send endpoint), Components V2 layouts, per-channel variants, join image cards. Shown nowhere until the endpoint exists.

### 2.5 Composition by width

```
2560:  [Header + tabs]
       ┌ Composer 560 ───────┐ ░░░░░░░░░░░░░░░ Stage (fluid) ░░░░░░░░░░░░░░░░░
       │ delivery strip       │ ░        ┌ Discord preview (720) ────────┐    ░
       │ channel · format     │ ░        │ # welcome                      │    ░
       │ fields …             │ ░        │ (bot) CLS  APP  Today at 14:02 │    ░
       └──────────────────────┘ ░        │ ▌ Welcome to cls-backup!       │    ░
                                ░        └────────────────────────────────┘    ░
1440:  Composer 480 | Stage fluid (≈ 640); both fully visible above the fold.
1024:  Composer 1fr | Stage 1fr at ≥ 900 content width; otherwise segmented [Edit | Preview] at the top, stage becomes a tab.
390:   [Edit | Preview] segmented control; preview is full-width Mobile mode; save bar pinned bottom (40 px controls).
```

---

## 3. Join to Create (Archetype E · Flow + config)

### 3.1 Concept

Show the real mechanism as a compact **flow lane**, then three setting rows. The lane is the page's instrument; the rows are its knobs.

```
Join to Create                          ● Active            [●━ Enabled]
━━────────────────────────────────────────────────────────────────────
░░ FLOW ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░⟋
░ ◆ JOIN CHANNEL      ━━━ ◆ TEMPORARY VC        ━━━ ◆ CONTROL PANEL    ━━━ ◆ CLEANUP        ░
░ 🔊 Join to create        Created in Gaming         # vc-control          Deleted when the  ░
░                          (or same category)        12 controls ⌄         last member leaves░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
SETTINGS ───────────────────────────────────────────────── 2 of 2 required set
 Join channel        Members join this voice channel to get their own.   [🔊 Join to create ⌄]
 Control channel     Text channel where owners manage their channel.     [# vc-control ⌄]
 Category            Where new channels are created.                     [Automatic (same as join) ⌄]
```

### 3.2 Details

- **Nodes** (`cut-sm`-free, 1 px outline, 44 px tall): configured `◆` `fg-1` name + channel-type glyph; missing `◇` dashed outline + `warn` "Pick a voice channel"; automatic `neutral` "Automatic". Clicking a node selects (rail slides) and focuses its setting row; the row gets the same selection rail — the page teaches the mapping between flow and settings.
- **Connectors**: `line-strong` between configured nodes; dashed `line` where a node is missing; the **signal path** (`brand-400`, 1 px) runs the full lane only when enabled and both required channels are set. After a save that completes the flow it draws once (AD §7.2, the page's single moment).
- **Control panel node** expands (accordion) to list the 12 real controls the bot posts: Limit, Privacy, Thread, Untrust, Invite, Kick, Region, Unblock, Claim, Transfer, Delete, Block — as small neutral text tokens. This replaces the "How it works" marketing card with fact.
- **Cleanup node**: static text, no setting (the bot behaviour).
- **Enable switch** in the header. Because disabling saves all three IDs as `null`, turning it off opens a medium-tier confirmation: "Turn off Join to Create? This clears the join, control and category channels." Off state: lane renders at full legibility with nodes `neutral` and the caption "Off — members joining voice channels get nothing."
- Header state: `ok` Active / `warn` Incomplete (one required missing) / `neutral` Off. Never red.
- Save via sticky save bar.
- **Future**: live temporary-channel count and list (needs a read endpoint over `private_channels`), "Repost control panel" action (needs endpoint). Not rendered in 1.6.

### 3.3 Width behaviour

2560/1440: lane fluid to 1200 px, start-aligned; settings column 760 below, context rail (320) at ≥ 1440 holds only permission prerequisites from permission health (Manage Channels, Move Members) when missing. 1024: lane 4 nodes in one row (labels wrap to 2 lines). 390: lane becomes a vertical stepper (nodes stacked, connectors vertical), settings rows stack control under text.

---

## 4. Custom Roles (Archetype D · Roster)

### 4.1 Concept

A **command roster**: each row binds a prefix command to a Discord role, rendered like Discord role management. The permission gate sits above the roster as the rule that governs it.

```
Roles    [Custom roles | Voice role | Vanity roles]
━━───────────────────────────────────────────────────────────── 3 of 5 assigned
GATE ─────────────────────────────────────────────────────────────────────────
 Who can use these commands       ● Moderators  (#4 of 40)           [Change ⌄]
 Members without this role can't run the commands below. Unset: admins only.
ROSTER ───────────────────────────────────────────────────────────────────────
 COMMAND       ROLE                         POSITION     STATE
 ▌ .staff      ● Staff                      #6 of 40     Assigned        ⋯
   .girl       ◌ Not set                    —            Not set         ⋯
   .vip        ● VIP                        #9 of 40     Assigned        ⋯
   .guest      ◌ Not set                    —            Not set         ⋯
   .frnd       ● Friend                     #14 of 40    Assigned        ⋯
 The bot's role must be above every assigned role to hand them out.
```

### 4.2 Details

- **Command token**: mono, uses the guild's **real prefix** from `/prefix` (e.g. `.staff`, `!staff`). Tooltip: "Adds or removes the role for the mentioned member."
- **Role cell**: role colour dot (Discord colour; `#000000`/0 = default → `fg-3` hollow dot) + role name in `fg-1` (never coloured text: contrast). Click → role combobox popover (search, colour dots, position, `@everyone` and managed roles excluded).
- **Position**: `#6 of 40` from `position` (highest = #1), tabular. Gives hierarchy context without drag and drop.
- **State**: Assigned (`ok` label) / Not set (`neutral`). Row menu: Change role, Clear.
- Rows 44 px, one panel, no cards, no decorative preset icons.
- **Prerequisite line**: static fact line under the roster. **Future**: a pass/fail check "Bot role #3 is above all assigned roles ✔" once the API exposes the bot's top role position (small read addition; not in 1.6).
- **Context rail (≥ 1440)**: role ladder mini-visual — the assigned roles and the gate role drawn as a vertical list ordered by position with their colour dots, so hierarchy is visible at a glance. Real data only.
- IDs stay strings end to end (fixes the `parseInt` precision bug).
- Save via sticky save bar.

### 4.3 Width behaviour

2560/1440: roster fluid to 1100, start-aligned, rail 320. 1024: rail folds below. 390: rows become list items (command + state line 1, role + position line 2); gate stays on top.

---

## 5. Tickets (pre-V2 treatment)

Tickets V2 (Phase 4) is the flagship builder (AD §9 archetype F; DS §18). Phase 1.6 only makes the current page coherent and points in that direction.

### 5.1 Change now (Task C)

| Area | Now |
|---|---|
| Header | Module header; inline-end readout `1 open · 2 categories` (real); "Panels are published from Discord with the ticket command." notice kept. |
| Delivery settings | Setting rows: Panel channel, Logging channel (channel comboboxes), Closed-ticket category (category combobox), Panel type (segmented `Dropdown | Buttons`). Replaces raw ID text inputs and the icon-tile header. |
| Categories | Compact table: name, emoji, staff roles (role swatches), description truncate, row menu (Edit, Delete medium-tier confirm). "Add category" secondary in the table toolbar. Duplicates are shown as data (no dedupe). |
| Panel appearance | Workspace-split lite: the existing embed fields (title, description, colour, image, thumbnail) in a composer + a Discord preview of the panel embed with its buttons/dropdown rendered from categories. Reuses the Welcome preview renderer. |
| Staff | Global staff roles remain hidden (Phase 1.5 decision). |
| Save | Sticky save bar. |

### 5.2 Waits for Tickets V2

Palette / canvas / inspector builder, drag and drop, form (modal) builder, Components V2, live tickets table, transcripts, staff management, SLA and analytics charts (tickets opened/closed, first response, by category) — the analytics use AD §6 patterns once Phase 4 records ticket events.

---

## 6. Security direction (Phase 7 target)

Full art direction in AD §10. Composition sketch at 1440:

```
┌ POSTURE (cut-lg, signal edge, lattice) ───────────────────────────────────────────⟋┐
│ [perimeter]  SECURE        Incident Mode: off   Dashboard lock: off   Events current 14:02:31 │
└──────────────────────────────────────────────────────────────────────────────────────┘
│ OPEN ● 0 critical · 1 high · 2 medium │ PROTECTIONS ▰▰▰▰▱▱ 4/6 │ QUARANTINED 0 │ LAST EVENT 3 min │
┌ Incident rail (table) ───────────────────────────────────────────────────────────────┐
┌ Event stream (60 %) ───────────────────────┐ ┌ Protection coverage matrix (40 %) ─────┐
┌ Timeline 24 h (severity-stacked histogram on stage, incident markers, brush) ────────┐
┌ Actor × action matrix (sev heatmap) ───────┐ ┌ Permission change history (diff rows) ─┐
```

Phase 1.6 builds only the primitives (severity chip, segment meter, timeline track, matrix cell) and rebuilds the Antinuke page as a protection-coverage matrix plus a whitelist roster (Task C). No fake radar, globe, world map or counters, now or later.
