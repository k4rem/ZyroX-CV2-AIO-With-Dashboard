# CLS OS — Phase 2A Early Protection Architecture

**Status:** ACCEPTED (owner review 2026-10-01, revisions incorporated)\
**Baseline:** `phase-2-early-protection` @ `510641e` (Phase 1.6 closed)\
**Authority:** `docs/CLS_DISCORD_V2_SPEC.md` v1.1 (§0.1 amendment, §40, §59). Owner decisions: `docs/PHASE_2_OWNER_DECISIONS.md`. Delivery sequence: `docs/CLS_OS_PHASE_2_IMPLEMENTATION_PLAN.md`.\
**Runtime implementation:** NOT STARTED.

All numeric values marked **PROPOSED** are development defaults. Production values are chosen after OBSERVE evidence review (OD-13).

---

## 1. Scope

Phase 2A delivers:
- Human Antinuke;
- the Bot Protection foundation;
- actor attribution;
- incidents and evidence;
- reversible quarantine;
- CLS Ops security alerts.

Not in Phase 2A:
- Structure snapshots, ban and member-role maps, checksums, KNOWN_GOOD/SUSPECT state, and the encrypted legacy config archive. These are Phase 2B.
- Recovery. This is Phase 2S.
- Bot Trap, phishing, Dashboard Lock, and the full Security Center. These are Phase 7.
- Incident Mode. This is Phase 8.
- In-place restore or recreation of deleted objects (spec §30, §62).

## 2. Core principle: separated stages

```text
OBSERVED EVENT → ATTRIBUTED ACTION → SUSPICIOUS ACTOR → CONFIRMED POLICY VIOLATION → RESPONSE ACTION
```

| Stage | Record | Table |
|---|---|---|
| Observed event | Gateway signal (temporary) or audit-backed observation (durable) | `security_gateway_signals`, `security_observations` |
| Attributed action | Attribution state on the observation | `security_observations` |
| Suspicious actor | Rule match recorded as a policy decision | `security_incident_events` |
| Confirmed policy violation | Incident with rule, explanation, trust snapshot | `security_incidents` |
| Response action | Ledger row plus containment outcome | `security_response_actions`, `security_quarantines` |

Every stage persists before the next stage runs.

Hard rules:
- Unknown or ambiguous attribution never automatically punishes a human.
- Uncertainty never escalates a response.
- No path falls back from a failed quarantine to a kick or ban.

## 3. Runtime topology

- Bot and FastAPI share one event loop and one process (spec §4). Single-process operation is an explicit assumption. Database constraints remain the final guard.
- **Primary signal:** `on_audit_log_entry_create`.
  - Requires the moderation intent and `view_audit_log`.
  - Exact semantics are verification item V-1 (§23).
- **Secondary signal:** gateway events. They corroborate, and they detect actions whose audit entry is missing.
- **Fallback:** bounded `guild.audit_logs(...)` fetches, used only for pending gateway signals.
- **Durable work:** `scheduler_jobs`, hardened in step 2A.1 with leases, stuck-job reclaim, and exponential backoff.
- **Configuration authority:** FastAPI only. The legacy Discord configuration commands for antinuke, whitelist, and extra owner are retired in step 2A.5.

## 4. Threat model

| Case | Description | Detection | Containment | Hard limits |
|---|---|---|---|---|
| A. Compromised staff account | Legitimate permissions used destructively | Rate, aggregate, and sequence rules over CONFIRMED, non-late audit entries | Quarantine in ENFORCE | Guild owner and Root are never contained. Hierarchy may make a member uncontainable. Member-specific overwrites survive quarantine. |
| B. Malicious or compromised bot | Untrusted bot added, or a bot turns hostile | `bot.add`, bot privilege changes, bot-actor actions | Only after a subsequent CONFIRMED destructive or security behaviour (§10) | Managed roles cannot be removed |
| C. Malicious inviter | Human adds a hostile bot | Linked to the bot incident as a related actor | **Never** punished for the add itself (OD-11). Ordinary human rules still apply to the inviter's other actions. | CLS cannot tell whether the inviter's account was compromised |
| D. Legitimate admin work | Cleanup, restructuring, raid response | Same rules as A | OBSERVE by default. Trust suppresses containment. Root-only Maintenance Window. | Threshold tuning happens after OBSERVE review |
| E. CLS failure modes | Delayed or missing audit entries, 429, outage, reconnect, duplicates, restart, partial DB failure, missing permissions, hierarchy loss, incomplete remediation | Covered in §6, §7, §14, §19 | Fails toward record and alert | — |
| F. CLS impairment | Attacker reduces CLS's role permissions, moves its role down, or removes it | `cls.impairment` class | Feeds sequence rules. Critical alert. | CLS may lose the ability to act at all |

## 5. Permission tiers

The tiers replace the flat legacy dangerous-permission set. Rules refer to tiers, not individual bits.

| Tier | Permissions | Use |
|---|---|---|
| `CRITICAL_CONTROL` | Administrator, Manage Guild, Manage Roles, Manage Channels | Escalation to this tier is the highest-severity signal |
| `DESTRUCTIVE` | Ban Members, Kick Members, Manage Webhooks | Escalation is high severity |
| `ELEVATED` | Moderate Members, Mention Everyone, Manage Threads, Manage Events, Manage Expressions | Medium severity. Feeds alerts and sequences only. |
| `OBSERVABILITY` | View Audit Log | Required for protection health. **Never** an escalation containment trigger by itself. Record only. |

