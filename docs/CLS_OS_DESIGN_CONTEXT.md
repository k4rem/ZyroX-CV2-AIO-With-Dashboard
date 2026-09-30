# CLS OS Design Context (Phase 1.5 Bootstrap)

This document summarizes **locked owner preferences** for Phase 1.5 design planning. It is **not** the final design specification. Tokens (hex, type, spacing, radius, motion timing) will be chosen in the dedicated **design architecture** task (Claude Opus).

**Platform baseline:** Phase 0 and Phase 1 are closed. Do not redesign auth, database, or API architecture during design-system bootstrap.

---

## Product identity

- **Name:** **CLS OS** (not ZyroX, CLS Dashboard, or CLS System as primary title)
- **Purpose:** Private-first Discord operations / control platform for CLS
- **Tone:** Premium, dark, technical, dense, animated, security-focused, command-center inspired, professional, enterprise-usable with gaming-tech influence

---

## Aesthetic intent

- **Dark only** — black / near-black surfaces with **CLS purple** as brand accent
- **Semantic colors** remain standard (green success, amber warning, red danger, blue/cyan info) — do not purple-wash status UI
- **Density:** Admin-tool / command-center compactness; avoid oversized cards and wasted whitespace
- **Depth:** Layered surfaces, subtle purple-tinted borders, controlled glow — not flat UI, not glow on everything
- **Logo:** Official owner-supplied CLS geometric logo — no AI-generated logo or icons
- **Icons:** One primary library (Lucide / Phosphor / Tabler TBD); established libraries + official assets only
- **DNA:** Owner CLS screenshots are primary reference; ZyroX is polish/motion inspiration only — not target identity

---

## Landing vs dashboard

| Surface | Direction |
|---------|-----------|
| **Landing** | Cinematic allowed; becomes CLS OS **login gateway**; real positioning; Discord sign-in CTA; no fake metrics, “Neural Core”, or Add to Server during CLS-only stage |
| **Dashboard** | Desktop-first, mobile-usable, RTL-ready; collapsible sidebar with icon rail; dense workspace |

---

## Navigation (target IA)

Overview · Management (Commands, Roles, Members) · Tickets (full subtree) · Engagement · Moderation · Security · System — see `cls-os-design-system` skill for full tree. Later-phase pages may be hidden or marked; do not fake functionality.

---

## Motion

- **Landing:** cinematic, orchestrated reveals, system visual motif, tasteful parallax
- **Dashboard:** purposeful micro-interactions (sidebar, modals, status pulse, charts, DnD)
- Always respect **`prefers-reduced-motion`**

---

## Data-heavy surfaces

Prefer tables/grids (search, filter, sort, pagination, bulk actions) for Members, Tickets, Audit, Logs, Sessions, Invites. Cards for KPIs and summaries.

---

## Security center

Operations / SOC command-center feel: threat level, incidents, feeds, permission health, timelines — **no fake metrics**.

---

## Tickets V2 (future)

Canva / Discord-builder style: palette, workspace, drag/drop, live Discord preview — not a single long form.

---

## RTL & responsive

- RTL-ready architecture now; full Arabic UI translation not required in Phase 1.5
- Prefer logical CSS (`start`/`end`, `inline`/`block`)
- Mobile: usable adaptations (drawer sidebar, adaptive tables), not a shrunk desktop layout

---

## ZyroX cleanup policy

Remove **user-facing** ZyroX branding (copy, metadata, env defaults, marks). Do not blindly rename deep internal modules (e.g. `core/zyrox.py`) if regression risk is high; Phase 11 may handle deep legacy names.

---

## Agent skills (repository)

Project-local Cursor skills under **`.cursor/skills/`**:

| Skill | Role |
|-------|------|
| `cls-os-design-system` | **Primary** CLS identity & UI rules |
| `cls-os-ui-review` | CLS-specific UI review severities |
| `frontend-design` | Official Anthropic craft / distinctive UI execution |
| `impeccable` | Audit, critique, polish, distill, motion quality (not brand source) |

**Workflow:** Design/implement → `cls-os-design-system` + `frontend-design`. Review/polish → `cls-os-ui-review` + `impeccable`.

**Impeccable hooks:** Not committed — installed with `--no-hooks` to avoid brittle nightly-only hook manifests and accidental global Cursor overrides. Reinstall locally: `npx impeccable install --providers=cursor --scope=project --yes --no-hooks`.

**Impeccable binary:** `.cursor/skills/impeccable/scripts/bin/` is gitignored; first local run downloads the engine via the skill launcher.

**Discovery:** Cursor may require **Agent Skills enabled** (Settings → Rules) and a **new Agent session** to refresh the skill catalog after adding skills.

---

## Explicit non-goals (this bootstrap)

- No landing or dashboard UI redesign yet
- No final color/type/spacing token sheet yet
- No Phase 2 feature work
