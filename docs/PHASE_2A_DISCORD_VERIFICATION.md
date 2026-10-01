# Phase 2A Discord verification

No live Discord verification has been run. Mocked audit objects and the local Postgres suite do not prove Discord's audit-log, RESUME, or hierarchy behavior. No channels, roles, or members were deleted for this record.

| ID | Item | Code | Mocks | Live Discord | Phase |
|---|---|---|---|---|---|
| V-1 | `on_audit_log_entry_create` delivery, actor, target, and latency | CODE READY | MOCK TESTED with fake entries | LIVE DISCORD PENDING | 2A.2 |
| V-2 | Hierarchy for equal positions and member edits | Not a containment behavior in this pass | Not tested against Discord | LIVE DISCORD PENDING | LATER PHASE (2A.6) |
| V-3 | Kick versus leave, and prune entry contents | CODE READY: kicks are audit-only; a pushed prune keeps its actor and is not containment-eligible | MOCK TESTED for the push classification | LIVE DISCORD PENDING | 2A.2 |
| V-4 | Bot-add managed-role creation and booster roles | CODE READY: managed roles are not recorded as human permission escalation | MOCK TESTED for managed skip / bot privilege class | LIVE DISCORD PENDING | 2A.4 |
| V-5 | Whether CLS can edit a managed bot role | Not implemented. No bot-role edits exist | Not tested | LIVE DISCORD PENDING | LATER PHASE (2A.7) |
| V-6 | Audit `reason` propagation for SELF matching | CODE READY: SELF requires a real mutation ledger row with action, target, time window, and `CLS-SEC` token. `WOULD_CONTAIN` does not match | MOCK TESTED | LIVE DISCORD PENDING | 2A.6 for real mutations |
| V-7 | RESUME replay versus a new session | CODE READY hook only: `on_resumed` does not reconcile; the first `on_ready` in a process may fetch one bounded page after the watermark. This is not a claim that Discord's RESUME semantics were verified | Not tested against a real gateway session | LIVE DISCORD PENDING | 2A.2 |
| V-8 | Member overwrite precedence over role denies | Not implemented. Overwrite actions stay inactive | Not tested | LIVE DISCORD PENDING | LATER PHASE |

Catch-up from the watermark skips role and member-role audit actions, because those need a permission diff. The live listener classifies them when the push arrives.
