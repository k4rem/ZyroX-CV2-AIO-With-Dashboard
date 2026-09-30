# Dashboard baseline

This describes the dashboard and bot API as they exist in the current source. It is not a redesign.

The website is a Next.js 14 app in `dashboard/`. It talks to a FastAPI app that starts inside the bot process (`bot/api/server.py`, mounted from `bot/CodeX.py`). Settings are written into the same SQLite and JSON files the bot cogs already use. The dashboard does not own a separate database.

## 1. Current dashboard structure

Auth for `/dashboard/*` is enforced by `dashboard/app/dashboard/layout.tsx`. If there is no Discord session, it starts Discord sign-in. Public pages do not use that layout.

| Route | What it does |
|---|---|
| `/` | Marketing home. Sign-in button calls NextAuth Discord login. Module blurbs on this page are copy, not live features. |
| `/docs` | Static documentation page. Not wired to the bot. |
| `/privacy` | Static privacy page. |
| `/terms` | Static terms page. |
| `/api/auth/[...nextauth]` | NextAuth Discord OAuth callback. Scope is `identify guilds`. |
| `/dashboard` | Signed-in home. Loads bot name, guild count, user count, command count, and latency from `GET /bot/info`. |
| `/dashboard/guilds` | Lists servers the bot is in that the signed-in user owns or can manage (`ADMINISTRATOR` or `MANAGE_GUILD`). |
| `/dashboard/admin` | Bot-owner panel: host stats, a maintenance flag, and a global notification string. Hidden unless the Discord user id is in `NEXT_PUBLIC_ADMIN_IDS`. |
| `/dashboard/guild/[guildId]` | Guild header (name, icon, member/role/channel counts) plus a static “Active Modules” grid and a fake console. Those cards are hardcoded. They do not read module state. |
| `/dashboard/guild/[guildId]/settings` | Changes the bot’s text prefix for that server. |
| `/dashboard/guild/[guildId]/antinuke` | Toggles antinuke feature flags and edits a whitelist of user ids. |
| `/dashboard/guild/[guildId]/automod` | Toggles automod rules, punishment, and ignore lists. |
| `/dashboard/guild/[guildId]/verification` | Enables verification and picks the channel and verified role. |
| `/dashboard/guild/[guildId]/welcome` | Edits the welcome/greet message, embed, channel, and auto-delete time. |
| `/dashboard/guild/[guildId]/leveling` | Edits XP amount, cooldown, level-up channel, and related leveling switches. |
| `/dashboard/guild/[guildId]/leveling/leaderboard` | Read-only top users by XP. |
| `/dashboard/guild/[guildId]/logging` | Turns log categories on or off and picks a channel per category. Present in the tab bar. Not in the sidebar. |
| `/dashboard/guild/[guildId]/tickets` | Edits ticket panel text, categories, and channel ids. Does not operate live tickets. |
| `/dashboard/guild/[guildId]/autorole` | Sets human and bot autoroles. |
| `/dashboard/guild/[guildId]/vanityroles` | Adds or removes vanity-status role setups. |
| `/dashboard/guild/[guildId]/reactionroles` | Adds or removes reaction-role bindings and a DM toggle. |
| `/dashboard/guild/[guildId]/autoreact` | Edits the list of auto-react triggers. |
| `/dashboard/guild/[guildId]/customroles` | Maps short names (`staff`, `girl`, `vip`, `guest`, `friend`) to roles the bot can assign. |
| `/dashboard/guild/[guildId]/invcrole` | Sets the role given for being in voice. |
| `/dashboard/guild/[guildId]/j2c` | Enables join-to-create and picks the related voice channels. |
| `/dashboard/guild/[guildId]/joindm` | Edits the DM sent when a member joins. |
| `/dashboard/guild/[guildId]/invites` | Read-only invite leaderboard. |
| `/dashboard/guild/[guildId]/tracking` | Invite-tracking settings, including the log channel. |

`dashboard/app/dashboard/loading.tsx`, `error.tsx`, and the guild `loading.tsx` are loading and error UI, not extra pages.

`dashboard/hooks/use-auth.ts` is a stub. It does not read the session. Real auth uses NextAuth.

## 2. Current server management

These are the settings the dashboard can actually save. Each row is backed by a page and an API call in `dashboard/lib/api.ts`.