- The tier of a permission diff is the highest tier among the bits **added**. Removing bits is never escalation.
- The residual-privilege check after quarantine (§12) uses tiers too. Residual `CRITICAL_CONTROL` or `DESTRUCTIVE` makes the result PARTIAL. Residual `ELEVATED` is recorded as a warning.
- The tier map lives in one module and is versioned. Each incident records `tier_map_version`.

## 6. Protected action taxonomy

| Class | Source | Severity | Phase 2A status |
|---|---|---|---|
| `channel.delete` | CHANNEL_DELETE | H | Required |
| `role.delete` | ROLE_DELETE | H | Required |
| `member.ban` | MEMBER_BAN_ADD | H | Required |
| `member.kick` | MEMBER_KICK. Audit only, because the gateway cannot tell a kick from a leave. | H | Required |
| `member.prune` | MEMBER_PRUNE | C | Required. A single prune is a **critical alert only** (OD-4). |
| `role.permission_escalation` | ROLE_UPDATE that adds bits; ROLE_CREATE carrying tiered bits | By tier. C for CRITICAL_CONTROL on @everyone. | Required |
| `member.privileged_role_grant` | MEMBER_ROLE_UPDATE adding a role that carries tiered bits | By tier | Required |
| `bot.add` | BOT_ADD | M. H if the bot has DESTRUCTIVE bits, C if CRITICAL_CONTROL. | Required (record and alert) |
| `bot.privilege_change` | The bot's managed role gains tiered bits, or a tiered role is granted to the bot | By tier | Required |
| `webhook.create` | WEBHOOK_CREATE | M | Required |
| `cls.impairment` | CLS's role loses bits or position, or CLS is targeted by a kick or ban | C | Required |
| `channel.overwrite_escalation` | CHANNEL_OVERWRITE_CREATE/UPDATE granting tiered bits | By tier, capped at H | Optional. Never a single-action trigger. |
| `channel.create` (burst) | CHANNEL_CREATE | M | Optional |
| `webhook.delete` / `webhook.update` | WEBHOOK_* | M | Optional |
| `guild.update` (vanity, verification, MFA, widget, system channel) | GUILD_UPDATE | M/H | Optional |
| `integration.create` | INTEGRATION_CREATE | M | Optional (overlaps `bot.add`) |
| AutoMod rule changes, unban, emoji/sticker, invites, events, threads | various | L/M | Later |
| Mention spam, message delete, voice move/disconnect | messages / aggregated audit | — | Out of scope. Automod, Phase 5, Phase 7. |

**Managed-role exclusion (false-positive guard).** These are never `role.permission_escalation` by a human:
- Discord-created managed roles (bot integration roles, booster roles).
- Role creates that belong to a `bot.add` correlation.

Managed bot roles are folded into the related `bot.add` or `bot.privilege_change` observation. Exact behaviour is verification item V-4.

## 7. Observation, idempotency and correlation

### 7.1 Durable idempotency authority

The **Discord audit entry ID is the only durable idempotency key.**

- `security_observations` has a partial `UNIQUE (guild_id, audit_entry_id) WHERE audit_entry_id IS NOT NULL`.
- Inserts use `ON CONFLICT DO NOTHING`. A repeated push, a repeated fetch, or a reconciliation overlap can never create a second observation.
- Each audit entry produces at most one durable observation, and each observation has at most one audit entry.
- **Policy counts use confirmed, distinct audit entry IDs only.** Distinct targets are used where a rule says so. Gateway events never count.

### 7.2 Gateway signals are temporary

Gateway events become rows in `security_gateway_signals`.

- **There is no retention-long uniqueness key.** The same legitimate change can happen again later and must not be suppressed.
- `correlation_key = (guild_id, action_class, target_id, change_digest)`. This is an ordinary indexed column, not unique.
- **Short dedupe window G** (PROPOSED 10 s, configurable, hard maximum 120 s):
  - A second signal with the same `correlation_key` inside G while the first is still `PENDING` is merged into it. `duplicate_count` goes up, and `last_seen_at` is updated.
  - Outside G, it is a new signal.
- **A gateway signal can never block, merge, or suppress an audit-backed observation.** A merge that is wrong inside G costs at most one corroboration link. It can never lose a counted action, because counting happens on audit entry IDs.
- Merging is performed under a per-guild `asyncio.Lock`. It is noise reduction, not a safety property.

### 7.3 Gateway signal states

| State | Meaning |
|---|---|
| `PENDING` | Waiting for an audit entry (up to T_attr) |
| `LINKED` | Matched to exactly one audit-backed observation |
| `SUPERSEDED` | Duplicate of, or redundant with, a signal already linked to an audit entry for the same class and target within the correlation window |
| `EXPIRED_UNATTRIBUTED` | No audit entry for that class and target by T_attr. Converted into a durable UNATTRIBUTED observation (source `gateway`, no audit ID). |

### 7.4 When an audit entry arrives

