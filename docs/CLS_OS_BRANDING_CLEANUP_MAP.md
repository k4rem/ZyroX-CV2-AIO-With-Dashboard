# CLS OS Branding Cleanup Map

**Scope:** repository-wide audit of user-facing ZyroX identity, Neural Core copy, fake metrics/infrastructure claims, `NEXT_PUBLIC_BRAND_NAME`, "Add to Server", old metadata and marks.
Line numbers refer to commit `e383420`. Ranges are approximate where a block spans many lines.
**This document performs no replacements.** It assigns each occurrence a classification and the Phase 1.5 task (A/B/C, see `CLS_OS_PHASE_1_5_IMPLEMENTATION_PLAN.md`) that handles it.

Classifications:

- **REMOVE IN PHASE 1.5**: the string, claim or surface disappears (no replacement text).
- **REPLACE WITH CLS OS**: keep the element, change identity/copy to CLS OS (or factual copy).
- **SAFE INTERNAL LEGACY NAME, DEFER**: not user-facing; leave until Phase 11 legacy cleanup.
- **NEEDS MANUAL REVIEW**: owner decision, legal consideration, or Discord-side asset that code search cannot judge.

Method: `rg -i "zyrox|neural|NEXT_PUBLIC_BRAND|add to server|codex|rayexo|99\.9|edge (region|cluster|shard|network)|global (shard|edges|reach|uptime)|support matrix|deauthorize|initialize console|12M|5,000|5\.2K"` over `dashboard/` and `bot/` (excluding `node_modules`, `.next`, lockfiles, virtualenvs, databases), plus manual reading of every dashboard page and shared component.

---

## 1. Summary

| Area | Occurrences | Outcome |
|---|---|---|
| Landing `dashboard/app/page.tsx` | 25+ (brand, Neural Core, fake stats, fake infra, Add to Server, FAQ) | Whole page replaced in Task B. |
| Dashboard shell and home | ~12 | Replaced in Task A (shell) and Task C (home/overview). |
| Guild overview | Entire page is hardcoded/fake | Replaced in Task C. |
| Feature forms | 6 user-facing strings | Replaced in Task C. |
| Public static pages (`docs`, `privacy`, `terms`) | ~25 | `docs` removed as a surface; `privacy`/`terms` rewritten (Task B), owner review of legal text. |
| Metadata / env | 5 | Replaced in Task B. |
| File banners "CodeX Devs", LICENSE | every source file | Internal; MIT notice retained. Manual review. |
| Bot (Discord-facing) | `BRAND_NAME` default, custom emoji | Owner env change + manual review; code deferred. |
| Bot internals (`core.zyrox`, `cogs/zyrox/`, `ZYROX_*` constants) | ~100 | Deferred to Phase 11. |

---

## 2. Dashboard: landing and public pages

### 2.1 `dashboard/app/page.tsx` (landing)

The entire file is replaced by the CLS OS gateway in **Task B**. Occurrence-level classification for completeness:

| Line | Occurrence | Classification |
|---|---|---|
| 22–47 | 25 imported Lucide icons used as decorative feature tiles | REMOVE IN PHASE 1.5 |
| 52, 55–56 | Red pulsing blur blobs background (`bg-red-500/[0.03] blur-[150px] animate-pulse`) | REMOVE IN PHASE 1.5 |
| 63–64 | `Bot` icon in red gradient tile used as a logo | REPLACE WITH CLS OS (official CLS mark) |
| 67 | `{process.env.NEXT_PUBLIC_BRAND_NAME \|\| "ZyroX"}` wordmark | REPLACE WITH CLS OS |
| 68 | "Dashboard" sub-label under wordmark | REMOVE IN PHASE 1.5 |
| 73–76 | Nav links Features / Architecture / Modules / Network | REMOVE IN PHASE 1.5 |
| 85 | Button "Initialize Console" | REPLACE WITH CLS OS ("Sign in with Discord") |
| 99 | "Neural Core v2 Active • Global Shard 07" | REMOVE IN PHASE 1.5 |
| 102–104 | Headline "Evolution Moderated." with gradient text (detector: `gradient-text`) | REPLACE WITH CLS OS |
| 107–109 | "hyper-performance Discord engine… world's most elite communities" | REPLACE WITH CLS OS (factual lead) |
| 118 | "Open Dashboard" CTA | REPLACE WITH CLS OS (single sign-in CTA) |
| 120–123 | **"Add to Server"** button | REMOVE IN PHASE 1.5 |
| 127–167 | Fake dashboard mockup, "sec.neural.core // active_node_01" | REMOVE IN PHASE 1.5 |
| 175–176 | "High-Scale Infrastructure… 20+ edge regions. Zero lag, zero downtime." | REMOVE IN PHASE 1.5 |
| 180–186 | Fake metrics "12ms Ping Latency", "99.99% Global Uptime" | REMOVE IN PHASE 1.5 |
| 193–228 | Feature grid: "Neuro-Security… Contextual AI analysis", "Edge Dispatch", "4K rank card", "enterprise encryption and lifetime transcripts", "zero-latency WebSocket", "off-site neural vaults" | REMOVE IN PHASE 1.5 |
| 247–283 | "Neural Core Technology", "custom Rust-based microkernel", "Custom DSL… ZyroX scripting language", "FPGA Ready", "Zero Trust… cryptographically verified", "Low Entropy", orbiting rings around `Bot` | REMOVE IN PHASE 1.5 |
| 288–319 | "The Matrix Complete." module grid with invented blurbs ("Predictive user metrics", "Support at lightspeed") | REPLACE WITH CLS OS (factual domain list, design §13.1) |
| 322–359 | "Global Reach", "12 million combined users", "12M+ Users Protected", "24 Edge Clusters", "5.2K Verified Communities", globe visual | REMOVE IN PHASE 1.5 |
| 361–384 | FAQ: "Is the ZyroX Engine free", "AES-256 encrypted at rest", "Migration Matrix", "What is the 'Neural Core'?" | REMOVE IN PHASE 1.5 |
| 387–408 | CTA "Ready to Evolve?", "Join 5,000+ communities… ZyroX Engine… 30 seconds", "Get Started Free", "Neural Uplink: Stable", external noise image `grainy-gradients.vercel.app` | REMOVE IN PHASE 1.5 |
| 416 | "{brand} Engine" footer wordmark | REPLACE WITH CLS OS |
| 418–419 | "Open-source, secure, and infinitely scalable" | REMOVE IN PHASE 1.5 |
| 425–435 | Footer links "GitHub Repository", "API References", "Privacy Shield", "Discord Server" (all `#` except docs/privacy/terms) | REPLACE WITH CLS OS (Privacy, Terms, CLS Discord only) |
| 441 | "© 2026 {brand} Development // Advanced Neural Infrastructure." | REMOVE IN PHASE 1.5 |
| 445–447 | "All Nodes Operational" pulsing status | REMOVE IN PHASE 1.5 |

### 2.2 `dashboard/app/docs/page.tsx`

| Line | Occurrence | Classification |
|---|---|---|
| 42 | "Learn about the Neural Core." | REMOVE IN PHASE 1.5 |
| 51 | "Captcha & Neural checks." | REMOVE IN PHASE 1.5 |
| 83 | "ZyroX Docs" | REMOVE IN PHASE 1.5 |
| 159 | "…ZyroX Engine documentation… cinematic management tools" | REMOVE IN PHASE 1.5 |
| 166 | "dispatched via our global edge network in under 12ms" | REMOVE IN PHASE 1.5 |
| 171 | "dedicated neural sandbox with AES-256 encryption" | REMOVE IN PHASE 1.5 |
| 179–185 | "Neural Architecture", "decentralized event stream… nearest edge cluster", `$ zyrox initialize --cluster-shard [neural_07]` | REMOVE IN PHASE 1.5 |
| Route | `/docs` itself | REMOVE IN PHASE 1.5 as a surface: unlink everywhere; route redirects to `/` (Task B). File deletion deferred. |

### 2.3 `dashboard/app/privacy/page.tsx`

| Line | Occurrence | Classification |
|---|---|---|
| 37 | "ZyroX Engine" header | REPLACE WITH CLS OS |
| 67 | "The ZyroX Engine collects only…" | REPLACE WITH CLS OS (rewrite from actual data handling: Discord `identify` scope, dashboard sessions, audit events, bot config stores) |
| 79 | "AES-256 encrypted at rest. Our neural vaults are distributed across global edge nodes…" | REMOVE IN PHASE 1.5 (claim is not implemented) |
| 91 | "…support matrix…" | REMOVE IN PHASE 1.5 |
| 97 | "Neural Jurisdiction: Global Edge Network" | REMOVE IN PHASE 1.5 |
| Whole page | Legal content | NEEDS MANUAL REVIEW: Task B writes a factual draft; the owner approves the final legal text. |