| Feature | What the dashboard saves |
|---|---|
| Prefix | Custom command prefix. |
| Antinuke | Feature toggles and whitelist user ids. |
| Automod | Rule toggles, punishment, ignored channels/roles. |
| Verification | Enabled flag, verification channel, verified role. |
| Welcome | Message type, text, embed, channel, auto-delete. |
| Leveling | XP settings and level-up channel. Leaderboard is read-only. |
| Logging | Which event categories are on, and which channel receives them. |
| Tickets | Panel embed, panel type, panel/log/closed-category ids, ticket categories and their staff role ids. |
| Autorole | Human and bot role lists. |
| Vanity roles | Vanity string, role, and channel rows. |
| Reaction roles | Message, emoji, role bindings, and whether DMs are sent. |
| Auto react | Trigger list. |
| Custom roles | Preset role ids used by prefix commands. |
| Voice role | Role applied in voice. |
| Join to create | Enabled flag and channel ids. |
| Join DM | Enabled flag and message text. |
| Invite tracking | Tracking config and log channel. Invites page itself is a leaderboard only. |
| Admin | Maintenance mode and one global notification string. Not per-server. |

Not configurable from the dashboard, even though the bot has commands for them: music, games, AI, moderation actions (ban, kick, mute), jail, emergency lockdown, extra owner, night mode, sticky messages, giveaways, birthdays, media-only channels, filters, ignore-command lists, and no-prefix users.

The guild overview does not toggle modules. The status labels on that page are fixed strings.

## 3. Tickets

The dashboard ticket page is a settings form (`dashboard/components/dashboard/tickets-form.tsx`). Saving calls `PATCH /api/v1/guilds/{id}/tickets`, which writes `db/ticket.db`. It does not send a Discord message, and it does not read or write individual ticket channels.

The bot’s ticket cog (`bot/cogs/commands/ticket.py`) is what creates panels, opens channels, claims, closes, reopens, and builds transcripts. Those actions stay in Discord.

The bot’s `guild_configs` table does not include a `staff_roles` column. The API still runs `UPDATE guild_configs SET staff_roles = ?` for the “global staff role ids” field. Per-category staff ids are stored in `ticket_categories.notified_roles`, and that is the column the bot actually uses when a ticket opens.

| Capability | Status | What exists |
|---|---|---|
| Create ticket panels | PARTIAL | The form stores panel channel, panel type, and embed text. Nothing in the API posts or updates the Discord panel message. The bot does that from the `ticket` command. |
| Edit ticket panels | PARTIAL | Same as create. Saved embed fields do not edit an existing panel message. |
| Configure ticket categories | SUPPORTED | Name, emoji, button style, Discord category id, and per-category staff role ids can be added, edited, and removed. |
| Configure staff roles | PARTIAL | Per-category role ids are saved and used by the bot. The separate global staff-id field is written to a column the bot schema does not create. |
| Configure ticket permissions | PARTIAL | There is no permission editor. The bot applies channel access from `notified_roles` when it opens a ticket. |
| Create forms/questions | NOT IMPLEMENTED | No question builder in the form or the API. |
| View open tickets | PARTIAL | The API returns `open_ticket_count` only. There is no ticket list, creator, or channel. |
| Claim/assign tickets | NOT IMPLEMENTED | Claim exists on Discord buttons in the bot, not in the dashboard. |
| Close/reopen tickets | NOT IMPLEMENTED | Same. Close, reopen, and delete stay on the ticket channel. |
| View transcripts | NOT IMPLEMENTED | The bot can generate a transcript inside the ticket channel. The dashboard has no transcript viewer. The logging channel id is only a setting. |
| Search transcripts | NOT IMPLEMENTED | No transcript store or search API. |
| View ticket logs | NOT IMPLEMENTED | No log feed. Only a logging channel id field. |
| Reply to tickets from the dashboard | NOT IMPLEMENTED | No message send route. |
| Configure ticket automation | NOT IMPLEMENTED | No auto-close, auto-claim, or schedule settings. |

## 4. Command management

There is no command-control system.

| Need | Status |
|---|---|
| View bot commands | NOT IMPLEMENTED | `GET /bot/info` returns a command count. It does not return command names. |
| Group commands by module | NOT IMPLEMENTED | Sidebar groups are page links, not command modules. |
| Enable/disable modules | NOT IMPLEMENTED | Some features have their own enabled switch (verification, leveling, j2c, automod, antinuke). There is no shared module registry. The overview switches are decorative. |
| Enable/disable individual commands | NOT IMPLEMENTED | No command table and no API for it. |
| Control command permissions | NOT IMPLEMENTED | Prefix is the only command-related setting. |
| Sync enabled slash commands with Discord | NOT IMPLEMENTED | Slash sync still happens inside the bot on startup (`bot/CodeX.py`). The dashboard cannot choose which slash commands are registered. |