1. Insert the audit-backed observation (`ON CONFLICT DO NOTHING`). If it already exists, stop.
2. Select `PENDING` signals with the same guild, action class, and target, with `first_seen_at` inside `[entry_time − skew, entry_time + T_attr]`.
3. Link the **earliest** of them: it becomes `LINKED`, and the observation is set to `corroborated = true`.
4. Mark the others for the same class and target `SUPERSEDED`, but **only if** their `correlation_key` equals the linked signal's (duplicate deliveries). Signals with a different change digest stay `PENDING` and wait for their own audit entries.
5. If an `EXPIRED_UNATTRIBUTED` observation exists for the same class and target inside the window, set its `superseded_by_observation_id` to the new observation. The audit-backed observation becomes authoritative. Because it is late, it is alert and evidence only (§8.3).

### 7.5 Fallback fetch

- **Wait:** T_push, PROPOSED 2 s.
- **Retries:** at most 3 fetches, at +2 s, +5 s, and +12 s.
- **Query:** `audit_logs(action=X, limit ≤ 25, after=snowflake(signal_time − skew))`.
- **Coalescing:** one fetch per `(guild, action_type)` serves every pending signal of that type.
- **Rate limit:** per-guild token bucket (PROPOSED 1/s, burst 3). Honour `retry_after`.
- **403:** the signal becomes UNATTRIBUTED, and one permission-health alert is sent per guild per hour.
- **Deadline:** T_attr, PROPOSED 30 s. Fetched entries go through §7.4.

### 7.6 Watermark and reconciliation

- `security_guild_state.last_audit_entry_id` advances monotonically.
- After a **new session** (not a RESUME), fetch from the watermark, bounded by time. Entries found this way are processed as **late** (§8.3).

### 7.7 Retention

- Gateway signals: purged after 24 h (PROPOSED). A linked signal's minimal corroboration data is copied into its observation first.
- Observations: see §15.

## 8. Actor attribution

### 8.1 States

| State | Definition | Allowed outcomes |
|---|---|---|
| `CONFIRMED` | Audit entry with exact action type and exact target ID, an actor ID, entry time within bounds, and not consumed by another observation | Full policy. Containment only if also **not late**. |
| `PROBABLE` | Fallback path only. Exactly one candidate matching action type and time window, where Discord gives no comparable target (prune, guild update). | Record and alert. **Never contains** (OD-5). |
| `AMBIGUOUS` | Two or more candidates with different actors | Record and alert, listing the candidates. Never contains. |
| `UNATTRIBUTED` | No entry by T_attr, audit access missing, or the entry has no user | Record. Alert if severity is H or C. Nothing is directed at any human. |
| `SELF` | Actor is CLS, and the entry matches a `security_response_actions` ledger row (§13) | Suppressed. Linked as response evidence. |
| `CLS_PROXIED` | Actor is CLS, with no security ledger match (another CLS module did it) | Record. Link the internal initiator when internal audit data shows one. Alert on destructive rate. Never contains CLS. |

### 8.2 Bounds

- Entry time must be inside `[signal_time − 15 s, signal_time + T_attr]` (PROPOSED).
- Older entries are rejected as stale.
- "Newest entry wins" is never used.

### 8.3 Late attribution

- An entry is **late** when `received_at − entry_created_at > T_late` (PROPOSED 30 s).
  - `received_at` is when the push arrived or the fetch returned. It is not processing time, so a processing backlog during a mass nuke does not make fresh evidence late.
  - Entries found by reconciliation are always late.
- Late entries are **alert and evidence only. They never lead to automatic containment** (OD-15).
- They count toward alert rules but are **excluded from containment-eligible counts**. A containment decision must be fully satisfied by CONFIRMED, non-late entries.

## 9. Trust model

`security_trusted_actors` is guild-scoped and covers humans and bots. Each entry has a scope list of action classes, an optional `expires_at`, and is revoked by soft delete.

| Topic | Rule |
|---|---|
| Who may edit | **Root only** (spec §39). Enforced by capability `security.trust.manage`, which is in `ROOT_ONLY`. |
| Effect | **Containment suppression only.** Trusted actors are still observed and recorded, and they count. Threshold violations by a trusted actor **alert** (OD-8). |
| Guild owner | Not a trust entry. Never contained. H and C actions alert and record (OD-7). |
| Root Discord identity | Never automatically contained. H and C actions always alert and record (OD-6). |
| OWNER_IDS | Not trusted by default. May be added explicitly. |
| CLS | Handled by the ledger (§13), not by trust. |
| When it applies | Read at decision time and recorded as `trust_snapshot`. **Re-checked right before every Discord mutation** (TOCTOU guard). An actor who becomes trusted in between causes the action to be skipped with outcome `SKIPPED_TRUSTED`. |
| Revocation | Future evaluations only. Not retroactive. |
| Validation | Snowflakes validated. Invalid IDs rejected with 422. Kind (human or bot) checked against Discord when it can be resolved. |
| Audit | `record_audit()` with before and after values, mirrored to CLS Ops. |
| Legacy data | **Not imported** (OD-12). V2 trust starts empty. Legacy `whitelisted_users` and `extraowners` are archived read-only. |

## 10. Engines

### 10.1 Human Antinuke

