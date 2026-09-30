# CLS Discord V2 — Final Product & Architecture Specification

**Status:** APPROVED FOR IMPLEMENTATION  
**Version:** 1.0  
**Date:** 2026-09-30  
**Project:** CLS Discord System  
**Repository base:** ZyroX-CV2-AIO-With-Dashboard fork  
**Primary deployment target:** CLS Discord server  
**Current main-server size:** ~400 members  

---

## 0. Purpose of This Document

This document is the single source of truth for CLS Discord V2 implementation.

It incorporates:
- the current repository baseline;
- the command inventory;
- the dashboard baseline review;
- the security audit;
- the security stabilization patch;
- the legacy-state cleanup findings;
- the architecture review by Claude;
- the repository-aware architecture review by Cursor;
- final owner decisions.

Implementation must follow this specification unless the owner explicitly approves a change.

No major architectural deviation should be implemented silently.


# 1. Product Direction

CLS Discord System is being built primarily for the CLS Discord community for approximately the next year.

It is **not** currently being built as a public SaaS product.

However, new V2 domains should avoid architectural decisions that would make future multi-guild or SaaS conversion require a full rewrite.

## 1.1 Product split

### Discord

Discord remains the primary surface for:
- day-to-day member interaction;
- ticket conversations;
- moderation actions;
- community engagement;
- member-facing workflows;
- voice features;
- operational staff interaction.

### Dashboard

The Dashboard is primarily for:
- configuration;
- security administration;
- audit;
- historical data;
- analytics;
- ticket administration;
- transcripts;
- member recovery;
- backups and disaster recovery;
- command/module controls;
- infrastructure health.

The Dashboard is **not** intended to become a full Discord chat client.


# 2. Core Engineering Principles

The following rules are non-negotiable.

1. No hidden external telemetry.
2. Root Owner is controlled server-side only.
3. No backend/service secret may appear in browser code.
4. Dashboard access requires an explicit server-side grant.
5. Discord Administrator or Manage Guild does not automatically grant Dashboard access.
6. FastAPI is the final authorization authority.
7. Every guild-specific action must be authorized against that guild.
8. One domain has one source of truth.
9. No SQLite/PostgreSQL dual writes for one domain.
10. New V2 Discord IDs must be semantically typed.
11. No unnecessary big-bang rewrite.
12. Critical actions are disabled by default.
13. Sensitive mutations are audited.
14. Backups and structure snapshots begin early.
15. Member recovery must pass a feasibility gate before production use.
16. Recovery is never marketed or represented as guaranteed.
17. Discord remains the daily operational surface.
18. Dashboard remains the control/security/history surface.
19. Join-to-Create is a required production module.
20. Major phases require isolated test-server validation.
21. Production readiness is determined by objective gates, not by intuition.
22. New V2 domains should be guild-scoped even while CLS currently uses one main guild.
23. Existing working code should be reused unless there is a concrete reason to refactor or rebuild it.
24. Dangerous legacy behavior must not be preserved merely for compatibility.


# 3. High-Level Runtime Architecture

The production request path is:

```text
Browser
  ↓
Next.js Dashboard
  ↓
Next.js authenticated server-side proxy
  ↓
Short-lived signed internal identity token
  ↓
FastAPI
  ↓
Authorization / Domain Services
  ↓
Discord Bot + PostgreSQL + Legacy Stores
```

## 3.1 Internet exposure

Only the public web entry point should be exposed.

Preferred public path:

```text
Internet
  ↓
Reverse Proxy / TLS
  ↓
Next.js Dashboard
```

FastAPI must remain internal-only in production.

The browser must not know or use a direct FastAPI service credential.


# 4. Bot and API Event Loop

The current repository starts uvicorn in a daemon thread with a separate event loop.

V2 must change this.

## Final decision

FastAPI and the Discord bot run inside the same async runtime/event loop.

Uvicorn should be started through an async server task rather than a separate thread.

This is required because:
- dashboard actions may invoke Discord operations;
- domain services are shared by Discord handlers and API routes;
- the PostgreSQL async pool should not be shared across unrelated loops;
- current cross-thread calls are unsafe.

## Constraint

Moving API and bot onto one loop makes blocking work more important.

Therefore:
- synchronous SQLite work must not be added to hot paths;
- expensive CPU work must be moved off the event loop;
- new Postgres access must use an async driver;
- long-running exports or rendering must use controlled worker/executor behavior.


# 5. Next.js → FastAPI Boundary

All Dashboard bot/API traffic must go through a Next.js server-side proxy.

Recommended shape:

```text
/api/bot/[...path]
```

The existing API client can remain conceptually centralized, but its base path must point to the Next.js proxy instead of the bot API directly.

## The proxy must

1. read the authenticated Dashboard session;
2. reject unauthenticated requests;
3. mint a short-lived internal token;
4. forward the request to internal FastAPI;
5. never expose the internal service credential to the browser.

## Internal identity token

The token may contain:
- user_id / subject;
- session_id;
- issued-at;
- expiry;
- audience;
- unique token ID.

It must **not** contain long-lived authorization state.

FastAPI reads current permissions/grants from PostgreSQL on each privileged request.


# 6. Dashboard Authentication

Dashboard authentication uses Discord OAuth.

For Dashboard login, the intended user identity scope should be minimal.