### 2.4 `dashboard/app/terms/page.tsx`

| Line | Occurrence | Classification |
|---|---|---|
| 37 | "{brand} Engine" | REPLACE WITH CLS OS |
| 51 | "Neural Protocol v2.4" | REMOVE IN PHASE 1.5 |
| 67 | "ZyroX Engine… 100% uptime through our neural edge clusters" | REPLACE WITH CLS OS (remove uptime/edge claim) |
| 79 | "…immediate neural deauthorization and blacklisting from the global cluster network" | REPLACE WITH CLS OS |
| 91 | "High-scale enterprise clusters… dedicated neural shards" | REMOVE IN PHASE 1.5 |
| 97 | "Distributed via {brand} Neural Cloud" | REMOVE IN PHASE 1.5 |
| Whole page | Legal content | NEEDS MANUAL REVIEW (as privacy). |

---

## 3. Dashboard: metadata, environment, config

| File | Line | Occurrence | Classification | Task |
|---|---|---|---|---|
| `dashboard/app/layout.tsx` | 18, 24–25 | `Inter`, `Outfit` fonts | REPLACE WITH CLS OS (Plex family, design §5) | A |
| `dashboard/app/layout.tsx` | 27 | `const brandName = process.env.NEXT_PUBLIC_BRAND_NAME \|\| "Zyrox"` | REMOVE IN PHASE 1.5 (constant `CLS OS`) | B |
| `dashboard/app/layout.tsx` | 30 | `title: \`${brandName} - Ultimate Discord Bot\`` | REPLACE WITH CLS OS ("CLS OS") | B |
| `dashboard/app/layout.tsx` | 31 | `description: "Advanced Discord community management and security."` | REPLACE WITH CLS OS ("The private control system for the CLS Discord.") | B |
| `dashboard/app/layout.tsx` | 41 | `text-slate-200` body class | REPLACE WITH CLS OS (tokens) | A |
| `dashboard/app/` | — | No `icon.png` / `apple-icon.png` / favicon (browser default icon) | REPLACE WITH CLS OS (icons from traced mark) | B |
| `dashboard/.env.example` | 20 | `NEXT_PUBLIC_BRAND_NAME="ZyroX"` | REMOVE IN PHASE 1.5 | B |
| `dashboard/.env.example` | 21 | `NEXT_PUBLIC_BRAND_NAME_WORD="ZX"` | REMOVE IN PHASE 1.5 | B |
| `dashboard/.env.local` | — | Local file, not read in this audit (may contain `NEXT_PUBLIC_BRAND_NAME`) | NEEDS MANUAL REVIEW (owner removes the two vars locally; harmless once code stops reading them) | Owner |
| `dashboard/tailwind.config.ts` | 30–42 | `primary: #ef4444 "Vivid Red"`, `secondary` navy, `accent.red` | REPLACE WITH CLS OS (token set, design §4.7) | A |
| `dashboard/app/globals.css` | 5–13, 30–75 | Red/navy CSS vars, red scrollbar hover, `.glass`, `.glass-red`, `.liquid-glass` | REPLACE WITH CLS OS | A |
| `dashboard/package.json` | 2 | `"name": "codex-dashboard"` | SAFE INTERNAL LEGACY NAME, DEFER | — |
| `dashboard/README.md` | 12, 34, 81, 114–115, 139–140 | "ZyroX Dashboard", ZyroX setup, brand env vars | REPLACE WITH CLS OS for the env-var rows (Task B, since those vars are removed); rest of README DEFER (developer doc) | B / Phase 11 |
| `dashboard/README.md` | 23–25, 211–224 | CodeX Devs / RayExo badges and links | NEEDS MANUAL REVIEW (attribution in docs; keep or trim per owner) | Owner |
| Root `README.md` | 35, 38, 151–152, 176, 237–238, 284–285, 302 | ZyroX project description, clone URL, `brand_name = 'ZyroX'`, brand env vars, `zyrox-api` tunnel | SAFE INTERNAL LEGACY NAME, DEFER (developer doc), except brand env rows: REPLACE in Task B | B / Phase 11 |

---

## 4. Dashboard: shell, home and pages