- **Subject:** a non-bot account that is the CONFIRMED actor.
- **Engine:** a pure function `evaluate(subject, observations, config, trust_snapshot, now) → Decision`. It is deterministic and has no Discord I/O.
- **Decision fields:** `rule_id`, `explanation`, `matched_observation_ids`, `severity`, `containment_eligible`, `effective_mode`.
- `bot.add` observations never count toward human containment rules (OD-11).

### 10.2 Bot Protection

The subject is a bot account.

| Trigger | Outcome |
|---|---|
| Untrusted `bot.add` | **Record and alert only.** Severity rises with the bot's permission tier. |
| Trusted `bot.add` | Record only (informational timeline entry, no alert) |
| `bot.privilege_change` alone | Record and alert by tier |
| Bot is the CONFIRMED, non-late actor of a rule match: a bot rate rule, a bot sequence such as "added, then gains CRITICAL_CONTROL, then destructive", or `cls.impairment` | **Bot containment** in ENFORCE |
| Inviter | Linked as `related_actor`. Never contained because of the add (OD-11). |

**Bot containment** follows the same outcome model as quarantine (§12):

1. Remove the bot's removable non-managed roles.
2. If the bot's managed role is below CLS, strip its CRITICAL_CONTROL and DESTRUCTIVE bits, recording the prior bits so they can be restored. This is verification item V-5.
3. **Never kick or ban automatically.**

Release of a bot containment (Root only) restores the recorded roles and the managed-role bits, subject to the same drift guard as §12.5.

## 11. Suspicious-actor policy

Every rule is explainable and comes from configuration (`security_action_policies`). All values are **PROPOSED**.

| Type | Rule | PROPOSED value | Containment-eligible |
|---|---|---|---|
| Rate | Distinct `channel.delete` | 3 in 60 s | Yes |
| Rate | Distinct `role.delete` | 3 in 60 s | Yes |
| Rate | `member.ban` + `member.kick` | 5 in 60 s | Yes |
| Rate | `webhook.create` | 5 in 60 s | Yes |
| Aggregate | Destructive classes combined | 6 in 120 s | Yes |
| Single (OD-4) | CONFIRMED `CRITICAL_CONTROL` bits added to **@everyone** (role ID equals guild ID) | 1 | **Yes.** This is the only single-action containment trigger. |
| Single | Administrator or CRITICAL_CONTROL granted to a non-@everyone role or a member | 1 | No. C alert, and it feeds sequences. |
| Single | `member.prune` | 1 | **No. Critical alert only.** |
| Single | Other isolated destructive action | 1 | No. Feeds rate and sequence rules. |
| Sequence | Actor gains CRITICAL_CONTROL or DESTRUCTIVE (self-escalation), then performs a destructive action | 120 s | Yes |
| Sequence | `cls.impairment`, then a destructive action, by the same actor | 300 s | Yes |
| Tier `ELEVATED` | Escalation | — | No. Alert or digest. |
| Tier `OBSERVABILITY` | Escalation | — | No. Record only. |

- Counts use distinct audit entry IDs, and distinct targets where the rule says so.
- In OBSERVE, an eligible decision is stored as `would_contain`. This is the evidence base for production thresholds.
- The explanation text is generated from the rule parameters and the matched IDs.

## 12. Quarantine semantics

### 12.1 Definition (OD-3)

Quarantine removes **all removable non-managed roles** and records the exact prior roles for safe restoration.

- **Timeout is not part of the default.**
- An optional quarantine role is applied **only if configured**. CLS never creates one.

### 12.2 Pre-flight classification (no mutation yet)

| Check | Outcome |
|---|---|
| Subject is guild owner, Root Discord ID, or trusted for the class | `NOT_ATTEMPTED_POLICY` (record and alert) |
| CLS lacks Manage Roles | `FAILED_PERMISSION`. No call is made. |
| Subject's highest role position ≥ CLS's highest role position | **`UNCONTAINABLE_HIERARCHY`**. No member mutation is attempted. Durable evidence, critical alert, **no stronger fallback**. |
| Otherwise | Member is editable. Proceed. |

The exact Discord hierarchy semantics are verification item **V-2**: equal positions, ties, and whether any member edit or only role edits are forbidden. Until V-2 passes, CLS treats equal positions as uncontainable.

### 12.3 Apply

1. Lock on `(guild_id, user_id)`.
2. Check the partial unique index for an active quarantine. If one exists, attach to it.
3. Insert `security_quarantines(status=APPLYING)` with `prior_role_ids`, `prior_role_perms`, positions, and a ledger row.
4. Make a single `member.edit(roles=managed_roles_kept)` call with reason `CLS-SEC {action_id}`.
5. Add the optional configured quarantine role.
6. Re-read the member and compute residual privilege: managed roles (such as a booster role) or member-specific channel overwrites still carrying CRITICAL_CONTROL or DESTRUCTIVE bits.

### 12.4 Outcomes

These are never collapsed into a generic failure.

