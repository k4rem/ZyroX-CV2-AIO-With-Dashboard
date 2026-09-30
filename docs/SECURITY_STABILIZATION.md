# Security stabilization patch

## Scope

This patch addresses the narrowly selected findings from `docs/SECURITY_AUDIT_V2.md`. It does not redesign the dashboard/API, add PostgreSQL or RBAC, implement member recovery, or change the ticket architecture.

No runtime database rows were deleted.

## Files changed

- `.gitignore`
- `bot/.env.example`
- `bot/cogs/events/on_guild.py`
- `bot/cogs/commands/np.py`
- `bot/cogs/commands/extra.py`
- `bot/utils/tunnel.py`
- `bot/utils/paginators.py`
- `bot/cogs/commands/autorole.py`
- `bot/cogs/commands/ai.py`
- `bot/cogs/commands/music.py`
- `bot/cogs/commands/image.py`
- `bot/cogs/commands/fun.py`
- `bot/cogs/commands/map.py`
- `docs/LEGACY_STATE_CLEANUP.md`
- `docs/SECURITY_STABILIZATION.md`

## Findings addressed

### H-01 — Original-project outbound telemetry

Removed from `bot/cogs/events/on_guild.py`:

- guild invite retrieval
- guild join and remove metadata embeds
- sends to hardcoded original-project channels
- the support-server advertisement posted into newly joined guilds

A targeted loaded-code check also found hardcoded original-project log sends in `bot/cogs/commands/np.py` and the hardcoded development-team destination in `bot/cogs/commands/extra.py`. Those outbound sends were removed. The explicit `report` command now says that no trusted destination is configured and sends nothing externally.

No replacement telemetry was added.

A follow-up review removed the remaining automatic partner-server integration in `bot/cogs/commands/np.py`. Guild `1401125905677553716` and role `1401134167873290311` were original-project identifiers. Boosting a guild listed in `autonp` inserted a global no-prefix row for 60 days, and ending that boost deleted it. The same guild and role were also updated when an owner or staff member added, removed, expired, or reset no-prefix. Those role updates and the `autonp` command group are removed. Owner and staff `np list`, `np add`, `np remove`, `np status`, and `np reset` still manage the local no-prefix table. The existing `autonp` table was not modified.

Compatibility impact:

- Joining or leaving a guild no longer sends an external notification.
- No-prefix changes no longer send logs or role updates to the original project.
- Membership, boosting, or activity in an original-project guild no longer grants no-prefix.
- The `report` command is unavailable until a future trusted reporting design is intentionally implemented.

### H-02 — Runtime package/binary installation

`bot/utils/tunnel.py` now uses only a preinstalled `cloudflared` executable found on `PATH`. It no longer:

- invokes pip
- imports `pycloudflared` to trigger downloads
- downloads a binary from GitHub
- changes permissions on a downloaded binary
- executes a newly downloaded binary

If `cloudflared` is missing, the tunnel is skipped with a clear message.

`TUNNEL_ENABLED` defaults to false. If the variable is absent, the tunnel stays disabled. `bot/.env.example` recommends `false` unless the operator explicitly needs a tunnel.

`bot/utils/paginators.py` no longer runs a GitHub pip install. `discord-ext-menus` is a required startup dependency, not an optional pagination extra. `bot/utils/__init__.py` imports paginators while the utils package loads, and `bot/core/zyrox.py` imports that package before the bot connects. A missing package raises `ModuleNotFoundError` during import. The bot cannot reach a Discord-facing error message first.

Compatibility impact:

- Install `discord-ext-menus` before startup. The bot does not start without it.
- Install `cloudflared` only when `TUNNEL_ENABLED` is explicitly true.

### M-02 — Stored-data `eval`

`bot/cogs/commands/autorole.py` and `bot/cogs/commands/ai.py` now:

- read JSON first
- use `ast.literal_eval` only as a typed legacy fallback; it does not execute code
- accept autorole JSON lists, legacy Python lists, and comma-separated positive integer IDs
- normalize the tuple that `ast.literal_eval` returns for a value such as `123,456`
- reject bools, non-integers, non-positive IDs, expressions, and malformed values as an empty list
- write new data as JSON

The calculator was intentionally unchanged.

Compatibility impact:

- Existing JSON lists, Python-list strings, and legacy comma-separated positive integer IDs remain readable.
- Malformed or wrong-type stored values become empty lists rather than being executed.

### M-03 — Hardcoded external credentials

Removed tracked Spotify, Pexels, Giphy, and MapQuest credentials. Added safe, blank environment examples:

- `SPOTIFY_CLIENT_ID`
- `SPOTIFY_CLIENT_SECRET`
- `PEXELS_API_KEY`
- `GIPHY_API_KEY`
- `MAPQUEST_API_KEY`

Removed the hardcoded public Lavalink host and shared password fallbacks. `LAVALINK_HOST` and `LAVALINK_PASSWORD` must now both be configured.

Compatibility impact:

- Spotify URL handling is disabled when Spotify credentials are absent.
- Pexels-backed image commands are disabled when its key is absent; the waifu image source is unaffected.
- Giphy-backed action commands are disabled when its key is absent; local/random fun commands are unaffected.
- The currently unloaded map cog also fails closed when its MapQuest key is absent.
- Music commands report an unavailable state when Lavalink is missing or cannot connect.
- Secret values are never printed.

### M-04 — Legacy state and Git hygiene

`docs/LEGACY_STATE_CLEANUP.md` records the exact no-prefix, extra-owner, and antinuke whitelist rows and provides transactional manual cleanup instructions. Test data was not automatically removed.

`.gitignore` now ignores future:

- SQLite databases, journals, WAL and shared-memory files
- runtime JSON under `bot/db/` and `bot/jsondb/`
- selected root runtime JSON files
- locally provisioned tunnel binaries under `bot/bin/`
- TypeScript incremental build state

## Already-tracked files needing a later decision

Ignore rules do not affect files already tracked. No `git rm` command was run. A later reviewed `git rm --cached` decision is required for:

- `bot/db/admin_config.db`
- `bot/db/afk.db`
- `bot/db/ai_data.db`
- `bot/db/anti.db`
- `bot/db/automod.db`
- `bot/db/autoreact.db`
- `bot/db/autoresponder.db`
- `bot/db/autorole.db`
- `bot/db/badges.db`
- `bot/db/block.db`
- `bot/db/blword.db`
- `bot/db/boost.db`
- `bot/db/customrole.db`
- `bot/db/emergency.db`
- `bot/db/fastgreet.db`
- `bot/db/giveaways.db`
- `bot/db/ignore.db`
- `bot/db/invc.db`
- `bot/db/invite.db`
- `bot/db/jail.db`
- `bot/db/leveling.db`
- `bot/db/media.db`
- `bot/db/messages.db`
- `bot/db/minecraft.db`
- `bot/db/notify.db`
- `bot/db/np.db`
- `bot/db/prefix.db`
- `bot/db/stats.db`
- `bot/db/stickymessages.db`
- `bot/db/ticket.db`
- `bot/db/ticket.db-journal`
- `bot/db/topcheck.db`
- `bot/db/vanity.db`
- `bot/db/verification.db`
- `bot/db/warn.db`
- `bot/db/welcome.db`
- `bot/j2c_data.db`
- `bot/rr.db`
- `bot/jsondb/birthdays.json`
- `bot/jsondb/logging_config.json`
- `dashboard/tsconfig.tsbuildinfo`

Before untracking databases, decide which schema/bootstrap data must be recreated for a fresh deployment. Do not delete current test data without a backup.

## Intentionally deferred

### C-01 — Dashboard/API authorization

The exposed browser API key, missing per-user/per-guild authorization, and role-escalation paths are unchanged. The current dashboard API must not be exposed for production until the V2 security foundation is implemented.

### M-01 — SSRF

No SSRF architecture change was made. Future work must address:

- `bot/cogs/commands/ai.py`: `AI.ai_analyse` / `AI.analyze_image`
- `bot/cogs/moderation/moderation.py`: `roleicon`
- `bot/cogs/commands/minecraft.py`: `SetupModal.on_submit`, `Minecraft.auto_detect_server`, and `Minecraft.refresh_all_statuses`

### M-05 — Dependency reproducibility

Dependency review, version locking, lockfile policy, and vulnerability scanning remain separate work. This patch only removes the two runtime installation/download paths.

Also deferred:

- dashboard authentication redesign
- per-guild API authorization and RBAC
- PostgreSQL
- command manager
- OAuth member recovery
- disaster recovery
- ticket dashboard redesign

## Manual steps still required

1. Revoke/rotate the previously committed Spotify, Pexels, Giphy, and MapQuest credentials at their providers. Removing them from the current tree does not remove Git history.
2. Configure private replacement credentials only in the real deployment environment if those integrations are needed.
3. Install `discord-ext-menus` before startup; it is required. Install `cloudflared` only if you set `TUNNEL_ENABLED=true`. Do not let the application install either one.
4. Follow `docs/LEGACY_STATE_CLEANUP.md` after confirming current test guild/user ownership.
5. Decide which tracked runtime files to remove from Git's index later; back up current test data first.
6. Keep the dashboard API private/disabled until C-01 is resolved.
