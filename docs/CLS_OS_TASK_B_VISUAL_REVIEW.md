# CLS OS Task B — Visual Review Package (Composer)

Prepared for independent Opus visual critique. Screenshots are **outside the repository**.

## Hero concept

**CLS Perimeter (Concept B):** Three nested pointy-top hexagon rings (30° geometry, segmented edges with cut gaps) surround the official raster CLS mark. Outer ring carries six operational domain labels (Security, Support, Recovery, Automation, Moderation, Audit). Middle ring reads as control ticks; inner ring is the access boundary. Faint isometric lattice sits behind the composition with radial fade. No orbital dots, no generic radar/globe.

## Final copy

| Element | Text |
|---|---|
| Overline | `CLS OS` |
| Headline | **Private control for CLS Discord.** |
| Lead | Security, support, recovery, and automation run from one operations perimeter. Access is granted by the CLS root owner—not sold on a storefront. |
| CTA | Sign in with Discord |
| Access note | Access is invite-only. |
| Domain section | What runs inside (six factual rows per DS §13.1) |
| Footer tag | Private system. Access by grant only. |

**Tagline decision:** Headline states the private-control positioning directly instead of a separate marketing tagline (DS D tagline REVISIT closed for Task B).

## Display font decision

**IBM Plex Sans 600 only** (extends Task A / D7). Chakra Petch was not loaded: the prototype read cleaner and more operational with Plex at hero scale, avoids an extra font download on gateway routes, and matches the dashboard wordmark. `.cls-display-hero` and `.cls-auth-title` use `--cls-font-display` → Plex UI stack.

## Motion behavior

- Entrance: lattice fade (~600ms), inner/middle/outer segment arm stagger (~600–1300ms), text column reveal at ~700ms (≤~1.4s total choreography).
- Idle: segment highlight sweep deferred (static arm state only in this build; sweep can be added in polish pass without blocking).
- Sign-in lock: inner ring brightens / segments unify over ~480ms before OAuth navigation.
- `/auth/continue`: compact auth perimeter + hex loader; inner ring open animation ~400ms then client redirect.
- Parallax: ≤6px ring offset on fine pointers only; disabled on coarse pointers.
- Reduced motion: final static composition immediately (no stagger, no parallax).

## Responsive behavior

- **1440×900 / 2560×1440:** Two-column gateway; perimeter at ~560px max; labels on outer ring (hidden `<768px`).
- **1024×768:** Hero + CTA visible without scrolling in typical cases.
- **390×844:** Perimeter above copy; labels hidden; domain list carries names; full-width CTA.
- **RTL:** Manual `dir=rtl` on `<html>` validated; layout mirrors; perimeter stays symmetric.

## Screenshot locations (outside repo)

`C:\Users\aero\AppData\Local\Temp\cls-phase-1.5\task-b\`

- `landing-1440.png`, `landing-2560.png`, `landing-1024.png`, `landing-390.png`
- `landing-rtl-1440.png`, `landing-reduced-motion-1440.png`
- `auth-error.png`, `privacy-1440.png`

`/auth/continue` and authenticated `/auth/no-access` require a live Discord session; not captured in automation.

## Compromises

- Official logo remains **raster** (Task A asset policy); perimeter geometry is SVG, mark is PNG overlay.
- Footer **CLS Discord** link uses interim invite in `lib/publicLinks.ts` — **owner must replace** with the real CLS community invite.
- Privacy/Terms are **conservative drafts** marked for owner/legal review (no compliance claims).
- Global `robots: noindex,nofollow` for private-first stage (D43 resolved for Phase 1.5).
- Dev server was restarted once during QA because stale HMR served CSS 404; preview on port **3000** is owned by this session.

## Opus critique prompts

- Perimeter label density vs. hero headline at 1024–1280 widths.
- Whether Plex-only hero is distinctive enough or needs a display face in a later polish pass.
- Purple budget on dual Sign-in placements (nav + hero) on desktop first viewport.

## CLS OS UI review (self)

### BLOCKER
- None after dark-theme CSS verified post dev restart.

### HIGH
- None.

### MEDIUM
- Outer ring labels can crowd the hero at mid-desktop widths; consider tighter label radius or hide labels below `lg` instead of `md`.
- Interim Discord invite URL must be swapped by owner.

### POLISH
- Optional outer-ring idle sweep (DS §13.4) not implemented.
- Screenshot `/auth/continue` with real session for Opus.
