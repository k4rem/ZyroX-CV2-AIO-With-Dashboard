# Phase 1 Implementation Report — Platform Core

## 1. Executive result

Phase 1 **architecture is largely implemented** on branch `phase-1-platform-core`, but **full acceptance validation is incomplete** (PostgreSQL migration exercised only via schema/migration files; no live auth-matrix integration suite; guild resource validation helpers minimal; backup restore not executed end-to-end in this environment).

**Final recommendation:** **NOT READY FOR PHASE 1 REVIEW** until owner runs Postgres migrations, configures secrets, and performs integrated smoke with grants + proxy.

## 2. Architecture implemented

- Browser → Next.js (`/api/bot/[...path]`) → short-lived internal JWT → FastAPI on **same asyncio loop** as discord.py.
- Persistent **`dashboard_sessions`**, grants, roles, audit, scheduler, snapshot metadata foundation in PostgreSQL (`cls_platform` package).
- **`ROOT_OWNER_ID`** separate from **`OWNER_IDS`**; root-only `/api/v1/access` and `/api/v1/admin`.

## 3. FastAPI event-loop migration

- Removed daemon `Thread` + `uvicorn.run` from `CodeX.py`.
- `api/lifecycle.py` starts `uvicorn.Server.serve()` via `asyncio.create_task` on bot `setup_hook`; shutdown on `bot.close()`.

## 4. PostgreSQL / Alembic

- Package: `bot/cls_platform/`
- Alembic: `bot/alembic/` revision `20260330_0001` (sessions, roles, grants, audit, scheduler_jobs, snapshot_metadata + seeded Admin/Moderator/Support templates).
- Commands (from `bot/`): `alembic upgrade head`

## 5. Dashboard authentication flow

- Discord OAuth scope **`identify` only**; access token used server-side once to create session via **`POST /api/internal/v1/sessions`** (`INTERNAL_SERVICE_KEY`).
- Session id stored in NextAuth JWT (`dashboardSessionId`); not exposed to browser JS as Discord token.

## 6. Sessions

- Create / revoke / revoke-all services in `cls_platform/services/sessions.py`.
- Logout attempts internal revoke (fail-open).

## 7. Internal token

- HS256 JWT (`PyJWT` / `jsonwebtoken`), claims `sub`, `sid`, `aud`, `iat`, `exp`, `jti`; verified in `api/auth/identity.py`.

## 8. Explicit grants / RBAC

- Grants + capability templates; root bypass; **`rbac.manage` root-only** (not in assignable templates).
- Root UI: `/dashboard/access`.

## 9. Route authorization coverage

- Central HTTP middleware (`api/auth/middleware.py`) + guild capability map (`api/auth/policy.py`).
- **Gap:** automated enumeration test for every `/api/v1/*` route policy not yet added.

## 10. Root Owner

- `ROOT_OWNER_ID` in `cls_platform/config.py`; startup warning if missing.

## 11. Audit foundation

- Append-only `audit_events` + `AuditService`; grant/role/session events wired on access routes.

## 12. Scheduler / role temp

- `scheduler_jobs` + SKIP LOCKED worker loop; `role_temp_remove` handler; **`role temp`** restored in `cogs/moderation/role.py` (schedule-before-assign).

## 13. Typed Discord references

- `cls_platform/discord_types.py` (Pydantic snowflakes for new V2 APIs).

## 14. Storage interface

- `cls_platform/storage.py` local filesystem `put/get/delete/exists`.

## 15. Backup system

- `bot/scripts/cls_backup.py` — SQLite backup API, jsondb copy, optional pg_dump/restic hooks.
- **Gap:** scratch restore verification not run here.

## 16. Permission/hierarchy health

- `cls_platform/health/permissions.py`; exposed via `/api/v1/system/health`.

## 17. Module/system health

- Integrated with Phase 0 `module_health` in system health endpoint.

## 18. Docker topology

- Root `docker-compose.yml` + nginx reverse proxy (Dashboard public; bot-api loopback-mapped for dev only).

## 19. Dependency changes

- Python: SQLAlchemy[asyncio], asyncpg, alembic, PyJWT.
- Dashboard: `jsonwebtoken`, tracked `package-lock.json`.

## 20. Dashboard changes

- Proxy route, server-side bot fetch, guild picker from authorized backend list, removed Discord `guilds` scope / Manage Guild gate.

## 21. Tests and exact results

| Suite | Result |
|-------|--------|
| `pytest tests/test_phase0_security.py tests/test_module_loader.py tests/test_phase1_platform.py` | **20 passed** |
| `npm run build` (dashboard) | **PASS** (ESLint warnings only) |
| Client secret scan (`.next/static`) | **No backend secret strings found** |
| `docker compose config` | **PASS** |
| Postgres migration on live DB | **NOT RUN** (owner action) |
| Auth matrix integration | **NOT RUN** |
| Compose up / E2E smoke | **NOT RUN** |

## 22. Security self-review findings/fixes

- Fixed SQLAlchemy reserved name `metadata` → `snapshot_meta`.
- Allowlist import avoids loading full `utils` package (discord side effect).
- Proxy blocks `/internal` paths and sanitizes upstream auth headers.
- **Open:** broad legacy guild routes still rely on middleware path map (may default capabilities); dedicated resource ownership helpers not applied across all mutating endpoints.

## 23. Deferred items

- Full route-policy enumeration test.
- Comprehensive auth-matrix automated tests.
- Guild channel/role ownership validators on all legacy mutators.
- Anti-escalation on grant operations beyond root-only management.
- Off-host restic repository (owner/deployment).
- Blocking SQLite hot-path audit document (not started as refactor).

## 24. Manual owner actions

See `docs/PHASE_1_MANUAL_ACTIONS.md`.

## 25. Acceptance matrix

| Criterion | Status |
|-----------|--------|
| Single event loop | **PASS** |
| PostgreSQL + Alembic clean DB | **PARTIAL** (migration present; not applied in CI here) |
| No browser FastAPI credential | **PASS** |
| Next.js proxy boundary | **PASS** |
| Session + JWT + grants + RBAC | **PARTIAL** (implemented; needs integrated test) |
| Route auth coverage | **PARTIAL** |
| Scheduler + role temp | **PARTIAL** (code + unit smoke; no restart integration test) |
| Backup restore | **DEFERRED** |
| Compose topology | **PARTIAL** (config valid; not brought up) |
| Dashboard build | **PASS** |
| Phase 0 tests | **PASS** |
| Phase 2 not started | **PASS** |

## 26. Final recommendation

**NOT READY FOR PHASE 1 REVIEW** — complete owner manual steps, run `alembic upgrade head`, grant smoke test, and integrated auth/scheduler/backup validation; then re-run acceptance checklist.
