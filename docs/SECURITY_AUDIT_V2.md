# Security audit V2

## SECURITY VERDICT

**CRITICAL ISSUE FOUND**

Static review found no hardcoded replacement bot owner and no evidence that the original developer can use `commands.is_owner()` or Jishaku. However, the dashboard API has a practical guild-takeover path: its shared API key is intentionally exposed to browsers, the API performs no user or per-guild authorization, and several routes can configure roles that the bot automatically grants.

Counts in this report: **1 Critical, 2 High, 5 Medium**.

## 1. Executive summary

- Do not expose the current dashboard API to the internet or invite the bot to a production guild with a highly privileged bot role.
- A visitor can recover `NEXT_PUBLIC_DASHBOARD_API_KEY` from the dashboard client and directly change any guild known to the bot. By setting the voice role, autorole, or reaction role to a powerful role, the visitor may have the bot grant that role to their Discord account.
- The loaded guild event cog still sends a permanent invite and guild metadata to a hardcoded original-project channel.
- Startup can install Python packages and download/execute a current Cloudflare binary without a version or checksum.
- No source path was found that transmits the Discord bot token, OAuth client secret, or `.env` contents to the original developer. A sensitive invite and guild metadata are transmitted.
- No obfuscated executable payload, encoded backdoor, arbitrary remote shell command, SQL injection, or React HTML injection was found.

## 2. Critical findings

### C-01 — Public dashboard credential and missing guild authorization permit role escalation

- **Exact files:** `dashboard/lib/api.ts`; `bot/api/server.py`; `bot/api/dependencies.py`; `bot/api/routes/guilds.py`; `bot/cogs/commands/Invc.py`; `bot/cogs/events/autorole.py`; `bot/cogs/commands/reactionroles.py`.
- **Relevant functions/classes:** `request`; `create_app`; `verify_api_key`; the guild role, `invcrole`, `autorole`, and `reactionroles` routes; `Invcrole.on_voice_state_update`; `Autorole2.on_member_join`; `ReactionRoles.on_raw_reaction_add`.
- **What the code does:** `NEXT_PUBLIC_DASHBOARD_API_KEY` is compiled into browser code. FastAPI accepts that one bearer value globally and never identifies the Discord user or verifies that they may manage the supplied `guild_id`. The API reveals guild roles and accepts role IDs for automatic assignment. The voice-role listener grants any configured role and does not honor the API's `enabled` field.
- **Realistic attack path:** an internet visitor extracts the public key, lists a target guild's roles, sets its voice role to a role with Administrator, then joins a voice channel. Autorole on rejoin and reaction-role bindings provide alternate paths. Discord role hierarchy is the only remaining barrier.
- **Who could exploit it:** anyone who can load the deployed dashboard or otherwise obtain the browser bundle; Discord OAuth login is not required for direct API calls.
- **Impact:** takeover of a Discord guild, permission changes, data access, member moderation, channel/role deletion, webhook creation, and other actions allowed by the granted role.
- **Recommended remediation:** remove the key from all `NEXT_PUBLIC_*` code; keep service credentials server-side; authenticate each API request with a server-side user session; re-check Discord owner/Administrator/Manage Guild permission for every requested guild; validate every role/channel/message against that guild and reject administrator or otherwise unsafe role assignment. Do not expose this API until fixed.

## 3. High findings

### H-01 — Loaded guild events disclose invites and metadata to an original-project channel

- **Exact file:** `bot/cogs/events/on_guild.py`.
- **Relevant class/functions:** `Guild.on_guild_join`, `Guild.on_guild_remove`.
- **What the code does:** on join, it creates or retrieves a non-expiring invite and sends that invite plus guild name, ID, owner, description, member counts, and channel counts to hardcoded channel `1396794297386532978`. On removal it sends guild metadata to the same channel. It also posts the original support-server link in the new guild. `bot/cogs/__init__.py` loads this cog.
- **Realistic attack path:** inviting the bot to a real server automatically gives whoever controls that hardcoded Discord channel a persistent invite and server details.
- **Who could exploit it:** members able to read the hardcoded destination channel, including the original project operators.
- **Impact:** unauthorized server access and private deployment/guild intelligence. No bot token is included.
- **Recommended remediation:** remove the external notification behavior or route it only to an explicitly configured channel owned by the deployer; never create an invite for telemetry.