The Discord access token must not be copied into browser-visible session JSON.

After FastAPI validates the Discord identity during session creation, the Discord OAuth access token should not be required for normal Dashboard authorization.


# 7. Dashboard Session Model

Final decision:

```text
dashboard_sessions
```

Use a persistent session table instead of relying only on a non-revocable JWT cookie.

A session record should support at least:
- session ID;
- user ID;
- created timestamp;
- last-seen timestamp;
- authentication time;
- revoked state;
- revoked timestamp/reason;
- expiry;
- optional device/session metadata where useful.

## Required capabilities

- revoke one session;
- revoke all sessions for one user;
- immediately reflect removed Dashboard access;
- support recent-auth checks for high-risk actions;
- support incident response.

A lightweight indexed lookup per privileged request is acceptable because Dashboard staff count is small.


# 8. Root Owner Model

Two concepts must remain separate.

## ROOT_OWNER_ID

The single highest-trust application identity.

Controls:
- Dashboard root access;
- RBAC root;
- security administration;
- recovery;
- disaster restore;
- critical operations;
- break-glass decisions.

## OWNER_IDS

Discord bot developer/owner command access.

The same person may initially appear in both, but they are conceptually distinct.

## Root Owner restrictions

Root Owner cannot be granted by:
- Dashboard role editing;
- Discord commands;
- normal application flows;
- Discord Administrator role.

Changing ROOT_OWNER_ID is an infrastructure/server operation only.

## High-risk Root actions

Critical actions should require recent authentication.

A break-glass runbook must document how Root ownership is recovered if the account is unavailable or compromised.


# 9. Dashboard Access Grants

Dashboard access is explicit.

A Discord server role is not sufficient.

Example:

```text
Root Owner
  ↓
grants Dashboard access
  ↓
User receives Admin / Moderator / Support / Custom capabilities
```

Discord membership or roles may later be additional eligibility conditions.

They are not the trust root.


# 10. RBAC Model

Use capability-based authorization with role templates.

## Example capabilities

```text
tickets.config
tickets.transcripts.view
tickets.analytics.view
tickets.staff.manage

logging.view

security.config
security.incidents.view

audit.view

giveaways.manage
invites.manage

rbac.manage
```

## Templates

Initial templates:
- Admin;
- Moderator;
- Support;
- Custom.

Templates are bundles of capabilities.

## Anti-escalation rule

A user may not grant a capability they do not possess.

Initially:

```text
rbac.manage = Root Owner only
```

Avoid:
- field-level permissions;
- per-channel Dashboard RBAC;
- overly granular policy matrices;

unless a real CLS requirement appears.


# 11. Guild Allowlist

The bot must use an explicit guild allowlist during the CLS-only phase.

Expected guilds may include:
- CLS Test;
- CLS Main;
- CLS Ops.

The bot must not automatically become fully operational in an arbitrary guild merely because it was invited.

The allowlist is an infrastructure/security control.


# 12. CLS Ops Guild

Create a separate private Discord server used for out-of-band operational alerts.

Expected members:
- Root Owner;
- a very small number of trusted people;
- CLS Bot.

## Intended alerts

- critical security incidents;
- Root security/login events;
- Incident Mode activation;
- critical command execution;
- backup failures;
- snapshot failures;
- bot startup/failure/recovery;
- disaster recovery activity;
- required-module health failures.

## Ops Guild exclusions

The Ops guild must be excluded from normal CLS product behavior, including where applicable:
- verification gating;
- welcome automation;
- regular giveaways;
- standard antinuke configuration;
- destructive "global" owner command loops;
- ordinary customer-facing Dashboard management.


# 13. Database Strategy

PostgreSQL is introduced in Phase 1.

Use Alembic from the first Postgres migration.

## 13.1 One domain = one source of truth

This rule is mandatory.

Do not:

```text
write SQLite
+
write PostgreSQL
+
synchronize later
```

for the same domain.

## 13.2 Migration model

A legacy domain migration is:

```text
backup
→ migrate
→ validate
→ cut over
→ PostgreSQL becomes authoritative
→ old SQLite becomes read-only archive
```

## 13.3 Postgres first-use domains

Initial Postgres domains should include:
- dashboard sessions;
- dashboard grants;
- capabilities / templates;
- internal audit events;
- scheduler jobs;
- snapshot metadata;
- later: recovery data;
- later: Tickets V2;
- later: Logging V2;
- later: Invite/Giveaway V2.

## 13.4 Legacy SQLite

Low-value or stable legacy modules may remain SQLite indefinitely.

Do not migrate a module simply because PostgreSQL exists.


# 14. Legacy Store Reality

Until legacy domains are migrated, backups must cover:
- PostgreSQL;
- SQLite databases;
- JSON stores;
- J2C root-level database;
- reaction-role database;
- other required runtime state.

Do not copy active SQLite database files blindly while they are being written.

Use:
- SQLite backup API where practical;
- or a short controlled application pause.


# 15. Typed Discord References

New V2 schemas must not store opaque Discord IDs without semantic meaning.

Use explicit typed fields such as:
- guild_id;
- role_id;
- channel_id;
- category_id;
- message_id;
- user_id.

For legacy formats, use per-module snapshot/remapping adapters.

Do not attempt to rewrite every old schema before it is needed.


# 16. Service Layer

