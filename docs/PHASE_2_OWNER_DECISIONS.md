# Phase 2 — Owner Decisions

**Status:** ALL RESOLVED (owner review 2026-10-01)\
**Applies to:** `docs/CLS_OS_PHASE_2_ARCHITECTURE.md`, `docs/CLS_OS_PHASE_2_IMPLEMENTATION_PLAN.md`, `docs/CLS_DISCORD_V2_SPEC.md` v1.1

These decisions are locked. They are not open questions. Changing one requires an explicit owner amendment recorded in this file.

| ID | Topic | Resolution |
|---|---|---|
| OD-1 | Phase order | **RESOLVED.** Phase 2A covers Early Protection: Human Antinuke, the Bot Protection foundation, attribution, incidents and evidence, quarantine, and CLS Ops alerts. Phase 2B is the Snapshot Foundation: structure snapshots, ban and member-role maps, checksums, KNOWN_GOOD/SUSPECT, and the encrypted legacy configuration archive. Phase 2S is Recovery Feasibility. Phase 3 and later follow unchanged. Snapshots must exist before Tickets V2 and before Production-Lite Gate 4. |
| OD-2 | Rollout posture | **RESOLVED.** OBSERVE only until observation data has been reviewed. Production ENFORCE is never enabled automatically. |
| OD-3 | Quarantine scope | **RESOLVED.** Remove all removable non-managed roles and record the exact prior roles for safe restoration. Timeout is **not** part of the default. An optional quarantine role is configuration-only and is never auto-created. |
| OD-4 | Single-action containment | **RESOLVED (split policy).** A CONFIRMED CRITICAL_CONTROL escalation on @everyone may contain in ENFORCE. A single member prune is a critical alert only. Other isolated destructive actions feed alert, rate, and sequence rules unless a specific approved policy says otherwise. |
| OD-5 | PROBABLE attribution | **RESOLVED.** Never contains automatically. |
| OD-6 | Root Discord identity | **RESOLVED.** Never contained automatically. H and C actions always alert and record. |
| OD-7 | Guild owner | **RESOLVED.** Never contained. H and C actions alert and record. |
| OD-8 | Trusted actors | **RESOLVED.** Still detected and recorded. Threshold violations alert. Trust suppresses automatic containment only. |
| OD-9 | Quarantine release | **RESOLVED.** Root only for Phase 2. |
| OD-10 | ENFORCE switch | **RESOLVED.** Root only. `security.config` may configure policy but cannot enable ENFORCE. |
| OD-11 | Untrusted bot added | **RESOLVED.** Record and alert only. Administrator or other tiered permissions raise alert severity. Automatic bot containment requires a subsequent confirmed destructive or security behaviour under the Bot Protection policy. The inviter is never automatically punished because the bot was added. |
| OD-12 | Legacy trust data | **RESOLVED.** No automatic import of legacy whitelist or extra-owner trust. Legacy configuration is archived read-only, and V2 trust starts clean. |
| OD-13 | Thresholds | **RESOLVED.** Current thresholds remain DEVELOPMENT PROPOSALS. Production values are chosen after OBSERVE evidence review. |
| OD-14 | Ops destination and retention | **RESOLVED.** A valid CLS Ops security-alert destination is mandatory for ENFORCE. If it is missing or invalid, ENFORCE is refused. Retention: unlinked observations 30 days; delivered alert outbox 30 days; incidents, response evidence, and quarantine history 365 days. |
| OD-15 | Late attribution | **RESOLVED.** Alert and evidence only. Never automatic containment. |
| OD-16 | Dangerous permissions | **RESOLVED** by the tiered taxonomy: CRITICAL_CONTROL (Administrator, Manage Guild, Manage Roles, Manage Channels); DESTRUCTIVE (Ban Members, Kick Members, Manage Webhooks); ELEVATED (Moderate Members, Mention Everyone, Manage Threads, Manage Events, Manage Expressions); OBSERVABILITY (View Audit Log, which is required for health and never an escalation containment trigger by itself). |
| OD-17 | Maintenance Window | **RESOLVED.** Root only. Time-boxed, with a maximum of 60 minutes initially. ENFORCE drops to OBSERVE. Observation is never disabled. It expires automatically, is fully audited, and is mirrored to CLS Ops. It must never be named or modelled as Incident Mode. |

## Architecture revisions accepted with these decisions

1. **Gateway idempotency.** The Discord audit entry ID is the durable idempotency authority. Gateway events are temporary signals with a short, bounded dedupe window and no retention-long uniqueness. Policy counts use confirmed, distinct audit entry IDs.
2. **Hierarchy.** A member whose highest role is at or above CLS's is `UNCONTAINABLE_HIERARCHY`: durable evidence, critical alert, and no stronger fallback. `PARTIAL_QUARANTINE` is reserved for editable members where some operations fail or privilege remains. Exact semantics are a test-guild verification item.
3. **Incident lifecycle.** Inactivity window of 15 minutes, configurable, plus a maximum lifetime. Manual resolve or false-positive closes immediately. No incident is an eternal bucket.
4. **Permission tiers.** As described under OD-16.
5. **Distinct outcomes.** `UNCONTAINABLE_HIERARCHY`, `PARTIAL_QUARANTINE`, `FAILED_PERMISSION`, `FAILED_DISCORD`, `ACTIVE`, and `RELEASE_PARTIAL` are never collapsed into a generic failure.

## Values still marked PROPOSED

Each of these is configuration and is confirmed after OBSERVE review:
- rate thresholds and windows;
- T_push, T_attr, T_late, and the skew bounds;
- the gateway dedupe window G (10 s, hard max 120 s);
- the maximum incident lifetime (6 h);
- alert coalescing and caps;
- gateway signal retention (24 h).