| File | Line | Occurrence | Classification | Task |
|---|---|---|---|---|
| `dashboard/app/dashboard/layout.tsx` | 91 | Loading tile `{NEXT_PUBLIC_BRAND_NAME_WORD \|\| "ZX"}` + "Authenticating..." | REPLACE WITH CLS OS (auth continue screen, design §14) | B |
| `dashboard/app/dashboard/layout.tsx` | 166–169 | Red/indigo pulsing blur blobs | REMOVE IN PHASE 1.5 | A |
| `dashboard/app/dashboard/layout.tsx` | 189–199 | `Bot` icon tile + "{brand \|\| ZyroX}" + "Dashboard" | REPLACE WITH CLS OS (mark + "CLS OS") | A |
| `dashboard/app/dashboard/layout.tsx` | 353 | Search placeholder "Query neural network..." (non-functional input) | REMOVE IN PHASE 1.5 | A |
| `dashboard/app/dashboard/layout.tsx` | 373 | "Broadcast Metrics" | REMOVE IN PHASE 1.5 (bell removed) | A |
| `dashboard/app/dashboard/layout.tsx` | 439 | "Support Matrix" (no handler) | REMOVE IN PHASE 1.5 | A |
| `dashboard/app/dashboard/layout.tsx` | 447 | "Deauthorize" | REPLACE WITH CLS OS ("Sign out") | A |
| `dashboard/app/dashboard/layout.tsx` | 328, 331, 421, 423 | "Administrator"/"Admin" fallback names; "User"/"Active" role labels (not real) | REPLACE WITH CLS OS (real access level) | A |
| `dashboard/app/dashboard/page.tsx` | 42 | Fallback bot name `"ZyroX Bot"` | REMOVE IN PHASE 1.5 | C |
| `dashboard/app/dashboard/page.tsx` | 53 | "System Uptime" `"99.9%"` (hardcoded) | REMOVE IN PHASE 1.5 | C |
| `dashboard/app/dashboard/page.tsx` | 61 | "System Core." headline | REMOVE IN PHASE 1.5 | C |
| `dashboard/app/dashboard/page.tsx` | 114 | "Support Matrix… neural support team", `href="#"` | REMOVE IN PHASE 1.5 | C |
| `dashboard/app/dashboard/page.tsx` | 115 | "Learn how to master the ZyroX engine.", `href="#"` | REMOVE IN PHASE 1.5 | C |
| `dashboard/app/dashboard/page.tsx` | 135 | "Global operational health of ZyroX core." | REMOVE IN PHASE 1.5 | C |
| `dashboard/app/dashboard/page.tsx` | 139–141 | Fake services "Neural Gateway: Optimal", "Database Cluster: Synchronized", "Edge Shards: Operational" | REMOVE IN PHASE 1.5 | C |
| `dashboard/app/dashboard/page.tsx` | 155 | "System Diagnostics" button (no handler) | REMOVE IN PHASE 1.5 | C |
| `dashboard/app/dashboard/loading.tsx` | 28–29 | "Initializing System", "Fetching parameters from edge cortex..." | REPLACE WITH CLS OS (skeleton, no copy) | A |
| `dashboard/app/dashboard/error.tsx` | 41, 43 | "System Fault Detected", "The neural link experienced an unexpected interruption…" | REPLACE WITH CLS OS (design §25) | A |
| `dashboard/app/dashboard/guild/[guildId]/page.tsx` | 34–38 | Hardcoded "Active Modules" (statuses are fixed strings) | REMOVE IN PHASE 1.5 (real modules table) | C |
| `dashboard/app/dashboard/guild/[guildId]/page.tsx` | 70–84 | Fake "System Console", "guild_event_stream_…", "Dashboard connected to WebSocket pool..." | REMOVE IN PHASE 1.5 | C |
| `dashboard/app/dashboard/guild/[guildId]/page.tsx` | 94–96 | "Database Status… encrypted and replicated across our high-performance edge network." | REMOVE IN PHASE 1.5 | C |
| `dashboard/app/dashboard/guild/[guildId]/page.tsx` | 100–102 | "Uptime 99.98%", "Sync Delay 12ms", "Region Global Edges" | REMOVE IN PHASE 1.5 | C |
| `dashboard/app/dashboard/guild/[guildId]/page.tsx` | ~118–130 | "Trust Factor 100%", "Bot is fully authenticated with administrator privileges." (not checked; production must not use Administrator, spec §55) | REMOVE IN PHASE 1.5 (replaced by real permission health) | C |
| `dashboard/app/dashboard/guild/[guildId]/layout.tsx` | 112 | "Server Owner Dashboard" (inaccurate: access is by grant) | REMOVE IN PHASE 1.5 | A |
| `dashboard/app/dashboard/guild/[guildId]/layout.tsx` | 97–101 | Always-green "Active" pulse on guild icon (not a real check) | REMOVE IN PHASE 1.5 | A |
| `dashboard/app/dashboard/guilds/page.tsx` | 84–88, 110–113 | Always-green "Bot Online" dot, "Active" label per guild (not real) | REMOVE IN PHASE 1.5 | C |
| `dashboard/components/dashboard/admin-content.tsx` | 115 | "Admin Control Panel" | REPLACE WITH CLS OS ("Platform") | C |
| `dashboard/components/dashboard/admin-content.tsx` | 116 | "Restricted access for ZyroX administrators only." | REPLACE WITH CLS OS ("Root owner only.") | C |
| `dashboard/components/dashboard/admin-content.tsx` | 125 | "Real-time Mode" (is a 30 s poll) | REPLACE WITH CLS OS ("Refresh", with last-updated time) | C |
| `dashboard/components/dashboard/admin-content.tsx` | 139–140 | "Live" badge on every stat | REMOVE IN PHASE 1.5 | C |
| `dashboard/components/dashboard/admin-content.tsx` | 156, 158 | "System Nodes Status", "Auto-Polling Active" | REPLACE WITH CLS OS ("Runtime", honest poll note) | C |
| `bot/api/routes/admin.py` | 70, 76, 82, 88 | Node names "Primary API Cluster", "Database Shards", "Bot Microservices", "Auth Sockets" (misleading infrastructure names for one process + SQLite files) | REPLACE WITH CLS OS at display time. The dashboard maps the four API names to "API process", "SQLite stores", "Loaded modules" and "Gateway connection" (Task C). The bot-side string change is deferred to Phase 11 so Phase 1.5 stays frontend-only. | C / Phase 11 |
| `dashboard/components/dashboard/automod-form.tsx` | 200 | "Our neural network analyzes message context to prevent false positives." (false: rule-based automod) | REMOVE IN PHASE 1.5 | C |
| `dashboard/components/dashboard/antinuke-form.tsx` | 227 | "Ensure that Zyrox's role is at the TOP…" | REPLACE WITH CLS OS ("the CLS bot's role") | C |
| `dashboard/components/dashboard/antinuke-form.tsx` | 226 | "Maximum Protection" | REPLACE WITH CLS OS ("Current behaviour": factual description of legacy instant ban) | C |
| `dashboard/components/dashboard/autorole-form.tsx` | 200 | "Ensure ZyroX's top role is higher…" | REPLACE WITH CLS OS | C |
| `dashboard/components/dashboard/verification-form.tsx` | 205 | "Zyrox Verification ensures that no unauthorized bots or malicious users enter…" (overclaims) | REPLACE WITH CLS OS (factual legacy description) | C (page hidden from nav; copy still fixed) |
| `dashboard/components/dashboard/customroles-form.tsx` | 159 | "Ensure Zyrox is placed higher…" | REPLACE WITH CLS OS | C |
| `dashboard/components/dashboard/customroles-form.tsx` | — | Preset key "girl" among custom role names (unprofessional alias, spec §59 Phase 11) | NEEDS MANUAL REVIEW (keys are bot-defined; label display may change in Task C, key rename is bot-side, Phase 11) | Owner / Phase 11 |
| `dashboard/app/dashboard/guild/[guildId]/invites/page.tsx` | 108 | Emoji medals 🥇🥈🥉 | REMOVE IN PHASE 1.5 | C |
| `dashboard/app/dashboard/guild/[guildId]/invites/page.tsx` | 57–61 | "Invite Leaderboard… tracked join events" presented as trusted | REPLACE WITH CLS OS ("Legacy counts, unverified", spec §48) | C |