Use thin domain services.

Examples:
- TicketService;
- VerificationService;
- SnapshotService;
- SecurityService;
- InviteService;
- GiveawayService;
- JoinToCreateService where refactoring provides value.

Discord handlers and Dashboard API routes should invoke the same domain logic.

Do not build a generic abstraction layer that hides all SQLite/Postgres differences.


# 17. Module Loading & Health

The current package-wide cog loading model is too fragile for production.

V2 must move toward a module registry that can load modules independently.

## Required module concept

Production-Lite requires a defined set of mandatory modules.

Example:

```text
Moderation
Security
Tickets
Verification V2
Logging baseline
Welcome
Join-to-Create
```

If a required production module fails to load:
- health status must fail;
- CLS Ops must receive an alert;
- the failure must not be silently ignored.

Optional modules may fail without declaring the whole bot healthy.


# 18. Existing Module Classification

## 18.1 Required / actively supported

- Moderation;
- Security / Antinuke;
- Tickets;
- Verification;
- Logging;
- Welcome;
- Invite Tracking;
- Auto Roles;
- Reaction Roles;
- Join-to-Create.

## 18.2 Keep and potentially improve later

- AI;
- Music;
- Counting.

## 18.3 Keep source, disabled/unloaded by default, no active development now

- Minecraft;
- Games;
- Leveling;
- Birthdays.

The source should not be deleted solely because these modules are not currently needed.


# 19. Join-to-Create

Join-to-Create is a required CLS production feature.

The existing implementation should be reused, not rewritten from scratch, unless a concrete defect requires change.

## 19.1 Existing core flow to preserve

- trigger voice channel;
- create temporary voice channel;
- move joining user;
- persist owner;
- delete channel when empty.

## 19.2 Minimum required fixes before Production-Lite

- give the owner explicit channel permissions;
- prevent lock from locking the owner out;
- add rename support;
- handle channel-create failures;
- handle member-move failures;
- delete the new channel if move fails;
- clean up stale channel rows;
- reconcile missing/empty temp channels at startup;
- guard empty-channel deletion against races;
- fix invite-selector limits;
- fix SetLimitModal missing-cog behavior;
- make reset delete only tracked objects, not objects matched only by name;
- fix database deletion ordering;
- persist category_id correctly;
- ensure block/untrust behavior is coherent;
- validate channel types and guild ownership in the API;
- move J2C runtime data to an appropriate mounted data location;
- use persistent views correctly instead of resending control panels unnecessarily on ready.

## 19.3 Dashboard minimum

The Dashboard should support practical J2C configuration including:
- enabled state;
- trigger channel;
- control channel;
- target category;
- default user limit;
- naming template where supported;
- owner controls;
- cleanup behavior.


# 20. Verification V2

The current verification implementation must **not** be reused as the production gating engine.

It is a rebuild.

## 20.1 Phase 0 containment

Until V2 Verification is ready, dangerous legacy verification commands must be blocked from the main guild.

This includes commands that can broadly rewrite channel overwrites.

## 20.2 Final gate model

Do not use one Verified role that grants view access to every channel.

Preferred model:

```text
Existing permissions remain unchanged.

New member
  ↓
receives Unverified role
  ↓
Unverified role is denied access to protected categories
  ↓
Verification succeeds
  ↓
remove Unverified
  ↓
optional Verified status role
```

The Verified role must not be a master permission key.

## 20.3 Verification configuration

### Verification Gate

```text
OFF
ON
```

### Recovery Authorization

```text
DISABLED
OPTIONAL
REQUIRED
```

Target CLS default may become:

```text
Verification = ON
Recovery Authorization = REQUIRED
```

only if the Recovery Feasibility Spike and policy review pass.


# 21. Existing Member Migration

Main CLS currently has approximately 400 existing members.

The initial production rollout must not suddenly hide the server from all existing members.

Support:

```text
GRANDFATHER
GRACE_PERIOD
REQUIRE_NOW
```

## Initial rollout decision

### New members

Verification applies immediately.

### Existing members

Use GRACE_PERIOD.

Existing members retain current access initially.

Verification/recovery adoption is encouraged during the grace period.

If enforcement is later required, the transition should be explicit and controlled.

Do not bulk-grant a permission-master Verified role.


# 22. Verification UX

The verification channel should be clearly branded as official CLS infrastructure.

The message should explain:
- why verification exists;
- what Discord permissions are requested;
- what Recovery Authorization means;
- what the application cannot access;
- that no Discord password is requested;
- privacy information;
- the official CLS domain;
- the difference between verification and recovery where optional.

The design should minimize scam-like appearance.


# 23. Member Recovery Feasibility Gate

Recovery must not be considered production-ready until a dedicated spike passes.

Use:
- disposable test guilds;
- multiple test accounts.

Verify with official documentation and real tests:
- OAuth grant;
- guilds.join behavior;
- token refresh;
- refresh-token rotation;
- revocation;
- long-term token behavior;
- rate limits;
- failed joins;
- banned-user behavior;
- role assignment;
- batching;
- target guild restrictions;
- Discord Developer Policy / Terms.

The result is a formal decision gate.


# 24. Recovery Vault

Do not finalize online-key versus offline-private-key architecture until the Recovery Spike clarifies token lifecycle requirements.

