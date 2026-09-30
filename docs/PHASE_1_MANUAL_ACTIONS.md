# Phase 1 — Manual owner actions

## Required before production Dashboard use

1. Set **`ROOT_OWNER_ID`** (same snowflake in bot `.env` and dashboard server env).
2. Generate and set matching secrets:
   - **`INTERNAL_SERVICE_KEY`** (bot + dashboard server)
   - **`INTERNAL_IDENTITY_SIGNING_KEY`** (≥32 random bytes; bot + dashboard server)
3. Configure **`DATABASE_URL`** and run migrations from `bot/`:
   - `alembic upgrade head`
4. Set production **`ALLOWED_GUILD_IDS`** (remove dev-only `ALLOW_EMPTY_GUILD_ALLOWLIST`).
5. Configure Discord OAuth redirect URLs for your production **`NEXTAUTH_URL`**.
6. Point **`BOT_INTERNAL_URL`** at the internal bot-api service (Compose: `http://bot-api:8000`).

## Backup / off-host (Production-Lite gate)

7. Configure **`RESTIC_REPOSITORY`** and **`RESTIC_PASSWORD`** when an off-host destination is chosen (Phase 1 ships local staging + optional restic hook only).

## Optional

8. Set **`OPS_GUILD_ID`** to exclude ops guild from normal product guild lists.
9. Production reverse proxy + TLS termination on the Dashboard entrypoint only (not FastAPI).