### H-02 — Startup downloads and executes unverified dependencies

- **Exact files:** `bot/utils/tunnel.py`; `bot/utils/paginators.py`.
- **Relevant functions:** `_ensure_pycloudflared`, `_download_cloudflared_direct`, `_get_binary`, `_run_tunnel`; the module-level `discord.ext.menus` fallback.
- **What the code does:** if packages are absent, startup invokes pip. The paginator fallback installs directly from the moving GitHub repository head. Tunnel setup can install unpinned `pycloudflared`, download the latest `cloudflared` executable from GitHub, make it executable, and run it. No hash, signature, or fixed release is checked. Tunnel support defaults enabled, although it skips without a token.
- **Realistic attack path:** compromise of a package, GitHub release, DNS/TLS trust path, or upstream account results in attacker-controlled code executing as the bot's OS user during startup.
- **Who could exploit it:** a compromised upstream publisher or distribution path; a local actor who can replace a cached binary may also gain execution on restart.
- **Impact:** bot token and all environment secrets could be stolen, databases altered, and every guild controlled by the bot affected.
- **Recommended remediation:** prohibit runtime installation/download; install reviewed, pinned artifacts during deployment; verify hashes/signatures; use a separately managed, fixed Cloudflare package if a tunnel is required. Avoid passing the tunnel token on the process command line, where local process inspection may expose it.

## 4. Medium findings

### M-01 — User-controlled outbound requests allow SSRF and internal probing

- **Exact files:** `bot/cogs/commands/ai.py`; `bot/cogs/moderation/moderation.py`; `bot/cogs/commands/minecraft.py`.
- **Relevant functions/classes:** `AI.ai_analyse`, `AI.analyze_image`; the `roleicon` command; `SetupModal.on_submit`, `Minecraft.auto_detect_server`, `Minecraft.refresh_all_statuses`.
- **What the code does:** `ai analyse` fetches an arbitrary URL without an allowlist, address filtering, response-size cap, or explicit timeout, then sends the resulting image to Gemini. `roleicon` performs a similar fetch for an administrator-supplied HTTPS URL. Minecraft setup accepts a hostname and port and the background task probes it every two minutes.
- **Realistic attack path:** a Discord user supplies a loopback, LAN, or cloud-metadata URL to the AI command; a Manage Guild user configures an internal host as a Minecraft server; a malicious database row makes probing persistent.
- **Who could exploit it:** ordinary users for `ai analyse`; administrators for `roleicon`; users with Manage Guild for Minecraft setup; anyone able to alter the relevant database.
- **Impact:** internal-service discovery, requests from the VPS trust zone, bandwidth/memory exhaustion, and possible disclosure of fetched image content to Gemini.
- **Recommended remediation:** allow only approved schemes and public IP destinations, resolve and reject loopback/private/link-local ranges before every connection, limit redirects/size/time, and restrict persistent probes.

### M-02 — SQLite text is executed with `eval`

- **Exact files:** `bot/cogs/commands/autorole.py`; `bot/cogs/commands/ai.py`.
- **Relevant functions/classes:** `_autorole_humans_add`, `_autorole_humans_remove`, `_autorole_bots_add`, `_autorole_bots_remove`; `SQLiteCollection.update_one`, `find`, `find_one`.
- **What the code does:** Python `eval()` parses autorole lists and trivia history read from SQLite. The calculator also uses `eval`, but its current UI only contributes fixed digits/operators and is classified safe under the present input path.
- **Realistic attack path:** a malicious or corrupted database row executes Python when an administrator edits autoroles or when trivia data is read. Current dashboard autorole writes are numeric-list sanitized, so no direct browser-to-`eval` path was proven.
- **Who could exploit it:** anyone who can replace/edit a database, a compromised backup/deployment artifact, or another future write path that fails to sanitize.
- **Impact:** arbitrary code execution with access to bot tokens, files, network, and Discord privileges.
- **Recommended remediation:** use JSON and `json.loads`, or `ast.literal_eval` only as a migration bridge; validate element types before use.

