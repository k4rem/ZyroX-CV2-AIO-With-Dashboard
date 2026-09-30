---
name: cls-os-design-system
description: >-
  Primary authority for CLS OS product UI — private-first Discord operations
  platform. Use for CLS landing pages, Dashboard UI, components, visual redesign,
  responsive layout, RTL-ready styling, motion, charts, forms, tables, security
  UI, and ticket UI. Encodes locked CLS OS identity (dark-only, purple accent,
  dense command-center admin UX). Overrides generic frontend aesthetics when they
  conflict with CLS rules.
---

# CLS OS Design System (Project Authority)

This skill is the **primary authority** for CLS-specific frontend design decisions. External skills (e.g. Anthropic `frontend-design`, Impeccable) add craft and review capability but **must not override** locked identity rules here.

## Skill interaction

| Phase | Skills |
|-------|--------|
| Design / implementation | `cls-os-design-system` + `frontend-design` |
| Review / polish | `cls-os-ui-review` + `impeccable` |

**Precedence:** CLS project skills win on product identity, naming, navigation IA, density, and brand policy. Generic skills win only on execution craft where CLS rules are silent.

---

## Product identity

**Official product name:** **CLS OS**

Do **not** use as the primary product title: ZyroX, CLS Dashboard, CLS System.

CLS OS is a **private-first Discord operations / control platform** for CLS.

**Character:** Premium · Dark · Technical · Dense · Animated · Security-focused · Command-center inspired · Professional · Gaming-tech influence · Enterprise usability

**Avoid:** Generic SaaS look · AI-slop layouts · Childish gaming UI · Fake cyberpunk jargon · Excessive neon · Random glassmorphism · Huge wasted whitespace · Flat boring cards · Marketing claims that are not factual

---

## Brand

- **Theme:** DARK ONLY
- **Identity:** Black / near-black surfaces + **CLS purple** accent (exact tokens defined in a later design-architecture pass)
- **Semantic colors stay independent:** green = healthy/success · amber = warning · red = danger/threat · blue/cyan = informational where useful
- Do **not** turn every status chip purple

**Logo:** Owner-supplied official CLS geometric logo only. Do not generate a replacement logo. Do not use AI-generated icons.

**Icons:** Lucide, Phosphor, or Tabler (pick **one** primary library for interface consistency); official platform/service assets where appropriate; official CLS logo.

---

## Design DNA

Owner-provided CLS website/dashboard screenshots are the **primary brand DNA**.

**Preserve strengths:** Compact/dense layout · black surfaces · purple accent · clear module grouping · professional admin-tool feel

**Inspiration (not copy):** Modern dashboards, command centers, Linear/Vercel-class discipline, premium fintech, security operations tools, polished developer products. ZyroX is inspiration only for **polish, motion, cinematic presentation** — **not** ZyroX content, branding, or identity.

Do not copy another product pixel-for-pixel.

---

## Landing page rules

Landing may be cinematic and expressive. Target: **CLS OS login gateway**, not a long fake public SaaS sales page.

**Desired:** Premium animation · distinctive hero · strong CLS logo moment · rich dark/purple system · interactive/system visual motif where useful · excellent motion · concise **real** product positioning · Discord sign-in CTA

**Avoid:** Fake users/community counts · fake uptime · fake edge regions · invented infrastructure claims · “Neural Core” · fake AI/cyber terminology · **Add to Server** CTA during CLS-only stage · excessive marketing length

---

## Dashboard rules

- **Desktop-first**, mobile-usable, **RTL-ready from the foundation**
- **Navigation:** icons + labels + clear sections · collapsible sidebar · compact icon rail when collapsed
- **Workspace:** dense — avoid massive cards that waste screen space
- Brand identity visible on every page without overpowering functional content

---

## Sidebar information architecture (target)

**OVERVIEW** — Overview

**MANAGEMENT** — Commands · Roles · Members

**TICKETS** — Overview · Live Tickets · Panels · Categories · Forms · Transcripts · Staff · Analytics

**ENGAGEMENT** — Welcome · Leveling · Reaction Roles · Auto Roles

**MODERATION** — Moderation · Automod · Logging · Verification

**SECURITY** — Security Overview · Antinuke · Bot Protection · Bot Trap · Whitelist · Disaster Recovery

**SYSTEM** — Audit Log · Bot Settings · Integrations

Some pages belong to later phases. Do not fake feature functionality to fill navigation. Hide or clearly mark unavailable/future items per approved phase.

---

## Surfaces / cards

Do **not** use completely flat UI.

Use disciplined depth: layered near-black surfaces · subtle purple-tinted borders · restrained inner highlights · controlled glow · elevation on interaction · meaningful gradients · occasional glass/translucency for overlays, modals, floating controls

Avoid making every card glow. Visual importance drives visual intensity.

---

## Typography

- **Landing:** expressive large type allowed
- **Dashboard:** compact, legible, highly functional · premium and technical
- Do not default to generic “AI UI” font stacks without intentional CLS alignment (families chosen in design-architecture task)

---

## Motion

**Landing:** cinematic animation · tasteful parallax · orchestrated reveals · animated system visual · subtle background motion

**Dashboard:** sidebar transition · drawers/modals · status pulse · counters · chart transitions · drag/drop feedback · useful hover/micro-interactions

Motion communicates hierarchy/state. Do not animate everything. **Respect `prefers-reduced-motion`.**

---

## Data-dense UI

For Members, Tickets, Audit, Logs, Sessions, Invites — prefer **data tables / grids** with search, filters, sorting, status chips, pagination, date ranges, column controls, bulk actions where valid.

Do not replace large datasets with hundreds of cards. Cards are for summaries, KPIs, modules, and actions.

---

## Security center

Should feel like a real **operations / security command center:** threat level · system status · active incidents · live security feed · permission health · recent actors · module status · security metrics · timeline/event streams

Do **not** fake metrics. Visual language may be more dynamic here than ordinary settings pages.

---

## Tickets (future V2 builder)

Locked direction: **Canva / Discord-builder style** — component palette · builder workspace · drag/drop · live Discord preview · form/modal preview · direct feedback

Do not reduce the final builder to one long settings form.

---

## Analytics

Charts may use purple glow, subtle gradients, live markers, controlled animation — **readability always wins**.

---

## RTL

Arabic full UI translation is not required in Phase 1.5, but architecture must be **RTL-ready.**

Prefer logical properties: `start`/`end`, `inline`/`block`. Avoid hardcoded left/right assumptions. Components must tolerate Arabic labels, RTL layout, and different text widths.

---

## Responsive

Desktop first. Mobile must remain usable — do not shrink the desktop command center unchanged onto mobile. Sidebar may become a drawer. Tables may use responsive/adaptive views.

---

## ZyroX branding policy

**User-facing ZyroX branding must ultimately disappear** (wordmarks, “ZyroX Dashboard”, Neural Core, ZyroX marketing copy, browser metadata, env brand defaults, visual marks).

Do **not** mass-rename deep internal architecture blindly (e.g. `core/zyrox.py` may remain until low-risk cleanup phases).

Phase 1.5 focus: **user-facing identity** + safe internal branding cleanup. Deep legacy internal names may wait for Phase 11.

---

## Out of scope for agents using this skill

- Do not invent final hex colors, type families, spacing scales, radius tokens, or animation timings unless the active design-architecture task explicitly authorizes tokens
- Do not implement backend/auth/database changes when doing UI work unless explicitly requested
