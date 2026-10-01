# V2 completion sprint

## 2A.1–2A.4.1
DONE. Commits 5282414..609ee87. Pushed to origin/phase-2-early-protection. Tests: 139 passed before this sprint.

## Discord verification V-1 V-3 V-4 V-6 V-7
MANUAL PENDING. No disposable guild mutation was run from this environment. Do not use the production guild.

## 2A.5–2A.8
DONE for runtime and dashboard data. Tests: 146 passed, 12 subtests.
Commit follows this note.
## 2B snapshot foundation
DONE on branch phase-2b-snapshot-foundation. Tests: tests/test_snapshots.py (checksum, large snowflake, guild isolation, SUSPECT). No restore.

## 2S recovery feasibility
DONE. docs/PHASE_2S_RECOVERY_FEASIBILITY.md. Member rejoin is NO-GO without guilds.join.

## Phase 3 verification
DONE on phase-3-verification-v2. Tests: tests/test_verification_v2.py. Gate stays off until enabled. Verified role is not an allow key. Visual QA of the page was not opened in a browser this session.

## Phase 3.25 readiness
PARTIAL. No deploy. Health stays `/health`. Rollback of verification is alembic downgrade to 20261001_0004. VPS, firewall, proxy, and lifeOS were not touched.

## Phase 4 tickets
PARTIAL on phase-4-tickets-v2. Postgres categories, panels, open/claim/close/reopen, transcript, dashboard workspace. Tests: tests/test_tickets_v2.py. Deferral: browser QA not run; cooldown and blacklist not built; no legacy ticket.db import.