## 5. API

Every route below is on the FastAPI app. `verify_api_key` is a global dependency, so all of them expect `Authorization: Bearer <DASHBOARD_API_KEY>`. They do not check the Discord user.

`GET /` and `GET /health` are outside `/api/v1` and still require that key.

Duplicate registrations: `GET` and `PATCH /api/v1/guilds/{guild_id}/welcome` are declared twice in `bot/api/routes/guilds.py`. `GET /{guild_id}/autoreact` is also declared twice. FastAPI keeps the first match, so the later copies do not run. The later welcome block also declares `DELETE /welcome`, which the dashboard never calls. `dashboard/lib/api.ts` has `updateInvites` (`PATCH /invites`), but the API only implements `GET /invites`.

| Method | Path | Purpose | Auth | Data |
|---|---|---|---|---|
| GET | `/` | Process status string | API key | None |
| GET | `/health` | Health check | API key | None |
| GET | `/api/v1/bot/status` | Live latency, guild count, user count, shards | API key | Bot memory |
| GET | `/api/v1/bot/info` | Name, counts, command count | API key | Bot memory |
| GET | `/api/v1/admin/stats` | CPU, RAM, DB file size, guild count | API key | Process stats and `db/*.db` file sizes |
| GET | `/api/v1/admin/config` | Maintenance flag and notification text | API key | `db/admin_config.db` |
| PATCH | `/api/v1/admin/config` | Update those two values | API key | `db/admin_config.db` |
| GET | `/api/v1/guilds/` | Guilds the bot is in | API key | Bot cache |
| GET | `/api/v1/guilds/{guild_id}` | Name, icon, member/role/channel counts | API key | Bot cache |
| GET | `/api/v1/guilds/{guild_id}/channels` | Text/voice channel list | API key | Bot cache |
| GET | `/api/v1/guilds/{guild_id}/roles` | Role list | API key | Bot cache |
| GET | `/api/v1/guilds/{guild_id}/prefix` | Current prefix | API key | `db/prefix.db` |
| POST | `/api/v1/guilds/{guild_id}/prefix` | Set prefix | API key | `db/prefix.db` |
| GET | `/api/v1/guilds/{guild_id}/automod` | Automod rules | API key | `db/automod.db` |
| PATCH | `/api/v1/guilds/{guild_id}/automod` | Update automod | API key | `db/automod.db` |
| GET | `/api/v1/guilds/{guild_id}/tickets` | Ticket config and open count | API key | `db/ticket.db` |
| PATCH | `/api/v1/guilds/{guild_id}/tickets` | Update ticket config | API key | `db/ticket.db` |
| GET | `/api/v1/guilds/{guild_id}/leveling` | Leveling settings | API key | `db/leveling.db` |
| PATCH | `/api/v1/guilds/{guild_id}/leveling` | Update leveling | API key | `db/leveling.db` |
| GET | `/api/v1/guilds/{guild_id}/leveling/leaderboard` | Top 100 by XP | API key | `db/leveling.db` `user_xp` |
| GET | `/api/v1/guilds/{guild_id}/welcome` | Welcome config (first handler) | API key | `db/welcome.db` |
| PATCH | `/api/v1/guilds/{guild_id}/welcome` | Update welcome (first handler) | API key | `db/welcome.db` |
| GET | `/api/v1/guilds/{guild_id}/antinuke` | Antinuke flags and whitelist | API key | `db/anti.db` |
| PATCH | `/api/v1/guilds/{guild_id}/antinuke` | Update antinuke | API key | `db/anti.db` |
| GET | `/api/v1/guilds/{guild_id}/verification` | Verification config | API key | `db/verification.db` |
| PATCH | `/api/v1/guilds/{guild_id}/verification` | Update verification | API key | `db/verification.db` |
| GET | `/api/v1/guilds/{guild_id}/vanityroles` | Vanity setups | API key | `db/vanity.db` |
| POST | `/api/v1/guilds/{guild_id}/vanityroles` | Add or replace one setup | API key | `db/vanity.db` |
| DELETE | `/api/v1/guilds/{guild_id}/vanityroles/{vanity}` | Remove one setup | API key | `db/vanity.db` |
| GET | `/api/v1/guilds/{guild_id}/autorole` | Autorole lists | API key | `db/autorole.db` |
| PATCH | `/api/v1/guilds/{guild_id}/autorole` | Update autoroles | API key | `db/autorole.db` |
| GET | `/api/v1/guilds/{guild_id}/tracking` | Invite tracking config | API key | `db/invite.db` |
| PATCH | `/api/v1/guilds/{guild_id}/tracking` | Update tracking | API key | `db/invite.db` |
| GET | `/api/v1/guilds/{guild_id}/invites` | Invite leaderboard | API key | `db/invite.db` |
| GET | `/api/v1/guilds/{guild_id}/j2c` | Join-to-create config | API key | `j2c_data.db` (bot working directory, not `db/`) |
| PATCH | `/api/v1/guilds/{guild_id}/j2c` | Update join-to-create | API key | `j2c_data.db` |
| GET | `/api/v1/guilds/{guild_id}/joindm` | Join DM text | API key | `jsondb/joindm_messages.json` |
| PATCH | `/api/v1/guilds/{guild_id}/joindm` | Update join DM | API key | `jsondb/joindm_messages.json` |
| GET | `/api/v1/guilds/{guild_id}/customroles` | Preset role map | API key | `db/customrole.db` |
| PATCH | `/api/v1/guilds/{guild_id}/customroles` | Update preset roles | API key | `db/customrole.db` |
| GET | `/api/v1/guilds/{guild_id}/logging` | Log categories and channels | API key | Logging cog memory, else `jsondb/logging_config.json` |
| PATCH | `/api/v1/guilds/{guild_id}/logging` | Update logging | API key | Cog cache, then the logging cog’s save (JSON file) |
| GET | `/api/v1/guilds/{guild_id}/autoreact` | Auto-react triggers (first handler) | API key | `db/autoreact.db` |
| PATCH | `/api/v1/guilds/{guild_id}/autoreact` | Update triggers | API key | `db/autoreact.db` |
| GET | `/api/v1/guilds/{guild_id}/invcrole` | Voice role config | API key | `db/invc.db` |
| PATCH | `/api/v1/guilds/{guild_id}/invcrole` | Update voice role | API key | `db/invc.db` |
| GET | `/api/v1/guilds/{guild_id}/reactionroles` | Reaction role rows | API key | `rr.db` (bot working directory, not `db/`) |
| PATCH | `/api/v1/guilds/{guild_id}/reactionroles` | Update reaction roles | API key | `rr.db` |

