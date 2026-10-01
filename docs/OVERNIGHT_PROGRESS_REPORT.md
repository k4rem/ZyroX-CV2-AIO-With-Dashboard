# Overnight progress

This is a progress record, not a closure. Phase 1.6 is not closed. Nothing was pushed.

## 1. Starting commit

`28e4f2b` — `add CLS OS overview analytics instruments` on `phase-1.6-premium-dashboard`.

Phase 1.5 baseline: `a4ff916`. Task A: `4a7a520`. Task A.1: `28e4f2b`.

## 2. Phase 1.6

### Task B

Local commit `3f99a7f` — `implement CLS OS premium module workspaces`. Not pushed.

- Welcome is a composer beside a fenced Discord preview. Default template colour is `#2F3136`. A colour without `#` is rejected.
- Join to Create is a four-node flow. Turning it off keeps the saved channel ids. The bot arms only when enabled and both required channels are set.
- Custom Roles is a command roster. Role ids stay strings. Prefix comes from `/prefix`.

Authenticated layout check on the local preview guild at 1440 and, after the width fix, at 390. RTL `dir` mirrored the Welcome preview. No configuration was saved to the guild. Screenshot files were not retained.

### Task C

Local commit `54d489e` — `migrate remaining surfaced modules onto the graphite instrument`. Not pushed. Not closed.

Surfaced pages that still used the navy panel were moved onto the same graphite setting rows:

- Tickets: channel and category selectors, a category list, panel embed preview, contextual save for delivery. This is the current ticket API only. No builder, transcripts, or analytics.
- Auto roles: member and bot lists, ten-role limit kept, no guideline card, no full-width save bar.
- Reaction roles, vanity roles, voice role, auto react: dense rows. Role and channel ids stay strings. Turning voice role off does not clear the selected role.
- Bot settings: one prefix row and a dirty save bar.
- Logging: the existing category routing, plus a count of categories that are both enabled and have a destination.
- Antinuke: still the real master switch and whitelist only. The page says so. No score, no incident timeline.

Automod, Access, and Platform were already on graphite tokens and were not rewritten.

`node scripts/check-legacy-tokens.mjs --strict` exits 0. It skips hidden Verification and Leveling, and unused legacy components that no surfaced route imports. Those files still contain `#141B2D` and `slate-800` / `slate-900`.

### Closure

Not closed.

The Playwright browser context has no dashboard session (`/?notice=session-ended`). Task C pages were not reviewed at 2560, 1440, 1024, or 390, and not in RTL or reduced motion. Phase 2 was not started.

## 3. Phase 2

Not started. It waits on a closed Phase 1.6.

## 4. Later phases

None.

## 5. Bugs fixed

- Welcome default colour is stored with `#`.
- Disabling Join to Create no longer nulls the saved channel and category ids.
- Custom role ids are not passed through `parseInt`.
- Saving ticket delivery or a category no longer wipes unsaved panel title and description.

## 6. Bugs deferred

- Welcome cannot clear a channel by sending null. The API ignores a null channel id. The form does not offer a clear action.
- Hidden Verification and Leveling pages, and unused legacy form components, still use the navy skin.
- Antinuke has no per-action coverage in the current API, so there is no protection matrix.

## 7. Owner decisions

None new. Phase 2 has not been opened, so no `PHASE_2_OWNER_DECISIONS.md` yet.

## 8. Tests

- `node --test lib/*.test.mjs` — 72 passed
- `npx tsc --noEmit` — passed
- `python -m unittest tests.test_j2c_enabled` — 3 passed (Task B)
- `node scripts/check-legacy-tokens.mjs --strict` — passed, 0 files
- Production `next build` was not run. A build would write `.next` while `next dev` is serving port 3000.

## 9. Screenshots

Not retained. Task B was measured in an authenticated browser. Task C was not, because this browser context is logged out.

## 10. Branches

`phase-1.6-premium-dashboard` only. No `phase-2-early-protection`.

## 11. Commits

- `3f99a7f` implement CLS OS premium module workspaces
- `54d489e` migrate remaining surfaced modules onto the graphite instrument

## 12. Processes

- `3000` — Next dev, listening
- `3001` — not listening
- `8000` — preview bot API, listening
- `5433` — Postgres, listening, not modified

## 13. Git status

Recorded after the Task C commit in the following section of this file's history. Untracked preview env and preview scripts stay unstaged.

## 14. Review first

1. Welcome, Join to Create, and Custom Roles on the preview guild.
2. Tickets, Auto roles, Reaction roles, Vanity roles, Voice role, Auto react, and Bot settings.
3. Confirm disabling Join to Create and Voice role keeps the saved ids.
4. Hidden Verification and Leveling are still the old skin on purpose.