### M-03 — Real third-party credentials are hardcoded in tracked source

- **Exact files:** `bot/cogs/commands/music.py`; `bot/cogs/commands/image.py`; `bot/cogs/commands/fun.py`.
- **Relevant locations:** module-level `spotify_api`; `PEXELS_API_KEY`; `Fun.__init__`.
- **What the code does:** tracked source contains a Spotify client secret and API keys for Pexels and Giphy. Music also falls back to a public Lavalink host and shared password when environment values are absent.
- **Realistic attack path:** anyone with repository access copies the credentials and consumes quota or impersonates this application to those providers.
- **Who could exploit it:** any repository reader; the public-origin history should be treated as already disclosed.
- **Impact:** quota theft, service suspension, unexpected billing, and external-service abuse. These keys do not grant Discord bot ownership.
- **Recommended remediation:** revoke/rotate the credentials, load replacements only from secrets storage, and fail closed rather than using a shared public Lavalink password.

### M-04 — Tracked runtime databases ship persistent privilege/configuration state

- **Exact files:** `bot/db/np.db`; `bot/db/anti.db`; all tracked `bot/db/*.db`; `bot/rr.db`; `bot/j2c_data.db`; `bot/db/ticket.db-journal`; `bot/jsondb/logging_config.json`; `.gitignore`.
- **Relevant consumers:** `Owner.load_staff` in `bot/cogs/commands/owner.py`; `is_owner_or_staff` in `owner.py`/`np.py`; antinuke listeners under `bot/cogs/antinuke/`; dashboard API routes.
- **What the code does:** runtime databases and a live SQLite journal are tracked. Current local data has zero `staff` rows, but four global no-prefix users, two guild-scoped extra owners, and one fully whitelisted user for an old hardcoded guild. User `767979794411028491` appears both in no-prefix state and the old guild's antinuke whitelist. These rows do not grant `commands.is_owner()` or Jishaku.
- **Realistic attack path:** production deployment from the repository silently imports old privilege/config rows, or later commits leak guild IDs, user IDs, tickets, XP, warnings, transcripts/configuration, and other live state. A maliciously altered `staff` row would grant the selected staff command set.
- **Who could exploit it:** repository readers for leaked data; anyone able to influence deployment artifacts or committed DB state.
- **Impact:** stale bypasses, privacy leakage, environment contamination, and selected staff-command access. The observed legacy rows are guild-scoped where applicable and are not a cross-guild bot-owner backdoor.
- **Recommended remediation:** deploy clean databases outside source control, explicitly migrate required configuration, remove legacy privilege rows, ignore DB/journal/JSON runtime data, and purge sensitive history if it has contained production information.

### M-05 — Dependency definitions are unpinned, ambiguous, and not reproducible

- **Exact files:** `bot/requirements.txt`; `dashboard/package.json`; `.gitignore`.
- **Relevant configuration:** the complete Python requirement list, npm dependency ranges, and ignored `package-lock.json`.
- **What the code does:** most Python packages have no version pin. The list includes ambiguous or unnecessary-looking names such as `discord`, `discord.ui`, `typing`, `pathlib`, and `collection`, while also listing `discord.py`. Most npm packages use ranges, and the lockfile is deliberately ignored. No install hook was found in `package.json`.
- **Realistic attack path:** a fresh VPS build resolves a different or compromised release, or a typo/squat package is installed under a trusted name.
- **Who could exploit it:** a malicious or compromised package publisher or registry path.
- **Impact:** dependency code executes during install/import with access to deployment secrets and the bot host.
- **Recommended remediation:** review every direct dependency, remove stdlib/duplicate/unknown entries, pin exact versions with hashes where practical, commit a lockfile, and perform a separate offline/approved dependency-vulnerability scan before deployment.

## 5. Low findings

