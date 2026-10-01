# CLS OS — Phase 2 Implementation Plan

**Status:** APPROVED SEQUENCE. Runtime implementation not started.\
**Architecture:** `docs/CLS_OS_PHASE_2_ARCHITECTURE.md`\
**Decisions:** `docs/PHASE_2_OWNER_DECISIONS.md`\
**Spec:** `docs/CLS_DISCORD_V2_SPEC.md` v1.1, §59

Each step follows spec §65. Read the spec, scope the step, implement, run targeted validation, review the diff, test in an isolated server where applicable, and commit only after approval. Never use `git add .`. Never stage preview env files or helpers, runtime databases, or secrets.

## Phase order

```text
Phase 2A — Early Protection   (this plan, steps 2A.1–2A.9)
Phase 2B — Snapshot Foundation
Phase 2S — Recovery Feasibility Spike
Phase 3  — Verification V2 … (unchanged)
```

2B must be accepted before Phase 3.25 (snapshot validation), Production-Lite Gate 4, and Phase 4 (Tickets V2).

---

## Phase 2A steps

| Step | Goal | Files (indicative) | Schema | Tests | Depends on | Risk | Acceptance gate |
|---|---|---|---|---|---|---|---|
| **2A.1 Foundation** | Schema, models, config, tier map, RBAC capabilities, hardening. No behaviour change. | `bot/cls_platform/security/{models,config,trust,tiers,taxonomy}.py`; Alembic `0002_security_core`; `cls_platform/capabilities.py` (adds `security.enforce.manage`, `security.trust.manage`, `security.quarantine.release`, `security.maintenance.manage` to `ROOT_ONLY`, plus `security.incidents.manage`); `cls_platform/policy.py`; route registry; scheduler leases, reclaim and backoff; discord.py pin; startup allowlist sweep; `view_audit_log` added to Antinuke health | All tables in architecture §20 | Migration up and down; constraints (partial uniques, no gateway uniqueness); RBAC matrix; isolation | Docs accepted | Low | Migrations reversible; `test_route_coverage` green; no listener behaviour change |
| **2A.2 Observation and attribution (record only)** | Audit feed, gateway signals, correlation, fallback fetch, watermark and reconciliation, late flag | `security/feed.py`, `security/signals.py`, `security/attribution.py`, `cogs/security/protection.py` | — | Push only; gateway then push; push then gateway; repeated legitimate change outside G is **not** deduplicated; merge inside G only on an identical digest; SUPERSEDED vs PENDING; EXPIRED_UNATTRIBUTED then late supersede; stale rejection; one entry per observation; 403 and 429; replay idempotency; restart resume | 2A.1 | Medium | **Verification items V-1 to V-8 executed in a disposable test guild** and recorded in `docs/PHASE_2A_DISCORD_VERIFICATION.md`; no false CONFIRMED results |
| **2A.3 Incidents, evidence, Ops alerts** | Incident lifecycle, timeline, outbox, Ops delivery and validation | `security/incidents.py`, `security/alerts.py`, scheduler handlers (`security_alert_deliver`, `security_incident_sweep`) | — | 15-minute inactivity attach and new-incident cases; max lifetime; manual close; partial-unique race; alert dedupe, coalescing and cap; invalid or missing destination | 2A.2 | Low | Alerts reach only the Ops channel; no product-channel leak; no eternal incidents |
| **2A.4 Policy engines (OBSERVE)** | Human and Bot engines, tiers, rules, `would_contain` | `security/policy_engine.py`, `security/bot_engine.py` | Policy rows | Each rule below, at, and above threshold; tier mapping; @everyone CRITICAL_CONTROL single action; prune is alert only; ELEVATED and OBSERVABILITY never eligible; managed-role exclusion; `bot.add` never counts for the inviter; trusted actors alert; late entries excluded from eligible counts | 2A.3 | Medium | OBSERVE runs in real guilds and produces explainable decisions |
| **2A.5 Legacy retirement** | Unload 17 legacy listeners; retire legacy config commands (antinuke, whitelist, extra owner); `/antinuke` routes return 410; decouple Emergency mode; read-only archive of `anti.db` | `cogs/cog_loader.py`, `cogs/commands/{antinuke,anti_wl,extraown,emergency}.py`, `api/routes/guilds.py`, dashboard antinuke page | — | Legacy loaded means ENFORCE refused; no SQLite writes; no Supreme role creation | 2A.4 | Medium | No dual protection path; no legacy trust import |
| **2A.6 Containment (ENFORCE capable)** | Quarantine engine, outcome enum, release, self-action ledger, ENFORCE switch with preconditions, Maintenance Window | `security/containment.py`, `security/quarantine.py`, `security/self_actions.py`, `security/maintenance.py` | — | `ACTIVE`; `PARTIAL_QUARANTINE` (sub-operation fails, residual managed or overwrite privilege); `UNCONTAINABLE_HIERARCHY` (no call made); `FAILED_PERMISSION`; `FAILED_DISCORD` with member re-read; `NOT_ATTEMPTED_POLICY` (owner, Root, trusted); `SKIPPED_TRUSTED` (TOCTOU); `SKIPPED_MODE` (window or precondition change before mutation); OBSERVE decisions never replayed after switching to ENFORCE; 403 re-classification; idempotent re-apply; crash mid-apply; release; `RELEASE_PARTIAL`; drift guard; no self-release; SELF suppression with no loop; ENFORCE refused without Ops, Root, verification, or with legacy loaded; continuous degradation; Maintenance Window cap, auto-expiry, persistence across restart, audit and Ops mirror; observation continues during a window | 2A.5 | **High** | All tests green; test-guild containment drill; ENFORCE remains off in production |
| **2A.7 Bot Protection containment** | Bot containment after subsequent confirmed behaviour | `security/bot_engine.py`, `security/containment.py` | — | Bot added is alert only (severity by tier); bot destructive rate leads to containment; managed-role bit strip is recorded and reversible (V-5); never kick or ban; inviter never punished for the add | 2A.6 | Medium | Test-guild bot drill |
| **2A.8 Dashboard and API** | Protection settings, trusted actors, incidents, quarantines, Maintenance Window, Overview attention | `bot/api/routes/security.py`, `dashboard/app/dashboard/guild/[guildId]/antinuke/*` (or a renamed security route), `lib/api.ts`, attention derivation | — | Authorization matrix: Root, Admin, Moderator, Support, Custom, no grant, Ops guild, non-allowlisted, revoked; cross-guild ID returns 404; Root-only controls hidden and enforced server-side | 2A.3 onward, incrementally | Low/Medium | Real data only; owner UI review |
| **2A.9 OBSERVE review** | Soak in OBSERVE; review `would_contain`, false positives, and alert volume; choose production thresholds | Report `docs/PHASE_2A_OBSERVE_REVIEW.md` | — | — | 2A.8 | — | Owner sets production thresholds. Root decides ENFORCE per guild manually. |

## Phase 2B — Snapshot Foundation (outline; scoped later)

- Native structure snapshot capture (spec §26.1), including the ban list and member-role map.
- Metadata: `schema_version`, checksum, source guild, incident state. SUSPECT marking when an active 2A incident with severity H or above exists. KNOWN_GOOD and pinned state.
- Encrypted raw legacy configuration archive (§27), including the archived `anti.db`.
- Semantic adapters for Production-Lite modules (§27 priority list).
- Snapshot and backup failure alerts through the 2A Ops outbox.
- Gate: a known-good, checksummed main-guild snapshot exists (Production-Lite Gate 4).

## Phase 2S — Recovery Feasibility Spike

Unchanged (spec §23, §59).