Counted as live routes: 2 root routes, 2 bot routes, 3 admin routes, and 41 guild routes. That is **48**. The shadowed welcome and autoreact duplicates, and the unused `DELETE /welcome`, are not included in that 48.

## 6. Storage

There is no dashboard database. NextAuth keeps the Discord session in the encrypted session cookie. It does not use a user table.

Dashboard-managed data is spread across many files next to the bot process:

| Store | Used for |
|---|---|
| `db/prefix.db` | Prefix |
| `db/automod.db` | Automod |
| `db/ticket.db` | Ticket config, categories, open tickets, per-user ticket counts |
| `db/leveling.db` | Leveling settings and XP |
| `db/welcome.db` | Welcome |
| `db/anti.db` | Antinuke and whitelist |
| `db/verification.db` | Verification |
| `db/vanity.db` | Vanity roles |
| `db/autorole.db` | Autoroles |
| `db/invite.db` | Tracking config and invite leaderboard |
| `db/customrole.db` | Custom roles |
| `db/autoreact.db` | Auto react |
| `db/invc.db` | Voice role |
| `db/admin_config.db` | Maintenance flag and global notification |
| `j2c_data.db` | Join to create |
| `rr.db` | Reaction roles |
| `jsondb/joindm_messages.json` | Join DMs |
| `jsondb/logging_config.json` | Logging, also mirrored in the Logging cog’s `config_cache` |

Ticket rows, open tickets, and transcripts are not in one place. Config and open-ticket rows share `db/ticket.db`. Transcripts are generated in Discord by the bot and are not stored for the dashboard. Logging config is separate. Other features each have their own file.

`bot/api/db_manager.py` keeps a few SQLite connections open. Many guild routes ignore it and open `aiosqlite.connect` themselves.

## 7. Authorization

**Discord OAuth.** `dashboard/lib/auth.ts` uses NextAuth’s Discord provider with client id and secret from the server environment (`DISCORD_CLIENT_ID`, `DISCORD_CLIENT_SECRET`). Those two are not `NEXT_PUBLIC_`. The scope is `identify guilds`. The access token is copied onto the JWT and the session. The sign-in page is `/`.

**Who may manage a guild.** Only `dashboard/app/dashboard/guilds/page.tsx` checks the user. It loads the user’s guilds from Discord with the OAuth token, keeps guilds they own or where they have Administrator or Manage Server, then intersects that with guilds the bot is in. Opening `/dashboard/guild/{id}` does not repeat that check. The guild layout only asks the bot API whether the bot is in that guild. Anyone with a dashboard login who knows a guild id can open that server’s pages.