- `bot/CodeX.py`, `on_command_completion`, sends every successful non-owner command name, user ID, guild name/ID, and channel ID to `CMD_WEBHOOK_URL`. The destination is deployer-configured, not hardcoded, and no token/config value is sent. Treat it as disclosed telemetry, minimize fields, and document retention.
- `dashboard/lib/auth.ts`, `jwt`/`session`, copies the Discord OAuth access token into the browser-visible NextAuth session. No XSS sink was found, but an XSS or malicious browser extension would obtain `identify guilds` access. Prefer server-side Discord calls and keep bearer tokens out of session JSON.
- `bot/utils/tunnel.py`, `_run_tunnel`, supplies the Cloudflare tunnel token in a subprocess argument. Other users/process-inspection tools on the VPS may see it.
- `bot/cogs/commands/owner.py` locally defines `blacklist_check` and `ignore_check` that always return true. These shadow the real checks only in that module. The affected commands are separately owner/staff gated where relevant, but blacklist/ignore labels there provide no protection.
- `bot/cogs/commands/leveling_original.py` contains null bytes and cannot be parsed. It is not loaded. `bot/cogs/moderation/Moderation.tar` contains source plus compiled `.pyc` files but is not executed. Both are unexplained generated/legacy artifacts.
- Many original-project support links, custom emoji IDs, avatar URLs, and bot credits remain. They are branding/resource dependencies, not privilege checks.

## 6. Informational findings

- Parameter binding is used for values in the inspected SQL. Dynamic column/table identifiers are selected from fixed code choices or integer guild IDs; no reachable SQL injection was found.
- No `dangerouslySetInnerHTML` or equivalent raw React HTML rendering was found; ordinary React escaping applies.
- No pickle/marshal loading, `shell=True`, user-controlled shell command, curl/wget/PowerShell execution, base64-decoded executable payload, hidden URL reconstruction, or XOR-obfuscated code was found.
- `os.system("clear")` in `bot/CodeX.py` is a fixed local command. `os.execv` in `bot/utils/sync_emojis.py` restarts the current executable/arguments after optional Discord emoji synchronization; Discord input does not control the executable.
- The local Git remote is `https://github.com/k4rem/ZyroX-CV2-AIO-With-Dashboard` with no embedded credential. Branch `main` is two local commits ahead of `origin/main` in the locally available metadata; no network contact was made.

## 7. Ownership privilege map

| Principal/system | Source | Effective power | Who can change it |
|---|---|---|---|
| Root bot owners | `OWNER_IDS` in `bot/utils/config.py`; passed to Discord.py in `bot/core/zyrox.py` | `commands.is_owner`, owner commands, cross-guild commands, and Jishaku if enabled | VPS environment operator only |
| Bot staff | `staff` table in `bot/db/np.db`; `Owner.load_staff` | Selected commands guarded by `is_owner_or_staff`; not `commands.is_owner` | Root bot owner via staff commands, or local DB modification |
| No-prefix users | `np` table in `bot/db/np.db` | Can invoke prefix commands without a prefix; command permission checks still apply | Root owner/bot staff, or local DB modification |
| Guild extra owners | `extraowners` in `bot/db/anti.db` | Antinuke configuration/bypass and nightmode paths for that guild; not bot owner | Guild owner or root owner through the command flow, or DB modification |
| Antinuke whitelist | `whitelisted_users` in `bot/db/anti.db` | Per-action antinuke bypass in one guild | Guild owner/extra owner, dashboard API, or DB modification |
| Emergency authorized users | `authorised_users` in `bot/db/emergency.db` | Can execute emergency permission stripping in one guild | Guild owner |
| Ignore/media/word bypasses | Feature SQLite tables | Bypass only that feature | Guild administrators or DB/API paths |
| Dashboard admin IDs | `NEXT_PUBLIC_ADMIN_IDS` in `dashboard/lib/utils.ts` | UI access to admin page only; API itself ignores this list | Dashboard environment operator |
| Any API caller with shared key | API global dependency | All dashboard API reads/writes for every guild; can indirectly acquire a Discord admin role | Anyone who extracts the public browser key |

