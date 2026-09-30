# SQLite on shared bot/API event loop (Phase 1)

Phase 1 colocates FastAPI and discord.py on one asyncio loop. Synchronous SQLite still appears on API hot paths:

| Area | Risk | Phase 1 action |
|------|------|----------------|
| `api/routes/guilds.py` | Many handlers use `aiosqlite` (async) — lower risk | No change |
| `api/db_manager.py` / legacy admin SQLite | Sync connection per request patterns | Monitor; prefer async paths for new code |
| Prefix/config resolution via legacy utils | Possible sync SQLite in cog paths when invoked from commands | Documented; not API hot path |
| `messages.py` / ticket SQLite | Sync reads under load could stall loop if called from async without executor | **Deferred** — avoid calling sync ticket DB from FastAPI until Tickets V2 |
| `role temp` | Uses Postgres scheduler (async) | Addressed in Phase 1 |

**Rule:** New V2 domains use PostgreSQL. Do not expand synchronous SQLite usage from FastAPI handlers.
