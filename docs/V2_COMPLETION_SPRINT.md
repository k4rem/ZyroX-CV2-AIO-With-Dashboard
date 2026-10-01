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

## Phase 3 verification
DONE on phase-3-verification-v2. Tests: tests/test_verification_v2.py. Gate stays off until enabled. Verified role is not an allow key. Visual QA of the page was not opened in a browser this session.

## Phase 3.25 readiness
PARTIAL. No deploy. Head migration is 20261001_0005. `/health` remains the process check. Backup stays the existing Postgres dump path. Rollback is `alembic downgrade 20261001_0004` for the verification tables only. ENFORCE and live restore stay off. VPS, firewall, proxy, and lifeOS were not touched.



