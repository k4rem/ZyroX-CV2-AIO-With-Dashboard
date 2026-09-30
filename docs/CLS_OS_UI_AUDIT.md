# CLS OS UI Audit (pre-Phase 1.5)

**Subject:** current `dashboard/` (Next.js 14 App Router) on branch `phase-1.5-cls-os-design` at `e383420`, plus the five owner-supplied reference images.
**Standard:** `docs/CLS_OS_DESIGN_SYSTEM.md`, `.cursor/skills/cls-os-design-system`, spec `CLS_DISCORD_V2_SPEC.md` (§2, §18, §25, §55, §59).
**Severity:** BLOCKER (must not survive Phase 1.5; breaks trust, access or correctness), HIGH (major UX or brand failure), MEDIUM (clear defect, bounded impact), POLISH. No numeric scores.

## 0. Method and limitations

- **Source-based.** Every dashboard page, layout, shared component and `lib/` helper was read. The current UI was **not** rendered in a browser for this audit. The local preview stack exists, but screenshots are a Task A checkpoint (see the implementation plan), not an input here. Visual findings are inferred from class names and structure. Findings needing a render to confirm are marked *(render to confirm)*.
- **Skills.** `cls-os-ui-review` (checklist and severity model), `impeccable` critique protocol (heuristics, anti-pattern detector), `cls-os-design-system` (authority). The impeccable protocol normally runs two independent sub-agent assessments; this run was **single-context**. The deterministic detector (`impeccable detect`) was run over `dashboard/app` and `dashboard/components` and reported **2 findings**, both `gradient-text` in `dashboard/app/page.tsx` (hero headline). The detector does not catch copy-level problems (fake metrics, ZyroX strings), which make up most of this audit.
- **References.** No standalone screenshot of the current ZyroX landing was supplied. The orbital/ZyroX reference image was treated as the "current direction to leave behind" sample.

---

## 1. Reference image critique

| Image | Take | Leave | Notes |
|---|---|---|---|
| CLS home (existing CLS site) | Near-black purple-tinted surfaces (`#060608`–`#131218`), purple accent `#A855F7`, compact nav, strong wordmark | Low-contrast secondary labels (sampled ≈3.3:1, below 4.5:1); large-radius soft cards | Establishes the CLS family feel. The dashboard uses the logo purple `#6025E2` as the fill hue instead of `#A855F7` so product and mark agree (design §4.3). |
| CLS license admin | Dense tables, left rail, status labels | "ACTIVE" status rendered in brand purple (brand colour used as a semantic state); uppercase everywhere | Confirms the density target. Status must use semantic colours (design §23). |
| Stakent dashboard | Hierarchy discipline: one hero number, calm secondary panels, restrained glow | Crypto/marketing KPI tiles, large rounded cards, decorative line charts without axes | Borrow the calm; not the tile grid (design §16 rejects KPI card grids). |
| Orbital / ZyroX sample | Nothing structural | Orbiting rings, "neural" core, glow on everything, red/indigo blobs | This is the "Neural Core" aesthetic the brief bans. |
| CLS logo (`NEW-LOGO`) | 30° stroke geometry, `#6025E2` violet, hex silhouette | — | Source for the Perimeter hero and hex loader. The logo must be traced to SVG (owner approval, see plan). |

---

## 2. Findings by severity

### 2.1 BLOCKER