| Outcome | Meaning |
|---|---|
| `ACTIVE` | All removable roles removed, configured quarantine role applied, no residual CRITICAL_CONTROL or DESTRUCTIVE |
| `PARTIAL_QUARANTINE` | Member was editable, but a sub-operation failed (for example the quarantine role add) or residual tiered privilege remains |
| `UNCONTAINABLE_HIERARCHY` | Pre-flight hierarchy failure. No mutation attempted. |
| `FAILED_PERMISSION` | CLS lacks the permission, or Discord returned 403 and re-running pre-flight shows a permission gap |
| `FAILED_DISCORD` | 5xx, network error, or 429 retries exhausted, with the member re-read showing no change |
| `NOT_ATTEMPTED_POLICY` | Owner, Root, or trusted subject |
| `SKIPPED_TRUSTED` | Trust re-check right before mutation |
| `SKIPPED_MODE` | Mode re-check right before mutation found no ENFORCE (Maintenance Window, failed precondition, mode change) |
| `RELEASED` | All recorded roles restored |
| `RELEASE_PARTIAL` | Some roles restored. Others are gone, held by the drift guard, or failed. |
| `RELEASE_FAILED` | Nothing restored |

**403 classification.** Discord returns Missing Permissions for both hierarchy and permission gaps. On a 403, CLS re-runs pre-flight:
- hierarchy now insufficient → `UNCONTAINABLE_HIERARCHY`;
- otherwise → `FAILED_PERMISSION`.

**After an ambiguous failure,** CLS re-reads the member before choosing an outcome. A change that actually landed becomes `ACTIVE` or `PARTIAL_QUARANTINE`.

### 12.5 Release

- **Root only** (OD-9). The subject can never release themselves.
- Restores only `removed_role_ids` that still exist and are still below CLS.
- **Drift guard:** a role whose permission bits changed since quarantine, or that now carries CRITICAL_CONTROL or DESTRUCTIVE, is held back and needs explicit Root confirmation.
- Removes the quarantine role only if CLS added it.
- Release never depends on Discord roles. Dashboard access is grant-based, so Root can always release.

### 12.6 Retry and expiry

- Every step is a set difference against live member state, so re-running is safe.
- Quarantine never expires automatically.

## 13. Self-action suppression

1. Every CLS security mutation first commits a `security_response_actions` row.
2. It then calls Discord with the reason `CLS-SEC {action_id}`.
3. An audit entry where actor = CLS that matches a ledger row by token, or by type and target inside the window, is `SELF`.
4. Actor = CLS with no match is `CLS_PROXIED` (§8.1). Other bots are never suppressed implicitly.

## 14. Response matrix

| Attribution | Late | Subject | Mode | Rule | Response |
|---|---|---|---|---|---|
| CONFIRMED | No | Untrusted human | ENFORCE | Containment-eligible rule met | Quarantine, incident, Ops alert |
| CONFIRMED | No | Untrusted human | OBSERVE or Maintenance Window | Containment-eligible rule met | Incident (`would_contain`) and alert |
| CONFIRMED | No | Trusted | Any | Threshold met | Incident and alert. No containment. |
| CONFIRMED | Any | Owner or Root | Any | H/C | Incident and alert (`NOT_ATTEMPTED_POLICY`) |
| CONFIRMED | No | Hierarchy ≥ CLS | ENFORCE | Rule met | `UNCONTAINABLE_HIERARCHY` and critical alert |
| CONFIRMED | Yes | Any | Any | Rule met | Alert and evidence only |
| CONFIRMED | No | Untrusted bot | ENFORCE | Bot rule met (§10.2) | Bot containment and alert |
| CONFIRMED | — | Untrusted bot | Any | `bot.add` only | Alert, severity by tier |
| PROBABLE / AMBIGUOUS | — | — | Any | H/C | Alert |
| UNATTRIBUTED | — | — | Any | H/C | Alert. M/L goes to the digest. |
| SELF | — | — | — | — | Suppressed |
| CLS_PROXIED | — | — | Any | Destructive rate | Alert with internal initiator if known |
| CONFIRMED | No | Human | ENFORCE | `member.prune` single | **Critical alert only** |

## 15. Modes, ENFORCE preconditions, Maintenance Window

### 15.1 Modes

Each subsystem (human, bot) has a mode: `OFF`, `OBSERVE`, or `ENFORCE`.

- New guilds default to `OBSERVE`.
- **Production ENFORCE is never enabled automatically** (OD-2).
- Effective mode is `min(configured_mode, preconditions, maintenance_window)`.

- It is evaluated at decision time **and re-checked immediately before every Discord mutation**, alongside the trust re-check.
  - If the re-check finds that the mode is no longer ENFORCE (a window started, a precondition failed, or the mode was switched), the action is skipped with outcome `SKIPPED_MODE`.
- **A decision made under OBSERVE (`would_contain`) is never executed later.** Switching to ENFORCE or a window expiring does not replay past decisions. Only new qualifying activity can lead to containment.

### 15.2 Switching to ENFORCE

Root only, through capability `security.enforce.manage` (OD-10). `security.config` may configure policy but cannot enable ENFORCE.

Every precondition below must hold, both when switching and **continuously at decision time**. If any fails, effective mode drops to OBSERVE, a health alert fires, and the dashboard shows a banner.

1. A valid CLS Ops security-alert destination: the channel exists, it belongs to `OPS_GUILD_ID`, and CLS can send to it (OD-14).
2. Legacy antinuke listeners are unloaded.
3. `ROOT_OWNER_ID` is configured, so release is possible.
4. Permission health is OK for Manage Roles and View Audit Log.
5. The Phase 2A verification checklist (§23) is recorded as passed.

### 15.3 Maintenance Window (OD-17)

