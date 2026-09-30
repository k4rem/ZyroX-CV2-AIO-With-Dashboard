# CLS OS Phase 1.5 Implementation Plan

**Inputs:** `docs/CLS_OS_DESIGN_SYSTEM.md` (authority; section numbers below are "DS §n"), `docs/CLS_OS_UI_AUDIT.md` (findings B1–B7, H1–H11, M1–M12, P1–P7), `docs/CLS_OS_BRANDING_CLEANUP_MAP.md`.
**Branch:** `phase-1.5-cls-os-design`. Each task is committed separately, with no push until the owner reviews screenshots.
**Skills every implementing agent must load:** `cls-os-design-system` (authority), `frontend-design`, and `cls-os-ui-review` plus `impeccable` for the review step at the end of each task.

Phase 1.5 is **frontend-only**. No FastAPI, bot, Postgres or schema changes. Payloads sent to existing endpoints must not change, except that the dead tickets field stops being sent (audit B7).

---

## 0. Order, parallelism and shared rules

```
Task A (tokens, primitives, shell) ──┬──► Task B (landing + auth)
                                     └──► Task C (dashboard pages + cleanup)
```

- A lands first. B and C may run in parallel after A, because their file sets do not overlap (listed per task). If they run in parallel, only B edits `app/layout.tsx` metadata and `lib/auth.ts`; C must not touch those files.
- **Global must-not-touch (all tasks):** `bot/**`, FastAPI, Postgres/migrations, `dashboard/lib/api.ts` request/response shapes, `dashboard/lib/proxyUtils.ts`, `dashboard/lib/serverBotRequest.ts`, `dashboard/lib/botInternal.ts`, `dashboard/lib/internalIdentity.ts`, `dashboard/app/api/bot/[...path]/route.ts`, JWT minting, session callbacks' token contents, grant logic, `.env*` files with secrets, untracked preview helpers (`bot/.preview.env`, `bot/scripts/_*.py`, `bot/scripts/prepare_local_preview.py`, `bot/scripts/run_preview_bot.py`), `dashboard/LICENSE`, existing source banner comments.
- **Global rules:** tokens only (no raw hex in components); logical CSS properties only (`ms-/me-/ps-/pe-/start-/end-/text-start`); Lucide icons only; no new packages except the six Radix packages in DS §29.3 (Task A only); no "coming soon" placeholders; no fake data; no `animate-in` classes; stage files by explicit path (never `git add .`).
- **Staging discipline:** `git status --short` before each commit. Untracked preview helpers must remain untracked.

### 0.1 Shared checks (run at the end of every task, from `dashboard/`)

| Check | Command | Pass condition |
|---|---|---|
| Lint | `npm run lint` | 0 errors |
| Type check + build | `npm run build` | Succeeds |
| Proxy tests | `node --test lib/proxyUtils.test.mjs` | All pass (Phase 1 baseline 3/3) |
| Legacy direct API tests | `node --test lib/legacyDirectApi.test.mjs` | All pass |
| Whitespace | `git diff --check` | No output |
| Raw colour gate | `rg -n "#[0-9a-fA-F]{3,8}\b\|rgba?\(" app components --glob "!**/*.svg"` | Only allowed in `app/globals.css` token block and brand SVG components |
| Physical direction gate | `rg -n "\b(ml\|mr\|pl\|pr\|left\|right)-[0-9\[]\|text-(left\|right)\b\|rounded-(l\|r\|tl\|tr\|bl\|br)-" app components` | 0 matches in files touched by the task (whole tree after Task C) |
| Dead animation gate | `rg -n "animate-in\|slide-in-from\|fade-in " app components` | 0 in touched files (whole tree after Task C) |
| Detector (run from repo root) | `.cursor/skills/impeccable/scripts/impeccable.cmd detect dashboard/app dashboard/components` | No new findings; 0 total after Task B |
| Branding gate | Command in branding map §8 | 0 matches after Task C (scoped to touched files for A/B) |

### 0.2 Screenshot protocol (all checkpoints)