Regardless of the final model:
- no recovery tokens in browser code;
- no recovery tokens in logs;
- no recovery tokens in Discord messages;
- no recovery tokens in source control;
- Root-only recovery execution;
- minimum exposure;
- explicit target-guild allowlist;
- dry runs;
- bounded batches;
- progress;
- cancellation;
- audit.

There is:
- one Primary Custodian;
- at least one highly trusted Backup Custodian.

Final key custody design is deferred until the feasibility decision gate.


# 25. Recovery Status Semantics

Do not use misleading labels.

Preferred statuses include:
- granted;
- revoked;
- dormant;
- unknown / untested.

Only use "healthy" when a real validation has occurred.

"Recovery coverage" should mean grants on file, not guaranteed recoverability.


# 26. Structure Snapshots

Capture begins early, before Tickets V2.

## 26.1 Structure data

Capture where supported:
- guild settings;
- roles;
- role hierarchy;
- permissions;
- categories;
- channels;
- channel positions;
- permission overwrites;
- ban list;
- member-to-role mappings;
- emoji/sticker metadata;
- relevant bot configuration.

## 26.2 Snapshot metadata

Include:
- schema_version;
- created_at;
- checksum;
- source guild;
- incident state.

Allow:
- SUSPECT snapshots;
- KNOWN_GOOD / pinned snapshots.

A snapshot taken during an active incident should be marked suspect.


# 27. Legacy Config Snapshot Strategy

Do not build semantic remapping adapters for every legacy database immediately.

Phase 2 should capture:
1. native Discord structure;
2. a consistent encrypted raw archive of legacy runtime configuration;
3. semantic adapters only for Production-Lite modules first.

Priority adapters:
- Verification V2;
- Welcome;
- Autorole;
- Reaction Roles;
- J2C;
- Logging;
- Tickets;
- Antinuke;
- Automod;
- Voice Role;
- Custom Roles.

Message-bound configs require republishing rather than preserving old message IDs.


# 28. Off-Host Backups

Off-host encrypted backups begin during Platform Core.

Database backup and Discord structure snapshot are separate systems.

Backups should cover:
- PostgreSQL;
- active SQLite stores;
- JSON stores;
- important runtime configuration;
- snapshot metadata/data;
- recovery metadata once enabled.

The backup destination should be independent from the primary VPS where practical.

A restore must be tested periodically.


# 29. Snapshot-Before-Mutation

High-impact bulk operations should take a structure snapshot before executing when practical.

Examples:
- bulk permission changes;
- mass role changes;
- restore actions;
- selected destructive recovery operations.

Failure to create a required safety snapshot should block the mutation unless Root explicitly performs a defined break-glass override.


# 30. Disaster Recovery V1

V1 restores only into a **fresh empty replacement guild**.

Do not implement in-place partial restore in the first release.

## Restore stages

1. validate snapshot integrity;
2. create/prepare destination guild;
3. create safe roles;
4. create categories;
5. create channels;
6. apply permission overwrites;
7. restore guild-level settings where supported;
8. recreate emojis/stickers where supported and available;
9. restore bot config using typed mappings/adapters;
10. restore ban list;
11. manual review;
12. optionally recover authorized members;
13. restore safe member roles;
14. privileged member-role assignments require explicit Root approval;
15. remove temporary elevated bot permissions used for restore.

## ID mapping

Maintain a restore map similar to:

```text
restore_run_id_map
run_id
kind
old_id
new_id
```

Unknown/unmapped references must be surfaced.

Never silently reuse stale Discord IDs.

## Partial failure

Restore stages should be idempotent where practical and recorded in a run journal.

For V1, rollback of a badly restored empty replacement guild may simply mean discarding it and starting again.


# 31. Tickets: Production Stabilization Before V2

The existing ticket system is not production-ready without fixes.

Before Production-Lite:
- fix or remove hybrid ticket commands that call nonexistent logic;
- re-register in-ticket persistent views after restart;
- ensure closed-ticket controls have stable custom IDs;
- reconcile deleted channels/orphaned ticket rows;
- fix or disable the broken Dashboard ticket save path;
- verify open → restart → claim → close → reopen;
- verify transcript generation/storage.

Do not pretend legacy tickets are fully operational until this passes.


# 32. Tickets V2.0

Tickets are the flagship product module.

The first V2 release must be strong but constrained.

## Include

- department-ready data model;
- one active department initially;
- categories;
- panel builder;
- actual Discord Publish/Update;
- short text form fields;
- long text form fields;
- single staff claim/unclaim;
- manual priority:
  - Low;
  - Normal;
  - High;
  - Urgent;
- required close reason;
- reopen;
- max concurrent tickets;
- creation cooldown;
- ticket blacklist;
- live transcript capture;
- attachment capture;
- transcript viewer;
- transcript search;
- internal staff notes;
- basic metrics:
  - opened;
  - closed;
  - open count;
  - first response time;
  - resolution time;
- migration/cutover plan for existing tickets.

## Postpone to V2.1

- multi-assignment;
- team assignment;
- automatic priority rules;
- advanced automation;
- multiple active departments UI;
- ratings;
- staff performance analytics;
- peak-time analytics;
- highly customized retention per category.


# 33. Tickets V2 Migration

The safest legacy ticket cutover must preserve compatibility.

## Migration outline

