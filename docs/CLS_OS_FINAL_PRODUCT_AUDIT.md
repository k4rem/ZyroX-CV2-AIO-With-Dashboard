# CLS OS — Final Deep Product / Competitive Audit

Date: 2026-10-02
Scope: current checked-out state (`1623b7c complete Tickets advanced product recovery`) plus the running local preview (dashboard `:3000`, bot + API `:8000`).
Mode: audit only. No product code, migrations, or commits were changed. This file is the only intended repository change.

Evidence labels used throughout:

- **Verified (code)**: traced in source with file and line references.
- **Verified (live data)**: confirmed against the running preview, its logs, or its local databases (read-only).
- **Verified (visual)**: confirmed by rendering the page in a browser.
- **Inferred**: a reasonable product consequence of verified code, not observed live.

Severity model: **P0** release blocker, **P1** must fix before serious production, **P2** important polish / differentiation, **P3** later.
Type labels: BUG, RUNTIME MISMATCH, MISSING FEATURE, UX, VISUAL, SECURITY, DATA, PERFORMANCE, TECH DEBT, DIFFERENTIATOR.

---

## 1. Executive verdict

**CLS OS is not production-ready.** The V2 platform underneath it (Postgres stores, Logging V2, Tickets V2, Role Menus, Role Automation, Messages, Config Transfer, Growth V2) is genuinely solid, and several recovered modules are competitive. But the product still contains visible features that do nothing, one security boundary that is silently broken, two features that become dangerous the moment someone enables them, and three flagship surfaces (Automod, Protection, Commands) that are far below the professional bar.

### Direct answers

**Is CLS OS actually production-ready?** No. Five P0 release blockers and 29 P1 issues remain.

**The 5 areas furthest from professional quality**

1. **Automod.** Every rule configured from the dashboard is ignored at runtime (confirmed root cause, Section 2). Even when it works, it is a 2019-era single-punishment filter with hardcoded thresholds, no strike system, no per-rule exclusions, and no violation history.
2. **Security Center / Protection.** A developer console stacked into one long page: raw engine IDs (`aggregate.destructive`, `DEVELOPMENT_PROPOSAL`, `eligible`), terminal-style event lines, punishment selectors that never execute, a Release button that always fails, and no way to manage trusted actors.
3. **Commands.** A ~500-row inventory of every registered bot command (including bot-owner and system commands), ~116 with no description, no module/subcommand structure, no bulk control, and no explanation of what the page is for.
4. **Legacy split-brain.** 119 cogs load; many legacy cogs and legacy API routes still read or write SQLite stores that V2 no longer reads, and some still act on member joins (FastGreet). The fat legacy `bot/api/routes/guilds.py` is still mounted.
5. **Verification / Vanity Roles (hidden dangers).** Verification V2 can lock every new member out because nothing posts the verify button. Vanity Roles mass-assigns a role to the entire server based on a public invite check while the UI promises status-text matching.

**Modules that are already strong and should NOT be rewritten (KEEP / POLISH ONLY)**

- Messages / Embed Builder
- Tickets V2 (queue, panels, categories, settings, transcripts, advanced)
- Role Menus
- Role Automation (V2 core)
- Welcome / Welcome DM / Goodbye (V2 core; retire legacy writers)
- Auto React V2
- Invites V2
- Giveaways V2 (core flow)
- Config Transfer
- Join-to-Create
- Logging V2 architecture (store, routing, retention, cursor pagination, render) — extend, do not rebuild
- App shell / navigation / guild switcher
- Security backend architecture (observe/enforce lock, incidents, attribution, quarantine model) — rebuild the UI, not the safety model

**Visible features that are misleading or non-functional**

| Feature | What the UI implies | What actually happens |
|---|---|---|
| Automod rules (all five) | Rule on + punishment selected = enforced | Runtime never matches dashboard keys; nothing fires |
| Automod "Delete message" / "Warn user" | Selectable actions | Not implemented in any automod cog |
| Automod toggle off | Rule disabled | DB row is never deleted; rule state drifts |
| Overview → Automod "On · N punishment rules configured" | Protection active | Inert |
| Overview → Welcome | Incomplete / unavailable | Reads a legacy endpoint that returns HTTP 500; V2 welcome actually works |
| Phishing protection action (Delete / Timeout / Kick / Ban) | Phishing handled | Only recorded; phishing link stays visible |
| Bot Trap | "Trap" | Only untrusted bots/webhooks recorded; humans (incl. compromised accounts) ignored; bans hardcoded off |
| Quarantine "Release" | Release a member | Always HTTP 409 |
| Trusted actors | Dashboard-managed trust | Read-only list; no grant/revoke route |
| Verification "Where the verify button is posted" | Button published | No code posts the button; enabling locks new members out |
| Vanity Roles "status contains the vanity text" | Per-member status match | Checks a public invite code, then adds/removes the role on every member |
| InVC role "Enabled" switch | Off = stopped | Runtime never reads `enabled` |
| Giveaways "Scheduled" tab | Scheduling exists | Create form never sends `starts_at` |
| Commands "Aliases / Cooldown" in inspector | Configurable | Display only |
| Logging "Exclusions" | Exclude channels/roles/users | Applied to message events only |

**Competitor capabilities we are clearly missing**

- Automod: per-rule thresholds, compound actions, per-rule scope, strike escalation with expiry, violation history (ProBot, Dyno, MEE6, Carl-bot, YAGPDB, Wick).
- Security: per-detector observe/enforce, honeypot for compromised human accounts, temporary scoped whitelists, Undo, raid/join gate, panic/lockdown (Wick, Security Bot, SCNX, RaidProtect).
- Logging: thread, invite, emoji/sticker, webhook, scheduled event, voice mute/deafen, moderator move/disconnect, AutoMod execution, moderation-command coverage; per-event color (ProBot, Carl-bot, Wick, Sapphire).
- Commands: module toggles, per-command cooldown/visibility/auto-delete, cascading overrides, effective-access checker (ProBot, MEE6, YAGPDB, Carl-bot).
- Tickets: CSAT rating, per-staff analytics (TicketsBot).
- Messages: Components V2 and scheduling (Discohook, YAGPDB).

**Where CLS can realistically become better than existing bots**

1. **Truthful operations.** Every competitor has silent failures: hidden staff immunity, escalations that silently don't count, logs without actors. CLS can show, for every rule and every event: *will it work* (permissions + hierarchy preflight), *did it work* (per-action result), and *how sure are we* (attribution confidence). CLS already has the confidence field and the incident model; competitors do not.
2. **Observe-first security that graduates safely.** CLS's locked OBSERVE architecture is unusual and defensible. Turned into a product ("what would have happened" replay, per-detector graduation to ENFORCE, Undo), it beats Wick's "log action" and SCNX's "alert only".
3. **One message system everywhere.** CLS already shares one composer across Messages, Welcome, Tickets and Role Menus. Extending it to Components V2 and to automod/security notifications is a real differentiator; most bots have five different editors.
4. **Searchable, paginated, attributed history in the dashboard.** Most competitors only post into Discord channels.
5. **Policy-safe growth.** Invite tracking for analytics and raid forensics, without invite rewards (which Discord policy prohibits).

**What should be fixed first**

1. Phase F0 (safety and truth, days not weeks): allowlist auto-leave cog, Verification lockout guard, Vanity Roles guard, Automod vocabulary hotfix, Overview truth.
2. Phase F1: shared primitives (permission/hierarchy health, save semantics, details drawer, paginated table, label registry, status tokens) and legacy containment.
3. Phase F2: Automod V2 as a full product, alone in its sprint.
4. Then Security Center (F3) and Logging completion (F4) in parallel, then Commands (F5).

---

## 2. Release blockers (P0)

### P0-01 — Automod: no dashboard-configured rule is ever enforced

Labels: RUNTIME MISMATCH, BUG. Verified (code + live data).

**Full runtime trace (Discord message → action):**

1. Discord message arrives → `AntiSpam.on_message` (`bot/cogs/automod/antispam.py:77-137`).
2. Active-rule check: `is_anti_spam_enabled` queries `automod_punishments WHERE event = 'Anti spam'` (`antispam.py:35-39`).
3. The dashboard writes rule IDs, not legacy names. `dashboard/components/dashboard/automod-form.tsx:31-35` defines `anti_spam`, `anti_caps`, `anti_links`, `anti_invites`, `anti_mentions`. The legacy `PATCH /guilds/{id}/automod` (`bot/api/routes/guilds.py:147-193`) stores whatever keys it receives.
4. The match fails → `on_message` returns at line 87 before counting messages. **No detector, no threshold, no violation, no action, no log.**

Every automod cog has the same mismatch:

| Dashboard key / value | Runtime expects | Cog |
|---|---|---|
| `anti_spam` | `'Anti spam'` | `antispam.py:37` |
| `anti_caps` | `'Anti caps'` | `anticaps.py:36` |
| `anti_links` | `'Anti link'` | `antilink.py:39` |
| `anti_invites` | `'Anti invites'` | `anti_invites.py:36` |
| `anti_mentions` | `'Anti mass mention'` | `anti_mass_mention.py:35` |
| *(no UI)* | `'Anti emoji spam'` | `anti_emoji_spam.py:36` |
| `delete`, `warn`, `mute`, `kick`, `ban` | `"Mute"`, `"Kick"`, `"Ban"` | all cogs |

**Live confirmation** (read-only query of `bot/db/automod.db`):

```
automod             (1543105121804615781, 1)                         ← master switch on
automod_punishments (1543105121804615781, 'anti_spam', 'warn')       ← dashboard write
                    (1543105121804615781, 'anti_links', 'delete')
                    (1543105121804615781, 'anti_mentions', 'delete')
                    (1448948375658565662, 'Anti spam', 'Mute') ...  ← legacy prefix-command write
```

The owner's test guild has `anti_spam → warn`. The runtime looks for `'Anti spam'`, finds nothing, and exits. This exactly explains the confirmed live failure (rapid burst from a real non-owner alt, nothing happened).