**It is not Incident Mode and must never be named or modelled as Incident Mode** (spec §46).

| Property | Rule |
|---|---|
| Who | Root only (`security.maintenance.manage`). A reason is required. |
| Duration | Time-boxed. Maximum 60 minutes (cap in config, initial value 60). |
| Effect | Effective mode ENFORCE becomes OBSERVE for that guild |
| Never | Disables observation, attribution, incidents, or alerts. Alerts are tagged "maintenance window active". |
| Expiry | Automatic. `expires_at` is checked at every decision (the scheduler job only records the expiry event). Root may end it early. |
| Stacking | One active window per guild. Extending creates a new audited window. |
| Persistence | `security_maintenance_windows`. Survives restart. |
| Audit | `record_audit()` on start, end, and expiry. Mirrored to CLS Ops. |

## 16. Incident lifecycle

- **Correlation key:** `(guild_id, subject_id, engine)`.
- **Attach** to an active incident only if both hold:
  - `now − last_activity_at ≤ inactivity_window` (**15 min**, owner-approved initial value, configurable 5–60 min);
  - `now − opened_at ≤ max_incident_lifetime` (PROPOSED 6 h, configurable). This stops an actor who acts every 14 minutes from keeping one eternal bucket.
- **Otherwise** close the old incident (`closure = EXPIRED_INACTIVE` or `EXPIRED_LIFETIME`) and open a new one with `previous_incident_id` set.
- **Uniqueness:** a partial unique index allows one `ACTIVE` incident per `(guild_id, subject_id, engine)`. The close-then-open happens in one transaction with `SELECT … FOR UPDATE`.
- **Manual closure:** `RESOLVED` or `FALSE_POSITIVE` closes immediately (`security.incidents.manage`).
- **Incident vs quarantine:** quarantine has its own lifecycle. Closing an incident never releases a quarantine. New activity by a quarantined subject opens a new incident that references the active quarantine. There is no second quarantine.
- **Sweep:** a scheduler job closes expired incidents lazily (PROPOSED every 5 min). Correlation also re-checks the window at attach time, so a late sweep cannot cause wrong attachment.
- **Phase 2B hook:** any active incident with severity H or above in a guild marks snapshots taken during it SUSPECT (spec §26.2).

## 17. Incident evidence

Every incident answers these questions:

| Question | Source |
|---|---|
| What | Action classes and targets |
| When | Entry time, received time, attribution time |
| Where | Guild, plus channel or role context |
| Who | Subject and related actors |
| How attributed | State, method, corroboration, late flag |
| Why triggered | `rule_id`, generated explanation, `tier_map_version`, trust snapshot |
| Response | Each response action: attempt, outcome, Discord error |
| Closure | Who closed it, and why |

Evidence is kept minimal:
- IDs, names truncated to 100 characters, permission bit diffs;
- no message content, no tokens;
- payloads redacted with the existing `record_audit` key rules.

The timeline (`security_incident_events`) is append-only.

## 18. CLS Ops alerting

- **Destination:** `OPS_SECURITY_ALERT_CHANNEL_ID`, validated to belong to `OPS_GUILD_ID`. **No fallback** to product-guild channels or the legacy webhooks.
  - The destination lives in the Ops guild, so an attacker inside a product guild cannot delete it.
- **Delivery:** outbox, then scheduler job `security_alert_deliver`, keyed by `dedupe_key = alert:{incident_id}:{kind}:{seq}`. At least once.
- **Content:** incident ID, guild, subject, classes and counts, attribution state and late flag, rule explanation, response outcome, maintenance-window flag, dashboard link. `allowed_mentions = none`.
- **Noise control** (PROPOSED values):
  - one alert when an incident opens;
  - updates coalesced to at most 1 per 30 s per incident;
  - per-guild cap of 20 per 10 min, with the overflow sent as a digest.
- **Missing destination:** outbox status `UNDELIVERABLE_NO_DESTINATION`, health warning, dashboard banner, **ENFORCE refused** (§15.2).
- **Also delivered:**
  - protection-health alerts;
  - trust, config, mode, and Maintenance Window changes (spec §38 mirror);
  - `cls.impairment`.

## 19. Fail-open / fail-closed

Fail-closed means "no destructive response". It never means "punish anyway".

| Condition | Observation | Containment | Alert |
|---|---|---|---|
| Postgres down | Bounded memory buffer (PROPOSED 1,000 per guild), drops counted | **Blocked** (no ledger) | Best-effort direct send marked "unpersisted" |
| Ledger write fails | Retry | Blocked until the write commits | Yes |
| No View Audit Log | Gateway signals only | Blocked (CONFIRMED impossible) | Health |
| Audit push missing | Fallback fetch | Only on CONFIRMED and non-late | — |
| 429 during containment | `retry_after`, maximum 5 attempts | `FAILED_DISCORD` if exhausted | Yes |
| Hierarchy | — | `UNCONTAINABLE_HIERARCHY` | Critical |
| Ops destination invalid | — | Effective OBSERVE | Banner and health |
| Config missing or corrupt | — | Effective OBSERVE | Yes |
| Reconnect (new session) | Reconcile from watermark | Never (late) | Yes |
| Startup before health check | Observe | Blocked | — |
| Legacy listeners loaded | — | ENFORCE refused | Yes |
| Ops guild or non-allowlisted guild | Ignored | — | — |