Explicit answers:

- **Can anyone except the configured root owner become bot owner?** No source or current database path was found. Only `OWNER_IDS` feeds Discord.py ownership.
- **Can dashboard users promote themselves?** Not to bot owner, but they can exploit the API/role listeners to gain a Discord guild role, potentially Administrator.
- **Can server admins indirectly gain bot-owner powers?** No. They have many destructive guild commands but do not pass `commands.is_owner`.
- **Are original-project developer IDs still privileged?** No hardcoded ID is a bot owner. A tracked legacy developer ID remains a no-prefix user and is antinuke-whitelisted for one old guild.
- **Are there hidden alternate owner/staff mechanisms?** The documented database staff, extra-owner, whitelist, emergency authorization, and no-prefix systems exist. None is equivalent to root owner; the exposed API role path is the major authorization bypass.

## 8. Outbound network destination map

| Destination | Source | Data sent |
|---|---|---|
| Discord API/CDN | Throughout the bot; `bot/utils/sync_emojis.py` | Normal bot events/messages/files; Bot authorization token only to Discord API during emoji sync |
| Hardcoded Discord channel `1396794297386532978` | `bot/cogs/events/on_guild.py` | Permanent guild invite and guild/owner/member/channel metadata |
| `CMD_WEBHOOK_URL` | `bot/CodeX.py` | Command name, user ID, guild name/ID, channel ID |
| Discord OAuth/API | `dashboard/lib/auth.ts`; guild picker | OAuth code/token exchange, user identity and guild list |
| Cloudflare tunnel | `bot/utils/tunnel.py` | Tunnel token and proxied dashboard API traffic |
| GitHub/PyPI | `bot/utils/tunnel.py`; `bot/utils/paginators.py` | Package/binary requests; downloaded code is executed |
| Spotify | `bot/cogs/commands/music.py` | Hardcoded client credentials, track/playlist requests |
| Lavalink node | `bot/cogs/commands/music.py` | Password, search/playback requests, voice/audio control metadata |
| Groq and Google Gemini | `bot/cogs/commands/ai.py`; `bot/utils/ai_utils.py` | API keys and user prompts/history; Gemini also receives images |
| Pollinations and Prodia | `bot/utils/ai_utils.py` | Image-generation prompts and parameters |
| Giphy, Pexels, waifu.pics | `bot/cogs/commands/fun.py`; `image.py` | API keys where applicable and user image/search choices |
| GitHub search, YouTube search | `bot/cogs/commands/extra.py`; `youtube.py` | User search queries |
| Translation, gTTS, dictionary, quote/typing APIs | Translation/general/game utilities | User-supplied text or query |
| Minecraft hosts | `bot/cogs/commands/minecraft.py` | Minecraft status probes to configured host/port |
| OpenStreetMap/MapQuest | `bot/cogs/commands/map.py` | Location query and hardcoded MapQuest key; cog is not loaded |

No outbound path was found that intentionally posts the Discord bot token, `.env`, OAuth client secret, full config, or database files. Third-party AI/search/translation features necessarily disclose the user content submitted to them.

## 9. Dangerous execution primitives

| Classification | Primitive | Reachability and control |
|---|---|---|
| **CRITICAL when enabled** | Jishaku loaded by `bot/CodeX.py` | Full Python/shell-style owner debugging. Only configured `OWNER_IDS` pass Discord.py ownership; disabled unless `JISHAKU_ENABLED=true`. |
| **RISKY** | `eval` in `autorole.py` and `ai.py` | SQLite text reaches Python execution. No direct untrusted API-to-eval path was proven, but database integrity becomes a code-execution boundary. |
| **SAFE under current UI** | `eval` in `calc.py` | Calculator buttons provide only fixed numeric/operators and enforce the initiating user. |
| **RISKY** | `subprocess.run`/`Popen` in `utils/tunnel.py` | Fixed executable/arguments, but downloaded code is unverified and the tunnel token is an argument. |
| **RISKY** | Runtime pip/Git install in `utils/paginators.py` | Fixed command, moving GitHub source, executes package installation code. |
| **SAFE under current path** | `os.execv` in `utils/sync_emojis.py` | Restarts the current process using existing arguments; remote emoji data only changes a generated Python mapping. |
| **SAFE** | `os.system("clear")` in `CodeX.py` | Fixed string; no Discord/dashboard input. |
| **SAFE** | Extension loading in `core/zyrox.py` | Fixed extension list (`cogs`), not user/database/remote controlled. |