1. stop writes and back up ticket.db;
2. import configs;
3. import categories while preserving legacy category IDs or stable compatibility identifiers;
4. convert comma-separated notified roles into typed references;
5. import open tickets preserving ticket numbers;
6. rebuild per-user open-ticket counts from imported open rows;
7. validate each referenced Discord channel;
8. mark missing channels orphaned;
9. backfill open-ticket history into the V2 transcript store;
10. update existing panel messages to V2 components;
11. keep a temporary compatibility handler for legacy component IDs;
12. post V2 controls in each imported open ticket;
13. archive legacy ticket.db read-only.

The migration must not invalidate existing test or production panels unnecessarily.


# 34. Ticket Transcript Architecture

Capture ticket content while the ticket exists.

Do not wait until close time.

## Message events

```text
message create → persist
message edit   → update / event
message delete → mark deleted
```

Use raw Discord edit/delete events where required for uncached messages.

At startup, backfill missing ticket messages after the last captured message where possible.

Do not render raw untrusted transcript HTML into the Dashboard.

Use structured data rendering.


# 35. Attachments

Ticket attachments should be stored independently from transient Discord URLs when required for retention.

Before implementation, verify current Discord attachment URL behavior against official documentation/testing.

Use:
- file-size limits;
- per-guild quotas where needed;
- retention policy;
- safe content disposition;
- no inline execution of risky formats.

A small storage interface is acceptable:

```text
put
get
delete
exists
```

Initial implementation may use a local persistent volume.

S3-compatible storage is deferred.


# 36. Discord Activity Logging

Discord activity logging is separate from internal Dashboard audit.

## 36.1 Message content

Deleted-message content requires pre-delete storage.

Introduce a short-term forensic message store.

Starting policy proposal:

```text
30 days of message content
```

After retention:
- delete content;
- retain selected metadata longer where appropriate.

Ticket channels should not duplicate storage unnecessarily because the transcript subsystem already stores them.

The 30-day policy must be checked against applicable Discord policy requirements before production.


# 37. Logging Attribution

Actor attribution must be honest.

Supported states:
- certain;
- probable / confidence-based;
- unknown.

Never guess.

Audit-log correlation must use:
- action type;
- target;
- channel/context;
- timestamp window;
- uniqueness of candidate entry.

Where attribution is not reliable, show Unknown.

A shared audit event feed should replace repeated independent audit-log fetching where practical.


# 38. Internal Audit Log

Dashboard/system audit is separate from Discord server activity logs.

Use PostgreSQL.

The application database role should support append-only behavior where practical.

Record:
- actor;
- guild;
- action;
- target;
- before;
- after;
- timestamp;
- session;
- request context where appropriate.

Audit:
- Dashboard mutations;
- grants/revocations;
- transcript views;
- exports;
- Root logins;
- recovery actions;
- restore steps;
- security changes;
- Incident Mode;
- critical commands.

Secrets must be redacted.

Sensitive events should also be mirrored to CLS Ops.


# 39. Security Trust Model

Do not use one global trusted role as a bypass for all security.

For high-risk security modules such as:
- Antinuke;
- Bot Trap;

prefer explicit trusted:
- user IDs;
- bot IDs.

Security trust modifications are Root-controlled.

Automod may support role exemptions.

Staff must not automatically bypass phishing detection.


# 40. Antinuke V2 Direction

Move away from universal:

```text
one suspicious action → instant ban
```

Use:
- thresholds where appropriate;
- evidence;
- actor confidence;
- quarantine;
- incident logging;
- rollback where feasible.

Default response for suspicious human/staff behavior should favor reversible quarantine rather than immediate ban.

Bot Trap is a separate case and may still default to ban.

The bot's own actions must be exempt from its antinuke logic where appropriate.


# 41. Bot Trap

Support one or more configured trap channels.

If an untrusted bot posts there:

1. detect the bot;
2. verify it is not trusted;
3. apply configured action;
4. default action: ban;
5. delete recent messages where supported/configured;
6. create security incident;
7. log to Dashboard;
8. notify CLS Ops.

Webhook activity must be handled separately from ordinary bot accounts.


# 42. Phishing Protection

Initial design should remain simple.

For a human account posting detected phishing:

Default:

```text
delete message
+ timeout
+ security incident
```

Allow configured actions:
- delete only;
- timeout;
- kick;
- ban.

Do not build a large rules engine in the first release.

Do not automatically exempt staff.


# 43. Command Policy Architecture

Do not dynamically resync slash commands every time a Dashboard toggle changes.

Use:

```text
Code/module metadata
  ↓
Fixed command registration
  ↓
Runtime policy evaluation
```

## Central policy path

Use:
- one global bot check for prefix/hybrid commands;
- one application-command interaction check for pure slash commands;
- both call one CommandPolicy evaluator.

Before relying on hybrid behavior, confirm the pinned discord.py version's check behavior.


# 44. Command Registry Scope

Do not manually annotate all 559 commands immediately.

Use:
- module-level defaults;
- explicit overrides for HIGH/CRITICAL commands;
- automatic source discovery where possible.

A validation test should walk loaded commands and fail if a privileged/destructive command lacks an explicit risk classification.

Help output should respect runtime policy.


# 45. Risk Model

## LOW

- normal permission check.

## MEDIUM

- permission;
- audit.

