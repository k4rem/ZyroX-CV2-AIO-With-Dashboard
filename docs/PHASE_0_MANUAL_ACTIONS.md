# Phase 0 — Owner manual actions

These items cannot be completed in the repository alone.

## Credentials and exposure

- [ ] Rotate `DASHBOARD_API_KEY` if it was ever committed, shared, or used from the browser.
- [ ] Rotate any provider keys (OpenAI/Gemini, webhooks, tunnel tokens) if they appeared in Git history or public dashboards.
- [ ] Revoke or audit old Discord bot invite links that could add the bot to non-CLS guilds.

## Production guild configuration

- [ ] Set `ALLOWED_GUILD_IDS` in production `bot/.env` to CLS Test, CLS Main, and CLS Ops guild IDs (comma-separated).
- [ ] Keep `ALLOW_EMPTY_GUILD_ALLOWLIST=false` in production (bot will not start with an empty allowlist otherwise).
- [ ] For local dev without allowlist IDs yet, set `ALLOW_EMPTY_GUILD_ALLOWLIST=true` only on non-production machines.
- [ ] Confirm `LEGACY_VERIFICATION_ENABLED=false` on the main guild until Verification V2 ships.
- [ ] Keep `API_ENABLED=false` on production until Phase 1 proxy and auth are deployed.
- [ ] If enabling API for local dev only: `API_HOST=127.0.0.1`, do not set `API_ALLOW_PUBLIC_BIND=true` unless deliberately isolated.

## Legacy privilege cleanup (see `docs/LEGACY_STATE_CLEANUP.md`)

- [ ] Back up `bot/db/np.db` and `bot/db/anti.db`, then remove unapproved legacy no-prefix / whitelist rows before production.
- [ ] Prefer clean runtime DBs for production rather than copying tracked test databases from Git.

## Dashboard

- [ ] Do not rely on `NEXT_PUBLIC_DASHBOARD_API_KEY` in production browsers.
- [ ] Phase 1: deploy authenticated Next.js proxy before treating the dashboard as production-safe.

## Validation smoke test (owner)

From `bot/` with your dev `.env`:

```bash
python CodeX.py
```

Confirm startup shows module health summary, guild allowlist warning or enforcement, and API disabled unless explicitly enabled.