No ordinary Discord command capable of arbitrary code or system-command execution was found. Jishaku is the deliberate exception for root owners.

## 10. Dashboard/API findings

- Authentication is one shared bearer key. It is public by construction and not associated with a NextAuth user.
- Per-guild authorization exists only while building the `/dashboard/guilds` picker. Direct guild pages and API calls do not repeat it, creating direct-object-reference exposure.
- Admin API routes trust the shared key; `NEXT_PUBLIC_ADMIN_IDS` only gates the UI.
- User-supplied guild IDs are trusted. Discord IDs are generally parameterized in SQL, but role/channel ownership and safety are not consistently validated.
- Traditional cookie CSRF is not the primary issue because the bot API uses a bearer header. The exposed bearer credential makes cross-origin restrictions irrelevant to a direct attacker.
- NextAuth handles OAuth state; no custom state bypass or unsafe redirect was found.
- No obvious reflected/stored XSS sink or SQL injection was found.
- CORS uses an explicit origin list plus environment additions, not `*`, but allows all methods/headers and credentials. CORS does not protect a publicly readable bearer key.
- Rate limiting is IP-based at 1000 requests/minute, too high to mitigate credential abuse and not a substitute for authorization.
- Request logs contain client IP, path, method, status, and duration; they do not log authorization headers.
- API responses expose guild lists, role/channel IDs, member counts, leveling entries, ticket counts/config, and other configuration to any key holder.

## 11. Supply-chain findings

- See H-02 and M-05.
- No Dockerfile, Compose file, Python lockfile, npm lockfile, install script, or GitHub Actions workflow was present.
- `dashboard/package.json` has only standard dev/build/start/lint scripts and no preinstall/postinstall hook.
- No executable binary is currently tracked. Fonts, images, a 7.8 MB GIF, `dashboard/tsconfig.tsbuildinfo`, the moderation tar archive, SQLite files, and the null-byte legacy Python file are notable generated/binary artifacts.
- `Moderation.tar` contains moderation source and CPython bytecode. It is not imported or executed.
- This audit did not query online advisories. A later dependency scan must check exact resolved Python/npm versions, transitive dependencies, abandoned packages, and the Cloudflare binary.

## 12. Destructive Discord capability map

| Capability/path | Who can invoke | Required permission/check | Confirmation / scope |
|---|---|---|---|
| Ban/kick/timeout/unban | Moderation cogs | Matching Discord moderation permission | Single guild; ordinary commands generally no second confirmation |
| Global ban/kick/timeout/nickname | `bot/cogs/commands/owner2.py`, `Global` | Root bot owner | Button confirmation; iterates every mutual guild |
| Owner/guild ban and guild leave | `bot/cogs/commands/owner.py` | Root bot owner | No button confirmation on several commands; specified/current guild |
| Channel nuke | `moderation.py`, `_nuke` | Manage Channels plus top-check policy | Author-bound confirmation; deletes and clones current channel |
| Lock/hide/unlock/unhide all | `moderation.py` | Administrator | Author-bound confirmation; every channel in current guild |
| Mass unban | `moderation.py`, `unbanall` | Ban Members | Author-bound confirmation; all bans in current guild |
| Bulk role add/remove/create/delete | `moderation/role.py` | Manage Roles or Administrator | Some bulk operations have no second confirmation; current guild |
| Emergency/night mode | `commands/emergency.py`; `commands/nightmode.py` | Guild owner/extra owner/root owner as coded | Strips/restores dangerous role permissions; emergency restore confirms |
| Create/delete webhooks | `bot/CodeX.py` | Administrator | Current channel; created URL is sent by DM or posted if DM fails |
| Create permanent invites | `CodeX.py`, `make_invite`; `events/on_guild.py` | Root owner, or automatic join event | Any mutual guild for owner command; automatic telemetry has no confirmation |
| Purge/delete messages | `moderation/message.py`, automod, antinuke everyone listener | Manage Messages for commands; configured listeners automatic | Current channel/guild; automod and antinuke act without confirmation |
| Move/mute/deafen/disconnect voice members | `commands/voice.py` | Mostly Administrator or matching voice permission | Includes all-member and all-channel variants; no confirmation |
| Dashboard-driven role/config changes | Guild API plus role listeners | Public shared key at API; bot Manage Roles at Discord | Any guild in bot cache; no confirmation |

