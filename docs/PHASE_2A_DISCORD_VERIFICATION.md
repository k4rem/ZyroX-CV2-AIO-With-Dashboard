# Phase 2A Discord verification

**Status:** IMPLEMENTED — MANUAL TEST-GUILD VERIFICATION PENDING

Automated tests cover correlation, dedupe, attribution states, rate-limit coalescing, and guild isolation with fakes. They do not prove live Discord audit-log semantics. No channels, roles, or members were deleted to produce this record.

| ID | Item | Status |
|---|---|---|
| V-1 | `on_audit_log_entry_create` delivery, intent, permission, actor, target, latency, aggregation | IMPLEMENTED — MANUAL TEST-GUILD VERIFICATION PENDING |
| V-2 | Hierarchy semantics for equal positions and member edits | IMPLEMENTED — MANUAL TEST-GUILD VERIFICATION PENDING |
| V-3 | Kick versus leave, and prune entry contents | IMPLEMENTED — MANUAL TEST-GUILD VERIFICATION PENDING |
| V-4 | Bot add managed-role creation and booster roles | IMPLEMENTED — MANUAL TEST-GUILD VERIFICATION PENDING |
| V-5 | Whether CLS can edit a managed bot role | IMPLEMENTED — MANUAL TEST-GUILD VERIFICATION PENDING |
| V-6 | Audit reason propagation for SELF matching | IMPLEMENTED — MANUAL TEST-GUILD VERIFICATION PENDING |
| V-7 | RESUME replay versus a new session | IMPLEMENTED — MANUAL TEST-GUILD VERIFICATION PENDING |
| V-8 | Member overwrite precedence over role denies | IMPLEMENTED — MANUAL TEST-GUILD VERIFICATION PENDING |

Code already assumes, until those checks pass:

- equal role positions are uncontainable (no mutation exists in this pass anyway);
- a gateway member remove is not a kick;
- managed roles are not human permission escalations;
- a RESUME does not run reconciliation, and a new session's reconciliation entries are late.