The guild configured through legacy `>automod` commands has rules that *would* fire, but the dashboard cannot display them (its rule IDs don't match), so that guild's dashboard shows rules off while they are on.

### P0-02 — Automod: action vocabulary and toggles are false

Labels: RUNTIME MISMATCH, UX. Verified (code).

- "Delete message" and "Warn user" exist in the UI (`automod-form.tsx:22-28`) but no automod cog implements `delete` or `warn`.
- Anti-spam never deletes messages, even on `Mute/Kick/Ban` (`antispam.py:112-137`).
- With an unmatched punishment, the cog would still post "has been successfully **None** for Spamming" publicly (`antispam.py:124-128`).
- Turning a rule off in the dashboard removes the key client-side (`automod-form.tsx:163-166`), but the API only upserts submitted keys (`guilds.py:159-164`). The row is never deleted, so "off" never persists.
- Thresholds are hardcoded: spam is more than 5 messages in 10 s, keyed by user ID across all guilds; caps is 70%; mentions is 5; emoji is 5. Timeout durations are hardcoded per cog (1–12 minutes).
- All exceptions are swallowed (`except Exception: pass`). Missing Manage Messages, missing Moderate Members, or hierarchy failures are invisible.

### P0-03 — Guild allowlist auto-leave is broken

Labels: SECURITY, BUG. Verified (code + live log).

`cogs.events.on_guild` (`Guild`) fails to load: `TypeError: 'module' object is not callable` (preview module-health summary).

The cause is in `bot/cogs/events/on_guild.py:15-18`. It runs `from core import zyrox` followed by a module-level `client = zyrox()`. Once `core.zyrox` has been imported as a submodule, `core.zyrox` resolves to the module rather than the class, so instantiation raises.

This cog is the one that leaves a non-allowlisted guild on join (`on_guild.py:25-36`). With it broken, the private-first guild boundary is only enforced by the startup sweep (`bot/CodeX.py:77-86`). Until the next restart, any server that adds the bot gets the full runtime (all intents, automod, listeners, Security Center runtime, which itself is not guild-gated).

Dashboard access is still grant-gated, so this is a Discord-side exposure, not a dashboard data leak. Downgrade to P1 only if the Discord application has **Public Bot** disabled and that is verified.

### P0-04 — Verification V2 can lock every new member out

Labels: RUNTIME MISMATCH, SECURITY (availability). Verified (code).

- The only reference to the `cls-verify:` button is the listener (`bot/cogs/verification_v2.py:46`). No code anywhere posts that button.
- When enabled, the module assigns the unverified role on join (`verification_v2.py:21-40`) and the gate denies `view_channel` on protected categories (`bot/cls_platform/verification/gate.py`).
- The page copy says "Where the verify button is posted" (`dashboard/app/dashboard/guild/[guildId]/verification/page.tsx` ~L142).
- **Result: enabling Verification hides the server from every new member with no way to pass.**
- The nav item is hidden (`dashboard/lib/shellNav.ts:220-228`), but the page and its PATCH endpoint are reachable by URL.

### P0-05 — Vanity Roles promises status matching but mass-assigns to the whole server

Labels: RUNTIME MISMATCH, SECURITY, PERFORMANCE. Verified (code).

The UI says "Assign a role when a member's status contains the vanity text" (`vanityroles/page.tsx:100-101`). The runtime (`bot/cogs/commands/vanityroles.py:106-154`) does something different:

- Every 15 s it fetches `https://discord.com/api/v10/invites/{vanity}`.
- When the invite becomes reachable, it calls `add_roles` on **every member** of the guild.
- When the invite becomes unreachable, it calls `remove_roles` on every member.
- There is no hierarchy check, no rate shaping, and a new `aiohttp.ClientSession` per row per tick.

On a real server this is a mass role grant (and a mass revoke on any transient 404) that can hit rate limits and hand out a role everyone gets. It is not currently configured locally (`db/vanity.db` is empty), so it is latent. But it sits in the Roles nav and saves successfully.

---

## 3. Global UX / design findings

### 3.1 What is already right (preserve)

- Dark-only CLS identity, IBM Plex, purple brand, and dense command-center layouts are consistent in the V2 pages.
- No "ZyroX" strings remain in `dashboard/app` or `dashboard/components`.
- Snowflakes stay strings end to end in TypeScript; `lib/snowflake.ts` explicitly refuses `Number`/`parseInt`.
- A reduced-motion kill-switch exists (`dashboard/app/globals.css:126-158`, `:872-900`).
- The info banner uses the CLS `--cls-info` token, not raw Tailwind `blue-*` (`components/ui/state.tsx:51`). It is still cyan-blue (77 179 240), which is why it reads as generic (see 3.3).
- The shared `SaveBar` primitive is good (sticky, Discard/Save, Cmd/Ctrl+S, beforeunload, in-app leave guard).

### 3.2 Findings

| ID | Sev | Type | Finding | Where |
|---|---|---|---|---|
| G-01 | P1 | UX / A11Y | Shared `Button` has no `focus-visible` style; keyboard focus on primary actions is effectively invisible | `components/ui/button.tsx:30-80` |
| G-02 | P1 | UX | Save semantics are inconsistent. SaveBar is used by verification, security, j2c, invcrole, customroles, settings, antinuke. Welcome has an inline amber "Unsaved" without a leave guard. Messages has a custom guard. Logging, ticket settings, and automod are toast-only with no dirty indicator | `welcome-workspace.tsx:245-247`, `messages-workspace.tsx:84-101` |
| G-03 | P2 | VISUAL | Semantic colors bypass tokens: `amber-300`, `red-400`, `emerald-500`, `slate-*` instead of `warn`/`danger`/`ok` | welcome, messages, role-automation, media-field, leaderboard |
| G-04 | P2 | VISUAL | Pre-CLS UI pockets with `rounded-3xl` / `rounded-[40px]`, `#141B2D`, slate gradients | `leveling-form`, `vanityrole-form`, `reactionroles-form`, `verification-form`, `form-elements.tsx`, `server-card.tsx`, `metric-card.tsx` (last three appear dead) |
| G-05 | P2 | UX | Decorative images are natively draggable. Only `ClsMark` sets `draggable={false}`. Avatars, guild icons, `next/image` in guild list, and preview media all produce ghost images. Must keep: config-transfer drop zone (`config-transfer.tsx:157`). There is no dnd library, so a global rule is safe | `components/brand/cls-mark.tsx:39-40` |
| G-06 | P2 | VISUAL | Favicon: a 74×128 thin-stroke PNG declared as `128x128`. Browsers letterbox it into a square, so the glyph is ~9 px wide at 16 px. No `favicon.ico`, no SVG, no `apple-icon`, no manifest | `app/layout.tsx:63-66`, `public/brand/cls-mark-128.png` |
| G-07 | P2 | UX | Naming drift for one module: route `/antinuke`, nav "Protection", page "Security Center", Overview row "Antinuke", landing "Antinuke watches…", legacy tabs "Anti-Nuke" | `shellNav.ts:244-249`, `loadOverview.ts:261`, `landingDomains.ts`, `guild-tabs.tsx:70` |
| G-08 | P2 | UX | Pages swallow API failure into empty data (`catch(() => null)` → empty state) instead of an error state. Examples: Commands, Giveaways list | `commands/page.tsx`, `giveaway-manager.tsx` |
| G-09 | P2 | UX | Raw IDs exposed in normal UX: Security trust/incident rows, Leveling level-up channel as a raw snowflake input, Recovery raw JSON | security-panel, leveling-form ~L126-135, recovery |
| G-10 | P2 | VISUAL | Native `<details>` expanders used for developer data (Logging) create long inline panels | `logging-v2-workspace.tsx:579-588` |
| G-11 | P3 | TECH DEBT | No Next.js middleware; auth is enforced by layout redirects only (works, but fragile) | `dashboard/layout.tsx:42-62` |
| G-12 | P3 | TECH DEBT | Design docs mention Chakra Petch for display-hero; implementation forces Plex | `globals.css:663-666` |

### 3.3 Status / alert / toast color system

Current semantic tokens: `--cls-ok`, `--cls-warn`, `--cls-danger`, `--cls-info` (`globals.css:45-52`). Toasts (Sonner) use surface-2 with ok/danger borders (`components/ui/sonner.tsx:21-41`).

The problem is not raw Tailwind. It is that **info** is a saturated cyan-blue that sits outside the CLS palette and is used for "neutral platform notice" banners such as the landing notice bar (`notice-bar.tsx:16-24`).

Recommendation:

- Keep **danger / warn / ok** hues as they are (red / amber / green), because semantics must stay legible.
- Change **info** to a desaturated violet-steel derived from the brand ramp, for example brand-300 at 0.08 fill, a brand-400 at 0.3 hairline, and fg-2 text with a brand icon. This makes system notices feel native without pretending to be a success or warning.
- Add a fifth tone, **locked / observe**, for "this exists but is intentionally not enforcing" states (Security, Automod observe mode). Today these are expressed as grey prose, which is why they read as broken.
- Define the full set in one table (fill / border / icon / text) and lint for raw color classes.

### 3.4 Landing (Verified visual + code)

| ID | Sev | Finding |
|---|---|---|
| L-01 | P1 | **Rectangular glow artifact.** Three causes, from most to least visible. (1) `.cls-hero-visual::after` is a rectangular box (`inset: 16% 8%`) carrying a diagonal linear-gradient band animated across it for 11 s (`globals.css:838-862`); the band is hard-cut by the box's top and bottom edges, producing the "window" outline. (2) The core bloom is a `blur-2xl` circle inside a parallax-transformed layer (`perimeter-mark.tsx:195-201`), and `.cls-hero { overflow-x: clip }` (`globals.css:820-822`) gives it straight vertical edges near the sides. (3) The page wash is a 440 px radial gradient on an `inset-0` rectangle that tracks the pointer (`use-parallax.ts:81-106`), so its tail hits the clip when the pointer moves. **Fix direction:** replace the sweep with a radial or conic highlight masked to the hex shape (`mask-image` with a radial falloff or an SVG mask), let the wash live on an unclipped full-bleed layer behind the hero, and cap blur radius below the clip margin. |
| L-02 | P2 | Hex domain labels are plain mono uppercase text, hidden on mobile (`perimeter-mark.tsx:233`). Recommend small 16 px line icons (from the same icon set as the nav) plus a label at each vertex, with the active domain's icon carrying the brand color and the edge segment lit. |
| L-03 | P2 | The lower "What runs inside" list drives the hero's active domain via shared state (`gateway.tsx:14-23`, `domain-list.tsx:85-89`). Once the hero is off-screen this coupling has no value and looks like nothing happens. **Recommend:** the hero autonomously cycles domains (about 4 s per domain, paused on hover/focus and on reduced motion) with a synchronized one-line explanation under the hex. The lower section keeps its own local active state and its own visuals. |
| L-04 | P2 | The "What runs inside" detail panel is a plain four-row list in a large card ("Human protection / Bot protection / Rules / Trusted actors") with lots of dead space (Verified visual). It uses the legacy word "Antinuke". Recommend a richer detail: a small schematic or real UI excerpt per domain (for example a mini incident row, a ticket queue row, a log line), 3 capability lines with one-sentence value, and a "what you configure" footer. No fake metrics. |
| L-05 | P2 | Hero → section transition: a hairline rule plus a `pb-16` / `pt-10` gap. The hero glow ends abruptly at the rule. Let the ambient light continue into the section top with a long fade, and reduce the gap so the section header sits in the hero's light. |
| L-06 | P3 | Nav "Sign in" hidden below `sm` (`landing-nav.tsx:33`); the hero CTA remains, so this is acceptable but inconsistent. |
| L-07 | P3 | Infinite sweep animation keeps compositing while visible; pausing exists via `data-depth-paused`. Fine after L-01. |

### 3.5 Auth states (Verified visual + code)

- `/auth/no-access`, `/auth/error`, `/auth/continue` share `AuthLayout` (`components/auth/auth-layout.tsx:19-42`): a centered small hex mark, title, one paragraph, and buttons on a near-black lattice. The error page renders cleanly ("Discord sign-in wasn't approved.", reference code, Try again / Back).
- **No access (P2, UX/VISUAL):** static and empty. Recommend:
  - A slow breathing ambient light (opacity 0.6↔1 over about 6 s, radial, unclipped, reduced-motion safe) behind the mark.
  - A two-state status card: "Signed in as @user · ID copy" (ok tone) and "Access: awaiting grant from the CLS owner" (locked tone, with a subtle pulse dot).
  - A "What happens next" line, a "Check again" button that re-runs the grant lookup, and Sign out.
  - Do not add decoration beyond this.
- `/auth/no-access` correctly redirects to `/` when signed out (Verified).

---

## 4. Runtime truth mismatches

This is the most important section for preventing the next false "complete".

### 4.1 Dashboard setting exists, runtime ignores it

| # | Setting | Evidence | Sev |
|---|---|---|---|
| R-01 | Automod rules and punishments | P0-01 | P0 |
| R-02 | Automod "Delete" / "Warn" actions, rule disable | P0-02 | P0 |
| R-03 | Vanity role "status contains text" | P0-05 | P0 |
| R-04 | InVC role `enabled` switch | `bot/cogs/commands/Invc.py:92-105` selects only `role_id` | P1 |
| R-05 | Phishing action Delete / Timeout / Kick / Ban | `bot/cogs/security/center_runtime.py:41-49` records only | P1 |
| R-06 | Bot Trap ban when ENFORCE unlocked | `center_runtime.py:30` hardcodes `enforce_locked=True` | P1 |
| R-07 | Logging exclusions (channels/roles/users) | Runtime applies only to message edit/delete/bulk (`cls_platform/logging/pipeline.py:13-28`) | P1 |
| R-08 | Giveaway scheduling | API supports `starts_at`; UI never sends it (`giveaway-manager.tsx:80-95`) | P2 |
| R-09 | Commands aliases / cooldown shown in inspector | Read-only from inventory (`cls_platform/commands/policy.py`) | P2 |
| R-10 | Legacy `>autorole` / `PATCH /autorole` | Writes `db/autorole.db`; Role Automation V2 assigns from Postgres and migrates only once | P1 |
| R-11 | Legacy `>greet`/Welcomer commands and legacy `PATCH /welcome` | Write `db/welcome.db` without the V2 wrapper; can overwrite the dashboard composer state | P1 |

### 4.2 UI says Enabled / healthy, but the bot cannot or does not act

| # | Surface | Evidence | Sev |
|---|---|---|---|
| R-12 | Overview Automod "On · N punishment rules configured" | `dashboard/lib/loadOverview.ts:273-286` counts keys; runtime inert | P1 |
| R-13 | Overview Welcome status | Reads legacy `GET /guilds/{id}/welcome` (`loadOverview.ts:186`), which returns **HTTP 500** in the preview (pydantic: `channel_id` int vs str, `guilds.py:438`) and cannot parse V2 composer payloads. V2 welcome works; Overview shows unavailable or incomplete | P1 |
| R-14 | Overview "Antinuke On/Off" from `human_mode` + "whitelisted users" | No containment exists; trust list is not a whitelist | P2 |
| R-15 | Security "Release" | `bot/api/routes/security.py:200-206` always 409 | P1 |
| R-16 | Automod without Manage Messages / Moderate Members / role above target | No preflight; `except: pass` | P1 |
| R-17 | Security "Permission health" | Hardcoded string `"observability_only"` (`security.py:103`) | P1 |

### 4.3 Runtime supports it, but the dashboard cannot manage it

| # | Capability | Evidence | Sev |
|---|---|---|---|
| R-18 | Trusted actors grant/revoke | `cls_platform/security/trust.py` exists; no HTTP route or UI | P1 |
| R-19 | Maintenance windows | `security/maintenance.py` exists; display only | P2 |
| R-20 | Anti emoji spam rule | Cog exists; no UI row | P2 (absorbed by Automod V2) |
| R-21 | Leveling | XP listener live (`cogs/commands/leveling.py:552+`), page exists but nav hidden; rewards and multipliers not in API | P2 |
| R-22 | Word blacklist filter (`Blacklist`, `db/blword.db`), Media-only channels (`Media`, `db/media.db`), sticky messages, autoresponder, AFK, counting, birthdays, jail | Live listeners, no CLS dashboard | P2 (decide ship/hide) |
| R-23 | Ticket priority/tags/notes/transfer | Runtime present; partial dashboard | P3 |

### 4.4 Save succeeds, nothing changes in Discord

R-01, R-02, R-03 (inverse: something big changes), R-04, R-05, R-08, R-10, R-11, plus Commands PUT accepting role/channel IDs from another guild (C-03), which saves but can never match.

### 4.5 Runtime environment truth

- Preview module health shows these failing on missing packages: `Music`, `Games`, `Owner` (contains the protected `reload`/`sync`), `Badges`, `Stats`, `FilterCog`, `TranslateCog`, `Minecraft`. If production mirrors this, the Commands page lists commands that aren't loaded, or omits ones the docs promise. P2 ops.
- All legacy SQLite paths are **cwd-relative** (`"db/automod.db"`, `j2c_data.db` at bot root). Starting the bot or API from another directory silently creates empty databases and "loses" config. P2 DATA.

---

## 5. Competitive research methodology and sources

### 5.1 Method

- Competitors were chosen per module for strength in that specific job, not by brand.
  - Automod: Discord native, ProBot, Dyno, Carl-bot, MEE6, Wick, YAGPDB.
  - Security: Wick, Security Bot, Bleed, SCNX, ProBot, RaidProtect, RiskyMH Honeypot, Discord native.
  - Logging: Dyno, Carl-bot, ProBot, MEE6, Sapphire, Wick, YAGPDB.
  - Commands: Discord native, ProBot, Dyno, Carl-bot, MEE6, YAGPDB.
  - Tickets: Ticket Tool, TicketsBot, ProBot, Helper.gg.
  - Roles: Carl-bot, Zira, MEE6, Dyno, Discord Onboarding.
  - Messages: Discohook, Discord Components V2, MEE6, ProBot, Carl-bot.
  - Giveaways: GiveawayBot, Giveaway Boat.
  - Invites: Invite Tracker plus Discord policy.
  - Voice: TempVoice, VoiceMaster.
  - Backup: Xenon, Discord Server Templates.
- Sources were official docs, help centers, changelogs, and Discord developer docs first. Reddit and GitHub discussions were used only to identify pain points.
- All sources were fetched on 2026-10-02.
- Caveats:
  - `docs.dyno.gg` blocks direct fetch, so some Dyno details are medium confidence (community tutorials).
  - ProBot's giveaway docs returned 404.
  - `docs.discord.food` is unofficial.
  - PeakBot is competitor marketing.
- **Marketing checkmarks were not counted as capabilities.** Matrices below describe behavior.

### 5.2 Key industry facts that shape the plan

1. **Prefix commands are being retired across the ecosystem.** YAGPDB has discontinued built-in prefix commands. Carl-bot disables standard prefix commands on 2026-10-05. CLS has ~373 prefix-only commands.
2. **Discord AutoMod is complementary, not a replacement.** It blocks before posting and allows multi-action rules. But it has no warning or strike history, no kick/ban, and no rate-based message spam control (its spam filter explicitly misses copy-paste and repeated messages). A bot can consume `AUTO_MODERATION_ACTION_EXECUTION` and count native blocks as strikes.
3. **Bots cannot write Discord's native command permissions with a bot token,** and subcommands have no native permission IDs. A dashboard must enforce at runtime and *show* the two-layer reality.
4. **Invite rewards are prohibited** by Discord's Platform Manipulation policy. Invite Tracker removed invite-reward roles and invite giveaway requirements.
5. **No audit-log entry exists for self-deletes or for single deletes by bots.** Attribution must state certainty honestly.
6. **Honeypot channels target compromised human accounts** and must be visible to everyone (RaidProtect). Bots are exempt.
7. **Components V2** (flag `1<<15`, up to 40 components, containers/sections/media galleries) and **new modal inputs** (selects, file upload, radio, checkbox) are available. Most competitors still cap ticket forms at 5 text inputs.
8. **Paywalled basics are the top user complaint** (MEE6 Moderator and Welcome now Premium; Ticket Tool auto-close premium).
9. **Role hierarchy is the top support issue at every bot.** The best dashboards add a setup wizard, per-module health, and inline permission checks.

### 5.3 Sources (by area)

**Discord platform**

- AutoMod API: https://discord.com/developers/docs/resources/auto-moderation
- AutoMod FAQ: https://support.discord.com/hc/en-us/articles/4421269296535-AutoMod-FAQ
- AutoMod safety guide: https://discord.com/safety/auto-moderation-in-discord
- Regex in AutoMod: https://support.discord.com/hc/en-us/articles/10069840290711-Filter-Messages-Using-Regular-Expressions-Regex
- Gateway events: https://docs.discord.com/developers/events/gateway-events
- Audit log: https://discord.com/developers/docs/resources/audit-log
- No audit entry for self/bot single deletes: https://github.com/discord/discord-api-docs/issues/7856
- Command permissions: https://support.discord.com/hc/en-us/articles/4644915651095-Command-Permissions and https://docs.discord.com/developers/interactions/application-commands
- Permissions update (2023): https://support-apps.discord.com/hc/en-us/articles/26501842915607-Updates-to-Command-Permissions
- No subcommand permissions: https://github.com/discord/discord-api-docs/discussions/4719 and https://github.com/discord/discord-api-docs/discussions/7813
- Activity Alerts / Security Actions: https://support.discord.com/hc/en-us/articles/17439993574167-Activity-Alerts-Security-Actions
- Pause Invites: https://support.discord.com/hc/en-us/articles/8458903738647-Pause-Invites-FAQ
- Raids 101: https://support.discord.com/hc/en-us/articles/10989121220631-How-to-Protect-Your-Server-from-Raids-101
- Verification levels: https://support.discord.com/hc/en-us/articles/216679607-Verification-Levels
- Members page: https://support.discord.com/hc/en-us/articles/15946797617431-Members-Page
- Components V2: https://docs.discord.com/developers/components/reference, https://github.com/discord/discord-api-docs/pull/7487, https://github.com/discord/discord-api-docs/pull/7507
- Onboarding: https://support.discord.com/hc/en-us/articles/11074987197975-Community-Onboarding-FAQ and https://docs.discord.com/developers/resources/guild
- Platform manipulation policy (invite rewards): https://discord.com/safety/platform-manipulation-policy-explainer
- Developer policy: https://support-dev.discord.com/hc/en-us/articles/8563934450327-Discord-Developer-Policy

**Automod / moderation**

- ProBot AutoMod: https://docs.probot.io/docs/modules/automod
- ProBot commands: https://docs.probot.io/docs/getting-started/commands
- ProBot outage Q&A: https://www.reddit.com/r/probot/comments/1jw1enj/qa_regarding_the_ongoing_issues/
- Dyno Automod V2 walkthrough (community): https://www.youtube.com/watch?v=rLV_h9E2Lpw
- Dyno legacy defaults: https://gist.github.com/royalPanic/86c196ed59b4eff3ae6cac12bc52de14
- Dyno violation window: https://www.reddit.com/r/Dynodiscord/comments/kkqsem/dyno_not_muting_people_who_reach_a_certain_number/
- Dyno staff immunity confusion: https://www.reddit.com/r/Dynodiscord/comments/itom2t/auto_mod_not_triggering_for_some_roles/
- Carl-bot automod: https://docs.carl.gg/automod.md
- Carl-bot moderation: https://docs.carl.gg/moderation.md
- Carl-bot prefix notice: https://docs.carl.gg/notice.md
- MEE6 Moderator: https://wiki.mee6.xyz/plugins/moderator
- MEE6 Premium requirement: https://help.mee6.xyz/en/articles/615175-how-to-ban-kick-or-mute-with-mee6 and https://help.mee6.xyz/en/articles/710936-mee6-free-vs-premium-plans-comparison
- MEE6 escalation troubleshooting: https://help.mee6.xyz/en/articles/615179-automoderator-is-not-punishing-users-correctly
- Wick setup: https://docs.wickbot.com/setup/
- Wick features: https://docs.wickbot.com/intro/features/
- Wick v5.3 (native AutoMod management): https://docs.wickbot.com/changelog/v5.x/5.3.0/
- YAGPDB advanced automod: https://help.yagpdb.xyz/docs/moderation/advanced-automoderator/overview/, plus `/triggers/` and `/effects/`
- YAGPDB basic automod: https://help.yagpdb.xyz/docs/moderation/basic-automoderator/
- YAGPDB moderation tools: https://help.yagpdb.xyz/docs/moderation/moderation-tools/
- YAGPDB command settings: https://help.yagpdb.xyz/docs/core/command-settings/
- ProBot dashboard (command management): https://docs.probot.io/docs/getting-started/dashboard
- Carl-bot config: https://docs.carl.gg/config.md
- MEE6 custom commands: https://wiki.mee6.xyz/en/plugins/custom-commands

**Security**

- Wick FAQ: https://docs.wickbot.com/faq/
- Wick lockdown: https://docs.wickbot.com/commands/moderation/lockdown/
- Wick changelogs: https://docs.wickbot.com/changelog/v5.x/5.0.0/, `/5.1.0/`, `/5.2.0/`
- Security Bot anti-nuke: https://docs.securitybot.gg/anti-nuke/anti-nuke
- Security Bot punishments: https://docs.securitybot.gg/anti-nuke/anti-nuke/changing-punishments
- Security Bot whitelist: https://docs.securitybot.gg/whitelist/whitelist
- Security Bot Beast Mode: https://docs.securitybot.gg/other-modules/beast-mode
- Security Bot anti-raid: https://docs.securitybot.gg/other-modules/anti-raid
- Security Bot logs: https://docs.securitybot.gg/other-modules/logs
- Bleed anti-nuke: https://docs.bleed.bot/security/antinuke
- Bleed fake permissions: https://docs.bleed.bot/security/fake-permissions
- SCNX anti-nuke (alert-only, temporary whitelist, Undo): https://docs.scnx.xyz/docs/custom-bot/modules/moderation/anti-nuke/
- ProBot VIP Protection: https://docs.probot.io/docs/modules/vip_protection
- ProBot anti-raid: https://docs.probot.io/docs/modules/anti_raid
- RaidProtect HoneyPot: https://raidprotect.bot/en/docs/features/honeypot
- RiskyMH Honeypot: https://honeypot.riskymh.dev/docs/configuration
- Greed honeypot: https://greed.best/docs/moderation/honeypot
- Ticket Tool vs security bots: https://ticket-tool.app/docs/guides/whitelist-security-bots
- Xenon backups: https://xenon.bot/docs/backups
- Captcha.bot analytics: https://docs.captcha.bot/logging/server-analytics
- Honeypot field report: https://www.reddit.com/r/discordapp/comments/1uuxksh/how_to_avoid_mr_beast_images_spam_on_my_server/

**Logging**

- Dyno Action Log: https://docs.dyno.gg/en/modules/actionlog
- Carl-bot logging: https://docs.carl.gg/logging.md
- ProBot logs: https://docs.probot.io/docs/modules/logs
- Sapphire logging: https://docs.sapph.xyz/logging.md
- YAGPDB logging: https://help.yagpdb.xyz/docs/moderation/logging/
- Dyno action-log outages: https://www.reddit.com/r/Dynodiscord/comments/1k2nrh4/dyno_actionaudit_log_is_not_working/

**Tickets**

- TicketsBot panels: https://docs.tickets.bot/dashboard/ticket-panels
- TicketsBot forms: https://docs.tickets.bot/features/forms
- TicketsBot close requests: https://docs.tickets.bot/features/close-requests
- TicketsBot analytics: https://docs.tickets.bot/dashboard/analytics
- TicketsBot feedback: https://docs.tickets.bot/dashboard/settings/user-feedback
- TicketsBot thread mode: https://docs.tickets.bot/dashboard/settings/thread-mode
- Ticket Tool form options: https://docs.tickettool.xyz/dashboard/panel-configs/form-options.md
- Ticket Tool automation: https://docs.tickettool.xyz/dashboard/panel-configs/automation-options
- Ticket Tool transcripts: https://docs.tickettool.xyz/dashboard/panel-configs/transcript-options
- Ticket Tool FAQ: https://docs.tickettool.xyz/beta-docs/debugging/faqs
- ProBot tickets: https://docs.probot.io/docs/modules/tickets
- Ticket Tool paywall complaint: https://www.reddit.com/r/TicketTool/comments/1fm2qru/auto_close_ticket_after_x_hours/

**Roles, Welcome, Messages, Giveaways, Invites, Voice, Leveling, Dashboard UX**

- Carl-bot reaction roles: https://github.com/CarlGroth/carlbot-docs/blob/master/roles/reaction-roles.md
- Zira: https://docs.zira.bot/docs/intro/faq
- Dyno rolepersist: https://docs.dyno.gg/en/commands/rolepersist
- MEE6 welcome role and screening: https://help.mee6.xyz/en/articles/615145-how-to-give-a-role-to-new-members-welcome-role
- Phantom temp roles: https://docs.phantombot.gg/community/temp-roles
- MEE6 welcome: https://wiki.mee6.xyz/en/plugins/welcome-and-goodbye
- ProBot welcome image: https://docs.probot.io/docs/modules/welcome
- Discohook: https://discohook.org/
- YAGPDB scheduled custom commands: https://help.yagpdb.xyz/docs/custom-commands/commands/
- GiveawayBot: https://giveawaybot.party/ and https://github.com/jagrosh/GiveawayBot
- Giveaway Boat: https://giveaway.boats/
- Invite Tracker: https://docs.invite-tracker.com/dashboard/invite-tracking and https://docs.invite-tracker.com/faq
- Invite tracking accuracy: https://github.com/AnIdiotsGuide/discordjs-bot-guide/blob/master/coding-guides/tracking-used-invites.md
- TempVoice: https://easy.tempvoice.xyz/commands/interface
- VoiceMaster: https://voicemaster.xyz/guides/en/voice-commands-guide
- Channel rename rate limit: https://github.com/discord/discord-api-docs/issues/1900
- Arcane leveling: https://docs.arcane.bot/plugins/leveling/
- Lurkr multipliers: https://lurkr.gg/docs/guides/setting-up-leveling-multipliers
- Xenon role cooldown: https://xenon.bot/docs/help/role-cooldown
- Discord server templates: https://support.discord.com/hc/en-us/articles/360041033511-Server-Templates
- FlaviBot module health: https://flavibot.xyz/docs/getting-started/06-modules-and-commands
- ProBot setup (hierarchy workaround): https://docs.probot.io/docs/getting-started/setup
- SYNTHET permissions: https://www.synthet.gg/docs/getting-started/permissions
- MEE6 paywall backlash: https://www.reddit.com/r/discordapp/comments/1kon2am/literally_everything_mee6_is_used_for_is_now/

---

## 6. Module-by-module audit

Each module lists: current state, runtime truth, UX, gaps, and **verdict**. File references are to the current tree.

### 6.1 Public / global

**Landing.** See 3.4. Copy is factual and there are no fake claims. Parallax is good and reduced-motion safe. Verdict: **KEEP / POLISH** (L-01…L-05).

**Login / Auth / No Access.** See 3.5. Discord OAuth only; grant-based access; no middleware. Verdict: **KEEP / POLISH** (no-access richness, signed-in vs awaiting-grant states).

**Navigation / shell.** Inverted-L shell, rail/drawer breakpoints, guild switcher with search, grouped nav (`dashboard/lib/shellNav.ts:65-294`).

- Issues:
  - Verification and Leveling are hidden but live.
  - Group "Engagement" mixes Role Automation, Role Menus and Auto React while "Management → Roles" holds Custom/Voice/Vanity. Roles are split across two groups.
  - The Security group has a single item.
- Recommend: Roles group = Role Menus, Role Automation, Custom Roles, Voice Role, Vanity. Engagement = Welcome, Messages, Giveaways, Invites, Auto React.
- Verdict: **KEEP / POLISH**.

**Alerts / toasts / banners.** See 3.3. Verdict: **POLISH** (token rework, new "observe/locked" tone).

**Favicon / icons.** See G-06. Recommendation:

- Draw a dedicated **symbol-only small-size mark**. Use the "CS" glyph with the outline strokes converted to solid fills and strokes at least 2 px at 32 px, optically centered in a **square** 32×32 canvas with about 1–2 px padding. Optionally use a dark rounded-square plate (radius 6/32), because a purple glyph on a transparent background disappears on dark browser chrome.
- Export:
  - `app/icon.svg` (simplified geometry),
  - `favicon.ico` (16 and 32, hand-hinted at 16),
  - `apple-icon.png` 180×180 on a solid plate,
  - `icon-192.png` / `icon-512.png` plus a maskable variant and `manifest.webmanifest`.
- Fix the `sizes` metadata. Do not downscale the large logo.

**Responsive.** The shell drawer under 1024 px is correct. Tables wrap in `overflow-auto`. Legacy pages (leaderboard, vanity, leveling) are dense and overflow. Verdict: **POLISH**.

**Native image dragging.** See G-05. Add a global rule (`img, svg, video { -webkit-user-drag: none; user-select: none; }` scoped to non-editable contexts) plus `draggable={false}` on avatar, guild icon and media preview components. Keep the config-transfer drop zone and any future reorder handle explicitly draggable.

### 6.2 Core

**Overview.** Readout rail, analytics deck, attention queue, module matrix, facts column (`components/.../overview-content.tsx:23-41`). Most numbers are real.

- Defects:
  - R-12 (Automod false "On"),
  - R-13 (Welcome from a 500ing legacy endpoint),
  - R-14 ("Antinuke" + "whitelisted users"),
  - the Activity band is intentionally empty.
- Verdict: **KEEP / POLISH**, with fixes for module status sources.
- Overview should consume one **module health contract** (F1) instead of per-module heuristics.

**Messages / Embed Builder.** Library / Editor / Sent tabs; embeds (≤10), fields, media upload, link buttons (≤5), variables, templates, edit/resend/delete of sent messages, dirty guard (`messages-workspace.tsx`, `bot/cls_platform/messages/*`).

- Missing:
  - Components V2 (containers/sections/galleries),
  - action buttons and selects,
  - scheduling and recurrence,
  - "import from message link",
  - version history.
- Mentions are forced off on send (`api/routes/messages.py:30`), with no controlled allow-list.
- Verdict: **KEEP / POLISH ONLY**. Next differentiator: Components V2 with an irreversible-flag warning, and scheduling.

**Welcome / Welcome DM / Goodbye.** One workspace with tabs (`welcome-workspace.tsx:186-201`). It has a channel picker restricted to sendable channels, skip-bots, auto-delete, composer and preview, test-to-me / test-to-channel, and a `channel_ok` warning. `/joindm` redirects to `welcome?tab=dm`.

- Runtime: `cogs.events.greet2` calls the V2 senders; `joindm` defers when `greet` is loaded (no double DM).
- Defects:
  - FastGreet still loaded and posts "{mention} Welcome!" (latent; `fastgreet.db` empty locally) and uses blocking `sqlite3` on the event loop (`fastgreet.py:73-89`).
  - Welcomer prefix commands (required cog) and legacy `PATCH /welcome` can rewrite the same `db/welcome.db` without the V2 wrapper.
  - The DM is stored in `jsondb/joindm_messages.json` (weaker backup and isolation).
  - Save semantics are not SaveBar.
- Missing vs competitors: a welcome image card (ProBot/MEE6 make it premium; CLS could ship it free), and "join role after rules screening" linkage (lives in Role Automation).
- Verdict: **KEEP / POLISH ONLY**, plus legacy retirement.

### 6.3 Moderation

**Logging (V2).**

- **What's strong:**
  - Postgres event store with 90-day retention and a 30-day message-content cache.
  - Hourly purge.
  - Category routes plus per-event overrides (inherit / custom / stored_only / disabled).
  - Log-channel health (view/send/embed).
  - Server-side cursor pagination (`limit` default 50, max 100).
  - Filters (category, event type, member, text, date).
  - Render consumes appearance.
  - Static preview.
- **Coverage, verified:**
  - Member: ban, unban, kick, timeout given/removed, join, leave, nickname, roles.
  - Channel create/update/delete, with overwrite diffs inside `channel_update`.
  - Role create/update/delete; server update (subset).
  - Messages: edit, delete, bulk delete.
  - Voice: join, leave, switch.
- **Coverage, missing:**
  - thread create/update/delete,
  - invite create/delete,
  - voice server/self mute and deafen (returns early when the channel is unchanged, `logging_v2.py:509-510`),
  - moderator move/disconnect (no audit lookup),
  - emoji/sticker,
  - webhooks,
  - scheduled events,
  - pins,
  - boosts,
  - bot added (only generic join),
  - integrations,
  - Discord AutoMod executions,
  - moderation command used,
  - warns (`warn.py` never records an event).
- **Attribution:** an audit lookup over the last 15 s; it accepts the actor only on exactly one match → `certain`. Otherwise it records `unknown`. The store supports `probable`, but it is never written. CLS's own module actions (Role Automation, Role Menus, Verification) appear as actions by the bot user without a module source, so the owner's desired "by CLS SYSTEM · Role Automation" is not possible today.
- **Sentences:**
  - Role changes render as "{actor} updated {target}'s roles" / "{target}'s roles were updated" (`present.py:262`), with the diff as a secondary "+ Role" line.
  - Owner example: "+EVO+'s roles changed / + R7 Extra" is too shallow. Target: "+EVO+ received R7 Extra" with "by CLS · Role Automation · 3h ago".
- **Activity UX:**
  - "Older" *replaces* the list rather than paging with numbers.
  - No page-size control.
  - Developer details are an inline `<details>` JSON block.
- **Appearance:** guild-level style, avatars/moderator/jump/timestamp/IDs toggles, footer, and **category** colors only. No per-event color/icon/title. The preview is a static message-edit mock and is **not sticky**.
- **Exclusions:** message events only (R-07).
- **Health:** View Audit Log is not surfaced (silent "unknown" actors).
- **Legacy:** `cogs.commands.logging` skipped. `cogs.zyrox.logging` is a help stub only. Automod cogs still send their own embeds to `automod_logging.log_channel`, bypassing Logging V2.
- **Verdict:** **KEEP architecture, complete the product.**
  - Recommended customization level: **category default → per-event override for color, icon, and title only** (plus the existing per-event routing). Not a free-form embed builder: logs must stay scannable and consistent, and per-event templates (Sapphire) produce noise and breakage. A "compact / detailed" density per category is enough.

**Automod.** See P0-01 and P0-02, and the full redesign in 6.8.

- Current IA: one card with a master toggle and five rules, each a toggle plus one punishment dropdown. Global ignored channels/roles and a log channel exist in the API.
- Missing:
  - thresholds,
  - timeout duration,
  - compound actions,
  - per-rule exclusions,
  - bad-words list,
  - attachment/emoji/newline/duplicate rules,
  - a warning system,
  - violation history,
  - health.
- Storage is legacy SQLite with ~20 connection opens per message across six cogs (each `on_message` opens `db/automod.db` 2–4 times). PERFORMANCE.
- A second word filter (`Blacklist` cog, `db/blword.db`) and a media-only filter (`Media`) run separately.
- Verdict: **REBUILD as Automod V2** (new store, engine, UI). Do not patch the legacy cogs beyond the F0 hotfix.

**Commands.** `GET /commands` builds a live inventory via `bot.walk_commands()` (`cls_platform/commands/policy.py:215-266`), about 490–500 rows after filtering `__help__` stubs.

- **Policy:** enabled, allowed/blocked roles, allowed/blocked channels in Postgres `command_policies`. These are **enforced** by a global check plus the tree `interaction_check` (`policy.py:292-326`). This core works.
- **UX:**
  - Header "Turn commands on or off, and limit who can use them and where."
  - Search, category and on/off filters.
  - The first paint is a grid of category names with counts.
  - The list has 40 per page; there is a side inspector.
- **Problems:**
  1. No audience filter. Bot-owner and system commands (`np …`, `global …`, `GB`, `blacklist …`, `reload`, `sync`, `emergency authorise …`, `bdg …`, `leaveguild`, `ownerban`) show to every guild admin as "Administration".
  2. ~116 loaded commands show "No description."
  3. Subcommands are flat qualified-name rows instead of a tree.
  4. No module/category toggle and no bulk actions.
  5. Aliases and cooldown are display-only.
  6. No explanation of the two layers (Discord Integrations vs CLS policy).
  7. Offensive or unprofessional aliases still ship (`fuckban`, `stfu`).
  8. Fun/AI/nitro/games/slots/blackjack surfaces are registered in a "professional ops" product.
  9. PUT accepts role/channel IDs without checking they belong to the guild (`api/validators/discord_resources.py:21-45` does not walk `allowed_*_ids`).
  10. ~373 prefix-only commands while the ecosystem moves to slash.
  11. API errors are swallowed into an empty page.
- Verdict: **REBUILD the UI and the catalog model; KEEP the enforcement gate.**

**Security Center / Protection.** See 6.9.

### 6.4 Support

**Tickets (all surfaces).** Queue with metrics strip; panel builder (button/select, ≤5 modal questions, required/blocked roles, routing rules); categories and teams with staff roles, hours and close mode; settings (cooldown, max open, auto-close hours, transcript channel, blacklist); HTML transcripts saved in Postgres with a viewer; claim/unclaim/close/reopen; close requests; inactivity jobs; priority/tags/notes/transfer.

- Restart-safe via `custom_id` + `on_interaction`. The legacy TicketCog is skipped; `cogs.zyrox.ticket` is a help stub.
- Missing vs TicketsBot:
  - CSAT ratings,
  - per-staff analytics (first response, resolution, rating),
  - thread-mode tickets,
  - overflow category,
  - newer modal inputs (selects/file upload),
  - SLA targets with breach flags,
  - an audit log of panel changes.
- CLS already beats Ticket Tool on transcript durability (it stores them itself).
- Verdict: **KEEP / POLISH ONLY.**

### 6.5 Roles / automation

**Role Menus.** Reaction/button/select; modes toggle/add/remove/unique; max roles; hierarchy "above CLS" warnings in the builder; migrated from `rr.db`; restart-safe via custom IDs.

- Missing:
  - required/forbidden roles to use a menu,
  - max holders per role,
  - temp roles,
  - Carl-bot style "binding/verify" presets in plain language,
  - export to Discord Onboarding.
- Verdict: **KEEP / POLISH ONLY.**

**Role Automation / Join Roles.** Join roles (members/bots, delay, screening) plus rules (join / screening / role add / role remove → conditions → delay); Postgres; hierarchy check before add (`role_automation.py:53-61`).

- Defects:
  - Join roles do not show hierarchy health in the UI.
  - The legacy `AutoRole` commands and `/autorole` API write a store V2 no longer reads (R-10).
  - `cogs.events.auto` is misleadingly named `Autorole` but only sends a thank-you DM on bot join.
- Missing: sticky roles (role persistence on rejoin) and temp roles.
- Verdict: **KEEP / POLISH ONLY**, plus legacy retirement.

**Auto React V2.** Rules CRUD, health labels, channel scope, emoji picker; Postgres; legacy skipped. `cogs.events.react` only reacts to owner mentions (harmless). There is a duplicate legacy `GET /autoreact` in `guilds.py`. Verdict: **KEEP / POLISH ONLY.**

**Custom Roles.** SaveBar workspace, legacy SQLite, live cog with hierarchy checks in commands. Verdict: **KEEP / POLISH** (migrate store later).

**Vanity Roles.** P0-05. Verdict: **REWRITE or REMOVE.**

- A correct design would watch custom-status text via presence updates (presences intent is on) per member, with a hierarchy check, rate-shaped role edits, and grace periods.
- An alternative is to remove the module.

**InVC (Voice) Role.** Works but ignores `enabled` (R-04); no hierarchy health. Verdict: **FIX / POLISH.**

### 6.6 Growth / engagement

**Giveaways V2.** Button entry; required/blocked role; 1–20 winners; reroll one; end early; archive; DB-backed loop resumes after restart.

- Missing vs GiveawayBot / Giveaway Boat:
  - account age and time-in-server requirements,
  - bonus entries by role,
  - scheduled start in the UI (R-08),
  - recurring giveaways,
  - claim window with auto-reroll,
  - reroll-all,
  - an ephemeral "why you're not eligible" reply,
  - a public result with entry count.
- Do **not** add invite requirements (policy).
- Verdict: **KEEP / POLISH ONLY.**

**Invites V2.** Cache-diff attribution with honest `certain/ambiguous/unknown`, left tracking, leaderboard, and explicit "no invite rewards".

- Gaps:
  - vanity URL joins are not attributed to the vanity bucket (`_refresh` never sets `vanity=True`),
  - cold-cache joins are recorded as unknown,
  - no fake/alt heuristics (account age),
  - no campaign labels,
  - no join-cluster raid view.
- The legacy `inviteTracker` is a help stub only. The dead client `updateInvites` → `PATCH /invites` has no route.
- Verdict: **KEEP / POLISH ONLY.**

**Leveling.** Alive (XP listener, legacy SQLite) but hidden from nav. The dashboard uses a raw channel ID input; rewards and multipliers are not exposed. Verdict: **owner decision**. Either ship it properly (curve presets, multipliers, rewards, MEE6 import) or unload it. Do not keep a hidden live system.

### 6.7 Voice and operations

**Join-to-Create.** Dashboard flow lane, SaveBar, arm/disarm, legacy `j2c_data.db` at cwd. Required cog. Verdict: **KEEP / POLISH.** Later: a Components V2 control panel, a visible rename cooldown (Discord allows about 2 renames per 10 min per channel), a trust list, and a waiting room.

**Config Transfer.** Upload → Review → Map → Changes → Apply; ID remapping by name with a manual map; snapshot before apply plus rollback.

- Modules: welcome, welcome_dm, goodbye, messages, logging, automod, tickets, role_menus, join_roles, role_automation, commands, j2c, autoreact.
- Not covered: giveaways (arguably correct), security settings, verification, custom/vanity/invc roles.
- **Note:** it exports the broken legacy automod format; Automod V2 must ship with a transfer schema version.
- No competitor documents config ID remapping. This is already a differentiator.
- Verdict: **KEEP / POLISH ONLY.**

**Bot Settings.** Prefix only. Verdict: **KEEP**. Later it should host language/timezone/default log channel/bot nickname.

**Access / Platform / Admin.** Root-only grant management, sessions, platform stats, maintenance. Verdict: **KEEP.**

**Recovery.** Snapshots, dry-run plan, raw JSON, execution disabled unless a disposable guild. Honest, but developer-facing. Verdict: **POLISH** (a readable plan diff instead of raw JSON; it remains Root-only).

**Verification V2.** P0-04. Otherwise a reasonable button gate with categories, grace hours and live counts. The legacy `cogs.commands.verification` is still loaded (mutations gated by env), plus a `_verify` help stub.

- Verdict: **FINISH or HIDE HARD.** Finishing requires a publish/preview/republish flow for the verify message, a health check (role below CLS, categories deny correctly), a test-as-member preview, and optionally captcha.
- Until then, the API must refuse `enabled=true`.

### 6.8 Automod — what an excellent CLS implementation becomes

**Information architecture:** Overview · Rules · Violations · Strikes · Settings. Overview shows health, recent violations, top rules, and a false-positive rate.

**Rule model (each rule):**

- **Trigger with real tuning** (progressive disclosure: preset first, then "Advanced"):
  - Spam / flood: messages ≥ N in T seconds (per user, optionally per channel); duplicates ≥ N within T; similarity (normalized text, case/whitespace/zero-width stripped, optional fuzzy ratio).
  - Caps: percentage ≥ X with minimum length L.
  - Mentions: unique user/role mentions ≥ N; `@everyone/@here` attempts by members without permission; mention raid rate.
  - Emoji: count ≥ N (unicode plus custom).
  - Links: allowlist/denylist domains, "only allow in channels", known phishing/scam list.
  - Invites: allow own server and an allowlisted server list.
  - Bad words: list with match mode (whole word / contains / wildcard), normalization (leet, confusables, repeated characters), exceptions, import/export.
  - Attachments: rate, file types, image-only channels.
  - Message policy: newline/length limits, zalgo.
  - Advanced: custom keyword rules; RE2-safe regex only for Root/advanced users with a test bench and a complexity cap.
- **Scope:** global exclusions plus per-rule include/exclude for channels/categories (including future channels) and roles. Deny wins. Staff immunity is an **explicit visible toggle** listing who is immune (the most common competitor complaint).
- **Actions (three fixed slots, not a free list):**
  - Message: delete / keep.
  - Member: none / warn / timeout (60 s–28 d) / kick / ban.
  - Notify: in-channel notice (auto-delete) and/or DM template from the shared composer.
  - Combinations like Delete + Timeout fall out naturally.
- **Engine badge:** "Discord-native" (blocks before posting; writes a native rule within Discord limits: 6 keyword rules, 10 regex, 20 exempt roles, 50 exempt channels) or "CLS" (post-hoc delete). Show capacity meters for native limits. Count native `AUTO_MODERATION_ACTION_EXECUTION` as violations.
- **Health per rule:** Manage Messages for delete; Moderate Members for timeout; Kick/Ban; role hierarchy vs typical targets; native rule sync state.
- **Strike system:** points per rule; expiry per strike; "N strikes within T → action" thresholds evaluated **highest-first, one action only** (fixes MEE6's manual ordering bug); optional repeat multiplier; manual warns from `/warn` feed the same ledger; DM on warn with reason; member history view; clear/pardon with reason.
- **Violations:** paginated, server-side, filterable (rule, member, channel, action, result). Each row shows the matched excerpt (redacted by default), engine, every action with its **result** (e.g. "Timeout failed: role above CLS"), and a "mark false positive" control that offers an allowlist entry.
- **Logging:** a structured Logging V2 category "Automod" with event types per rule family. Human sentence: "Spam detected — @user sent 9 messages in 4 s in #general · Deleted 9, timed out 10 min · Rule: Message flood".
- **Simulator:** "Test a message" and a per-rule **Observe** mode (record would-have actions, no punishment) before Enforce. This reuses the Security observe concept consistently.

### 6.9 Security Center — what an excellent CLS implementation becomes

Do not weaken the architecture: the ENFORCE lock, the DB trigger, Root-only trust, and `discord_mutation=False` in OBSERVE are correct. Rebuild the **presentation and the safe operational surface**.

**Current page** (`components/dashboard/security-panel.tsx`, ~314 lines), stacked in one column:

1. status strip,
2. modes,
3. stored-incident analytics,
4. event stream (`{occurred_at} · {event_type} · {actor_id}`),
5. health (`observability_only`),
6. rules (`aggregate.destructive · 3/60s · DEVELOPMENT_PROPOSAL · eligible`),
7. trusted actors (IDs),
8. incidents (`severity · engine · status · subject_id`),
9. evidence timeline (kind + timestamp, no payload),
10. configuration (phishing select, trap channel, dashboard lock),
11. quarantine (release always 409).

**Target IA (tabs within Protection):**

1. **Overview** — posture banner (Normal / Elevated / Lockdown); mode per engine explained in plain language; a "What CLS will do right now" card (e.g. "Records and alerts. Does not ban, kick, or remove roles."); a health checklist (CLS role position, Ban/Manage Roles/View Audit Log, ops alert destination reachable, snapshot freshness); and open incidents.
2. **Incidents** — a table with human titles ("Mass channel deletion by @mod — 5 in 40 s"); severity chip; attribution confidence; status (Open / Resolved / False positive) with notes. **Incident drawer** with a narrative timeline, evidence payload (redacted), "would have contained" explanation, related audit entries, and actions (Resolve with note, Mark false positive → offer a scoped temporary trust entry, Export).
3. **Detectors** (rules) — grouped by human category (Destructive actions, Permission escalation, Bot additions, Webhooks, CLS impairment). Each card: plain-language description, threshold and window, response (shown as "Observe" with the future ENFORCE response visibly disabled and labeled "Available when Enforcement is unlocked"), last-triggered time, and a 30-day trigger count. Hide `DEVELOPMENT_PROPOSAL` behind a "Threshold tuning: provisional" badge with a tooltip; raw IDs only in a developer drawer.
4. **Trust** — tiers (Owner, Root, Trusted admin, Trusted bot), each entry with who granted it, when, why, and an optional expiry; per-detector scope; a warning "This actor's destructive actions are not contained". Grant/revoke Root-only with a re-auth prompt.
5. **Traps & phishing**
   - **Honeypot for compromised human accounts** (RaidProtect model): a visible channel at the top, warning text, regenerable name, staff/bot exemption. In OBSERVE: delete the message and record (deleting a scam message is a low-risk, message-level action that should be allowed in OBSERVE). In ENFORCE: timeout or softban plus a purge of recent messages.
   - The existing bot trap becomes a sub-option.
   - Phishing: delete in OBSERVE plus record; member punishment shown disabled until ENFORCE.
6. **Quarantine & recovery** — quarantined members with prior roles; Release enabled when a quarantine exists (fix the 409 path, or hide the button and explain); snapshot freshness; a link to Recovery dry-run.
7. **Settings** — dashboard lock, maintenance windows (start/end with reason), ops alert destination with a delivery test and failure count.

**Mode clarity:**

- OBSERVE = "detect, record, alert".
- ENFORCE = "detect and contain", shown as locked with a lock icon and a one-line reason ("Enforcement is locked platform-wide until thresholds are validated").
- Locked controls render in the new observe/locked tone, never as plain grey text.

**Bot Trap verdict:** the observed result is correct by design. Humans are filtered before any check (`center_runtime.py:22`), and bans are hardcoded off (`:30`). But the wording ("Bot trap channel… Untrusted bots that post here are recorded") is easy to read as a generic honeypot, and the real-world use case (compromised human accounts posting scams) is not covered at all. Punishment wording must be visually disabled and labeled as future ENFORCE.

---

## 7. Competitive gap matrices (important modules)

"Runtime verified?" means verified in CLS code or live data, not just present in the UI.

### 7.1 Automod

| Workflow | CLS today | Runtime verified? | ProBot | Dyno | MEE6 | Carl-bot | Specialist (Wick / YAGPDB / Discord) | Gap | CLS opportunity | Pri |
|---|---|---|---|---|---|---|---|---|---|---|
| Rule actually fires from dashboard | No | **Verified broken** | Yes | Yes | Yes (Premium) | Yes | Yes | Total | Truth first | P0 |
| Tunable thresholds | Hardcoded | Verified hardcoded | Mostly fixed (spam 5/5s, caps 70%) | Caps %, counts | Defaults | Rate per window | YAGPDB per-user/per-channel rates | Large | Preset + advanced tuning per rule | P1 |
| Compound actions | Single dropdown | Delete/Warn not implemented | Per detection: block, mute, timeout | Stackable warn/delete/mute/ban | Delete, Warn, Delete+Warn | Comma list incl. tempmute/tempban/dm | Discord: block + alert + timeout | Large | Three fixed slots (message / member / notify) with per-action result | P1 |
| Per-rule exclusions | Global only | Global verified | Per-detection disabled channels/roles | Per-rule affected/ignored | Four scope modes per rule | Global whitelist | Discord: 20 roles / 50 channels per rule | Large | Global + per-rule, deny wins, visible immunity | P1 |
| Strikes / escalation | None (`warn.db` is a counter) | Verified absent | Manual warns only | Auto-mute after N in 5 min | Windowed thresholds, manual ordering | One threshold, never expires | YAGPDB expiry ≤31d, Wick heat decay | Large | Points + expiry + highest-first thresholds | P1 |
| Violation history | None | Verified absent | — | Log channel | Webhook batched 1–5 min | Modlog cases | YAGPDB logs tab (no message/action) | Large | Searchable violations with action results and false-positive control | P1 |
| Native AutoMod integration | None | — | Writes native rules | — | — | — | Wick manages native rules (v5.3) | Medium | Engine badge + capacity meter + native executions as strikes | P2 |
| Simulator / observe | None | — | — | — | — | — | Rare | Opportunity | Per-rule Observe + test-a-message | P2 / DIFF |

**What competitors still lack:** visible staff immunity, explained failures (hierarchy/permission), and escalation that never silently skips. CLS should make these first-class.

### 7.2 Security / Protection

| Workflow | CLS today | Runtime verified? | Wick | Security Bot | SCNX | ProBot | Gap | Opportunity | Pri |
|---|---|---|---|---|---|---|---|---|---|
| Destructive-action detection | Yes (policy engine, attribution) | Verified (observe) | Per-minute and per-hour limits | 10 actions, fixed 10-min window | Sliding windows per action | Per-role limits (Premium) | Small | Keep; humanize | KEEP |
| Containment | Locked platform-wide | Verified locked | Quarantine | Ban/kick/strip/quarantine | Strip/ban/alert-only | Strip admin perms + owner revert code | Large by design | Per-detector graduation with Undo | P1 (product) |
| Observe mode | Global OBSERVE | Verified | "Log Action" | Quarantine for testing | "Alert only" | — | CLS ahead conceptually | "What would have happened" replay | DIFF |
| Trusted actors | Read-only list | Verified no route | Permit tiers 1–5 | Per-action whitelists | Temporary entries with reason | Bot whitelist | Large | Tiered, scoped, expiring, audited | P1 |
| Incident workflow | List + kind timeline | Verified shallow | Logs per type | Logs | Undo button, incomplete flags | — | Large | Incident drawer, resolve, false positive → scoped trust | P1 |
| Honeypot | Bots/webhooks only, record | Verified | — | — | — | — | RaidProtect: humans, visible, purge, softban | Large | Human honeypot with OBSERVE delete | P1 |
| Phishing | Regex, record only | Verified | — | — | — | — | Discord native suspicious-link filter | Medium | Delete in OBSERVE; punish in ENFORCE | P1 |
| Join / raid gate | None | — | Join gate + raid detection | Score-based anti-raid | — | Account-age anti-raid | Large | Join cohort scoring + one-click Discord Security Actions (pause invites/DMs) | P2 |
| Panic / lockdown | None | — | Panic mode, lockdown modes | Beast Mode | — | — | Large | Lockdown with CLS snapshots (after ENFORCE) | P3 |
| Recovery | Dry-run only | Verified | Imaging every 3 h | — | Undo from snapshots | Backup code | Medium | Readable restore diff; disposable gate kept | P2 |

### 7.3 Logging

| Workflow | CLS today | Runtime verified? | Dyno | Carl-bot | ProBot | Wick / Sapphire | Gap | Opportunity | Pri |
|---|---|---|---|---|---|---|---|---|---|
| Core member/role/channel/message/voice | Yes | Verified | Yes | Yes (~30) | 27 | 35 / 80+ | — | KEEP | — |
| Threads, invites, webhooks, emoji/sticker, scheduled events | No | Verified absent | Partial (emoji) | Partial | Invites | Wick: all audit types | Large | Full audit-type union, noisy ones default off | P1 |
| Voice mute/deafen, mod move/disconnect | No | Verified absent | Moves | Moves | Disconnects | — | Medium | Audit-attributed voice moderation | P1 |
| Moderator attribution | certain/unknown | Verified | **No deleter attribution** | Modlog | — | — | CLS ahead | certain / probable / self / unknown, always stated | DIFF |
| Dashboard history | Cursor pages, filters | Verified | None | None | None | YAGPDB snapshots | CLS ahead | Numbered pagination, page size, drawer, export | P1 |
| Per-event appearance | Category colors | Verified | — | — | Per-event color | Sapphire templates | Medium | Category → per-event color/icon/title | P2 |
| Exclusions | Message events only | Verified | Channels + roles (deleted msgs) | Channels, members, prefixes | — | Sapphire many | Medium | Scoped exclusions per category, staff-only mode | P1 |
| Delivery health | Channel perms shown | Verified | Back-queues hours, unexplained | — | Admits missing logs | Wick fallback channel | CLS ahead | Show queue lag + View Audit Log health | P2 |

### 7.4 Commands

| Workflow | CLS today | Runtime verified? | ProBot | MEE6 | YAGPDB | Carl-bot | Discord native | Gap | Opportunity | Pri |
|---|---|---|---|---|---|---|---|---|---|---|
| Enable / roles / channels per command | Yes | **Verified enforced** | Yes | Yes | Cascading | ignore/disable/restrict | Integrations page | — | KEEP gate | — |
| Audience (hide owner/system) | No | Verified exposed | N/A | N/A | N/A | N/A | Hidden if not usable | Large | Audience tags; never list bot-owner commands | P1 |
| Module toggle / bulk | No | — | Module master switch | Plugin toggle | Global → channel → command | — | App-level | Large | Module switch + selection bulk + reset | P1 |
| Subcommand tree | Flat rows | — | — | — | — | — | No native subcommand perms | Medium | Tree with inherited policy | P1 |
| Descriptions / usage / examples | ~116 missing | Verified | Usage tables | — | Docs | — | Required for slash | Large | Curated catalog | P1 |
| Cooldown / visibility / auto-delete | Display only | Verified | Auto-delete options | Visibility modes, delete usage | Ephemeral, auto-delete | restrict | — | Medium | Per-command behavior fields | P2 |
| Effective-access checker | No | — | — | — | Warns on visibility vs access | — | — | Opportunity | "Can @Role use /x in #channel?" | DIFF |
| Slash-first | Hybrid/prefix-heavy | Verified | Slash | Slash | Prefix retired | Prefix off 2026-10-05 | — | Strategic | Slash-first catalog | P2 |

### 7.5 Tickets

| Workflow | CLS today | Verified? | Ticket Tool | TicketsBot | Gap | Opportunity | Pri |
|---|---|---|---|---|---|---|---|
| Panels, forms, claim, close requests, auto-close, blacklist | Yes | Verified | Yes (some premium) | Yes | — | KEEP | — |
| Transcript durability | Stored by CLS + viewer | Verified | Lost if message deleted | 30 days free | CLS ahead | Staff-only hosted viewer, permanent | DIFF |
| CSAT rating | No | Verified absent | — | 1–5 stars | Medium | Post-close rating plus exit survey | P2 |
| Per-staff analytics | Aggregate only | Verified | Claimed-only stats | Per-staff + CSV | Medium | Staff table, first response, SLA breach | P2 |
| Modal inputs beyond text | Text only | Inferred | 5 text | 5 text | Opportunity | Selects / file upload / radio (new Discord inputs) | P2 / DIFF |
| Thread mode / overflow | No | — | Thread style | Thread mode, overflow | Medium | Thread mode for large servers | P3 |

### 7.6 Roles (Menus + Automation)

| Workflow | CLS today | Verified? | Carl-bot | Zira / MEE6 / Dyno | Gap | Opportunity | Pri |
|---|---|---|---|---|---|---|---|
| Button/select/reaction menus, modes, max roles, hierarchy warning | Yes | Verified | Yes | Yes | — | KEEP | — |
| Required/forbidden roles to use menu | No | Verified absent | Whitelist/blacklist per message | — | Medium | Add | P2 |
| Max holders per role, temp roles | No | — | Maxroles, temp | Zira timed roles | Medium | Add | P2 |
| Sticky roles on rejoin | No | — | Reassign on rejoin | Dyno rolepersist | Medium | Allow/deny list | P2 |
| Join roles after screening | Yes | Verified | — | MEE6 | — | KEEP | — |
| Join-role hierarchy health in UI | No | Verified | — | — | Small | Inline badge | P1 (via F1) |

### 7.7 Welcome / Messages

| Workflow | CLS today | Verified? | MEE6 / ProBot / Carl-bot | Discohook | Gap | Opportunity | Pri |
|---|---|---|---|---|---|---|---|
| Shared composer, preview, variables, edit sent | Yes | Verified | Partial | Yes | CLS ahead (one system) | KEEP | — |
| Components V2 | No | Verified | — | Yes | Medium | CV2 with 40-component counter + irreversible warning | P2 |
| Scheduling / recurrence | No | Verified | Carl repeating announcements | No | Medium | Schedule + "run now" | P2 |
| Welcome image card | No | — | Premium at MEE6 | — | Medium | Free layered card | P3 / DIFF |

### 7.8 Giveaways / Invites

| Workflow | CLS today | Verified? | Competitors | Gap | Opportunity | Pri |
|---|---|---|---|---|---|---|
| Button entry, winners, reroll, end early, restart-safe | Yes | Verified | GiveawayBot same | — | KEEP | — |
| Requirements (account age, time in server, level), bonus entries | Roles only | Verified | Giveaway Boat | Medium | Add (no invite reqs) | P2 |
| Scheduled / recurring | API only | Verified | Giveaway Boat | Small | Expose | P2 |
| Invite attribution honesty | certain/ambiguous/unknown | Verified | Invite Tracker counts fakes/left | CLS ahead on honesty | Vanity bucket, fake delay, campaign labels, raid clusters | P2 |
| Invite rewards | Explicitly none | Verified | Removed by Invite Tracker (policy) | Correct | Keep out | — |

---

## 8. Missing capabilities and problems the owner did not identify

1. **Guild allowlist auto-leave cog is broken** (P0-03), so the private-first boundary only holds at restart.
2. **Verification V2 lockout** (P0-04).
3. **Vanity Roles mass-assigns the whole server** (P0-05).
4. **Overview misreports** Automod and Welcome; the legacy `GET /welcome` returns HTTP 500 in the preview (R-12, R-13).
5. **InVC role ignores the Enabled switch** (R-04).
6. **FastGreet** still loaded and capable of duplicate welcomes, using blocking `sqlite3` on the event loop.
7. **Legacy write paths** (Welcomer, AutoRole, legacy `guilds.py` endpoints for welcome/autorole/reactionroles/tickets/invites/autoreact/tracking/joindm) remain mounted and can mutate retired or parallel stores.
8. **Global no-prefix users**: `db/np.db` holds 4 users who can run commands without a prefix in every guild (`bot/core/zyrox.py:111-122`). The `LEGACY_STATE_CLEANUP.md` cleanup is not applied.
9. **Nightmode still reads the "retired" `db/anti.db`** including `extraowners` (`cogs/commands/nightmode.py:26-55`), contradicting the legacy-archive claim.
10. **Commands PUT accepts foreign-guild role/channel IDs** (validator gap).
11. **Security Center runtime (trap + phishing) is not guild-gated** by `security_guild_eligible`, unlike Protection.
12. **Phishing links are never deleted**, even though deletion is a low-risk, message-level action.
13. **Two extra message-moderation pipelines** (`Blacklist` word filter, `Media` channels) run outside Automod with their own SQLite stores.
14. **Warns are not logged and are a bare counter** (`db/warn.db`: guild, user, count). No reasons, no history, no expiry.
15. **"Moderation Command Used" doesn't exist** in Logging V2, and CLS's own module actions have no source attribution.
16. **Logging never writes `probable` attribution**, so ambiguous audit matches lose the actor entirely.
17. **Giveaways Scheduled tab is unreachable** from the create UI.
18. **Leveling is a hidden live system** (XP still accrues with no nav entry).
19. **Config Transfer exports the broken automod format**; Automod V2 needs a schema version and migration.
20. **The runtime environment is missing packages** (wavelink, numpy, chess, deep_translator, mcstatus), so the `Owner` cog (protected `reload`/`sync`) fails to load in preview.
21. **cwd-relative SQLite paths** can silently create empty databases.
22. **`Intents.all()`** maximizes the privileged surface beyond module needs (`bot/core/zyrox.py:41-42`).
23. **Ecosystem shift to slash commands** (Carl-bot prefix shutdown on 2026-10-05; YAGPDB retired prefix), while CLS has ~373 prefix-only commands.
24. **Invite rewards are prohibited** by Discord policy. CLS is already correct, and this must stay a non-goal.
25. **Offensive command aliases** (`fuckban`, `stfu`) and toy surfaces (nitro, slots, blackjack, AI roleplay) in a professional operations product.
26. **`docs/COMMANDS_REFERENCE.md` is stale** (lists retired ticket/antinuke/tracking commands).
27. **Global `tree.sync()` on every ready** (`bot/CodeX.py:91-99`), a rate-limit and drift risk.
28. **Source files and console banner still carry CodeX/ZyroX branding** (file headers, ASCII banner on boot).

---

## 9. Security / permissions findings

### 9.1 Security findings

| ID | Sev | Finding | Evidence |
|---|---|---|---|
| S-01 | P0 | Allowlist auto-leave broken | P0-03 |
| S-02 | P0 | Verification can lock out members | P0-04 |
| S-03 | P0 | Vanity mass role grant/revoke | P0-05 |
| S-04 | P1 | Global no-prefix users in `np.db` | `bot/core/zyrox.py:111-122` |
| S-05 | P1 | Nightmode authorizes via legacy `anti.db.extraowners` | `nightmode.py:26-55` |
| S-06 | P1 | Commands policy accepts foreign-guild IDs | `api/validators/discord_resources.py:21-45` |
| S-07 | P1 | Legacy `guilds.py` routes still mutate retired stores (larger attack and confusion surface) | `api/server.py:97-112` |
| S-08 | P2 | Security Center runtime not guild-gated | `cogs/security/center_runtime.py` vs `security/guild_gate.py:15-19` |
| S-09 | P2 | Owner `Global` cross-guild ban/kick/timeout: intentional, but the highest blast radius. Require a Root re-auth or two-step confirm and log to Ops | `cogs/commands/owner2.py:30+` |
| S-10 | P2 | `Intents.all()` | `core/zyrox.py:41-42` |
| S-11 | P3 | Optional Jishaku via env | `CodeX.py:48,310` |

### 9.2 Discord permission and hierarchy reality

The current health service (`bot/cls_platform/health/permissions.py:10-52`) checks guild-level permission flags per module. It covers Moderation, Antinuke, Tickets, Welcome, JoinToCreate and Logging. It does **not** check:

| Action | Needed | Pre-checked today? | Required UI |
|---|---|---|---|
| Automod delete | Manage Messages (channel-level) | No | Per-rule health badge |
| Automod timeout | Moderate Members + target below CLS + not admin/owner | No | Per-rule badge, "cannot timeout admins" note |
| Automod kick/ban | Kick/Ban Members + hierarchy | No | Per-rule badge |
| Join roles / role rules | Manage Roles + role below CLS + not managed | Rules yes; join roles no | Inline badge on every role picker |
| Role menus | Manage Roles + hierarchy + Add Reactions (reaction mode) | Yes (hierarchy) | KEEP; add Add Reactions |
| Verification | Manage Roles + Manage Channels (category overwrites) + role position | Partial | Health card + publish check |
| Vanity / InVC roles | Manage Roles + hierarchy | No | Inline badge |
| Tickets | Manage Channels + Manage Roles in the target category + Attach Files for transcripts | Guild-level only | Per-category health |
| Logging | View Channel / Send / Embed in log channel; **View Audit Log** for attribution | Channel yes; audit no | Add an audit-log health row |
| Welcome | Send + Embed + Attach Files (media) in channel; DMs may be closed | Channel yes | KEEP; show DM delivery failure count |
| Giveaways | Send + Embed in channel | No | Inline check on publish |
| J2C | Manage Channels + Move Members + Connect in category | Guild-level | Per-category check |
| Security containment (future) | Ban Members, Manage Roles, hierarchy above all staff roles | Stub string | Health checklist on Overview |
| Messages using external emoji | Use External Emojis | No | Composer warning |

**Principle:** health is computed **before** save and shown inline next to the control that needs it. Runtime failures are recorded per action with the Discord error, never swallowed.

---

## 10. Legacy / split-system findings

**Loader:** 119 cogs load and 9 are skipped (`bot/cogs/cog_loader.py`). Skipped and safe: Tracking, Giveaway (×2), TicketCog, Logging, ReactionRoles, Autorole2, AutoReaction, AutoReactListener. The 17 legacy antinuke listeners are not loaded (dead code only; accidental re-add would double-punish).

| Legacy component | Still active? | Conflict | Sev |
|---|---|---|---|
| `cogs.automod.*` (6 cogs) + `cogs.commands.automod` | Yes, the only automod | Dashboard vocabulary mismatch; legacy prefix config uses a different vocabulary on the same table | P0 (fix via V2) |
| `cogs.commands.fastgreet` | Yes, `on_member_join` | Duplicate welcome vs V2; blocking sqlite3 | P1 |
| `cogs.commands.welcome` (Welcomer, **required**) | Commands only | Writes `db/welcome.db` without the V2 wrapper | P1 |
| Legacy `GET/PATCH /guilds/{id}/welcome` | Yes | 500 on V2 data; Overview depends on it | P1 |
| `cogs.commands.autorole` + `/autorole` API | Yes | Writes a store V2 no longer reads | P1 |
| `cogs.events.auto` ("Autorole") | Yes | Misnamed; only a bot-join DM | P3 |
| `cogs.commands.verification` | Yes (mutations env-gated) | Parallel verification system | P2 |
| `cogs.commands.joindm` | Yes | Defers to `greet`; safe | — |
| `cogs.commands.vanityroles` | Yes | P0-05 | P0 |
| `cogs.commands.Invc` | Yes | Ignores `enabled` | P1 |
| `cogs.commands.Blacklist` (words), `Media` | Yes | Parallel message moderation | P1 |
| `cogs.commands.nightmode` | Yes | Reads `anti.db` extraowners | P1 |
| `cogs.commands.np` / `db/np.db` | Yes | Global no-prefix | P1 |
| Sticky (commands + events listener) | Yes | Two sticky handlers | P2 |
| `cogs.zyrox.*` help cogs (~25) | Yes | Help catalog advertises retired `/ticket` etc. | P2 |
| `guilds.py` legacy routes: reactionroles (`rr.db`), tickets (`ticket.db`), invites (`invite.db`), autoreact (duplicate GET), tracking, joindm, leveling, vanity, customrole, j2c, prefix | Mounted | Retired stores still mutable; duplicate handlers; dead `PATCH /invites` client | P1 |
| SQLite files | 35 under `db/` + `j2c_data.db` + `rr.db` | Dead: `ticket.db`, `giveaways.db`, `autoreact.db`, `invite.db` (API still wired to some) | P2 |

**Recommended containment order** (report only, nothing deleted):

1. Skip FastGreet.
2. Make Welcomer and AutoRole commands read-only redirects ("Use the dashboard").
3. Return 410 from legacy `guilds.py` write routes that have V2 equivalents, and point Overview to V2 endpoints.
4. Move Nightmode off `anti.db`.
5. Apply the `np.db` cleanup.
6. Fold the word blacklist and Media rules into Automod V2.
7. Unload `cogs.commands.verification` and leveling/sticky per the owner's product decisions.

---

## 11. Global shared-component opportunities

Build these once in F1 and adopt them module by module (never all modules in one sprint):

1. **Module health contract + `HealthBadge` / `HealthPanel`.** One backend function per module returns `{status, checks:[{id, label, ok, fix_hint, scope}]}`, including hierarchy checks for every referenced role and permission checks per referenced channel. It is consumed by the Overview, each page header, and inline next to pickers. Replaces the hardcoded `observability_only` and the per-module Overview heuristics.
2. **`RolePicker` / `ChannelPicker` with inline health.** Shows "above CLS", "managed", "CLS can't send here" at selection time.
3. **Save semantics.** `SaveBar` everywhere a draft exists: dirty indicator, Discard, Save, leave guard, keyboard shortcut, field-level error mapping. Toggle-and-save-immediately is allowed only for single switches, and labeled.
4. **`DetailsDrawer`.** A right-side drawer (sheet on mobile) for event, incident, violation and command details. Developer data (IDs, raw JSON) lives in a collapsed "Developer" tab inside the drawer, with copy buttons.
5. **`DataTable` with server pagination.** Page numbers plus a page-size select (25 / 50 / 100, default 25), total count when cheap, sticky filters in the URL, keyboard row navigation, empty/loading/error states. Used by Logging, Violations, Incidents, Commands, Transcripts, Giveaways.
6. **Label registry.** Maps internal IDs (`aggregate.destructive`, `sequence.cls_impairment`, `DEVELOPMENT_PROPOSAL`, log event keys, automod rule types) to human title, description, icon and severity. Raw IDs appear only in developer views.
7. **Status tone system.** ok / warn / danger / info (re-tinted toward the brand) / **locked-observe**, with icon and copy patterns ("Locked — available when Enforcement is unlocked").
8. **`ActionResult` chips.** For every action CLS takes on Discord (succeeded / failed: reason / skipped: reason), reused by Automod, Security, Role Automation, Welcome DMs, Giveaways.
9. **`ActivitySentence` renderer.** Actor (with confidence), verb, target, object, source module, relative time; shared by Logging, Overview activity and incident timelines.
10. **Decorative asset rules.** Global non-draggable images/SVG; `ClsMark` variants; the favicon set.
11. **`EmptyState` and `ErrorState` with retry**, banning `catch(() => null)` page loads.
12. **Shared `Button` focus ring** and focus-visible audit across primitives.

---

## 12. Backlog (P0 / P1 / P2 / P3)

Counts: **P0 = 5, P1 = 29**, P2 = 34, P3 = 12.

### 12.1 P0: release blockers

| ID | Area | Type | Item | Ref | Phase |
|---|---|---|---|---|---|
| P0-01 | Automod | RUNTIME MISMATCH | Dashboard-configured rules are never enforced (key/value vocabulary mismatch with legacy cogs) | §2, R-01 | F0 hotfix → F2 |
| P0-02 | Automod | BUG / RUNTIME MISMATCH | "Delete" / "Warn" not implemented; disable never persists | §2, R-02 | F0 hotfix → F2 |
| P0-03 | Platform | SECURITY / BUG | `on_guild` allowlist auto-leave cog crashes on load (`client = zyrox()`); private-first boundary only enforced at startup | §2, S-01 | F0 |
| P0-04 | Verification | BUG / SECURITY | Enabling Verification V2 locks every new member out (no button publisher) | §2, S-02 | F0 |
| P0-05 | Vanity Roles | RUNTIME MISMATCH / SECURITY | Mass-assigns/revokes a role for the whole server from a public invite check | §2, R-03, S-03 | F0 (disable/guard) → F7 |

### 12.2 P1: must fix before serious production

| ID | Area | Type | Item | Ref | Phase |
|---|---|---|---|---|---|
| P1-01 | Automod | MISSING FEATURE | V2 engine: per-rule config, thresholds/presets, compound actions (message / member / notify), timeout durations | §6.8, §7.1 | F2 |
| P1-02 | Automod | MISSING FEATURE / UX | Global + per-rule exclusions (roles, channels, users; deny wins) with visible staff immunity | §6.8 | F2 |
| P1-03 | Automod | MISSING FEATURE | Warning / strike system: points, reasons, expiry, escalation thresholds, history | §6.8 | F2 |
| P1-04 | Automod | MISSING FEATURE / PERFORMANCE | Violation history + structured log events + permission/hierarchy preflight; remove silent `except: pass`; fix ~20 SQLite opens per message | §6.8, R-16 | F2 |
| P1-05 | Moderation | TECH DEBT / RUNTIME MISMATCH | Unify message moderation: fold word Blacklist (`blword.db`) and Media channels into the Automod pipeline | §10, R-22 | F2 |
| P1-06 | Security | UX | Security Center IA rebuild (Overview / Detectors / Incidents / Trust / Recovery; no single long console) | §6.9 | F3 |
| P1-07 | Security | UX | Humanized taxonomy via label registry; raw engine IDs only in developer view | §6.9, G-09 | F3 |
| P1-08 | Security | RUNTIME MISMATCH | Punishment controls truthful (visibly locked as future ENFORCE); phishing message deleted in OBSERVE | R-05 | F3 |
| P1-09 | Security | MISSING FEATURE / UX | Human honeypot (compromised accounts) with delete + record; trap copy fixed; remove hardcoded `enforce_locked=True` in favor of the platform lock | R-06, §6.9 | F3 |
| P1-10 | Security | BUG / MISSING FEATURE | Quarantine Release (always 409); trusted-actor grant/revoke API + UI (tiered, scoped, expiring); maintenance window management | R-15, R-18, R-19 | F3 |
| P1-11 | Security | MISSING FEATURE | Incident detail drawer: evidence, timeline, resolve, false positive → scoped trust | §7.2 | F3 |
| P1-12 | Security | RUNTIME MISMATCH | Real permission & hierarchy health on Protection (replace hardcoded `observability_only`) | R-17, §9.2 | F1 → F3 |
| P1-13 | Logging | MISSING FEATURE | Event coverage gaps: threads, invites, webhooks, emoji/sticker, scheduled events, voice mute/deafen, mod move/disconnect, AutoMod executions, moderation commands | §7.3 | F4 |
| P1-14 | Logging | MISSING FEATURE / UX | Event depth & attribution: `probable` confidence, CLS module source, before/after diffs, human sentences | §7.3, §8.15-16 | F4 |
| P1-15 | Logging | UX | Activity workspace: numbered pagination (25 default, 25/50/100), details drawer replacing inline `<details>` | G-10, §11 | F1 → F4 |
| P1-16 | Logging | RUNTIME MISMATCH | Exclusions apply to message events only; scope them per category; add View Audit Log health | R-07, §9.2 | F4 |
| P1-17 | Commands | UX | IA rebuild: audience filter (hide bot-owner/system), module → command → subcommand tree, module + bulk toggles, onboarding, explanation of Discord vs CLS permission layers | §7.4 | F5 |
| P1-18 | Commands | UX / DATA | Catalog curation: ~116 missing descriptions, offensive aliases (`fuckban`, `stfu`), decide fun/AI/nitro surface | §8.25 | F5 |
| P1-19 | Commands | SECURITY / BUG | Policy PUT accepts role/channel IDs from other guilds | S-06 | F0 |
| P1-20 | Legacy | RUNTIME MISMATCH | FastGreet still greets on join (duplicate welcome, blocking sqlite3) | §10 | F1b |
| P1-21 | Legacy | BUG / RUNTIME MISMATCH | Welcomer commands + legacy welcome API (500 on V2 data) write outside V2 | R-11, R-13 | F1b |
| P1-22 | Legacy | RUNTIME MISMATCH | AutoRole split brain (legacy command/API write a store V2 no longer reads) | R-10 | F1b |
| P1-23 | Legacy | TECH DEBT / SECURITY | Legacy `guilds.py` endpoints (reactionroles, tickets, invites, autoreact duplicate GET, tracking, joindm; dead `PATCH /invites`) | S-07, §10 | F1b |
| P1-24 | Overview | RUNTIME MISMATCH | Overview misreports Automod and Welcome (legacy sources) | R-12, R-13 | F0 |
| P1-25 | InVC | RUNTIME MISMATCH | `enabled` ignored at runtime | R-04 | F0 |
| P1-26 | Platform | SECURITY | Global no-prefix users (`np.db`, 4 users) + Nightmode authorizing from `anti.db.extraowners` | S-04, S-05 | F1b |
| P1-27 | Platform | MISSING FEATURE | Permission/hierarchy health primitive gaps: Automod (Manage Messages / Moderate Members), join-role hierarchy, giveaways, verification, InVC/vanity | §9.2 | F1a |
| P1-28 | Global UI | UX / A11Y | Save semantics standard (SaveBar + leave guard) and `Button` focus-visible | G-01, G-02 | F1a |
| P1-29 | Landing | VISUAL | Rectangular glow artifact in hero | L-01 | F6 |

### 12.3 P2: important polish / differentiation

| ID | Area | Item | Ref |
|---|---|---|---|
| P2-01 | Global | Favicon set (square SVG + ICO + apple-icon + manifest; heavier glyph at 16 px) | G-06 |
| P2-02 | Global | Global non-draggable decorative images (keep config-transfer drop zone) | G-05 |
| P2-03 | Global | Info tone re-tinted toward brand; new locked/observe tone | §3.3 |
| P2-04 | Global | Raw Tailwind semantic colors → tokens | G-03 |
| P2-05 | Global | Pre-CLS `rounded-3xl` / slate pockets; delete dead components | G-04 |
| P2-06 | Global | API errors swallowed into empty states → `ErrorState` with retry | G-08 |
| P2-07 | Global | Naming drift Antinuke / Protection / Security Center | G-07 |
| P2-08 | Auth | Richer no-access page (reason, which account, invite-bot / switch-account / contact owner) | §3.5 |
| P2-09 | Landing | Domain icons at hex vertices; autonomous domain cycling | L-02, L-03 |
| P2-10 | Landing | Richer "What runs inside" detail; hero → section light transition | L-04, L-05 |
| P2-11 | Automod | Native Discord AutoMod integration (engine badge, capacity, executions as strikes) | §7.1 |
| P2-12 | Automod | Per-rule Observe mode + message tester | §7.1 |
| P2-13 | Automod | Config Transfer schema version + migration for Automod V2 | §8.19 |
| P2-14 | Security | Security Center runtime gated by `security_guild_eligible` | S-08 |
| P2-15 | Security | Join cohort / raid scoring + Discord Security Actions shortcut | §7.2 |
| P2-16 | Security | Recovery: readable restore diff | §7.2 |
| P2-17 | Security | Owner `Global` moderation: re-auth / two-step + Ops log | S-09 |
| P2-18 | Logging | Per-event appearance overrides (color/icon/title) on top of category | §7.3 |
| P2-19 | Logging | Delivery health (queue lag), export | §7.3 |
| P2-20 | Logging | Sticky preview / "Older" pagination semantics cleanup (absorbed by P1-15 if done together) | — |
| P2-21 | Commands | Per-command cooldown / visibility / auto-delete become real settings | R-09 |
| P2-22 | Commands | Slash-first strategy for the catalog | §8.23 |
| P2-23 | Tickets | CSAT rating + per-staff analytics (first response, SLA) | §7.5 |
| P2-24 | Tickets | Modal selects / file upload inputs | §7.5 |
| P2-25 | Messages | Components V2 + scheduling / recurrence | §7.7 |
| P2-26 | Giveaways | Scheduling in create UI; requirements (account age, tenure, level), bonus entries | R-08, §7.8 |
| P2-27 | Invites | Vanity bucket, fake-join delay, campaign labels, raid clusters; cold-cache honesty | §7.8 |
| P2-28 | Role Menus | Required/forbidden roles, max holders, temp roles, sticky roles | §7.6 |
| P2-29 | Leveling | Ship or stop: XP accrues with hidden nav | R-21 |
| P2-30 | Verification | Unload legacy `cogs.commands.verification` | §10 |
| P2-31 | Platform | Replace `Intents.all()` with module-derived intents | S-10 |
| P2-32 | Platform | Missing runtime packages (wavelink, numpy, chess, deep_translator, mcstatus) / unload their cogs; `Owner` cog must load | §4.5 |
| P2-33 | Platform | Absolute SQLite paths (cwd-independent) | §4.5 |
| P2-34 | Platform | Decide ship/hide for live dashboard-less listeners (sticky ×2, autoresponder, AFK, counting, birthdays, jail); help catalog stops advertising retired commands | R-22, §10 |

### 12.4 P3: later

| ID | Item |
|---|---|
| P3-01 | `docs/COMMANDS_REFERENCE.md` stale |
| P3-02 | Global `tree.sync()` on every ready → explicit sync command / hash check |
| P3-03 | CodeX/ZyroX banners and file headers |
| P3-04 | Recovery raw JSON readability (beyond P2-16) |
| P3-05 | Next.js middleware for auth (defense in depth) |
| P3-06 | Chakra Petch doc drift |
| P3-07 | Ticket priority/tags/notes/transfer dashboard |
| P3-08 | Ticket thread mode / overflow |
| P3-09 | Welcome image card |
| P3-10 | Panic / lockdown mode (requires ENFORCE) |
| P3-11 | `cogs.events.auto` misnamed "Autorole" |
| P3-12 | Landing nav "Sign in" below `sm`; Jishaku env flag review |

---

## 13. Differentiation opportunities

Ranked by leverage and feasibility on the current architecture:

1. **Truthful operations (top).** Make every configured thing answer three questions in the UI: *Will it work?* (preflight permissions + hierarchy, §9.2), *Did it work?* (per-action result chips with Discord error reason), and *Who did it, how sure?* (certain / probable / self / unknown). No competitor does all three, and most admit silent failures (Dyno log back-queues, ProBot missing logs, Carl-bot staff immunity confusion). CLS already has attribution confidence, the incident model, and the health service seed.
2. **Observe-first security graduation.** Per-detector OBSERVE → ENFORCE with a "what would have happened" replay over the last 7 / 30 days of incidents, explicit Undo for each containment, and expiring scoped trust. It beats Wick's "Log Action" and SCNX's "alert only" because it turns observation into evidence for turning enforcement on.
3. **Automod with explained escalation.** Strike points with expiry and visible staff immunity ("this member is exempt because of @Moderator"), plus a message tester. These are exactly the complaints about Carl-bot and MEE6 automod.
4. **One composer everywhere, Components V2 ready.** Messages, Welcome, Tickets, Role Menus, plus automod and security notifications from the same composer with the 40-component counter and an irreversible-conversion warning.
5. **History in the dashboard, not just in channels.** Logging, violations, incidents, transcripts: searchable, paginated, drawer-based, exportable. Competitors mostly post into Discord channels only.
6. **Policy-safe growth analytics.** Invite attribution confidence, raid cluster detection on join cohorts, campaign labels, and explicitly no invite rewards.
7. **Effective-access checker.** "Can @Role use /ban in #general?" combines Discord integration permissions with the CLS policy and answers in one sentence.

**Non-goals:** do not chase music, economy, games, or AI chat; do not rewrite modules that work just because a competitor's UI differs.

---

## 14. Recommended recovery roadmap

Each phase ends with a live acceptance pass (Section 15) on the preview guild with an alt account. A phase is not "done" because tests pass.

| Phase | Scope | Items | Depends on | Can run in parallel with |
|---|---|---|---|---|
| **F0 Safety & Truth** | Small, surgical fixes; days | P0-03 allowlist cog; P0-04 verification enable guard (refuse to enable without a published verify message, or publish it); P0-05 vanity disable/guard; P0-01/02 minimal vocabulary hotfix (map dashboard keys/actions, implement delete, persist disable) **or** disable the Automod page with an honest banner; P1-24 Overview truth; P1-25 InVC enabled; P1-19 cross-guild IDs | — | F6 |
| **F1a Shared primitives** | Platform contracts | P1-27 health service + `HealthBadge`; P1-28 SaveBar standard + focus; status tones (P2-03); `DetailsDrawer`; `DataTable` pagination (foundation for P1-15); label registry; `ActionResult`; `ActivitySentence`; non-draggable (P2-02); favicon (P2-01); `ErrorState` (P2-06) | F0 | F1b, F6 |
| **F1b Legacy containment** | Backend | P1-20 FastGreet; P1-21 Welcomer + legacy welcome API; P1-22 AutoRole; P1-23 legacy endpoints → 410 / V2; P1-26 np.db + Nightmode; P2-30, P2-32, P2-33 | F0 | F1a, F6 |
| **F2 Automod V2** | Full product, alone in its sprint | P1-01..P1-05, P2-11..P2-13. Defines the violation log event contract consumed by F4 | F1a (health, drawer, table, ActionResult), F1b | F6 only |
| **F3 Security Center product** | UI rebuild on existing safety model | P1-06..P1-12, P2-14..P2-17 | F1a | F4 |
| **F4 Logging completion** | Coverage + workspace | P1-13..P1-16, P2-18..P2-20 (consumes F2 violation events) | F1a, F2 event contract | F3 |
| **F5 Commands rebuild** | IA + catalog | P1-17, P1-18, P2-21, P2-22 | F1a; owner decisions on fun/AI surface and slash strategy | F7 |
| **F6 Public surfaces** | Frontend only | P1-29 glow, P2-07..P2-10, P3-12 | — | Any phase |
| **F7 Module polish wave** | Competitive depth | P2-23..P2-29, P2-31, P2-34, Vanity rewrite, Verification finish | F1a | F5 |
| **F8 Release candidate** | Full acceptance | All of Section 15 on a clean deployment; Section 16 sign-off | All | — |

**Acceptance criteria per phase (summary):**

- **F0:** A fresh guild not in the allowlist is left within seconds of joining (no restart). Enabling verification without a published button is refused in the UI and the API. Vanity cannot assign to members without a matching status. A dashboard automod rule fires on the alt account with the selected action, or the page is honestly disabled. Overview Welcome/Automod rows match runtime.
- **F1a:** Every module page header shows a computed health status; a role above CLS shows an inline warning in every role picker; every editable page uses SaveBar with a leave guard; keyboard focus is visible on every button.
- **F1b:** Joining with the alt account produces exactly one welcome (V2). Legacy write routes return 410. `np.db` cleanup is applied. Nightmode no longer opens `anti.db`.
- **F2:** On the alt account, each rule type fires with each action; compound actions report per-action results; exempt roles show as exempt; strikes accrue and expire; the escalation threshold timeouts the member; a violation appears in history and in Logging; missing Moderate Members shows a red health badge before save.
- **F3:** No raw engine ID visible outside developer view; incidents open in a drawer with evidence and resolve / false-positive actions; trust can be granted/revoked with expiry; Release works; a phishing link posted by the alt is deleted in OBSERVE; a human posting in the honeypot is recorded and the message removed.
- **F4:** Every event in the coverage list has a live test result; ambiguous audit matches show "probable"; pagination defaults to 25 with page numbers; details open in a drawer; exclusions apply where the UI says they do.
- **F5:** A server admin sees no bot-owner commands; module toggle disables all its commands live; every listed command has a description; the effective-access checker matches what the alt account experiences.
- **F6:** No rectangular glow edge at any viewport width or pointer position; favicon legible at 16 px; reduced motion respected.

---

## 15. Manual acceptance checklist

Run on the preview guild with the owner account and one **alt account** that has no staff roles. No credentials, tokens, or cookies are ever shared with an agent; the human operator performs the steps and records results.

**Setup checks**

- [ ] Bot role position is above all roles it must manage; note it.
- [ ] Alt account has default permissions only.
- [ ] Preview log shows no cog load errors (Owner cog loads).

**Platform / access**

- [ ] Invite the bot to a guild not in the allowlist → bot leaves without restart.
- [ ] Non-admin opens `/dashboard/<guild>` → no-access page with reason.
- [ ] Remove the bot from a guild → dashboard shows the invite state, not an error.

**Automod (repeat per rule: spam, caps, links, invites, mentions, emoji)**

- [ ] Enable the rule with Delete → alt triggers it → message deleted, nothing else.
- [ ] Change to Delete + Timeout 10 min → both happen; result visible in violations.
- [ ] Disable the rule → alt triggers it → nothing happens (after reload, the rule is still off).
- [ ] Add the alt's role to exclusions → no action; the UI shows the role as exempt.
- [ ] Remove Moderate Members from CLS → the UI warns before save; runtime records "failed: missing permission".
- [ ] Strikes: trigger N times → escalation fires; wait past expiry → count drops.

**Security Center**

- [ ] Alt posts a phishing test link → message deleted in OBSERVE; incident recorded with human-readable title.
- [ ] Alt posts in the honeypot channel → message removed and recorded; no ban while ENFORCE is locked; the UI shows the ban as locked.
- [ ] Open the incident → drawer shows evidence and timeline; mark as false positive → scoped trust created with expiry.
- [ ] Grant then revoke a trusted actor → reflected in the list and in the audit trail.
- [ ] Release a quarantined test member → succeeds.
- [ ] Permission health lists real missing permissions after you remove one from CLS.

**Logging**

- [ ] For each event in the coverage list, perform the action with the owner or alt → event appears in the right channel and in the dashboard with actor and confidence.
- [ ] Delete the alt's message as a moderator → attribution shows the moderator (certain or probable), never blank.
- [ ] Pagination: 25 rows default, page numbers work, page size 50/100 works, filters persist in the URL.
- [ ] Open an event → drawer; developer tab shows IDs and copy works.
- [ ] Exclude a channel → no events from it for the categories the UI claims.
- [ ] Remove View Audit Log from CLS → health warns; attribution becomes "unknown" (not wrong).

**Commands**

- [ ] Admin view lists no bot-owner/system commands.
- [ ] Disable a module → alt cannot run any command in it (prefix and slash).
- [ ] Restrict a command to a role → alt is denied with a clear message; adding the role allows it.
- [ ] Try to save a role ID from another guild via the API → rejected.

**Welcome / Roles / Verification / Vanity / InVC**

- [ ] Alt leaves and rejoins → exactly one welcome message, one DM if enabled, join roles assigned.
- [ ] Join role placed above CLS → the UI warns before save.
- [ ] Verification: cannot be enabled until the button is published; alt verifies and gains access.
- [ ] Vanity: only members whose status contains the text get the role (or the module is disabled).
- [ ] InVC disabled → joining voice assigns nothing.
- [ ] Role menu: alt picks and removes roles; max roles enforced.

**Tickets / Messages / Giveaways / Invites / J2C / Config Transfer**

- [ ] Alt opens a ticket from the panel, staff claims it, it closes, and the transcript is viewable in the dashboard.
- [ ] Send and edit a message from Messages; the edit appears in Discord.
- [ ] Create a giveaway, alt enters, restart the bot before it ends → it ends correctly; reroll works.
- [ ] Alt joins via a tracked invite → attribution recorded with confidence.
- [ ] Join the J2C hub → a channel is created and deleted when empty.
- [ ] Export the config, import into a test guild → modules match (including Automod V2 schema).

**Global UI**

- [ ] Tab through each page → focus is visible on every control.
- [ ] Leave a page with unsaved changes → guard appears.
- [ ] Drag avatars, icons and logos → no ghost image (except the drop zone).
- [ ] Favicon legible in the browser tab; landing hero has no rectangular glow edge at 1280, 1440, 1920 and mobile widths.

---

## 16. Definition of release-ready

CLS OS is release-ready only when **all** of the following are true:

1. **Zero open P0** and **zero open P1** items, each closed by a recorded live acceptance result (Section 15), not only by passing tests.
2. **Every visible control does what it says.** No setting in the dashboard is ignored by runtime; anything not implemented is either hidden or visibly marked locked or unavailable with the reason.
3. **Every action CLS takes on Discord is preflighted and reported.** Permission and hierarchy health is shown before save, and runtime failures are recorded with the Discord error. No silent `except: pass` on moderation paths.
4. **The private-first boundary holds at runtime**: unallowlisted guilds are left immediately; no global no-prefix bypass; no authorization from retired stores.
5. **One source of truth per module.** No legacy cog or legacy API route writes configuration that a V2 module reads, or acts on the same Discord event as a V2 module.
6. **Overview tells the truth.** Every Overview status is computed from the same store and health service the runtime uses.
7. **Restart persistence verified** for Automod strikes, giveaways, tickets, verification, security incidents and logging routes.
8. **Guild isolation verified**: no API accepts IDs from another guild; Security runtime respects guild eligibility.
9. **Runtime environment complete**: all loaded cogs load without errors in the deployment image; SQLite paths are absolute or retired.
10. **Global UI standards met**: SaveBar semantics, visible focus, token colors, error states with retry, non-draggable decorative assets, legible favicon, landing without artifacts.
11. **Automod, Security Center and Commands each pass their phase acceptance criteria** (Section 14) and can be explained to a new server admin without developer vocabulary.