The bot cannot perform actions above its Discord role or without its own Discord permissions. Granting Administrator to the bot greatly increases impact.

## 13. Automatic/background behavior

- Loaded antinuke listeners in `bot/cogs/antinuke/` watch bans, kicks, prune, bot additions, member dangerous-role updates, channel/role create-delete-update, guild updates, integrations, everyone mentions, and webhook changes. When enabled they can ban the audit-log executor and attempt to revert the action. Owner/bot and per-action whitelist checks exist. Audit-log races and broad automatic punishment remain operational risks.
- Emoji/sticker/unban antinuke listeners in the `extra events (unused)` directory are not loaded.
- Automod listeners in `bot/cogs/automod/` inspect messages and can delete, warn, timeout, kick, or ban according to stored policy.
- `Autorole2.on_member_join`, reaction-role listeners, vanity roles, and `Invcrole.on_voice_state_update` grant/remove configured roles automatically.
- Welcome/greet, join-DM, invite tracking, leveling, AFK, counting, auto-react, autoresponder, sticky message, verification, and ticket listeners act from stored guild configuration.
- `Minecraft.refresh_all_statuses` probes configured hosts and edits status messages every two minutes.
- `Guild.on_guild_join`/`on_guild_remove` performs the hardcoded external telemetry described in H-01.
- `CodeX.py` starts FastAPI and, when configured, a reconnecting Cloudflare tunnel thread. The command-completion listener sends telemetry to `CMD_WEBHOOK_URL`.
- No loaded scheduled job was found that modifies every guild automatically without either stored per-guild configuration or a root-owner command.

## 14. Git/secrets hygiene

- Local remote: `origin` → `https://github.com/k4rem/ZyroX-CV2-AIO-With-Dashboard` (no credential in URL).
- Current branch: `main`; locally available `origin/main` points to commit `16bd843`, while local `HEAD` is `89a3495`.
- Local security cleanup is present in commit `3bef601`; command documentation is in `89a3495`.
- Existing unrelated working-tree state at audit time: modified `bot/db/leveling.db`, `messages.db`, `prefix.db`, `ticket.db`; deleted `ticket.db-journal`; untracked `docs/DASHBOARD_BASELINE.md`. This audit did not change those files.
- `.env` and `.env.local` are ignored. Local Git history inspected here showed only `.env.example` files, not real `.env` paths. Secret values from local environment files were not read or printed.
- SQLite databases, journals, runtime JSON, generated `tsconfig.tsbuildinfo`, and future tunnel binaries are not adequately ignored. Many are already tracked, so adding ignore rules alone would not remove them.
- Hardcoded Spotify/Pexels/Giphy credentials are in tracked source and therefore in history.

## 15. Verification of previous fixes

- **PASS:** `bot/utils/config.py` has no fallback owner ID. `OWNER_IDS` must be present and every item numeric; otherwise startup raises a clear `SystemExit`.
- **PASS:** `bot/core/zyrox.py` passes only parsed `OWNER_IDS` to Discord.py.
- **PASS in `bot/CodeX.py`:** the three prior startup/stat channel behaviors for `1419729255977189467`, `1419729283861184632`, and `1396794297386532978` are absent there.
- **FAIL repository-wide:** `1396794297386532978` remains active in loaded `bot/cogs/events/on_guild.py` and receives guild telemetry/invites.
- **PASS:** Jishaku loads only when `JISHAKU_ENABLED` is explicitly equal to `true`; the example setting defaults false.
- **PASS:** no replacement hardcoded root-owner path was found.
- **CAVEAT:** tracked DB rows retain legacy no-prefix and guild-scoped antinuke bypass state, but not root bot ownership.

