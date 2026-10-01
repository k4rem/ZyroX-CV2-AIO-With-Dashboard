# Overnight progress

Starting commit: `phase-1.6-premium-dashboard` at the beginning of this session (Task A / A.1 already on the branch).

## Phase 1.6 Task B

Status: implemented locally, not pushed.

Welcome, Join to Create, and Custom Roles no longer share the old title / panel / giant Save composition.

- Welcome is a composer beside a fenced Discord preview. The default template colour is `#2F3136`, which `greet2` will honour. A colour without `#` is rejected in the form.
- Join to Create is a four-node flow (join, temporary voice, control panel, cleanup). Turning it off keeps the saved channel ids. The bot only creates temporary channels when the module is enabled and both required channels are set.
- Custom Roles is a command roster. Role ids stay strings. The command prefix comes from `/prefix` (this guild's prefix is `>`, not a hardcoded `.`).

### Discrepancies

- The phase plan said disabling Join to Create saves all three ids as null. The overnight instruction says disabling must not erase configuration. The implementation follows the overnight instruction and adds a reversible `enabled` column.
- The reference page lists 13 welcome variables. `greet2` substitutes 12. The UI lists those 12.
- Join DM sends the message as written and appends `Sent from {server}`. It does not substitute welcome variables, so the direct-message page does not pretend that it does.
- Voice role and Vanity roles are linked from the roster, and their own pages still use the old navy skin. They move in Task C.
- Permission-health context rail on Join to Create is omitted. This page does not receive a permission-health payload, and a pass/fail line would be invented.

### Checks so far

- `node --test lib/*.test.mjs` — 72 passed
- `npx tsc --noEmit` — passed
- `python -m unittest tests.test_j2c_enabled` — 3 passed
- Authenticated layout check on the local preview guild at 1440 and 390: Welcome reads as a message workspace, Join to Create as a flow, Custom Roles as a roster using `>`. RTL `dir` mirrors the preview. No save was sent to the guild during review.

Screenshots were taken by the browser tool into a local `qa-shots` path and are not part of the commit.