---

## 5. Source banners and license

| File(s) | Occurrence | Classification |
|---|---|---|
| ~70 dashboard source files (every `app/**`, `components/**`, `lib/utils.ts`, `types/*`, `hooks/use-auth.ts`, `tailwind.config.ts`) | ASCII banner "© 2026 CodeX Devs — All Rights Reserved", discord.gg/codexdev, youtube, github RayExo | NEEDS MANUAL REVIEW. Comments are not user-facing. The upstream project is MIT-licensed and MIT requires keeping the copyright notice, but the banner's "All Rights Reserved" wording conflicts with MIT. Recommendation: leave banners untouched in Phase 1.5; new files created by CLS do not add banners; owner decides banner policy in Phase 11. |
| `dashboard/LICENSE` | "Copyright (c) 2026 CodeX Devs" (MIT) | NEEDS MANUAL REVIEW. Keep. Removing an upstream MIT notice is a licence violation. The owner may add a CLS copyright line for CLS-authored work. |
| Bot source banners (`bot/**/*.py`, e.g. `bot/CodeX.py`, `bot/api/*.py`, `bot/cogs/zyrox/*.py`) | Same banner | NEEDS MANUAL REVIEW (same recommendation). |

---

## 6. Bot (Discord-facing and internal)

| File | Line | Occurrence | Classification | Owner / Task |
|---|---|---|---|---|
| `bot/utils/config.py` | 21–23 | `BRAND_NAME = os.environ.get("brand_name", "Zyrox X")`, reused as `NAME`/`BotName` in embeds and help | NEEDS MANUAL REVIEW. Discord-facing. Immediate fix without code: owner sets `brand_name` in `bot/.env` (e.g. "CLS"). Changing the code default to a CLS value is a safe Phase 11 task (or Task C if the owner approves a one-line bot change). | Owner |
| `bot/cogs/commands/general.py` | 394–398 | "Quick Actions" / "{BotName} Integration Hub!" invite text (likely includes an invite/"add bot" link) | NEEDS MANUAL REVIEW (CLS-only stage should not advertise bot invites; command policy Phase 8/11) | Owner / Phase 8 |
| `bot/utils/emoji.py` + users (`stats.py`, `np.py`, `mention.py`, `general.py`) | `ZYROX_CODE`, `ZYROX_GLOBAL`, `ZYROXLINKS`, `ZYROXSYS`, `ZYROXHAMMER`, `ZYROXCONNECTION`, `ZWARNING`… | Constant names: SAFE INTERNAL LEGACY NAME, DEFER. The **emoji images** they reference may show ZyroX artwork in Discord: NEEDS MANUAL REVIEW (check the application emojis in the Discord Developer Portal). | Owner / Phase 11 |
| `bot/cogs/commands/Games.py` | 29 | Docstring `"""Zyrox Games"""` (may surface in help as the cog description) | NEEDS MANUAL REVIEW (Games are disabled by default per spec §18.3; fix with Phase 11) | Phase 11 |
| `bot/cogs/commands/help.py` | 22, 36, 178–180, 273 | `from core.zyrox import zyrox`, local variable named `zyrox` | SAFE INTERNAL LEGACY NAME, DEFER | Phase 11 |
| `bot/cogs/commands/help_backup.txt`, `bot/cogs/events/mentionold.txt` | Legacy copies with ZyroX strings | SAFE INTERNAL LEGACY NAME, DEFER (dead files; delete in Phase 11 "remove dead help stubs") | Phase 11 |
| `bot/core/zyrox.py`, `bot/core/__init__.py`, `bot/CodeX.py` | Bot class `zyrox`, entry file `CodeX.py` | SAFE INTERNAL LEGACY NAME, DEFER (explicitly protected by `cls-os-design-system`) | Phase 11 |
| `bot/cogs/zyrox/*` + `bot/cogs/cog_loader.py` (28 refs) | Cog package `cogs.zyrox` | SAFE INTERNAL LEGACY NAME, DEFER | Phase 11 |
| `bot/api/dependencies.py`, `bot/api/routes/*.py` | Type hints `"zyrox"` | SAFE INTERNAL LEGACY NAME, DEFER | Phase 11 |
| Other cogs (`autoblacklist.py`, `autorole.py`, `auto.py`, `on_guild.py`, `Errors.py`, `music.py`, `booster.py`, `extra.py`, `owner.py`, `moderation.py`) | `from core import zyrox` imports, type hints | SAFE INTERNAL LEGACY NAME, DEFER | Phase 11 |
| `bot/utils/tunnel.py` | 16–36 | Docstring "ZyroX API", `zyrox-api` example subdomain | SAFE INTERNAL LEGACY NAME, DEFER | Phase 11 |
| `bot/README.md` | 5 refs | Developer doc | SAFE INTERNAL LEGACY NAME, DEFER | Phase 11 |
| `bot/scripts/prepare_local_preview.py` (untracked) | 1 ref | Local helper, not committed | Not touched |