## 16. Future member-recovery security requirements

Do not add `guilds.join` until the current API authorization issue is fixed.

- Obtain explicit, informed consent and request only `identify guilds.join`; do not reuse dashboard OAuth tokens implicitly.
- Use OAuth state with short expiry and one-time consumption; use PKCE where supported; bind callback, user, and intended guild.
- Keep access/refresh tokens server-side. Never place them in NextAuth session JSON, browser storage, logs, URLs, Discord messages, or tracked SQLite files.
- Encrypt refresh tokens at rest with an external key/KMS not stored beside the database. Separate token records by user and issuer; limit DB/file permissions.
- Restrict recovery execution to the configured root `OWNER_IDS` on the server side. Do not accept an asserted owner ID or guild ID from the browser without reauthorization.
- Maintain an explicit guild allowlist and verify the bot/root owner is authorized for that guild immediately before each join.
- Add per-user and global rate limits, dry-run counts, bounded batches, confirmation, cancellation, and immutable audit logs without token material.
- Rotate refresh tokens, detect replay, support user revocation/deletion, handle Discord revocation, and set a retention policy.
- Never use recovered members to evade Discord enforcement or add users without their original OAuth consent.

## 17. Items that could NOT be proven by static source review

- Whether deployed environment variables currently point telemetry, API, OAuth, AI, Lavalink, or Cloudflare traffic to trustworthy accounts.
- Whether the hardcoded third-party credentials are still valid or have been abused.
- Vulnerabilities or malicious behavior inside installed/transitive dependencies, downloaded binaries, Discord, Cloudflare, Lavalink, AI providers, or other remote services.
- Runtime Discord role hierarchy, granted bot permissions, channel visibility, and whether the legacy guild/IDs are controlled by the original developer.
- Contents of ignored real `.env` files; they were deliberately not inspected.
- Production database contents, backups, logs, browser bundles, reverse-proxy controls, firewall rules, TLS, process-user isolation, and VPS access controls.
- Race conditions and behavior under real Discord audit-log timing, rate limits, malformed events, or concurrent commands.

## 18. Required fixes before production

1. Replace the public shared API key with server-side user authentication and enforce per-guild authorization on every API route.
2. Remove the hardcoded guild join/remove invite telemetry in `bot/cogs/events/on_guild.py`.
3. Eliminate runtime package installation and binary downloading; deploy pinned, verified artifacts.
4. Revoke and replace every hardcoded external credential; remove public service fallbacks.
5. Replace database `eval` parsing.
6. Add SSRF protections and strict resource/time limits to all user-controlled fetch/probe paths.
7. Start from clean databases, remove legacy privilege rows, and stop tracking runtime DB/journal/config files.
8. Review and lock all dependencies, then run a separate vulnerability/license scan.
9. Keep Jishaku off, disable the tunnel unless required, and invite the bot with least privilege rather than Administrator.
10. Test antinuke, automod, emergency, global-owner, webhook, invite, bulk-role, and mass-channel actions in an isolated server before production.

## 19. Recommended later hardening

- Split the API by feature, validate schemas centrally, add audit records for every settings mutation, and use shorter endpoint-specific authorization.
- Keep Discord OAuth access tokens server-side and rotate session secrets.
- Add confirmation and an audit trail to all root-owner cross-guild actions.
- Require explicit opt-in for command telemetry and minimize identifiers.
- Add outbound egress controls on the VPS so the bot can reach only required providers.
- Use a dedicated unprivileged OS account, read-only application files, restricted secret/database permissions, backups, and tested restore procedures.
- Add static analysis, secret scanning, dependency lock verification, and tests for permission checks in CI.