## HIGH

- permission;
- author-bound confirmation;
- cooldown;
- audit.

## CRITICAL

- disabled by default;
- Root or explicit special authorization;
- Incident Mode required;
- typed confirmation;
- audit;
- CLS Ops mirror.

Prefix-only is not a security control.


# 46. Incident Mode

CRITICAL functionality remains unavailable under normal operation.

Root Owner may temporarily enable Incident Mode.

Example duration:

```text
30 minutes
```

It automatically expires.

## Enforcement

Incident Mode must be enforced inside the critical service operation itself, not only at the command decorator/check layer.

This prevents bypass through:
- buttons;
- views;
- Dashboard routes;
- alternate command paths.

A simple Dashboard Lock may separately freeze non-root Dashboard mutations during an incident.


# 47. Scheduler

Introduce one persistent Postgres-backed scheduler for new important jobs.

Use a simple jobs table and one bot-side poller.

Redis and APScheduler are not required initially.

## First migration candidate

`role temp`

because its current expiry can be lost on bot restart.

## Existing persisted loops

Do not rewrite all existing background loops immediately.

Legacy loops that already persist their own state may remain until their module phase.


# 48. Invite Tracking V2

Legacy invite counters are not trusted enough for V2 eligibility decisions.

Final decision:

```text
V2 invite history starts fresh at cutover.
```

Legacy invite values may optionally be displayed as:

```text
Legacy / Unverified
```

They must not count toward V2 Giveaway eligibility.

## Attribution states

Use honest classifications:
- exact;
- inferred;
- vanity;
- unknown.

Do not claim exact inviter attribution where Discord cannot prove it.


# 49. Giveaway V2

Eligibility may include:
- required roles;
- excluded roles;
- account age;
- membership age;
- verification status;
- level if enabled;
- V2 valid invite count.

Eligibility must be revalidated at draw time.

If a candidate fails:
- record rejection reason;
- choose another candidate.

Use persistent scheduling so a giveaway that ends while the bot is offline is reconciled after startup.


# 50. Welcome

Start with one strong Welcome Profile.

Initial builder may support:
- text;
- embed;
- title;
- description;
- color;
- author;
- footer;
- thumbnail;
- image URL;
- GIF URL;
- placeholders;
- preview;
- test welcome.

Multiple invite-aware profiles are deferred.

The current multiple join handlers should be consolidated or clearly separated to avoid duplicate welcome behavior.


# 51. AI

AI is retained.

Do not redesign it now.

Architecture/security requirements to account for:
- SSRF protection for user-controlled fetches;
- provider secrets only server-side;
- free the generic `bot.db` attribute for V2/Postgres infrastructure;
- isolate provider failure so AI failure does not affect core bot health.


# 52. Music

Music is retained.

Do not redesign it now.

Requirements to account for:
- reviewed/pinned wavelink version;
- no public/shared Lavalink fallback;
- Lavalink included in deployment planning if self-hosted;
- Music failure must not affect core bot health.


# 53. Counting

Counting remains supported but is not a major development priority.

Reuse existing behavior unless a concrete bug appears.


# 54. Disabled Legacy Modules

The following remain in source but should not consume active V2 implementation effort:
- Minecraft;
- Games;
- Leveling;
- Birthdays.

The module registry should allow them to stay unloaded/disabled without:
- startup failure;
- broken help;
- broken imports;
- Dashboard dead links.


# 55. Production Discord Permissions

The test server may temporarily use Administrator during development.

Production must not rely on Administrator by default.

Before Production-Lite:
- produce a permission matrix;
- bot role is not Administrator;
- required permissions are verified automatically;
- bot role is above every role it needs to assign/manage;
- bot role remains below appropriate human staff roles;
- missing permissions appear as a health/readiness failure.


# 56. Docker & Deployment

Docker Compose starts during Phase 1.

Expected logical topology:

```text
reverse-proxy
dashboard
bot-api
postgres
lavalink
backup-runner
```

This does not imply unnecessary microservices.

`bot-api` remains one application process hosting Discord bot + FastAPI.

## Runtime data

Use appropriate persistent volumes.

Avoid unreliable SQLite database bind mounts on Docker Desktop where named volumes are safer.

## Working directory

The current bot assumes the working directory is `bot/`.

The container must either:
- set the correct WORKDIR;
- or gradually replace fragile relative paths.

## Other portability concerns

Account for:
- root-level j2c_data.db;
- root-level rr.db;
- config.yml;
- jsondb;
- logs;
- fonts;
- cloudflared path if ever used;
- source-writing emoji sync;
- console-clear behavior.

Production should keep emoji source rewriting disabled unless intentionally redesigned.


# 57. Public Dashboard Exposure

Final owner decision:

Dashboard should eventually be publicly reachable over HTTPS.

Preferred path:

```text
Internet
  ↓
Reverse Proxy
  ↓
Next.js
```

FastAPI remains private/internal.

Development may remain local-only.


# 58. Production-Lite Readiness Gates

Deployment to the real CLS server occurs only after these gates pass.

## Gate 1 — Auth

- no public Dashboard API key in client assets;
- FastAPI has no public host port;
- unauthenticated routes reject;
- ungranted users reject;
- cross-guild access rejects.

## Gate 2 — Single-loop runtime

A Dashboard action that invokes Discord succeeds without cross-loop errors.