| # | Surface | Finding | Evidence | Fix (task) |
|---|---|---|---|---|
| B1 | Landing | Entire landing is ZyroX marketing: fake statistics (12ms, 99.99 %, 12M+ users, 24 edge clusters, 5.2K communities, 5,000+), invented infrastructure (Rust microkernel, FPGA, edge network, neural vaults), false security claims ("AES-256 encrypted at rest"), "Neural Core", **"Add to Server"** CTA. Violates spec §2 (private-first, CLS only) and the brief. | `dashboard/app/page.tsx` (see branding map §2.1) | Replace with the CLS OS gateway (B) |
| B2 | Guild overview | Every visible value is hardcoded: module statuses, "System Console" log lines, "Uptime 99.98 %", "Sync Delay 12ms", "Region Global Edges", "Trust Factor 100 %" and "Bot is fully authenticated with administrator privileges". The last one is unchecked and contradicts spec §55 (the bot must not rely on Administrator). An operator would trust false health data. | `dashboard/app/dashboard/guild/[guildId]/page.tsx` | Rebuild from `/system/health`, `/bot/status` and module GETs (C, design §16) |
| B3 | Global home | "System Uptime 99.9 %" hardcoded; fake service list "Neural Gateway / Database Cluster / Edge Shards"; quick actions with `href="#"`; "System Diagnostics" button without handler. | `dashboard/app/dashboard/page.tsx:53,114–115,139–141,155` | Route home per design §14/§16.3 (C) |
| B4 | Shell / access | Root-only navigation can never render. `isAdmin()`/`isRootOwner()` read `process.env.ROOT_OWNER_ID` in a client component, where that server-only variable is `undefined`, so "Admin Panel" never appears. **Access management has no link anywhere** (not in the sidebar, not in the tab bar). The root owner must type URLs. | `dashboard/app/dashboard/layout.tsx:146`, `dashboard/lib/utils.ts` | Server-computed `isRoot` passed to the client shell (A) |
| B5 | Shell | The notification bell calls the root-only admin config endpoint for **every** user on every dashboard load. Non-root users trigger a guaranteed 403 per page view, noise in the Phase 1 audit log, and a console error. | `dashboard/app/dashboard/layout.tsx` (bell / `getAdminConfig`) | Remove the bell; broadcast shown only on Platform (A) |
| B6 | Access management | Revoke grant and template change apply **without confirmation**; grants are listed by raw Discord IDs with no name, avatar or template description. A mis-click removes someone's dashboard access. | `dashboard/components/dashboard/access-management.tsx` | Tier-2 confirm, identity cells, template select (C, design §22.3) |
| B7 | Tickets form | "Global Staff Role IDs" field sends `staff_roles`, which the API writes with `UPDATE guild_configs SET staff_roles = ?`. `guild_configs` has no such column (`DASHBOARD_BASELINE.md`), so the value never persists and the save may fail. Category rows also fall back to a "Global Staff" label that has no effect in the bot. | `dashboard/components/dashboard/tickets-form.tsx:350–355,392`, `bot/api/routes/guilds.py:296–298` | Hide the field and the fallback label until Tickets V2 (C). The backend fix is out of scope for Phase 1.5. |

### 2.2 HIGH