## 20. Persistence (single Alembic revision in 2A.1)

All tables follow project conventions:
- snake plural names;
- UUID primary keys;
- BigInteger snowflakes;
- `timestamptz` defaulting to `now()`;
- JSONB;
- `guild_id NOT NULL` in every unique key.

| Table | Purpose / key constraints |
|---|---|
| `security_guild_configs` | `guild_id` PK. Fields: `human_mode`, `bot_mode`, `quarantine_role_id`, `incident_inactivity_s` (default 900), `incident_max_lifetime_s`, `gateway_dedupe_s`, `version` (optimistic concurrency). |
| `security_action_policies` | PK `(guild_id, action_class)`. Fields: `enabled`, `threshold`, `window_s`, `tier_floor`, `containment_eligible`. |
| `security_trusted_actors` | Partial unique `(guild_id, subject_id) WHERE revoked_at IS NULL` |
| `security_guild_state` | `guild_id` PK. Fields: `last_audit_entry_id`, `last_reconciled_at`, `trust_version`, `verification_passed_at`. |
| `security_gateway_signals` | Index on `(guild_id, correlation_key, first_seen_at)`. **No uniqueness.** Fields: `state`, `duplicate_count`, `linked_observation_id`. 24 h retention. |
| `security_observations` | Partial unique `(guild_id, audit_entry_id)`. Fields: `attribution_state`, `late`, `corroborated`, `superseded_by_observation_id`, `received_at`, `entry_created_at`. Index on `(guild_id, actor_id, entry_created_at)`. |
| `security_incidents` | Fields: `status` (ACTIVE/CLOSED), `closure` (EXPIRED_INACTIVE / EXPIRED_LIFETIME / RESOLVED / FALSE_POSITIVE), `engine`, `subject_id`, `severity`, `opened_at`, `last_activity_at`, `previous_incident_id`, `trust_snapshot`, `tier_map_version`. Partial unique `(guild_id, subject_id, engine) WHERE status = 'ACTIVE'`. |
| `security_incident_events` | Append-only timeline (REVOKE UPDATE/DELETE from the app role; purge by the maintenance role only) |
| `security_response_actions` | Unique `idempotency_key`. Fields: `outcome` (the §12.4 enum), `lease_until`, `discord_error`. |
| `security_quarantines` | Fields: `status` (the §12.4 enum), `prior_role_ids`, `prior_role_perms`, `removed_role_ids`, `residual`. Partial unique `(guild_id, user_id) WHERE status IN ('APPLYING', 'ACTIVE', 'PARTIAL_QUARANTINE')`. |
| `security_maintenance_windows` | Fields: `guild_id`, `started_by`, `reason`, `starts_at`, `expires_at`, `ended_at`. Partial unique: one active per guild. |
| `security_alert_outbox` | Unique `dedupe_key`. Fields: `status`, `attempts`, `next_attempt_at`. |

**Retention** (OD-14):

| Data | Retention |
|---|---|
| Unlinked observations | 30 days |
| Delivered alert outbox | 30 days |
| Incidents, timeline, response actions, quarantine history | 365 days |
| Gateway signals | 24 h (PROPOSED) |

Active quarantines are never purged. Configuration changes go to `audit_events` via `record_audit()`.

## 21. RBAC

| Action | Capability | Holder |
|---|---|---|
| View config, policies, trust list | `security.view` | Admin, Moderator |
| Edit policies, thresholds, incident windows | `security.config` | Admin. Cannot enable ENFORCE. |
| Enable or disable ENFORCE | `security.enforce.manage` | **Root only** |
| Trust list changes | `security.trust.manage` | **Root only** |
| Release quarantine | `security.quarantine.release` | **Root only** |
| Start or end a Maintenance Window | `security.maintenance.manage` | **Root only** |
| View incidents, evidence, quarantines | `security.incidents.view` | Admin, Moderator |
| Resolve or mark false positive | `security.incidents.manage` | Admin |

- The four Root-only capabilities join `ROOT_ONLY`.
- Every new route is classified (`test_route_coverage`).
- Legacy `/antinuke` routes are retired (410) in 2A.5. There is no SQLite write path.

## 22. Guild isolation, concurrency, restart

**Isolation**
- Every query filters on the authorized path `guild_id`.
- Every in-memory structure is keyed by guild first.
- An ID belonging to another guild returns 404.
- Ops-guild and non-allowlisted events are dropped before signal creation.
- A startup allowlist sweep is added (2A.1).

**Concurrency**
- Per-`(guild, subject)` evaluation lock and per-`(guild, target)` response lock.
- Unique indexes are the real guard.
- Config edits use optimistic concurrency (`version`, 409 on conflict).

**Restart**
- Everything that matters is in Postgres. No counters live in memory.
- Containment stays blocked until DB, config, and health checks pass.
- `PENDING` signals within T_attr resume. Older ones expire as UNATTRIBUTED.
- In-progress responses past their lease are re-run idempotently.
- Reconciliation entries are late, so never contained.
- The outbox resumes.

## 23. Discord verification items (test guild only, before any rule relies on them)