## Gate 3 — Backups

- encrypted off-host backup succeeded within the defined recent window;
- includes Postgres, required SQLite stores, and JSON data;
- scratch restore has been verified.

## Gate 4 — Structure snapshot

A known-good, checksummed main-guild snapshot exists before configuration migration.

## Gate 5 — Required modules

All required production modules load successfully.

Health fails if a required module is absent.

## Gate 6 — Permissions

- bot is not Administrator;
- required permission check passes;
- role hierarchy check passes.

## Gate 7 — Verification

On the test guild:
- enable/disable changes only configured protected areas;
- private staff/log/ticket/J2C areas are not exposed;
- Grace Period does not affect existing members unexpectedly.

## Gate 8 — Join-to-Create

Full J2C checklist passes, including restart recovery.

## Gate 9 — Tickets

- open ticket;
- restart bot;
- controls still work;
- claim;
- close;
- reopen;
- delete;
- transcript persists.

## Gate 10 — CRITICAL commands

Every CRITICAL command/action refuses execution outside Incident Mode.

## Gate 11 — Legacy state

Production starts from clean runtime databases without legacy privileged rows.

## Gate 12 — Rotation & Ops

- previously exposed provider credentials are rotated where applicable;
- CLS Ops receives test alerts.

Failure of a critical gate blocks Production-Lite.


# 59. Phase Plan

## Phase 0 — Security Foundation + Scope Control

Objectives:
- contain current unsafe API;
- keep API disabled/private;
- remove browser public API credential path;
- implement guild allowlist foundation;
- block dangerous legacy verification commands on main guild;
- complete SSRF cleanup or disable unused vulnerable paths;
- begin dependency review/locking;
- clean tracked legacy runtime state;
- rotate exposed provider credentials;
- fix or disable restart-unsafe temporary-role behavior;
- begin module health/loading foundation;
- retain Join-to-Create.

No V2 Dashboard auth is built here.

---

## Phase 1 — Platform Core

First task:

```text
move FastAPI onto the bot's event loop
```

Then:
- Docker Compose development;
- PostgreSQL;
- Alembic;
- Next.js authenticated proxy;
- dashboard_sessions;
- short-lived internal identity token;
- FastAPI authorization;
- explicit Dashboard grants;
- capability RBAC;
- ROOT_OWNER_ID separation;
- append-only audit;
- persistent scheduler foundation;
- typed V2 Discord references;
- small storage interface;
- off-host backups;
- bot permission/hierarchy health;
- module health improvements.

---

## Phase 2 — Early Protection

- native Discord structure snapshot capture;
- ban list;
- member-role mapping;
- checksums;
- known-good/suspect snapshot state;
- encrypted raw legacy configuration archive;
- semantic adapters for Production-Lite modules;
- CLS Ops;
- critical operational alerts.

---

## Phase 2S — Recovery Feasibility Spike

Read-only/speculative recovery planning stops here until official documentation and test evidence exist.

Decision gate covers:
- guilds.join;
- refresh behavior;
- rotation;
- revocation;
- long-term token behavior;
- rate limits;
- failed joins;
- bans;
- roles;
- batching;
- policy requirements.

---

## Phase 3 — Verification V2 Rewrite

- Unverified-role gating model;
- configured protected areas only;
- Verification OFF/ON;
- Recovery Authorization DISABLED/OPTIONAL/REQUIRED;
- Grace Period;
- Grandfather;
- Require Now;
- manual staff fallback;
- truthful metrics;
- recovery integration only if Phase 2S passes.

---

## Phase 3.25 — Production Stabilization

Before Production-Lite:
- J2C production fix list;
- legacy ticket minimum fix list;
- module health;
- permission/hierarchy health;
- clean legacy state;
- critical command policy;
- snapshot and backup validation.

---

## Phase 3.5 — CLS Production-Lite

Deploy the core system to the actual CLS server after all readiness gates pass.

The system may begin replacing the currently disabled third-party bots.

---

## Phase 4 — Tickets V2.0

Implement the focused flagship ticket release and perform the ticket cutover.

---

## Phase 5 — Logging V2

- persistent event history;
- message content store;
- reliable attribution model;
- search;
- Discord routing;
- retention;
- Dashboard history.

---

## Phase 6 — Disaster Recovery Restore V1

Fresh empty replacement guild only.

- restore wizard;
- ID map;
- run journal;
- resume;
- structure restore;
- config adapters;
- ban restoration;
- optional member recovery;
- safe member roles;
- privileged-role manual approval;
- real restore drill.

Production-ready disaster-recovery claim is allowed only after a real successful drill.

---

## Phase 7 — Security Center

- Bot Trap;
- phishing protection;
- trusted IDs;
- Antinuke improvements;
- incident history;
- Dashboard Lock.

---

## Phase 8 — Simplified Command Manager

- module registry;
- runtime gating;
- risk levels;
- per-module defaults;
- HIGH/CRITICAL overrides;
- Incident Mode;
- help integration.

Do not implement dynamic slash resync per Dashboard toggle.

---

## Phase 9 — Invites + Giveaways

- fresh V2 invite event history;
- truthful attribution;
- valid invite rules;
- giveaway builder;
- eligibility revalidation;
- persistent scheduling.

---

## Phase 10 — Welcome + Engagement

