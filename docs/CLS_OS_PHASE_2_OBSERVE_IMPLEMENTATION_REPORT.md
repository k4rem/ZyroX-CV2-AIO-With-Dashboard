# CLS OS Phase 2A OBSERVE implementation report

Runtime pass through 2A.4 only. Architecture commit `c7c9802f9aa451679d3e23b4100b9fcb64c7b1c1` stays frozen. This report records what was implemented, what was tested, and what remains manual.

## Implemented

- **2A.1** PostgreSQL schema `20261001_0002_security_core`, guild config and trust services, Root-only security capabilities plus `security.incidents.manage`, scheduler lease / reclaim / backoff / idempotent claim, discord.py `2.7.1` pin, startup allowlist sweep that never leaves allowlisted product guilds or `OPS_GUILD_ID`, and `view_audit_log` on Antinuke health as observability only.
- **2A.2** Audit-push attribution, bounded gateway correlation, coalesced fallback fetch, late and reconciliation flags. Durable uniqueness is the Discord audit entry id. `SELF` / `CLS_PROXIED` classification exists; the response ledger is not filled by live containment.
- **2A.3** Incident correlation (15 minute inactivity, 6 hour lifetime, manual close), evidence events, Ops outbox with retry, backoff, coalesce, and cap. Destination must be `OPS_SECURITY_ALERT_CHANNEL_ID` inside `OPS_GUILD_ID`. `allowed_mentions` is `none`. Retention purge exists.
- **2A.4** Pure `evaluate()` with no Discord I/O. OBSERVE can store `WOULD_CONTAIN` with `discord_mutation=false` and `replayable` never true. Root, guild owner, and scoped trust suppress containment. Late, PROBABLE, AMBIGUOUS, and UNATTRIBUTED evidence cannot produce `would_contain`. Single-action `would_contain` is only a confirmed critical-control grant on `@everyone`. Member prune, ELEVATED, and OBSERVABILITY do not. Bot add records and alerts. A later confirmed destructive bot sequence can record `would_contain`. Maintenance windows are Root-only, capped at 60 minutes, and expire. They do not create a Discord mutation.

## Schema notes

Foundation migration creates the security tables through response and quarantine so later foreign keys exist. No code inserts an open quarantine or sets `discord_mutation`. Database triggers reject operational ENFORCE writes and Discord-mutation outcomes until 2A.6 drops them. Policy rows carry supporting columns (`rule_kind`, `distinct_targets`, `threshold_status`) on the approved `(guild_id, action_class)` key. Threshold status is forced to `DEVELOPMENT_PROPOSAL`.

Attribution requires both the architecture §7.4 and §8.2 windows, so the implemented match is their intersection.

The architecture sequence `cls.impairment` is stored as `sequence.platform_impairment`. The local test database password is the token `cls`, and the backup test rejects that token anywhere in `pg_dump` output. The rule behavior is unchanged: a platform-impairment action followed by a destructive action inside the window.

## Tests actually run

Disposable database `postgresql+asyncpg://postgres:cls@127.0.0.1:5433/cls_discord_test`.

- After 2A.1: full `bot/tests` — 97 passed, 12 subtests.
- After 2A.2: full `bot/tests` — 112 passed.
- After 2A.3: full `bot/tests` — 117 passed, 12 subtests.
- 2A.4 focused: `tests/test_security_policy.py` and `tests/test_security_attribution.py` — 25 passed.
- Final full `bot/tests` after 2A.4: 127 passed, 12 subtests passed.

## Manual Discord verification still pending

`docs/PHASE_2A_DISCORD_VERIFICATION.md` marks V-1 through V-8 as **IMPLEMENTED — MANUAL TEST-GUILD VERIFICATION PENDING**. No real channel, role, or member was deleted to satisfy those checks. Mocked audit objects do not count as passing V-1–V-8.

## Safe deferrals

- 2A.5 legacy unload, 410 routes, and `anti.db` archive.
- 2A.6 quarantine execution and the operational ENFORCE switch.
- 2A.7 bot kick / managed-role strip / inviter punishment.
- 2A.8 dashboard and public security API.
- 2A.9 ENFORCE rollout, Phase 2B, Phase 2S.
- Repeating scheduler rows for alert delivery, incident sweep, and retention are registered as handlers and are not auto-enqueued on a timer in this pass. Tests call the functions directly.
- The Ops sender is injected. `configure_alert_sender` is not attached to a live Discord channel in this pass, so an unconfigured destination stays undeliverable. There is no product-guild fallback.
- Live owner suppression uses the guild owner id observed by the security cog. A decision made before any event has seen that guild does not yet know the owner.

## Risks

- Legacy antinuke listeners are still loaded, by instruction. They can still punish. The V2 path does not.
- Threshold numbers are development proposals. `would_contain` is evidence, not a production certification.
- Gateway merge window, attribution timings, incident lifetime, and alert caps follow the approved proposed values.