**Admin checks.** `isAdmin` in `dashboard/lib/utils.ts` compares the session user id to `NEXT_PUBLIC_ADMIN_IDS`. The admin page redirects others to `/dashboard`. The FastAPI admin routes do not look at that list. They accept the shared API key.

**API authentication.** One bearer key, `DASHBOARD_API_KEY` on the bot, checked in `bot/api/dependencies.py`. It is not tied to a Discord user. Rate limit default is 1000 requests per minute per IP.

**`NEXT_PUBLIC_DASHBOARD_API_KEY`.** `dashboard/lib/api.ts` reads this and sends it as `Authorization: Bearer` from the browser. In Next.js, `NEXT_PUBLIC_` values are included in the client bundle. Anyone who can load the site can read the key and call the bot API directly, including `PATCH /api/v1/admin/config` and every guild settings route. The key is not a user secret.

Other client-exposed values: `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_ADMIN_IDS`, and the brand name. The admin id list tells the public which Discord accounts are treated as dashboard admins. The Discord OAuth client secret and `NEXTAUTH_SECRET` stay on the server.

`dashboard/hooks/use-auth.ts` does not participate in any of this.

## 8. Reusability

**KEEP**

- NextAuth Discord login and the session types in `dashboard/lib/auth.ts` and `dashboard/types/next-auth.d.ts`. The OAuth flow is the right shape. The missing piece is using the session on each guild request.
- The guild picker intersection in `dashboard/app/dashboard/guilds/page.tsx`. That permission check should move to the server and to the API, but the rule itself (owner, Administrator, or Manage Server, and the bot is in the guild) is the right rule.
- Small UI pieces in `dashboard/components/ui/` (button, card, input, switch, select). They are not tied to a feature.
- `dashboard/lib/utils.ts` `cn()`. Drop `isAdmin` as a client-side gate or stop publishing the id list.
- The idea of one API client in `dashboard/lib/api.ts`. The methods map cleanly onto the bot. The client must stop embedding the API key.

**REFACTOR**

- Feature forms (`antinuke-form`, `automod-form`, `welcome-form`, `leveling-form`, `logging-form`, `tickets-form`, and the other `dashboard/components/dashboard/*-form.tsx` files). They already edit the real bot config. They are one-off forms with copied save/toast code, raw id text fields, and `any` payloads. They can stay as the editors, behind a shared form shell and real guild authorization.
- Guild layout and `GuildTabs`. The header and navigation are usable. The layout must reject users who fail the guild check, and the overview page under it should be replaced because its data is fake.
- `bot/api/routes/guilds.py`. It is the real settings API, and it is one long file with duplicated welcome and autoreact routes, mixed connection styles, and no per-user check. Split by feature and add the Discord permission check before treating it as the control-center API.
- Logging’s cache-plus-JSON path. It works, but it is a different storage pattern from the SQLite features.

**REBUILD**

- Guild overview (`dashboard/app/dashboard/guild/[guildId]/page.tsx`). Hardcoded module cards and a fake log stream.
- Ticket operations. The settings form can be refactored. A ticket inbox, transcripts, claim, close, and reply do not exist and should be new API plus new pages. Do not pretend the current form is an inbox.
- Command management. No model, no routes, no UI.
- Admin authorization. The page gate is client-visible ids, and the API ignores it.
- `use-auth.ts`. Unused stub.
- Public marketing pages (`/`, `/docs`, `/privacy`, `/terms`) if the product becomes a control center. They are not part of server management.

## 9. Gap summary

The current dashboard is a settings panel for a subset of bot features. Discord commands still do the work: creating a ticket panel, moderating, playing music, and syncing slash commands.

A control center would need four additions the code does not have:

1. **Per-user authorization on the API**, using the Discord token or a server-side session, and removal of `NEXT_PUBLIC_DASHBOARD_API_KEY` from the browser.
2. **A command and module registry** the dashboard can list, enable, disable, and permission, then a bot path that registers only the enabled slash commands.
3. **Ticket operations**: list open tickets from `open_tickets`, post or edit the panel message, claim, close, reopen, store transcripts, and send a reply. Config editing already exists.
4. **One settings service** instead of a dozen database files and two JSON files, or a single API layer that hides that split so new modules are not another one-off route and form.

Until those exist, the dashboard can change stored configuration. It cannot replace the bot’s commands.