- Welcome V2;
- consolidate legacy join behavior;
- practical engagement improvements;
- J2C polish if necessary.

---

## Phase 11 — Legacy Cleanup + V2.1

- Tickets V2.1;
- command cleanup;
- remove dead help stubs;
- remove unprofessional aliases;
- legacy branding cleanup;
- obsolete source removal where justified;
- advanced analytics;
- deferred UX polish.


# 60. Testing Strategy

Each major implementation phase uses:

```text
Static checks
→ targeted unit tests
→ local runtime
→ isolated Discord test server
→ acceptance checklist
```

Security-sensitive work additionally tests:
- unauthorized user;
- revoked Dashboard grant;
- revoked session;
- cross-guild access;
- malformed IDs;
- wrong role hierarchy;
- missing permissions;
- race conditions where relevant;
- bot restart;
- database restart;
- partial Discord API failure.


# 61. CI Priorities

At minimum, CI should eventually include:
- Python syntax/import checks;
- linting;
- frontend type/build checks;
- authorization matrix tests;
- route authorization coverage test;
- dangerous command risk-classification coverage;
- migration tests;
- `git diff --check`;
- secret scanning;
- dependency lock validation.

The authorization matrix is one of the highest-value automated tests in the project.


# 62. Deferred Features

The following are intentionally deferred unless a real need appears:
- full Emergency Safe Mode;
- dynamic slash resync;
- per-field Dashboard RBAC;
- advanced ticket auto-priority;
- multi-assignment;
- multiple active departments UI;
- advanced staff analytics;
- custom retention per ticket category;
- multiple invite-aware Welcome profiles;
- S3 implementation;
- complex phishing rules engine;
- hash-chain audit;
- in-place partial Discord restore;
- large-scale SaaS infrastructure;
- Redis;
- Kubernetes.


# 63. Items Requiring Official Documentation / Test Verification

These are not assumptions to silently implement.

## Recovery
- guilds.join exact requirements;
- token lifetime;
- refresh rotation;
- idle expiry;
- revocation behavior;
- rate limits;
- joining banned users;
- role assignment during join;
- Developer Policy / Terms.

## Verification
- interaction with Discord native Onboarding;
- Membership Screening;
- pending members;
- overwrite resolution behavior.

## Logging
- audit-log gateway event semantics;
- required permission/intent;
- message-delete audit behavior;
- aggregation;
- message-content retention policy requirements.

## Attachments
- Discord CDN signed URL behavior / expiry.

## Invites
- invite usage edge cases;
- vanity behavior;
- attribution limits.

## Commands
- hybrid-command global-check behavior in the pinned discord.py version;
- current Discord command registration limits;
- persistent component limits/custom_id constraints.

## Disaster Recovery
- current APIs for:
  - onboarding;
  - AutoMod rules;
  - forum tags;
  - welcome screen;
  - templates;
  - emojis/stickers;
  - role position behavior.


# 64. Final Owner Decisions

The following decisions are locked unless explicitly changed later.

## Existing members

Use a gradual migration.

New members are gated first.

Existing members use a Grace Period.

Do not instantly hide the server from the current ~400 members.

## Dashboard exposure

Production Dashboard will be publicly reachable over HTTPS through Next.js only.

FastAPI remains internal.

## Legacy invite data

V2 invite eligibility starts fresh.

Legacy invite counts are not trusted for Giveaways.

## Recovery mode

Recovery Authorization supports:

```text
DISABLED
OPTIONAL
REQUIRED
```

The preferred CLS target is REQUIRED only if feasibility and policy checks pass.

## Dashboard access

Explicit grants are required.

Discord Administrator alone is insufficient.

## Join-to-Create

Required production feature.

## Main server timing

The main CLS server currently has low activity, so quality/readiness gates take priority over rushing deployment.

A short maintenance period is acceptable when Production-Lite is ready.


# 65. Implementation Discipline

Before each phase:

1. read this specification;
2. inspect only the source relevant to that phase;
3. create a scoped implementation plan;
4. identify exact files;
5. define acceptance criteria;
6. implement;
7. run targeted validation;
8. review the diff;
9. test on isolated server if applicable;
10. commit only after approval.

Avoid broad "refactor the project" prompts.

Do not edit unrelated modules.

Do not rewrite working systems without evidence.

Do not use `git add .` while runtime databases remain tracked or dirty.


# 66. Definition of Success

CLS Discord V2 is successful when:
- the Dashboard is securely authorized;
- critical secrets are not client-exposed;
- Root Owner is protected;
- required bot modules load reliably;
- the real server is protected by backups and snapshots;
- Verification does not expose private channels;
- J2C survives restart and works reliably;
- Tickets survive restart and later migrate cleanly to V2;
- Dashboard and Discord share domain logic;
- critical commands cannot run casually;
- logs and audits are trustworthy about uncertainty;
- Recovery is used only after being proven feasible;
- disaster restore has been tested on a disposable server;
- production does not depend on paid third-party bots the owner does not want;
- the codebase remains understandable enough to evolve later.


# 67. Next Execution Step

The next implementation phase is:

```text
PHASE 0 — SECURITY FOUNDATION + SCOPE CONTROL
```

No Phase 1 implementation should begin until Phase 0 acceptance criteria pass and the Phase 0 diff is reviewed.
