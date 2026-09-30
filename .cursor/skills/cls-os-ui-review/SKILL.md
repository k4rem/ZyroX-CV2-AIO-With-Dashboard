---
name: cls-os-ui-review
description: >-
  Reviews implemented CLS OS UI for design quality and brand compliance. Use
  after landing or dashboard UI changes, before merge, or when auditing for
  generic AI patterns, ZyroX leftovers, weak security-center presentation, low
  density, RTL issues, or missing interaction states. Produces severitized
  findings with actionable fixes aligned to cls-os-design-system.
---

# CLS OS UI Review

Use this skill to **review implemented CLS OS UI** (landing, dashboard, shared components). Pair with **`impeccable`** for deep audit/polish vocabulary; **CLS project rules override** generic aesthetic preferences.

**Reference authority:** `cls-os-design-system` for locked identity, IA, density, and brand policy.

---

## Review process

1. Confirm scope (page, route, component library slice).
2. Compare against `cls-os-design-system` and `docs/CLS_OS_DESIGN_CONTEXT.md`.
3. Inspect responsive behavior (desktop-first + mobile usability).
4. Check RTL tolerance (logical properties, no hardcoded LTR-only assumptions).
5. Verify interaction states: hover, focus-visible, disabled, loading, error, empty.
6. Check motion purpose and `prefers-reduced-motion` respect.
7. Classify findings and recommend **concrete corrections** (not vague dislike).

---

## Detect aggressively

- Generic AI / template SaaS visual patterns
- Too many rounded cards or excessive card nesting
- Unnecessary pills and chip spam
- Overused glow or purple on non-brand elements
- Inconsistent spacing, radius, or typography hierarchy
- Giant wasted whitespace / low information density
- Weak contrast or incorrect semantic colors (success/warn/danger)
- Missing hover/focus/disabled/loading/error/empty states
- Poor responsiveness or RTL-hostile layout
- Inaccessible controls (labels, focus order, touch targets)
- Animation without purpose; missing reduced-motion support
- Inconsistent icons or mixed icon libraries
- AI-generated imagery or icons; replacement of official CLS logo
- Remaining **ZyroX** branding, Neural Core copy, fake metrics/claims
- Visually weak security / command-center pages
- Design divergence between pages (different “products” feel)

---

## Severity model

| Level | Meaning |
|-------|---------|
| **BLOCKER** | Wrong product identity, fake claims, broken a11y, unusable mobile/RTL, or violates dark-only / CLS OS naming policy |
| **HIGH** | Major density/IA mismatch, missing critical states, semantic color misuse, security UI that undermines trust |
| **MEDIUM** | Inconsistent tokens/patterns, weak hierarchy, avoidable generic AI tropes |
| **POLISH** | Micro-interactions, motion refinement, spacing rhythm, delight within CLS tone |

Each finding should include: **location**, **issue**, **severity**, **recommended fix** (specific enough to implement).

---

## Output format

```markdown
## CLS OS UI Review — [scope]

### Summary
[1–3 sentences]

### Findings
1. **[SEVERITY]** [Title] — [path/component]
   - Issue: …
   - Fix: …

### Passed checks
- …
```

---

## Do not

- Redesign the entire product in a review pass unless explicitly asked
- Introduce new brand colors, fonts, or tokens not yet approved in design architecture
- Suggest fake metrics or marketing fluff to “improve” landing pages
