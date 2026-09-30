# Phase 1 Implementation Report — Platform Core

## 1. Executive result

Phase 1 platform core on branch `phase-1-platform-core` is **implemented and locally validated** against disposable PostgreSQL (port 5433), FastAPI integration tests, Dashboard build, and backup scratch restore.

**Final recommendation:** **READY FOR PHASE 1 REVIEW** — production deployment secrets, domain/TLS, and full Compose E2E on VPS remain owner/deployment actions (see §24).

## 2. Architecture implemented

- Browser → Next.js (`/api/bot/[...path]`) → short-lived internal JWT → FastAPI on **same asyncio loop** as discord.py.
- Persistent **`dashboard_sessions`**, grants, roles, audit, scheduler, snapshot metadata in PostgreSQL (`cls_platform` package).
- **`ROOT_OWNER_ID`** separate from **`OWNER_IDS`**; root-only `/api/v1/access` and `/api/v1/admin`.
- Fail-closed route registry + capability map; unknown `/api/v1/*` guild routes **deny** until classified.

## 3. FastAPI event-loop migration

- Removed daemon `Thread` + `uvicorn.run` from `CodeX.py`.
- `api/lifecycle.py` starts `uvicorn.Server.serve()` via `asyncio.create_task` on bot `setup_hook`; shutdown on `bot.close()`.

## 4. PostgreSQL / Alembic

- Package: `bot/cls_platform/`
- Alembic: `bot/alembic/` revision `20260330_0001`.
- **Local validation:** `alembic upgrade head` on disposable DB `cls_discord_test` @ `127.0.0.1:5433`; `test_phase1_tables_exist` confirms all Phase 1 tables.

## 5. Dashboard authentication flow

- Discord OAuth scope **`identify` only**; access token used server-side once to create session via **`POST /api/internal/v1/sessions`** (`INTERNAL_SERVICE_KEY`).
- Session id stored in NextAuth JWT (`dashboardSessionId`); not exposed to browser JS as Discord token.

## 6. Sessions

- Create / revoke / revoke-all services in `cls_platform/services/sessions.py`.
- Integration tests cover revoked session, revoke-all, subject/session mismatch, and internal session flow (mock Discord `/users/@me` only).

## 7. Internal token

- HS256 JWT (`PyJWT`), claims `sub`, `sid`, `aud`, `iat`, `exp`, `jti`; verified in `api/auth/identity.py`.

## 8. Explicit grants / RBAC

- Grants + capability templates; root bypass; **`rbac.manage` root-only**.
- Root UI: `/dashboard/access`; integration tests for grant/revoke, root-only access API, guild picker filtering.

## 9. Route authorization coverage

- `api/auth/route_registry.py` — every `/api/*` route classified (`EXPLICIT_PUBLIC`, `INTERNAL_SERVICE`, `ROOT_ONLY`, `AUTHENTICATED_USER`).
- `tests/test_route_coverage.py` — **fail** on any unclassified route.
- `api/auth/policy.py` — no permissive unknown-route capability fallback.

## 10. Root Owner

- `ROOT_OWNER_ID` in `cls_platform/config.py`; tests prove `OWNER_IDS` alone does not grant root.

## 11. Audit foundation

- Append-only `audit_events` + `AuditService`; grant/role/session events on access routes.

## 12. Scheduler / role temp

- `scheduler_jobs` + `FOR UPDATE SKIP LOCKED` claiming; `role_temp_remove` handler registered.
- Integration: single completion, bounded retry, missing-member safe terminal, **restart persistence** (job row survives; fresh tick completes once).

## 13. Typed Discord references

- `cls_platform/discord_types.py`; `api/validators/discord_resources.py` for mutation payload role/channel validation.

## 14. Storage interface

- `cls_platform/storage.py` local filesystem `put/get/delete/exists`.

## 15. Backup system

- `bot/scripts/cls_backup.py` — SQLite backup API, jsondb copy, optional pg_dump/restic hooks.
- **Local validation:** `test_backup_restore_sqlite_and_json` — stage, backup, restore SQLite + JSON; `.env` not captured.

## 16. Permission/hierarchy health

- `cls_platform/health/permissions.py`; `utils/module_health.required_modules_report`; `/api/v1/system/health` returns safe JSON (no secrets).