---

## 7. Other surfaces and concepts

| Concept | Where | Classification | Task |
|---|---|---|---|
| "Add to Server" | `dashboard/app/page.tsx:121` (only dashboard occurrence) | REMOVE IN PHASE 1.5 | B |
| Fake statistics | Landing (12ms, 99.99 %, 12M+, 24, 5.2K, 5,000+), home (99.9 %), guild overview (99.98 %, 12ms, 100 % Trust Factor) | REMOVE IN PHASE 1.5 | B, C |
| Fake infrastructure wording | Landing, docs, privacy, terms, guild overview ("edge network/regions/clusters/shards", "neural vaults", "microkernel", "FPGA", "Global Edges") | REMOVE IN PHASE 1.5 | B, C |
| Fake AI claims | Landing "Contextual AI analysis", automod "neural network", FAQ "predictive analysis" | REMOVE IN PHASE 1.5 | B, C |
| Unimplemented security claims | "AES-256 encrypted at rest" (landing FAQ, privacy, docs), "enterprise encryption and lifetime transcripts" | REMOVE IN PHASE 1.5 (Tickets transcripts don't exist in the dashboard; encryption at rest is not implemented for config stores) | B |
| Old logo/marks | `Bot` Lucide icon in red gradient tile (landing nav, sidebar), "ZX" text tile (auth loading) | REPLACE WITH CLS OS (official mark) | A, B |
| Red brand colour | `#ef4444` tokens, `red-*` utilities across ~40 files | REPLACE WITH CLS OS (tokens; red stays only as semantic danger) | A (tokens), C (pages) |
| Old fonts | Inter, Outfit (`font-outfit` utility used across pages) | REPLACE WITH CLS OS | A, C |
| Horizontal guild tab bar | `dashboard/components/guild-tabs.tsx` | REMOVE IN PHASE 1.5 as a surface (component file may remain unused until Phase 11) | A |

---

## 8. Verification gate for Tasks B and C

After Task C, this command must return **no matches** in user-facing dashboard code:

```bash
rg -n -i "zyrox|neural|NEXT_PUBLIC_BRAND|add to server|99\.9|edge (region|cluster|shard|network)|global (shard|edges|reach|uptime)|support matrix|deauthorize|initialize console|12M|5,000|5\.2K|cortex|uplink" dashboard/app dashboard/components dashboard/lib dashboard/.env.example \
  | rg -v "^\S+:\d+:\s*\*"
```

The `rg -v` filter excludes banner comment lines (Section 5, manual review). `bot/` is intentionally excluded (Section 6).

---

## 9. Task C completion (2026-09-30)

**User-facing dashboard cleanup:** **COMPLETE** for `dashboard/app`, `dashboard/components`, `dashboard/lib`, and `dashboard/.env.example` per the §8 gate (0 matches after Task C commit).

| Item | Task C action |
|---|---|
| `dashboard/app/dashboard/page.tsx` (fake home) | Replaced with auth router |
| Guild overview fake metrics / console | Replaced with real-data overview (DS §16) |
| Guild picker marketing cards | Compact list + single-guild redirect |
| Access / Platform ZyroX copy | CLS operational copy + UI redesign |
| Tickets global `staff_roles` UI | Removed; payload field omitted on global save (B7) |
| Feature form ZyroX / neural strings (automod, antinuke, autorole, customroles, verification) | Factual CLS copy |
| Invites emoji medals | Removed; legacy notice added |
| `/docs` surface | Already redirects to `/` (Task B) |
| `NEXT_PUBLIC_BRAND_NAME` on kept surfaces | Not used for product identity (CLS OS constant/metadata from Task B) |

**Deferred to Phase 11 (unchanged)**

- Internal symbols: `core/zyrox.py`, `cogs/zyrox/*`, `ZYROX_*` constants, codex-dashboard package name, bot `BRAND_NAME` default, tunnel docstrings, file banners (CodeX Devs MIT).
- Bot API node identifiers in `bot/api/routes/admin.py` (UI maps display names only).
- Deletion of unused `components/guild-tabs.tsx`.
- Deep legacy form layout (`#141B2D`, slate cards) on modules not fully rebuilt — shell + headers/copy pass only where Task C touched files.

Historical audit line references in Sections 2–7 are preserved as the pre-Task-C record.