- Stack: local preview (`bot/scripts/run_preview_bot.py` with `bot/.preview.env`, dashboard `npm run dev`). These are untracked local helpers and must never be committed.
- Tool: Playwright MCP. Viewports **1440×900**, **2560×1440**, **1024×768**, **390×844**.
- Variants: LTR; RTL (`<html dir="rtl">` via the dev-only toggle from Task A); `prefers-reduced-motion: reduce` (Playwright `emulateMedia`).
- Store screenshots outside the repository (e.g. `%TEMP%\cls-phase-1.5\<task>\`) so they can never be staged. Attach them in the task report.
- Review each checkpoint with `cls-os-ui-review`. Fix BLOCKER/HIGH before commit.

### 0.3 Owner actions (not agent work)

1. **Approve the traced CLS mark SVG** (Task A produces it from `NEW-LOGO`). B's Perimeter depends on it.
2. **Set `brand_name` in `bot/.env`** (e.g. `CLS`) so Discord embeds stop saying "Zyrox X" (branding map §6). No code change.
3. **Remove `NEXT_PUBLIC_BRAND_NAME*` from `dashboard/.env.local`** after Task B (harmless if left, since the code no longer reads them).
4. **Approve privacy/terms text** drafted in Task B.
5. **Decide D26** (Verification and Leveling hidden) and review the Discord application emojis (branding map §6).

---

## TASK A: Design System + Dashboard Shell

### A.1 Objectives

1. Implement the CLS OS token layer (colour, type, spacing, radius, depth/glow, motion, z-index) exactly as DS §4–§10, mapped into Tailwind.
2. Load fonts: IBM Plex Sans, IBM Plex Sans Arabic, IBM Plex Mono via `next/font/google` (DS §5.1). Chakra Petch is loaded by Task B only.
3. Build the primitive inventory (DS §29.5) on Radix + tokens, with RTL direction context.
4. Replace the dashboard shell with the inverted-L chrome: sidebar (DS §15.1), Phase 1.5 navigation tree (DS §15.2), topbar with breadcrumbs, health indicator and user menu (DS §15.3), mobile drawer (DS §15.6), save-bar primitive (DS §15.5).
5. Fix root visibility: `app/dashboard/layout.tsx` becomes a **server component** that reads the session and computes `isRoot` server-side, then renders a client `AppShell` with `isRoot` and the authorized guild list as props (audit B4). Access and Platform appear only when `isRoot`.
6. Remove from the shell: floating glass sidebar, blur blobs, fake search, notification bell and its admin-config call (audit B5), "Support Matrix", "Deauthorize", `GuildTabs` usage, the guild header card, the "Back to Servers" item.
7. Hide Leveling, Leaderboard, Verification and Docs from navigation (routes untouched).
8. Replace `app/dashboard/loading.tsx` and `app/dashboard/error.tsx` with the DS §25 states.
9. Trace the CLS logo to SVG (`components/brand/cls-mark.tsx`) and build `Wordmark`, `HexLoader`, `LatticeBackground` (DS §12). `PerimeterMark` is built in Task B.
10. Add a dev-only RTL toggle (`?dir=rtl` or `NODE_ENV=development` query) to exercise RTL before any Arabic copy exists.
11. Session handling in the shell: an unauthenticated `/dashboard/*` request redirects server-side to `/?notice=session-ended` instead of the current client `signIn('discord')` effect. Task B builds the notice UI; until then the redirect simply lands on the landing.

### A.2 Directories and components affected

| Path | Change |
|---|---|
| `dashboard/package.json`, `package-lock.json` | Add `@radix-ui/react-dropdown-menu`, `-popover`, `-dialog`, `-tooltip`, `-select`, `-direction` (exact versions, React 18 compatible). |
| `dashboard/tailwind.config.ts` | Token mapping, font families, type scale, spacing, radius, shadows/glows, keyframes (fade, scale-in, slide-inline, shimmer, pulse-ring, hex-step), z-index. Remove red/navy palette. |
| `dashboard/app/globals.css` | CSS variables (RGB triplets), base layer, focus ring, scrollbar, reduced-motion block, lattice texture. Remove `.glass*`, `.liquid-glass`, red scrollbar. |
| `dashboard/app/layout.tsx` | Font loading + `<html>` `dir`/`lang` attributes + body token classes. **Metadata block untouched** (Task B). |
| `dashboard/app/dashboard/layout.tsx` | Rewritten as server wrapper. |
| `dashboard/app/dashboard/guild/[guildId]/layout.tsx` | Remove header card and `GuildTabs`; provide guild context to breadcrumbs/switcher. |
| `dashboard/app/dashboard/loading.tsx`, `error.tsx` | New state components. |
| `dashboard/components/shell/*` (new) | `AppShell`, `Sidebar`, `SidebarItem`, `Topbar`, `Breadcrumbs`, `GuildSwitcher`, `HealthIndicator`, `UserMenu`, `MobileDrawer`, `nav-config.ts`. |
| `dashboard/components/ui/*` | Rebuild `button`, `select`, `table`, `form-elements`, `page-header`; add remaining DS §29.5 primitives. `metric-card` becomes `kpi-strip`. |
| `dashboard/components/brand/*` (new) | `ClsMark`, `Wordmark`, `HexLoader`, `LatticeBackground`. |
| `dashboard/components/providers/*` | `DirectionProvider` (Radix), sonner theme. |
| `dashboard/lib/utils.ts` | Remove the client-side use of `isRootOwner`/`isAdmin` from components. The helper itself may remain for server use; no logic change. |

Old primitives keep their export names where pages import them, so existing pages still compile and render (restyled) until Task C.

### A.3 Dependencies

- None on B or C. Needs the local preview stack for screenshots and the owner's logo approval for `ClsMark` (a provisional trace may ship; flagged in the report).

### A.4 Must not touch

Global list (§0), plus: `app/page.tsx`, `app/docs`, `app/privacy`, `app/terms`, `app/layout.tsx` metadata, `lib/auth.ts`, any `app/dashboard/guild/[guildId]/*/page.tsx` body content, `components/dashboard/*-form.tsx` logic (restyling only through shared primitives).

### A.5 Visual acceptance criteria

- The shell matches DS §15: 48 px topbar, 248 px sidebar / 56 px rail, `bg-chrome` chrome, flat full-height sidebar with no radius, blur or blobs.
- The active nav item shows a brand-tint background, a `brand-400` icon and a 2×16 px inline-start bar with G2 glow. No other glow in the shell except the live status dot.
- Groups and items exactly as the DS §15.2 table; icons per DS §11 map (no reused icon for different meanings, audit M2).
- The topbar shows breadcrumbs, the health indicator (real `/bot/status` data) and the avatar menu. There is no search and no bell.
- The guild switcher replaces the header card; the guild name truncates with the full name in a tooltip.
- Primitives render every state from DS §19–§25 in a dev-only `/dashboard/_primitives` gallery page. The gallery is removed before Task C commits, or excluded from production by a `NODE_ENV` check.
- The purple budget is respected (DS §4.3): brand fill only on the primary button, active nav, focus and selection.
- Existing module pages render inside the new shell without layout breakage (restyled via primitives; old page chrome may still look off until Task C).

### A.6 Functional regression criteria

- Sign-in → dashboard → guild → every module page loads and saves exactly as before (manual pass over all 20 guild routes, including the hidden ones reached by URL).
- Root user sees Access and Platform in the sidebar; non-root does not. Non-root requests to `/dashboard/access` and `/dashboard/admin` still get the API's 403 handling (UI shows the No access state, no crash).
- No request to the admin config endpoint from non-root sessions (verify in Playwright network log, audit B5).
- Sign out works and returns to `/`.
- Guild switcher lists exactly the authorized guilds from the existing API, and switching keeps the same module sub-route when it exists.
- The unauthenticated `/dashboard` redirect goes to `/` server-side (no Discord bounce loop).
- Tests in §0.1 pass.

### A.7 Responsive, RTL and motion criteria

- **≥1280:** full sidebar. **1024–1279:** rail by default, expandable. **<1024:** drawer with focus trap, `Esc`/scrim/route-change close, 40 px items.
- **2560×1440:** content max width and density hold (DS §6.2). No stretched full-width forms.
- **RTL:** sidebar at the right, rail tooltips on the left side, breadcrumbs reversed, directional icons (`PanelLeftClose`, chevrons) mirrored, Radix menus open on the correct side, keyboard arrows follow direction.
- **Motion:** only DS §10 tokens. Sidebar collapse 200 ms width + label fade; drawer 280 ms; menus 120 ms. Under reduced motion all transitions become ≤80 ms opacity or none, and the live pulse becomes static.
- Focus ring visible on every interactive element, including rail items and menu items.

### A.8 Tests / build checks

§0.1 in full, plus:
- `rg -n "isAdmin\(|isRootOwner\(" app components` shows no client component usage.
- `rg -n "GuildTabs" app` returns 0.
- Keyboard pass: Tab through the shell, open/close the drawer, user menu and guild switcher with keyboard only.

### A.9 Screenshot review checkpoints

1. **A-1 tokens:** primitives gallery at 1440×900 LTR and RTL.
2. **A-2 shell desktop:** a guild module page (Antinuke) at 1440×900 and 2560×1440, root and non-root sessions.
3. **A-3 shell compact:** 1024×768 rail and expanded; 390×844 drawer closed and open.
4. **A-4 RTL:** A-2 and A-3 with `dir="rtl"`.
5. **A-5 states:** `loading.tsx`, `error.tsx`, health indicator degraded/offline (stop the preview bot).
6. **A-6 reduced motion:** drawer open, sidebar collapse.

### A.10 Task A completion record

Status: implemented and committed on `phase-1.5-cls-os-design` (not pushed). Checkpoint run against the real local preview stack with a real Discord OAuth session.

**Delivered:** token layer (`app/globals.css`, `tailwind.config.ts`), IBM Plex Sans / Sans Arabic / Mono via `next/font/google`, primitives under `components/ui` (Button, IconButton, Tooltip, DropdownMenu, Popover, Dialog, Drawer, Skeleton, Status, Panel, State/ErrorState/NoPermissionState, Avatar; Input/Textarea/Switch/Label/Card/Select/Sonner retokened), brand components (`ClsMark`, `Wordmark`, `HexLoader`), the shell (`components/shell/*`), server `app/dashboard/layout.tsx` (session gate, `isRoot`, authorized guild list), reduced `guild/[guildId]/layout.tsx` (auth gate only), `loading.tsx`, `error.tsx`, `lib/shellNav.ts` and `lib/shellHealth.ts` with tests.

**Decisions recorded**
- **Chakra Petch (D7): CHANGE.** Dropped entirely from Task A (not loaded). Wordmark is IBM Plex Sans 600, 15 px, 0.04 em. The landing/auth display face falls back to the DS fallback candidate (Plex Sans 600) unless Task B's own prototype proves a display face is worth its weight. `--cls-font-display` currently resolves to Plex Sans.
- **Sidebar persistence:** cookie `cls_sidebar` (read on the server, so first paint matches). 1024-1279 px is a rail with a transient overlay that does not push content; below 1024 px a drawer.
- **Dev RTL:** cookie `cls_dir` plus a user-menu toggle, honoured only when `NODE_ENV !== "production"`. No query-string switch.
- **Active nav item:** brand tint + 2 px inline-start bar + brand icon (purple budget: active nav only).
- **Select:** legacy custom Select retained and retokened, with listbox/option roles, `aria-expanded` and Esc added. Rebuilding on `@radix-ui/react-select` is deferred to Task C (needs a new dependency and touches every form page).
- **Logo:** official owner asset used as-is (`public/brand/cls-logo-official.png`, plus resized 512/128 px marks). No vector trace. **Follow-up:** owner to supply a vector logo; `ClsMark` is the single swap point.
- **Health:** real `/bot/status` + `/system/health`, 30 s polling, 8 s probe timeout, 401 reported as "Session ended" (not "Bot unreachable"), state transitions announced via a polite live region.
- **Nav visibility:** Verification, Leveling, Docs are hidden from nav (routes untouched). Access and Platform appear only when the server computed `isRoot`; no client component imports `isRootOwner` and the client bundle contains none of the server env values.
- **Dependencies:** five Radix packages added (dialog, direction, dropdown-menu, popover, tooltip; slot and switch were already present). Nothing else.

**Backend finding (not changed, Phase 1 scope):** `/system/health` returns per-guild permission data for all guilds to any authenticated dashboard user. The shell only displays the current guild, but the endpoint should be scoped server-side.

**Hand-offs**
- Task B: root metadata title/description still says "Zyrox"; `Toaster` sits outside `UiProviders` (physical toast position in RTL).
- Known shell polish (POLISH, unscheduled): at 1024-1279 px the server renders the expanded sidebar content for one frame before hydration switches to the rail.
- Task C: `/dashboard` legacy home still shows hard-coded uptime; guild overview cards still show fake metrics; `components/ui/table.tsx` and `components/guild-tabs.tsx` are legacy/unused; `max-w-content` cap leaves the breadcrumb left-aligned on 2560 px while content is centred (decide per-page width classes); `isRootOwner` lives in `lib/utils.ts` next to client helpers (move to a server-only module); Select rebuild (above); legacy colour aliases in the LEGACY block of `globals.css` to be removed as pages migrate.
- Not verified visually: a non-root session (covered by `buildNav` unit tests and server-side gating of Access/Platform).

---

## TASK B: Landing + Authentication Experience

### B.1 Objectives

1. Replace `app/page.tsx` with the CLS OS login gateway (DS §13): ≈1.8 desktop viewports, Concept B "CLS Perimeter" hero, factual domain list, footer with Privacy, Terms and CLS Discord only. **No Add to Server, no statistics, no Neural Core, no feature marketing grid** (audit B1).
2. Build `PerimeterMark` (DS §12.3, §13.3) and the landing motion choreography (DS §13.4) in SVG + CSS + a small `requestAnimationFrame` parallax hook, with no motion library.
3. Load Chakra Petch (display, landing/auth only) via `next/font/google`, scoped so the dashboard never downloads it on dashboard routes if possible (preload false).
4. Implement every auth state in DS §14: sign-in pending, `/auth/continue`, routing after sign-in, No access, `/auth/error`, session-ended/signed-out notices, server redirect of authenticated `/` visits.
5. Metadata: constant `CLS OS` title template, description from DS §13.5, `app/icon.svg` + `app/apple-icon.png` from the approved mark, `robots` per D43 (REVISIT; default `noindex` for the private stage).
6. Remove `NEXT_PUBLIC_BRAND_NAME` and `NEXT_PUBLIC_BRAND_NAME_WORD` from all code and from `dashboard/.env.example`. Update the env rows in `dashboard/README.md` and root `README.md` (those rows only).
7. `/docs` is unlinked everywhere and redirects to `/` (`redirect()` in the page; file deletion Phase 11). `/privacy` and `/terms` are rewritten with factual, owner-reviewable drafts in the auth/legal layout (branding map §2.3–2.4).
8. Remove the third-party noise texture request (audit P4).

### B.2 Directories and components affected

| Path | Change |
|---|---|
| `dashboard/app/page.tsx` | Full replacement (server component; checks session and redirects). |
| `dashboard/components/landing/*` (new) | `Gateway`, `PerimeterHero`, `DomainList`, `SignInButton`, `LandingFooter`, `NoticeBar`, `useParallax`. |
| `dashboard/components/brand/perimeter-mark.tsx` (new) | Perimeter SVG. |
| `dashboard/app/auth/continue/page.tsx` (new) | Session establishment + routing. |
| `dashboard/app/auth/error/page.tsx` (new) | Error states. |
| `dashboard/app/auth/no-access/page.tsx` (new) or a component rendered by `/auth/continue` | No access state. |
| `dashboard/components/auth/*` (new) | `AuthLayout`, `AuthCard`, `CopyId` usage. |
| `dashboard/lib/auth.ts` | **Only** `pages: { signIn: "/", error: "/auth/error" }` and the post-sign-in `callbackUrl` target `/auth/continue`. Session/JWT callbacks, providers and scopes unchanged. |
| `dashboard/app/layout.tsx` | Metadata block and Chakra Petch variable only. |
| `dashboard/app/icon.svg`, `apple-icon.png` (new) | From the approved mark. |
| `dashboard/app/docs/page.tsx` | Replaced by a redirect. |
| `dashboard/app/privacy/page.tsx`, `terms/page.tsx` | Rewritten. |
| `dashboard/.env.example` | Delete the two brand vars. |
| `dashboard/README.md`, `README.md` | Brand-env rows only. |

### B.3 Dependencies

- Task A tokens, fonts, primitives (`Button`, `HexLoader`, `LatticeBackground`, `ClsMark`, `Wordmark`, `InlineBanner`) and the server-side session redirect from A.1 step 11.
- Owner approval of the mark (owner action 1) before the final screenshots; owner approval of legal text (owner action 4) before merge.

### B.4 Must not touch

Global list (§0), plus: everything under `app/dashboard/**` except reading the route list for redirects, `components/dashboard/**`, `components/shell/**` (consume only), NextAuth providers/scopes/callbacks' token logic, `app/api/auth/[...nextauth]/route.ts` beyond what `lib/auth.ts` exports.

### B.5 Visual acceptance criteria

- The first viewport at 1440×900 shows the wordmark, headline, one-line lead, the single "Sign in with Discord" CTA and the Perimeter hero. There is nothing else competing, and no secondary CTA.
- The Perimeter uses nested pointy-top hexagons derived from the mark's 30° strokes, with six segments labelled by real CLS OS domains (DS §13.3). The glow budget is G3 only on the inner ring during the sign-in lock.
- The second section is the factual domain list (DS §13.1). The page ends at ≈1.8 viewports with a minimal footer.
- The typography follows DS §5.3 (Chakra Petch display + Plex body). No gradient text (detector 0).
- Auth screens share one layout (400 px column, Perimeter mark 96 px, auth title) with copy exactly per DS §14.
- No statistics, testimonials, fake logos, feature tiles or "Add to Server" anywhere (branding gate).

### B.6 Functional regression criteria

- Full Discord sign-in works end to end against the preview stack: landing → Discord → `/auth/continue` → the correct destination for each routing case (0 guilds non-root → No access; 1 guild → Overview; >1 → picker; root with 0 → Platform).
- A `callbackUrl` inside `/dashboard` is honoured when authorized and ignored when not (open-redirect safe: only same-origin `/dashboard` paths).
- Cancelling on Discord lands on `/auth/error` with the cancelled copy. Visiting `/` while signed in redirects server-side with no landing flash.
- Sign out → `/` with "Signed out." notice; an expired session → `/` with "Your session ended." notice.
- `/docs` → `/`. `/privacy` and `/terms` render.
- Session token contents, proxy behaviour and grant checks are unchanged. The §0.1 tests pass.

### B.7 Responsive, RTL and motion criteria

- **390×844:** the hero stacks below the CTA and is scaled down; the CTA is visible in the first viewport; the Perimeter parallax is disabled on touch/coarse pointers.
- **2560×1440:** the composition stays centred with a capped max width; the Perimeter doesn't grow past its max size.
- **1024×768:** CTA and hero both visible without scrolling.
- **RTL:** layout mirrors; the Perimeter itself does not mirror (symmetric), but its segment labels are positioned by logical side; Discord glyph stays before the label in reading order.
- **Motion:** choreography per DS §13.4 (entrance ≤1400 ms total, sign-in lock 500 ms, `/auth/continue` open 400 ms). Parallax ≤ a few px, and only on fine pointers. **Reduced motion:** static Perimeter, instant content, loading button only.
- No layout shift from font loading (CLS metric < 0.05 in Lighthouse on the landing).

### B.8 Tests / build checks

§0.1 in full, plus:
- `rg -n "NEXT_PUBLIC_BRAND" dashboard` returns 0 (excluding `node_modules`).
- Lighthouse (Playwright or Chrome) on `/`: Accessibility ≥ 95, CLS < 0.05, no third-party requests.
- Manual keyboard pass: CTA reachable first, auth error actions focusable, visible focus.

### B.9 Screenshot review checkpoints

1. **B-1 landing:** 1440×900 (first viewport + full page), 2560×1440, 1024×768, 390×844.
2. **B-2 choreography:** 3–4 frames of the entrance and the sign-in lock (or a short screen recording), plus the reduced-motion static frame.
3. **B-3 auth states:** `/auth/continue`, No access, each `/auth/error` variant, session-ended and signed-out notices.
4. **B-4 RTL:** B-1 at 1440×900 and 390×844, and B-3 No access.
5. **B-5 legal:** privacy and terms at 1440×900 and 390×844.

---

## TASK C: Core Dashboard UI + Branding / Surface Cleanup

### C.1 Objectives

1. Rebuild the guild Overview (DS §16) from real data only: system line, needs-attention list, modules table, server facts, your access. **No** future widgets (DS §16.2) and no placeholders (audit B2).
2. Turn `/dashboard` into the router in DS §14/§16.3 and remove the fake home (audit B3).
3. Redesign the guild picker as a compact list with auto-redirect when there is exactly one guild (audit H10).
4. Redesign Platform (`/dashboard/admin`) and Access (`/dashboard/access`): identity cells (avatar, name, `CopyId`), template select with descriptions, tier-2 confirmation on revoke and template change (audit B6, M11), honest refresh copy, and display-time mapping of the API node names (audit H7).
5. Apply the page header grammar, setting rows, sticky save bar and tables to every KEEP route in the audit §3.1: antinuke, automod, tickets, welcome + joindm (tabs), autorole, reactionroles, autoreact, j2c, customroles + invcrole + vanityroles (Roles tabs), tracking + invites (Invites tabs), logging, settings.
6. Copy pass per branding map §4: all ZyroX, neural, "Maximum Protection" and overclaiming strings; factual antinuke/automod/verification descriptions; legacy notices (tickets panels, invites legacy counts).
7. Hide the tickets "Global Staff Role IDs" field and the "Global Staff" fallback label (audit B7). The form stops sending `staff_roles` at config level. Per-category `staff_roles` is unchanged.
8. Remove the remaining dead surfaces in audit §3.2 (quick-action tiles, fake console, emoji medals) and all `animate-in`/decorative `animate-pulse`/hover-lift classes across `app/` and `components/`.
9. Convert every remaining physical direction class to logical across `app/dashboard/**` and `components/**`.
10. Run the full branding gate (branding map §8) to zero.

### C.2 Directories and components affected

| Path | Change |
|---|---|
| `dashboard/app/dashboard/page.tsx` | Router (server component). |
| `dashboard/app/dashboard/guilds/page.tsx` | Compact list + single-guild redirect. |
| `dashboard/app/dashboard/guild/[guildId]/page.tsx` | New Overview. |
| `dashboard/components/overview/*` (new) | `SystemLine`, `NeedsAttention`, `ModulesTable`, `ServerFacts`, `derive-attention.ts` (pure function, unit-testable). |
| `dashboard/app/dashboard/guild/[guildId]/*/page.tsx` (all KEEP routes) | Page header, tabs for grouped routes, notices. |
| `dashboard/components/dashboard/*-form.tsx` | Adopt `SettingRow`/`SaveBar`/`Select`/`Table`; copy fixes. **Payload shapes unchanged** except the B7 field. |
| `dashboard/components/dashboard/access-management.tsx`, `admin-content.tsx` | Redesign. |
| `dashboard/app/dashboard/guild/[guildId]/invites/page.tsx`, `tracking/page.tsx` | Tabs, legacy notice, medals removed. |
| `dashboard/components/guild-tabs.tsx` | Left in place, unused (deletion Phase 11). |

### C.3 Dependencies

- Task A (all primitives, shell, save bar, tabs). Independent of Task B except that both must pass the branding gate at the end. If run in parallel, C's branding gate is scoped to its own files until B merges.

### C.4 Must not touch

Global list (§0), plus: `app/page.tsx`, `app/auth/**`, `app/docs`, `app/privacy`, `app/terms`, `app/layout.tsx`, `lib/auth.ts`, `components/landing/**`, `components/brand/perimeter-mark.tsx`, API client method signatures, **the hidden routes' behaviour** (Leveling, Leaderboard, Verification: restyle via primitives is allowed, but copy fixes only, no redesign).

### C.5 Visual acceptance criteria

- The Overview matches the DS §16 layout: a system line at top, needs-attention before the modules table, no KPI card grid, no chart, no future widget.
- Every page follows DS §15.4: one title, ≤1 primary action, grouped routes as link tabs, legacy notices as single-line banners.
- The dashboard body is 13 px Plex with density per DS §6.4–§6.5. No text above `page-title` size, no `rounded-[32px]`, no italic emphasis, no hover-lift on containers.
- Status uses semantic colours with text labels (never colour alone and never brand purple for a state, per the reference critique).
- Access: every grant row shows avatar, name and ID; destructive actions open a confirm dialog that names the user and effect.
- The invites leaderboard shows a numeric rank and a "Legacy counts, unverified" notice.
- The branding gate returns 0 across `app/`, `components/`, `lib/`, `.env.example`.

### C.6 Functional regression criteria

- Every KEEP module page loads and saves with identical request payloads. Verify by capturing the network requests on save before (Task A build) and after (Task C build) for each page and diffing. The only allowed difference is the absent config-level `staff_roles` on tickets.
- The Overview renders correctly when the bot is offline (system line shows unreachable; the modules table still loads from config endpoints or shows per-row errors), when permissions are missing (needs-attention items with links), and when there is nothing to report (empty state).
- `derive-attention.ts` has a `node --test` unit test covering each condition in DS §16.1 (new file `lib/deriveAttention.test.mjs` or co-located `.mjs` mirror, following the existing test pattern).
- `/dashboard` routing works for all four cases in DS §14.
- Access: grant, template change and revoke still hit the same endpoints; cancel in the confirm dialog makes no request.
- The sticky save bar appears only when dirty; Discard restores; navigating away when dirty prompts.

### C.7 Responsive, RTL and motion criteria

- **390×844:** tables become stacked rows or horizontally scroll with a sticky first column (DS §19/§27); setting rows stack label above control; the save bar stays reachable above the mobile keyboard.
- **1024×768:** Overview columns collapse to one; modules table keeps its columns.
- **2560×1440:** content max width holds; the Overview uses its two-column layout without stretching the table.
- **RTL:** the whole tree passes the physical direction gate; numbers and IDs stay LTR (`dir="ltr"` on `CopyId`, D39 Western digits); tabs, tables and confirm dialogs mirror correctly.
- **Motion:** only token transitions. Save bar slide 200 ms, dialog 200 ms, row hover 80 ms. Reduced motion is honoured everywhere.

### C.8 Tests / build checks

§0.1 in full with **whole-tree** gates, plus:
- `node --test lib/deriveAttention.test.mjs`.
- The payload diff from C.6.
- Branding gate (branding map §8) returns 0.
- `impeccable detect` returns 0 findings.
- Final `cls-os-ui-review` over all C screenshots; the audit's BLOCKER and HIGH items are each marked closed or moved to the decision register with a reason.

### C.9 Screenshot review checkpoints

1. **C-1 Overview:** healthy, bot offline, missing permissions, empty needs-attention. 1440×900 and 2560×1440.
2. **C-2 routing:** guild picker with >1 guild; No access handoff; Platform for root.
3. **C-3 module pages:** every KEEP route at 1440×900, and the three grouped pages (Roles, Welcome, Invites) with each tab.
4. **C-4 Access and Platform:** list, confirm dialog, empty state, error state.
5. **C-5 compact:** Overview, Antinuke and Access at 1024×768 and 390×844.
6. **C-6 RTL:** C-1 healthy, C-3 Antinuke and Tickets, C-4 list at 1440×900 and 390×844.
7. **C-7 dirty state:** a module page with the save bar visible, and the navigation guard prompt.
8. **C-8 reduced motion:** dialog open and save bar.

---

## Completion definition for Phase 1.5

- Tasks A, B, C committed separately, each with its own screenshots reviewed and every §0.1 check passing.
- All audit BLOCKER and HIGH findings closed; MEDIUM closed or registered; POLISH best-effort.
- The branding gate and detector are at 0; the untracked preview helpers are still untracked.
- The decision register items marked REVISIT AFTER VISUAL PROTOTYPE are resolved with the owner after the B-1/C-1 screenshots and updated in `CLS_OS_DESIGN_SYSTEM.md` §32.