## 17. Module/system health

- Integrated with Phase 0 `module_health` in system health endpoint.

## 18. Docker topology

- Root `docker-compose.yml` + nginx reverse proxy.
- **`docker compose config`:** PASS.
- **Compose E2E bring-up:** **DEFERRED — OWNER/DEPLOYMENT** (Docker Desktop daemon not running in closure environment; client only).

## 19. Dependency changes

- Python: SQLAlchemy[asyncio], asyncpg, alembic, PyJWT, pytest, pytest-asyncio, httpx.
- Dashboard: `jsonwebtoken`, tracked `package-lock.json`.

## 20. Dashboard changes

- Proxy route (`proxyUtils.ts` + tests), server-side bot fetch, guild picker from authorized backend list.

## 21. Tests and exact results

| Suite | Result |
|-------|--------|
| `pytest tests/` (60 tests + subtests) | **60 passed** (local Postgres 5433) |
| Auth matrix integration | **PASS** (`test_phase1_integration_auth.py`) |
| Route coverage | **PASS** |
| Cross-guild resource validation | **PASS** |
| Scheduler integration | **PASS** |
| Postgres migrations / tables | **PASS** |
| Backup restore (SQLite + JSON) | **PASS** |
| System health (no secret leak) | **PASS** |
| Phase 0 security / loaders | **PASS** |
| `npm ci` + `npm run build` (dashboard) | **PASS** |
| `node lib/proxyUtils.test.mjs` | **3/3 PASS** |
| Client secret scan (`.next/static`) | **No backend secret strings** |
| `docker compose config` | **PASS** |
| `git diff --check` | **PASS** |

## 22. Security self-review findings/fixes (closure)

- Fail-closed route registry and policy; centralized Discord resource validation on mutating payloads.
- Next.js proxy blocks `/internal`, strips spoofing headers, rejects untrusted browser Authorization upstream.
- Fixed circular import (`core/__init__.py` lazy `zyrox`; `Tools.py` import path; guarded prefix DB init under running event loop).
- `required_modules_report` implemented for system health.

## 23. Deferred / partial (acceptable for review)

| Item | Status |
|------|--------|
| Off-host encrypted restic target | **DEFERRED — OWNER/DEPLOYMENT** |
| Full Compose stack smoke (health + alembic in containers) | **DEFERRED — OWNER/DEPLOYMENT** (no local daemon) |
| Concurrent two-worker SKIP LOCKED race test | **PARTIAL / ACCEPTED** (locking path used; explicit dual-worker test not automated) |
| Every legacy guild mutator hand-audited | **PARTIAL / ACCEPTED** (central payload validator + cross-guild tests; not every route individually asserted) |
| Full delegated anti-escalation beyond root-only RBAC | **PARTIAL / ACCEPTED** (documented; root-only management) |
| Blocking SQLite hot-path full refactor | **DEFERRED** — see `docs/SQLITE_EVENT_LOOP_NOTES.md` |
| Production `ROOT_OWNER_ID`, signing secrets, `DATABASE_URL`, OAuth redirect, TLS, `ALLOWED_GUILD_IDS` | **DEFERRED — OWNER/DEPLOYMENT** |

## 24. Manual owner actions

See `docs/PHASE_1_MANUAL_ACTIONS.md`.

## 25. Acceptance matrix

| Criterion | Status |
|-----------|--------|
| Single event loop | **PASS** |
| PostgreSQL + Alembic clean DB | **PASS** (local disposable DB) |
| No browser FastAPI credential | **PASS** |
| Next.js proxy boundary | **PASS** |
| Session + JWT + grants + RBAC | **PASS** (integration tests) |
| Route auth coverage | **PASS** |
| Scheduler + role temp | **PASS** (integration; restart persistence) |
| Backup restore (local) | **PASS** (SQLite + JSON) |
| Compose topology config | **PASS** |
| Compose runtime E2E | **DEFERRED — OWNER/DEPLOYMENT** |
| Dashboard build + secret scan | **PASS** |
| Phase 0 tests | **PASS** |
| Phase 2 not started | **PASS** |

## 26. Final recommendation

**READY FOR PHASE 1 REVIEW** — all locally testable code and validation blockers addressed. Complete owner manual steps for production credentials, domain, and VPS Compose before go-live.