| ID | Item |
|---|---|
| V-1 | `on_audit_log_entry_create` delivery per protected class: required intent and permission; actor and target presence; latency; aggregation behaviour |
| V-2 | Hierarchy semantics: equal positions; whether member edit is entirely forbidden or only role edits; the exact error code |
| V-3 | Kick vs leave distinction; prune entry contents |
| V-4 | Bot add: managed role creation, whether ROLE_CREATE is emitted, and with which actor; booster role behaviour |
| V-5 | Whether a managed bot role's permissions are editable by CLS |
| V-6 | Audit `reason` propagation for SELF matching |
| V-7 | RESUME replay vs new-session behaviour for gateway events |
| V-8 | Member-specific overwrite precedence over role denies (residual privilege) |

Results are recorded in `docs/PHASE_2A_DISCORD_VERIFICATION.md` during 2A.2. ENFORCE precondition 5 depends on it.

## 24. Dashboard scope (real data only)

- **Protection settings:** mode per subsystem with effective-mode reason; policy table; incident windows; permission health; legacy status; Ops destination status.
- **Trusted actors:** list. Editing only for Root.
- **Incidents:** list and detail, covering the §17 fields and timeline.
- **Quarantines:** roster with the outcome enum, role breakdown, and residual privilege. Release is Root only, with drift-guard confirmation.
- **Maintenance Window:** state and countdown. Start and end are Root only.
- **Overview attention items:** active incidents; ACTIVE or PARTIAL quarantines; uncontainable incidents; "Ops alerts not configured"; "Audit permission missing"; Maintenance Window active.
- **Not included:** charts, live feed, or posture rings (Phase 7).

## 25. Phase boundaries

| Phase | What Phase 2A does or does not do |
|---|---|
| 2B | Snapshots use 2A's active-incident state for SUSPECT marking and 2A's Ops outbox for snapshot-failure alerts |
| 2S | Nothing |
| 3 | The quarantine role stays configuration-only |
| 4 | Nothing |
| 5 | Logging V2 may subscribe to the 2A audit feed. General logging stays in Phase 5. |
| 6 | No restore and no recreation of deleted objects |
| 7 | Bot Trap, phishing, Dashboard Lock, webhook message handling, full Security Center UI |
| 8 | Incident Mode, which is distinct from the Maintenance Window |

## 26. Security self-review (post-revision)

| Severity | Finding | Resolution |
|---|---|---|
| HIGH, fixed | A permanent gateway fingerprint would suppress a legitimate repeated change | Audit entry ID is the only durable key. Gateway dedupe is bounded to G (≤ 120 s) and can never suppress audit-backed observations (§7). |
| HIGH, fixed | A wrong merge of near-simultaneous distinct changes | Merging requires an identical change digest. Signals with different digests stay PENDING. Counting is on audit entry IDs anyway. |
| HIGH, fixed | A stale incident absorbing unrelated future activity | 15-min inactivity window plus max lifetime; close-then-open in a transaction (§16) |
| HIGH, fixed | Treating hierarchy ≥ CLS as partial would attempt forbidden mutations | `UNCONTAINABLE_HIERARCHY` pre-flight, no attempt. 403 re-classification. V-2. (§12) |
| HIGH, fixed | Bot-add managed role counted as human escalation by the inviter | Managed-role exclusion and V-4 (§6) |
| HIGH, fixed | Late evidence counted toward containment | Late entries excluded from containment-eligible counts. Lateness is measured at receipt, so backlog cannot hide fresh evidence (§8.3). |
| HIGH, fixed | ENFORCE remaining active after the Ops destination breaks | Preconditions are checked continuously, and effective mode degrades to OBSERVE (§15.2) |
| HIGH, fixed | Release impossible if Root is not configured | `ROOT_OWNER_ID` is an ENFORCE precondition |
| HIGH, fixed | A containment decided just before a Maintenance Window starts still executing during it | Mode is re-checked before every mutation, with outcome `SKIPPED_MODE` (§15.1) |
| HIGH, fixed | `would_contain` decisions from OBSERVE executed retroactively after ENFORCE is enabled | OBSERVE decisions are never replayed. Only new activity can contain (§15.1). |
| MEDIUM | Maintenance Window abuse by a compromised Root session | Root only, 60 min cap, observation and alerts continue, mirrored to Ops. A compromised Root is outside CLS's trust boundary. Step-up re-auth is a later hardening. |
| MEDIUM | Tier false positives (Manage Channels or Threads given to helpers) | Only @everyone CRITICAL_CONTROL is single-action eligible. ELEVATED is alert only. OBSERVE review sets thresholds. |
| MEDIUM | Trust bypass via legacy commands or the API | Legacy config commands and routes retired in 2A.5. Trust is Root only and re-checked before mutation. Trusted actors still alert. |
| MEDIUM | Owner or Root lockout | Owner and Root are never contained. Release is via the dashboard, independent of Discord roles. |
| MEDIUM | Residual privilege via managed or booster roles, or member overwrites | Recorded as `PARTIAL_QUARANTINE` and alerted. Removing overwrites is deferred. |
| MEDIUM | Destruction performed through CLS's own modules | `CLS_PROXIED` record and alert. Containing the initiator waits for command provenance (Phase 8). |
| LOW | Single-process assumption | Documented. Database constraints guard regardless. |

No HIGH or BLOCKER findings remain open.