| # | Surface | Finding | Fix (task) |
|---|---|---|---|
| H1 | Global | Brand identity is ZyroX red (`#ef4444` primary, red scrollbar, red glass, red blur blobs) with Inter/Outfit. Nothing reads as CLS. | Tokens + fonts (A) |
| H2 | Metadata | Title "Zyrox - Ultimate Discord Bot", generic description, no favicon/app icon (browser default), `NEXT_PUBLIC_BRAND_NAME` lets an env var rename the product. | Constant metadata + icons (B) |
| H3 | Auth | Unauthenticated `/dashboard` visits immediately call `signIn('discord')` from a client effect. The user is bounced to Discord with no explanation, and denied/failed OAuth has no designed error state. The "ZX" tile plus "Authenticating..." is the only feedback. next-auth `pages.signIn` is `/`, the marketing page. | `/auth/continue`, `/auth/error`, No-access screen, server redirect (B, design §14) |
| H4 | Navigation | Two competing navigation systems. The sidebar (3 groups) and a 17-pill horizontal `GuildTabs` bar list overlapping but **different** sets: Logging is only in tabs, Tracking only in the sidebar, Leveling and Verification in both. The tab bar sits sticky under the topbar with hover-only scroll arrows. | Single sidebar IA (A, design §15.2) |
| H5 | Shell | Floating rounded glass sidebar with blur and pulsing blobs costs space and contrast. Topbar contains a non-functional search ("Query neural network..."), "Support Matrix" (no handler), "Deauthorize" (sign-out). User card shows invented "User/Active" labels, not the real access level. | Inverted-L shell (A) |
| H6 | Guild header | Every guild page opens with a large header card (guild icon with an always-green "Active" pulse, name, "Server Owner Dashboard" — wrong: access is by grant — and a "Refresh" link). It pushes content below the fold at 1024×768 *(render to confirm)*. | Breadcrumb + guild switcher (A) |
| H7 | Admin (Platform) | Copy "Restricted access for ZyroX administrators", "Real-time Mode" (a 30 s poll), a "Live" badge on every stat, and misleading node names from the API ("Primary API Cluster", "Database Shards", "Bot Microservices", "Auth Sockets") for a single process with SQLite stores. | Rename the UI strings and map the API node names at display time (C). The `bot/api/routes/admin.py` edit is deferred to Phase 11. |
| H8 | Feature forms | False capability copy: automod "Our neural network analyzes message context" (rule-based); verification "ensures that no unauthorized bots or malicious users enter"; antinuke "Maximum Protection"/"Protected" labels on a legacy instant-ban engine. Spec §25/§59 require factual wording. | Copy pass (C) |
| H9 | Custom select | `components/ui/select.tsx` is a div-based dropdown with no keyboard support, no `role="listbox"`/`aria-*`, no typeahead and no focus management. It is used for channel/role pickers across most forms, so keyboard users cannot configure modules. | Radix Select primitive (A) |
| H10 | Guild picker | Card grid with an always-green "Bot Online" dot and an "Active" label per guild (not checked). With the CLS-only stage there is usually one guild, so the page is an unnecessary step. | Auto-redirect when one guild; compact list otherwise (C) |
| H11 | Motion | `animate-in fade-in slide-in-*` classes appear in ~30 files, but `tailwindcss-animate` is not installed, so they do nothing. Meanwhile `animate-pulse` runs on decorative elements everywhere (active tab icons, status dots that aren't live, blobs), and no `prefers-reduced-motion` handling exists. | Motion tokens + reduced-motion (A); strip dead classes (C) |

### 2.3 MEDIUM

| # | Surface | Finding | Fix (task) |
|---|---|---|---|
| M1 | Density | Oversized type and spacing throughout: 4xl–5xl page titles, `p-8`/`rounded-[32px]` cards, 56 px full-width "Save Configuration" buttons, `text-[10px] font-black uppercase tracking-[0.2em]` micro-labels as the dominant label style. Legibility is low and density is far below the command-centre target. | Scale + density tokens (A), page pass (C) |
| M2 | Icons | Arbitrary icon semantics in the sidebar: `Search` for Auto Role, Reaction Roles and Invites; `Settings` for Auto React and Voice Role; `ShieldCheck` for Anti-Nuke, Automod and Custom Roles; `Menu` for Join to Create. Icons carry no meaning. | Icon map (A, design §11) |
| M3 | Save model | Each form has its own full-width save button at the bottom. There is no dirty-state indicator and no navigation guard. Errors appear only as toasts. | Sticky save bar (A primitive, C adoption) |
| M4 | Tables | `components/ui/table.tsx` has no density variants, sticky header, sort semantics or empty/error rows. Pages build ad-hoc lists with cards instead. | Table primitive (A) |
| M5 | Loading / error | `loading.tsx` "Fetching parameters from edge cortex..." with a spinner; `error.tsx` "System Fault Detected / neural link…" with no retry detail or request ID. Pages have no designed empty states. | State components (A) |
| M6 | Invites leaderboard | Emoji medals 🥇🥈🥉, and legacy counts presented as authoritative (spec §48 marks them unverified). | Plain rank column + legacy notice (C) |
| M7 | RTL | Physical classes (`ml-*`, `mr-*`, `left-*`, `right-*`, `text-left`, `pl-*`) everywhere; no `dir` handling; hardcoded `ChevronLeft/Right` in the tab scroller. RTL would mirror incorrectly. | Logical utilities + `dir` foundation (A), page pass (C) |
| M8 | Responsive | Sidebar collapses to a hamburger, but the guild header card and pill tab bar remain. At 390 px the tab bar is the only navigation and hides its scroll arrows until hover (no hover on touch) *(render to confirm)*. | Drawer + single IA (A) |
| M9 | Contrast | Heavy use of `text-slate-500` on `#0f172a`-ish glass for body-level hints (≈4.0:1, below 4.5:1 at small sizes) and `opacity-50/80` on text *(render to confirm exact ratios)*. | Text tokens fg-1…fg-4 (A) |
| M10 | Public pages | `/docs` shows invented architecture and CLI (`$ zyrox initialize --cluster-shard`). `/privacy` and `/terms` claim encryption, edge nodes and "100 % uptime". These are the pages the landing footer links to. | Unlink `/docs`; rewrite privacy/terms (B) |
| M11 | Access page | Uses a native `<select>` for templates (inconsistent with the custom select), no search or filter, and no explanation of what each template allows. | Template select with descriptions (C) |
| M12 | Leveling, Verification | Linked in navigation although Leveling is disabled by default (spec §18.3) and Verification is a legacy engine scheduled for rebuild in Phase 3. Users configure things that may not run. | Hide from nav (A), routes kept |

### 2.4 POLISH

| # | Finding | Fix (task) |
|---|---|---|
| P1 | Gradient text on the landing headline (the detector's 2 findings). | Removed with the landing (B) |
| P2 | Mixed radii (`rounded-[14px]`, `[20px]`, `[24px]`, `[32px]`, `rounded-3xl`) with no scale. | Radius scale (A) |
| P3 | `italic` used for emphasis in headings ("System *Core.*", "Server Owner Dashboard"). | Remove (C) |
| P4 | External noise texture loaded from `grainy-gradients.vercel.app` (third-party request on the landing). | Removed with the landing (B) |
| P5 | Scrollbar styled red on hover. | Token scrollbar (A) |
| P6 | Inconsistent page title levels (`h1` on some pages, `h2` on others, several `h1` per page). | Page header primitive (A) |
| P7 | Hover scale/translate effects on cards (`hover:-translate-y-1`, `hover:scale-105`) on non-interactive containers. | Remove (C) |

---

## 3. Legacy and dead UI surface audit

Classes: **KEEP** (ship with token/copy restyle only), **REDESIGN** (rebuild in Phase 1.5), **HIDE FOR NOW** (route stays, unlinked), **REMOVE SURFACE** (unlink and redirect/delete element), **DEFER TO FEATURE PHASE** (keep the working legacy version; real redesign belongs to a later spec phase).

### 3.1 Routes

| Route | Current state | Class | Task | Notes |
|---|---|---|---|---|
| `/` | ZyroX marketing landing | REDESIGN | B | CLS OS gateway (design §13). |
| `/docs` | Invented docs | REMOVE SURFACE | B | Unlink; redirect to `/`. File deletion Phase 11. |
| `/privacy` | Fictional claims | REDESIGN | B | Factual rewrite; owner approves legal text. |
| `/terms` | Fictional claims | REDESIGN | B | As privacy. |
| `/dashboard` | Fake home | REMOVE SURFACE | C | Becomes a router: guild overview, guild list or Platform (design §16.3). |
| `/dashboard/guilds` | Card grid, fake online state | REDESIGN | C | Compact list; auto-redirect when one guild. |
| `/dashboard/admin` | Admin panel, misleading copy | REDESIGN | C | "Platform", root only. |
| `/dashboard/access` | Unlinked, raw IDs, no confirm | REDESIGN | C | "Access", root only, linked in SYSTEM group. |
| `/guild/[id]` | Fully fake overview | REDESIGN | C | Design §16. |
| `/guild/[id]/antinuke` | Working legacy config | KEEP | C | Restyle + copy fix. Security Center is Phase 7 (DEFER TO FEATURE PHASE for the redesign). |
| `/guild/[id]/automod` | Working legacy config | KEEP | C | Remove "neural network" claim. |
| `/guild/[id]/tickets` | Legacy config, one dead field | KEEP | C | Hide "Global Staff Role IDs". Tickets V2 builder is Phase 4 (DEFER TO FEATURE PHASE). |
| `/guild/[id]/verification` | Legacy engine | HIDE FOR NOW | A | Rebuilt in Phase 3. REVISIT D26 with owner. |
| `/guild/[id]/welcome` | Working | KEEP | C | Tab "Channel message" under Welcome. |
| `/guild/[id]/joindm` | Working | KEEP | C | Tab "Direct message" under Welcome. |
| `/guild/[id]/autorole` | Working | KEEP | C | |
| `/guild/[id]/reactionroles` | Working | KEEP | C | |
| `/guild/[id]/autoreact` | Working | KEEP | C | |
| `/guild/[id]/j2c` | Working, required module | KEEP | C | ENGAGEMENT group (REVISIT D25). |
| `/guild/[id]/invcrole` | Working | KEEP | C | Tab under Roles. |
| `/guild/[id]/vanityroles` | Working | KEEP | C | Tab under Roles. |
| `/guild/[id]/customroles` | Working; "girl" preset key | KEEP | C | Label display only; key rename Phase 11. |
| `/guild/[id]/tracking` | Working, sidebar only | KEEP | C | Tab "Tracking" under Invites. |
| `/guild/[id]/invites` | Legacy counts, emoji medals | KEEP | C | Tab "Leaderboard (legacy counts)"; notice per spec §48. |
| `/guild/[id]/logging` | Working, tab bar only | KEEP | C | Now linked in the sidebar under MODERATION. |
| `/guild/[id]/leveling` | Module disabled by default | HIDE FOR NOW | A | Spec §18.3. REVISIT D26. |
| `/guild/[id]/leveling/leaderboard` | As above | HIDE FOR NOW | A | |
| `/guild/[id]/settings` | Prefix only | KEEP | C | "Bot settings". |

### 3.2 Shell elements and components

| Element | Location | Class | Task |
|---|---|---|---|
| Floating glass sidebar | `app/dashboard/layout.tsx` | REDESIGN | A |
| Background blur blobs | `app/dashboard/layout.tsx`, `app/page.tsx` | REMOVE SURFACE | A, B |
| Topbar search ("Query neural network...") | `app/dashboard/layout.tsx:353` | REMOVE SURFACE (command palette deferred) | A |
| Notification bell / "Broadcast Metrics" | `app/dashboard/layout.tsx:373` | REMOVE SURFACE | A |
| "Support Matrix" menu item | `app/dashboard/layout.tsx:439` | REMOVE SURFACE | A |
| User menu | `app/dashboard/layout.tsx` | REDESIGN | A |
| `GuildTabs` 17-pill bar | `components/guild-tabs.tsx` | REMOVE SURFACE (file left unused until Phase 11) | A |
| Guild header card | `app/dashboard/guild/[guildId]/layout.tsx` | REMOVE SURFACE (replaced by breadcrumbs + guild switcher) | A |
| "Back to Servers" nav item | `app/dashboard/layout.tsx:140` | REMOVE SURFACE (guild switcher) | A |
| Auth loading "ZX" tile | `app/dashboard/layout.tsx:91` | REDESIGN (`/auth/continue`) | B |
| `loading.tsx` / `error.tsx` | `app/dashboard/` | REDESIGN | A |
| `ui/button` | `components/ui/button.tsx` | REDESIGN (variants per design §21) | A |
| `ui/select` | `components/ui/select.tsx` | REDESIGN (Radix) | A |
| `ui/table` | `components/ui/table.tsx` | REDESIGN | A |
| `ui/form-elements`, `page-header`, `metric-card` | `components/ui/` | REDESIGN (`metric-card` becomes `kpi-sm` stat strip only) | A |
| Dashboard quick-action tiles | `app/dashboard/page.tsx` | REMOVE SURFACE | C |
| Fake "System Console" | `guild/[guildId]/page.tsx` | REMOVE SURFACE | C |
| Emoji rank medals | `invites/page.tsx:108` | REMOVE SURFACE | C |
| Tickets "Global Staff Role IDs" field | `components/dashboard/tickets-form.tsx` | HIDE FOR NOW | C |
| Security Center, Tickets V2 builder, audit feed, incidents | not built | DEFER TO FEATURE PHASE (Phases 2, 4, 7; design §17–18 set the language) | — |

---

## 4. What already works and must survive

- The API client layer (`lib/api.ts`, proxy utilities and their tests `lib/proxyUtils.test.mjs`, `lib/legacyDirectApi.test.mjs`), the next-auth Discord flow, and the Phase 1 access grant model.
- All module config pages load and save through existing endpoints. Phase 1.5 changes presentation, not payloads. The only functional change is hiding the tickets field that writes nowhere.
- `sonner` toasts, `cva`/`tailwind-merge` utilities, Lucide icons.

## 5. Checks for the post-implementation review

After Task C, re-run this audit with `cls-os-ui-review` against rendered screenshots (plan checkpoints). Every BLOCKER and HIGH above must be closed or explicitly moved to the decision register with a reason.
