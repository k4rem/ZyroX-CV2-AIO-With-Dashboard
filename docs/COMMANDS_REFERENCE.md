# ZyroX command reference

This file is generated from the current bot source. It lists commands that `bot/cogs/__init__.py` actually loads, plus prefix commands registered in `bot/CodeX.py`.

`{prefix}` means the server's command prefix. Hybrid commands can be used with that prefix or as slash commands. A row marked `(group)` is a parent command; its subcommands are listed separately.

Permission and audience columns come from decorators and from obvious checks inside the command. Some commands add extra checks in the function body that this table summarizes rather than quotes.

## Summary

- Total unique commands: **559** (each loaded command or subcommand once)
- Total slash commands: **3** (slash-only; hybrid commands are counted on their own line)
- Total prefix commands: **388** (prefix-only)
- Total hybrid commands: **168** (usable as prefix and as slash)
- Total owner-only commands: **40** (decorator is bot-owner only; another **11** allow the bot-owner staff list)
- Total admin/moderation commands: **293** (Moderation or Antinuke category, or a Moderator / Administrator / Server Owner check)

Slash-invocable commands, if you count hybrids as well, are **171**.

## General

| Command | Syntax | Type | Description | Arguments | Permissions | Who | Setup first? | Aliases | Source |
|---|---|---|---|---|---|---|---|---|---|
| afk | `{prefix}afk <reason>` or `/afk` | Hybrid | Set your AFK status with a reason (Global or Local). | reason | None declared | Everyone | No | — | `bot/cogs/commands/afk.py` |
| avatar | `{prefix}avatar <member>` or `/avatar` | Hybrid | Get User avater/Guild avatar & Banner of a user. | member | None declared | Everyone | No | av | `bot/cogs/commands/general.py` |
| banner | `{prefix}banner` or `/banner` (group) | Hybrid | No description in source. | — | None declared | Everyone | No | — | `bot/cogs/commands/extra.py` |
| banner server | `{prefix}banner server` or `/banner server` | Hybrid | No description in source. | — | None declared | Everyone | No | — | `bot/cogs/commands/extra.py` |
| banner user | `{prefix}banner user <member>` or `/banner user` | Hybrid | No description in source. | member | None declared | Everyone | No | — | `bot/cogs/commands/extra.py` |
| boostcount | `{prefix}boostcount` | Prefix | Shows boosts count | — | None declared | Everyone | No | bco | `bot/cogs/commands/extra.py` |
| channelinfo | `{prefix}channelinfo <channel>` or `/channelinfo` | Hybrid | Get information about a channel. | channel | None declared | Everyone | No | cinfo, ci | `bot/cogs/commands/extra.py` |
| github | `{prefix}github <search_query>` | Prefix | No description in source. | search_query | None declared | Everyone | No | — | `bot/cogs/commands/extra.py` |
| invite | `{prefix}invite` | Prefix | Get Support & Bot invite link! | — | None declared | Everyone | No | invite-bot | `bot/cogs/commands/general.py` |
| joined-at | `{prefix}joined-at` | Prefix | Shows when a user joined | — | None declared | Everyone | No | — | `bot/cogs/commands/extra.py` |
| list | `{prefix}list` or `/list` (group) | Hybrid | No description in source. | — | None declared | Everyone | No | — | `bot/cogs/commands/extra.py` |
| list activedeveloper | `{prefix}list activedeveloper` or `/list activedeveloper` | Hybrid | List of members that have Active Developer badge. | — | None declared | Everyone | No | activedev | `bot/cogs/commands/extra.py` |
| list admins | `{prefix}list admins` or `/list admins` | Hybrid | List of all Admins of the Guild | — | None declared | Everyone | No | admin | `bot/cogs/commands/extra.py` |
| list bans | `{prefix}list bans` or `/list bans` | Hybrid | List of all banned members in Guild | — | User: view_audit_log; Bot: view_audit_log | Moderator | No | ban | `bot/cogs/commands/extra.py` |
| list boosters | `{prefix}list boosters` or `/list boosters` | Hybrid | List of boosters in the Guild | — | None declared | Everyone | No | boost, booster | `bot/cogs/commands/extra.py` |
| list bots | `{prefix}list bots` or `/list bots` | Hybrid | List of All Bots in a server | — | None declared | Everyone | No | bot | `bot/cogs/commands/extra.py` |
| list createdat | `{prefix}list createdat` or `/list createdat` | Hybrid | List of Account Creation Date of all Users | — | None declared | Everyone | No | — | `bot/cogs/commands/extra.py` |
| list early | `{prefix}list early` or `/list early` | Hybrid | List of members that have Early Supporter badge. | — | None declared | Everyone | No | sup | `bot/cogs/commands/extra.py` |
| list emojis | `{prefix}list emojis` or `/list emojis` | Hybrid | List of emojis in the Guild with ids | — | None declared | Everyone | No | emoji | `bot/cogs/commands/extra.py` |
| list inrole | `{prefix}list inrole <role>` or `/list inrole` | Hybrid | List of members that are in the specified role | role | None declared | Everyone | No | inside-role | `bot/cogs/commands/extra.py` |
| list invoice | `{prefix}list invoice` or `/list invoice` | Hybrid | List of all users in a voice channel | — | None declared | Everyone | No | invc | `bot/cogs/commands/extra.py` |
| list joinedat | `{prefix}list joinedat` or `/list joinedat` | Hybrid | List of Guild Joined date of all Users | — | None declared | Everyone | No | — | `bot/cogs/commands/extra.py` |
| list moderators | `{prefix}list moderators` or `/list moderators` | Hybrid | List of All Admins of a server | — | None declared | Everyone | No | mods | `bot/cogs/commands/extra.py` |
| list roles | `{prefix}list roles` or `/list roles` | Hybrid | List of all roles in the server with ids | — | User: manage_roles | Moderator | No | role | `bot/cogs/commands/extra.py` |
| membercount | `{prefix}membercount` or `/membercount` | Hybrid | Get total member count of the server | — | None declared | Everyone | No | mc | `bot/cogs/commands/general.py` |
| permissions | `{prefix}permissions <member>` | Prefix | Check and list the key permissions of a specific user | member | None declared | Everyone | No | perms | `bot/cogs/commands/extra.py` |
| ping | `{prefix}ping` or `/ping` | Hybrid | Checks the bot's latencies. | — | None declared | Everyone | No | latency | `bot/cogs/commands/extra.py` |
| poll | `{prefix}poll <message>` or `/poll` | Hybrid | No description in source. | message | None declared | Everyone | No | — | `bot/cogs/commands/general.py` |
| report | `{prefix}report <bug>` or `/report` | Hybrid | Report a bug to the Development team. | bug | None declared | Everyone | No | bug | `bot/cogs/commands/extra.py` |
| roleinfo | `{prefix}roleinfo <role>` or `/roleinfo` | Hybrid | Displays information about a specified role. | role | None declared | Everyone | No | ri | `bot/cogs/commands/extra.py` |
| servericon | `{prefix}servericon` or `/servericon` | Hybrid | Get the server icon | — | None declared | Everyone | No | — | `bot/cogs/commands/general.py` |
| serverinfo | `{prefix}serverinfo` or `/serverinfo` | Hybrid | No description in source. | — | Checked in the command body, not with a permission decorator | Server Owner | No | sinfo, si | `bot/cogs/commands/extra.py` |
| stats | `{prefix}stats` or `/stats` | Hybrid | Shows the bot's information. | — | None declared | Everyone | No | botstats, statistics, botinfo | `bot/cogs/commands/stats.py` |
| status | `{prefix}status <user>` | Prefix | Shows the status of the user in detail. | user | None declared | Everyone | No | — | `bot/cogs/commands/status.py` |
| uptime | `{prefix}uptime` | Prefix | Shows the Bot's Uptime. | — | None declared | Everyone | No | — | `bot/cogs/commands/extra.py` |
| userinfo | `{prefix}userinfo <member>` or `/userinfo` | Hybrid | No description in source. | member | Checked in the command body, not with a permission decorator | Server Owner | No | whois, ui | `bot/cogs/commands/extra.py` |
| users | `{prefix}users` | Prefix | No description in source. | — | None declared | Everyone | No | — | `bot/cogs/commands/general.py` |
| vcinfo | `{prefix}vcinfo <channel>` or `/vcinfo` | Hybrid | View information about a voice channel. | channel | None declared | Everyone | No | — | `bot/cogs/commands/extra.py` |

## Moderation

| Command | Syntax | Type | Description | Arguments | Permissions | Who | Setup first? | Aliases | Source |
|---|---|---|---|---|---|---|---|---|---|
| audit | `{prefix}audit <limit>` or `/audit` | Hybrid | See recents audit log action in the server . | limit | User: view_audit_log; Bot: view_audit_log | Moderator | No | — | `bot/cogs/moderation/moderation.py` |
| ban | `{prefix}ban <user> <reason>` or `/ban` | Hybrid | Bans a user from the Server | user, reason | User: ban_members; Bot: ban_members | Moderator | No | fuckban, hackban, kuttaban | `bot/cogs/moderation/ban.py` |
| clear | `{prefix}clear <Choice> <Amount>` (group) | Prefix | Clears the messages | Choice, Amount | User: manage_messages; Bot: manage_messages | Moderator | No | purge | `bot/cogs/moderation/message.py` |
| clear all | `{prefix}clear all <search>` | Prefix | Clears all messages | search | User: manage_messages; Bot: manage_messages | Moderator | No | — | `bot/cogs/moderation/message.py` |
| clear bot | `{prefix}clear bot <prefix> <search>` | Prefix | Clears the messages sent by bot | prefix, search | User: manage_messages; Bot: manage_messages | Moderator | No | bots, b | `bot/cogs/moderation/message.py` |
| clear contains | `{prefix}clear contains <string>` | Prefix | Clears the messages containing a specifix string | string | User: manage_messages; Bot: manage_messages | Moderator | No | — | `bot/cogs/moderation/message.py` |
| clear embeds | `{prefix}clear embeds <search>` | Prefix | Clears the messages having embeds | search | User: manage_messages; Bot: manage_messages | Moderator | No | — | `bot/cogs/moderation/message.py` |
| clear emoji | `{prefix}clear emoji <search>` | Prefix | Clears the messages having emojis | search | User: manage_messages; Bot: manage_messages | Moderator | No | emojis | `bot/cogs/moderation/message.py` |
| clear files | `{prefix}clear files <search>` | Prefix | Clears the messages having files | search | User: manage_messages; Bot: manage_messages | Moderator | No | — | `bot/cogs/moderation/message.py` |
| clear images | `{prefix}clear images <search>` | Prefix | Clears the messages having images | search | User: manage_messages; Bot: manage_messages | Moderator | No | — | `bot/cogs/moderation/message.py` |
| clear reactions | `{prefix}clear reactions <search>` | Prefix | Clears the reaction from the messages | search | User: manage_messages; Bot: manage_messages | Moderator | No | — | `bot/cogs/moderation/message.py` |
| clear user | `{prefix}clear user <member> <search>` | Prefix | Clears the messages of a specific user | member, search | User: manage_messages; Bot: manage_messages | Moderator | No | — | `bot/cogs/moderation/message.py` |
| clearwarns | `{prefix}clearwarns <user>` or `/clearwarns` | Hybrid | Clear all warnings for a user | user | User: moderate_members | Moderator | No | clearwarn, clearwarnings | `bot/cogs/moderation/warn.py` |
| clone | `{prefix}clone <channel>` or `/clone` | Hybrid | Clones a channel. | channel | User: manage_channels | Moderator | No | — | `bot/cogs/moderation/moderation.py` |
| delemoji | `{prefix}delemoji <emoji>` | Prefix | Deletes the emoji from the server | emoji | User: manage_emojis | Moderator | No | deleteemoji, removeemoji | `bot/cogs/moderation/moderation.py` |
| delsticker | `{prefix}delsticker <name>` | Prefix | Delete the sticker from the server | name | User: manage_emojis; Bot: manage_emojis | Moderator | No | deletesticker, removesticker | `bot/cogs/moderation/moderation.py` |
| give | `{prefix}give <member> <role>` or `/give` | Hybrid | Gives the mentioned user a role. | member, role | User: manage_roles; Bot: manage_roles | Moderator | No | addrole | `bot/cogs/moderation/moderation.py` |
| hide | `{prefix}hide <channel>` or `/hide` | Hybrid | Hides a channel from the default role (@everyone). | channel | User: manage_channels; Bot: manage_channels | Moderator | No | hidechannel | `bot/cogs/moderation/hide.py` |
| hideall | `{prefix}hideall` or `/hideall` | Hybrid | Hides all the channels . | — | User: administrator | Administrator | No | — | `bot/cogs/moderation/moderation.py` |
| kick | `{prefix}kick <member> <reason>` or `/kick` | Hybrid | Kicks a member from the server. | member, reason | User: kick_members; Bot: kick_members | Moderator | No | kickmember | `bot/cogs/moderation/kick.py` |
| lock | `{prefix}lock <channel>` or `/lock` | Hybrid | Locks a channel to prevent sending messages. | channel | User: manage_channels; Bot: manage_channels | Moderator | No | lockchannel | `bot/cogs/moderation/lock.py` |
| lockall | `{prefix}lockall` or `/lockall` | Hybrid | locks all the channels in Guild. | — | User: administrator | Administrator | No | — | `bot/cogs/moderation/moderation.py` |
| mute | `{prefix}mute <user> <time> <reason>` or `/mute` | Hybrid | Mutes a user with optional time and reason | user, time, reason | User: moderate_members; Bot: moderate_members | Moderator | No | timeout, stfu, chup | `bot/cogs/moderation/timeout.py` |
| nick | `{prefix}nick <member> <name>` or `/nick` | Hybrid | To change someone's nickname. | member, name | User: manage_nicknames; Bot: manage_nicknames | Moderator | No | setnick | `bot/cogs/moderation/moderation.py` |
| nuke | `{prefix}nuke` or `/nuke` | Hybrid | Nukes a channel | — | User: manage_channels | Moderator | No | — | `bot/cogs/moderation/moderation.py` |
| purgebots | `{prefix}purgebots <prefix> <search>` | Prefix | Clear recently bot messages in channel | prefix, search | User: manage_messages; Bot: manage_messages | Moderator | No | cleanup, pb, clearbot, clearbots | `bot/cogs/moderation/message.py` |
| purgeuser | `{prefix}purgeuser <member> <search>` | Prefix | Clear recent messages of a user in channel | member, search | User: manage_messages; Bot: manage_messages | Moderator | No | pu, cu, clearuser | `bot/cogs/moderation/message.py` |
| removerole | `{prefix}removerole` (group) | Prefix | remove a role from all members . | — | User: administrator | Administrator | No | rrole | `bot/cogs/moderation/role.py` |
| removerole all | `{prefix}removerole all <role>` | Prefix | Removes a role from all members in the server. | role | User: administrator | Administrator | No | — | `bot/cogs/moderation/role.py` |
| removerole bots | `{prefix}removerole bots <role>` | Prefix | Removes a role from all the bots in the server. | role | User: administrator | Administrator | No | — | `bot/cogs/moderation/role.py` |
| removerole humans | `{prefix}removerole humans <role>` | Prefix | Removes a role from all the humans in the server. | role | User: administrator | Administrator | No | — | `bot/cogs/moderation/role.py` |
| removerole unverified | `{prefix}removerole unverified <role>` | Prefix | Removes a role from all the unverified members in the server. | role | User: administrator | Administrator | No | — | `bot/cogs/moderation/role.py` |
| role | `{prefix}role <member> <role>` (group) | Prefix | No description in source. | member, role | User: manage_roles | Moderator | No | — | `bot/cogs/moderation/role.py` |
| role all | `{prefix}role all <role>` | Prefix | Gives role to all the members in the guild | role | User: administrator | Administrator | No | — | `bot/cogs/moderation/role.py` |
| role bots | `{prefix}role bots <role>` | Prefix | Gives role to all the bots in the guild | role | User: administrator | Administrator | No | — | `bot/cogs/moderation/role.py` |
| role create | `{prefix}role create <name>` | Prefix | Create a role in the guild | name | User: administrator; Bot: manage_roles | Administrator | No | — | `bot/cogs/moderation/role.py` |
| role delete | `{prefix}role delete <role>` | Prefix | Delete a role in the guild | role | User: manage_roles; Bot: manage_roles | Moderator | No | — | `bot/cogs/moderation/role.py` |
| role humans | `{prefix}role humans <role>` | Prefix | Gives role to all humans in the guild | role | User: administrator | Administrator | No | — | `bot/cogs/moderation/role.py` |
| role rename | `{prefix}role rename <role> <newname>` | Prefix | Renames a role in the server. | role, newname | User: administrator; Bot: manage_roles | Administrator | No | — | `bot/cogs/moderation/role.py` |
| role temp | `{prefix}role temp <role> <time> <user>` | Prefix | Give role to member for particular time | role, time, user | User: manage_roles; Bot: manage_roles | Moderator | No | — | `bot/cogs/moderation/role.py` |
| role unverified | `{prefix}role unverified <role>` | Prefix | Gives role to all the unverified members in the guild | role | User: administrator | Administrator | No | — | `bot/cogs/moderation/role.py` |
| roleicon | `{prefix}roleicon <role> <icon>` | Prefix | Changes the icon for the role. | role, icon | User: administrator; Bot: manage_roles | Administrator | No | — | `bot/cogs/moderation/moderation.py` |
| slowmode | `{prefix}slowmode <seconds>` or `/slowmode` | Hybrid | Changes the slowmode | seconds | User: manage_messages | Moderator | No | slow | `bot/cogs/moderation/moderation.py` |
| snipe | `{prefix}snipe` | Prefix | Shows the most recently deleted message in the channel. | — | User: manage_messages | Moderator | No | — | `bot/cogs/moderation/snipe.py` |
| topcheck | `{prefix}topcheck` (group) | Prefix | Manage topcheck settings for the server. | — | None declared | Everyone | No | — | `bot/cogs/moderation/topcheck.py` |
| topcheck disable | `{prefix}topcheck disable` | Prefix | Disable topcheck for the guild | — | Checked in the command body, not with a permission decorator | Server Owner | Yes | — | `bot/cogs/moderation/topcheck.py` |
| topcheck enable | `{prefix}topcheck enable` | Prefix | Enable topcheck for the guild | — | Checked in the command body, not with a permission decorator | Server Owner | This command is the setup step | — | `bot/cogs/moderation/topcheck.py` |
| unban | `{prefix}unban <user> <reason>` or `/unban` | Hybrid | Unbans a user from the Server | user, reason | User: ban_members; Bot: ban_members | Moderator | No | forgive, pardon | `bot/cogs/moderation/unban.py` |
| unbanall | `{prefix}unbanall` or `/unbanall` | Hybrid | Unbans Everyone In The Guild! | — | User: ban_members | Moderator | No | massunban | `bot/cogs/moderation/moderation.py` |
| unhide | `{prefix}unhide <channel>` or `/unhide` | Hybrid | Unhides a channel for the default role (@everyone). | channel | User: manage_channels; Bot: manage_channels | Moderator | No | unhidechannel | `bot/cogs/moderation/unhide.py` |
| unhideall | `{prefix}unhideall` or `/unhideall` | Hybrid | Unhides all the channels in the server. | — | User: administrator | Administrator | No | — | `bot/cogs/moderation/moderation.py` |
| unlock | `{prefix}unlock <channel>` or `/unlock` | Hybrid | Unlocks a channel to allow sending messages. | channel | User: manage_roles; Bot: manage_roles | Moderator | No | unlockchannel | `bot/cogs/moderation/unlock.py` |
| unlockall | `{prefix}unlockall` or `/unlockall` | Hybrid | Unlocks all channels in the Guild. | — | User: administrator | Administrator | No | — | `bot/cogs/moderation/moderation.py` |
| unmute | `{prefix}unmute <user>` or `/unmute` | Hybrid | Unmutes a user from the Server | user | User: moderate_members; Bot: moderate_members | Moderator | No | untimeout | `bot/cogs/moderation/unmute.py` |
| unslowmode | `{prefix}unslowmode` or `/unslowmode` | Hybrid | Disables slowmode | — | User: manage_messages; Bot: manage_messages | Moderator | No | unslow | `bot/cogs/moderation/moderation.py` |
| warn | `{prefix}warn <user> <reason>` or `/warn` | Hybrid | Warn a user in the server | user, reason | User: moderate_members | Moderator | No | warnuser | `bot/cogs/moderation/warn.py` |

## Server Management

| Command | Syntax | Type | Description | Arguments | Permissions | Who | Setup first? | Aliases | Source |
|---|---|---|---|---|---|---|---|---|---|
| addinvites | `{prefix}addinvites <member> <amount>` | Prefix | No description in source. | member, amount | User: administrator | Administrator | No | addinvs | `bot/cogs/commands/tracking.py` |
| autoresponder | `{prefix}autoresponder` (group) | Prefix | Manage autoresponders in the server. | — | None declared | Everyone | No | ar | `bot/cogs/commands/autoresponder.py` |
| autoresponder config | `{prefix}autoresponder config` | Prefix | List all autoresponders in the server. | — | User: administrator | Administrator | Yes | — | `bot/cogs/commands/autoresponder.py` |
| autoresponder create | `{prefix}autoresponder create <name> <message>` | Prefix | Create a new autoresponder. | name, message | User: administrator | Administrator | No | — | `bot/cogs/commands/autoresponder.py` |
| autoresponder delete | `{prefix}autoresponder delete <name>` | Prefix | Delete an existing autoresponder. | name | User: administrator | Administrator | No | — | `bot/cogs/commands/autoresponder.py` |
| autoresponder edit | `{prefix}autoresponder edit <name> <message>` | Prefix | Edit an existing autoresponder. | name, message | User: administrator | Administrator | Yes | — | `bot/cogs/commands/autoresponder.py` |
| birthday | `{prefix}birthday` | Prefix | Check your birthday. | — | None declared | Everyone | No | — | `bot/cogs/commands/Birthday.py` |
| birthdaysetup | `{prefix}birthdaysetup <channel> <role>` | Prefix | Set up the birthday log channel and role. | channel, role | User: administrator | Administrator | No | — | `bot/cogs/commands/Birthday.py` |
| ignore | `{prefix}ignore` (group) | Prefix | Manage ignored commands, channels, users, and bypassed users. | — | User: administrator | Administrator | No | — | `bot/cogs/commands/ignore.py` |
| ignore bypass | `{prefix}ignore bypass` (group) | Prefix | Manage bypassed users in this guild. | — | User: administrator | Administrator | No | — | `bot/cogs/commands/ignore.py` |
| ignore bypass add | `{prefix}ignore bypass add <user>` | Prefix | Adds a user to the bypass list. | user | User: administrator | Administrator | No | — | `bot/cogs/commands/ignore.py` |
| ignore bypass remove | `{prefix}ignore bypass remove <user>` | Prefix | Removes a user from the bypass list. | user | User: administrator | Administrator | No | — | `bot/cogs/commands/ignore.py` |
| ignore bypass show | `{prefix}ignore bypass show` | Prefix | Displays the list of bypassed users. | — | User: administrator | Administrator | No | list | `bot/cogs/commands/ignore.py` |
| ignore channel | `{prefix}ignore channel` (group) | Prefix | Manage ignored channels in this guild. | — | User: administrator | Administrator | No | — | `bot/cogs/commands/ignore.py` |
| ignore channel add | `{prefix}ignore channel add <channel>` | Prefix | Adds a channel to the ignore list. | channel | User: administrator | Administrator | No | — | `bot/cogs/commands/ignore.py` |
| ignore channel remove | `{prefix}ignore channel remove <channel>` | Prefix | Removes a channel from the ignore list. | channel | User: administrator | Administrator | No | — | `bot/cogs/commands/ignore.py` |
| ignore channel show | `{prefix}ignore channel show` | Prefix | Displays the list of ignored channels. | — | User: administrator | Administrator | No | — | `bot/cogs/commands/ignore.py` |
| ignore command | `{prefix}ignore command` (group) | Prefix | Manage ignored commands in this guild. | — | User: administrator | Administrator | No | — | `bot/cogs/commands/ignore.py` |
| ignore command add | `{prefix}ignore command add <command_name>` | Prefix | Adds a command to the ignore list. | command_name | User: administrator | Administrator | No | — | `bot/cogs/commands/ignore.py` |
| ignore command remove | `{prefix}ignore command remove <command_name>` | Prefix | Removes a command from the ignore list. | command_name | User: administrator | Administrator | No | — | `bot/cogs/commands/ignore.py` |
| ignore command show | `{prefix}ignore command show` | Prefix | Displays the list of ignored commands. | — | User: administrator | Administrator | No | — | `bot/cogs/commands/ignore.py` |
| ignore user | `{prefix}ignore user` (group) | Prefix | Manage ignored users in this guild. | — | User: administrator | Administrator | No | — | `bot/cogs/commands/ignore.py` |
| ignore user add | `{prefix}ignore user add <user>` | Prefix | Adds a user to the ignore list. | user | User: administrator | Administrator | No | — | `bot/cogs/commands/ignore.py` |
| ignore user remove | `{prefix}ignore user remove <user>` | Prefix | Removes a user from the ignore list. | user | User: administrator | Administrator | No | — | `bot/cogs/commands/ignore.py` |
| ignore user show | `{prefix}ignore user show` | Prefix | Displays the list of ignored users. | — | User: administrator | Administrator | No | — | `bot/cogs/commands/ignore.py` |
| invitelogging | `{prefix}invitelogging <channel>` | Prefix | No description in source. | channel | User: administrator | Administrator | No | invlog | `bot/cogs/commands/tracking.py` |
| invites | `{prefix}invites <member>` | Prefix | No description in source. | member | None declared | Everyone | No | inv | `bot/cogs/commands/tracking.py` |
| invitesleaderboard | `{prefix}invitesleaderboard` | Prefix | No description in source. | — | None declared | Everyone | No | invlb | `bot/cogs/commands/tracking.py` |
| listbirthdays | `{prefix}listbirthdays` | Prefix | List all members who have their birthday today. | — | None declared | Everyone | No | — | `bot/cogs/commands/Birthday.py` |
| media | `{prefix}media` or `/media` (group) | Hybrid | Setup Media channel, Media channel will not allow users to send messages other than media files. | — | None declared | Everyone | No | — | `bot/cogs/commands/Media.py` |
| media bypass | `{prefix}media bypass` or `/media bypass` (group) | Hybrid | Add/Remove user to bypass in Media only channel, Bypassed users can send messages in Media channel. | — | User: administrator | Administrator | Yes | — | `bot/cogs/commands/Media.py` |
| media bypass add | `{prefix}media bypass add <user>` or `/media bypass add` | Hybrid | Adds a user to the bypass list | user | User: administrator | Administrator | Yes | — | `bot/cogs/commands/Media.py` |
| media bypass remove | `{prefix}media bypass remove <user>` or `/media bypass remove` | Hybrid | Removes a user from the bypass list | user | User: administrator | Administrator | Yes | — | `bot/cogs/commands/Media.py` |
| media bypass show | `{prefix}media bypass show` or `/media bypass show` | Hybrid | Shows the bypass list | — | User: administrator | Administrator | Yes | list, view | `bot/cogs/commands/Media.py` |
| media config | `{prefix}media config` or `/media config` | Hybrid | Shows the configured media-only channel | — | User: administrator | Administrator | Yes | settings, show | `bot/cogs/commands/Media.py` |
| media remove | `{prefix}media remove` or `/media remove` | Hybrid | Removes the current media-only channel | — | User: administrator | Administrator | Yes | reset, delete | `bot/cogs/commands/Media.py` |
| media setup | `{prefix}media setup <channel>` or `/media setup` | Hybrid | Sets up a media-only channel for the server | channel | User: administrator | Administrator | This command is the setup step | set, add | `bot/cogs/commands/Media.py` |
| prefix | `{prefix}prefix <prefix>` or `/prefix` | Hybrid | Allows you to change the prefix of the bot for this server | prefix | User: administrator | Administrator | No | setprefix, prefixset | `bot/cogs/moderation/moderation.py` |
| removebirthday | `{prefix}removebirthday` | Prefix | Remove your birthday. | — | None declared | Everyone | No | — | `bot/cogs/commands/Birthday.py` |
| resetinvites | `{prefix}resetinvites <member>` | Prefix | No description in source. | member | User: administrator | Administrator | No | resetinvs | `bot/cogs/commands/tracking.py` |
| setbirthday | `{prefix}setbirthday` | Prefix | Set your birthday. | — | None declared | Everyone | No | — | `bot/cogs/commands/Birthday.py` |
| setinvites | `{prefix}setinvites <member> <amount>` | Prefix | No description in source. | member, amount | User: administrator | Administrator | No | setinvs | `bot/cogs/commands/tracking.py` |
| stickymessage | `{prefix}stickymessage` (group) | Prefix | No description in source. | — | User: manage_messages | Moderator | No | sticky, sm | `bot/cogs/commands/stickymessage.py` |
| stickymessage edit | `{prefix}stickymessage edit <channel>` | Prefix | No description in source. | channel | User: manage_messages | Moderator | Yes | — | `bot/cogs/commands/stickymessage.py` |
| stickymessage list | `{prefix}stickymessage list` | Prefix | No description in source. | — | User: manage_messages | Moderator | No | — | `bot/cogs/commands/stickymessage.py` |
| stickymessage remove | `{prefix}stickymessage remove <channel>` | Prefix | No description in source. | channel | User: manage_messages | Moderator | No | delete, del | `bot/cogs/commands/stickymessage.py` |
| stickymessage setup | `{prefix}stickymessage setup <channel>` | Prefix | No description in source. | channel | User: manage_messages | Moderator | This command is the setup step | — | `bot/cogs/commands/stickymessage.py` |

## Automod

| Command | Syntax | Type | Description | Arguments | Permissions | Who | Setup first? | Aliases | Source |
|---|---|---|---|---|---|---|---|---|---|
| automod | `{prefix}automod` or `/automod` (group) | Hybrid | No description in source. | — | None declared | Everyone | No | — | `bot/cogs/commands/automod.py` |
| automod config | `{prefix}automod config` or `/automod config` | Hybrid | View Automod settings. | — | User: administrator | Administrator | Yes | settings, show, view | `bot/cogs/commands/automod.py` |
| automod disable | `{prefix}automod disable` or `/automod disable` | Hybrid | Disable Automod in the server. | — | User: administrator | Administrator | Yes | — | `bot/cogs/commands/automod.py` |
| automod enable | `{prefix}automod enable` or `/automod enable` | Hybrid | Enable Automod on the server. | — | User: administrator; Bot: manage_guild | Administrator | This command is the setup step | — | `bot/cogs/commands/automod.py` |
| automod ignore | `{prefix}automod ignore` or `/automod ignore` (group) | Hybrid | Manage whitelisted roles and channels for Automod. | — | None declared | Everyone | Yes | exempt, whitelist, wl | `bot/cogs/commands/automod.py` |
| automod ignore channel | `{prefix}automod ignore channel <channel>` or `/automod ignore channel` | Hybrid | Add a channel to the whitelist. | channel | User: administrator | Administrator | Yes | — | `bot/cogs/commands/automod.py` |
| automod ignore reset | `{prefix}automod ignore reset` or `/automod ignore reset` | Hybrid | Reset the whitelist. | — | User: administrator | Administrator | Yes | — | `bot/cogs/commands/automod.py` |
| automod ignore role | `{prefix}automod ignore role <role>` or `/automod ignore role` | Hybrid | Add a role to the whitelist. | role | User: administrator | Administrator | Yes | — | `bot/cogs/commands/automod.py` |
| automod ignore show | `{prefix}automod ignore show` or `/automod ignore show` | Hybrid | Show the whitelisted roles and channels. | — | User: administrator | Administrator | Yes | view, list, config | `bot/cogs/commands/automod.py` |
| automod logging | `{prefix}automod logging <channel>` or `/automod logging` | Hybrid | Set the logging channel for Automod events. | channel | User: administrator | Administrator | Yes | — | `bot/cogs/commands/automod.py` |
| automod punishment | `{prefix}automod punishment` or `/automod punishment` | Hybrid | Set the punishment for automod events. | — | User: administrator | Administrator | Yes | punish | `bot/cogs/commands/automod.py` |
| automod unignore | `{prefix}automod unignore` or `/automod unignore` (group) | Hybrid | Remove channels and roles from the whitelist. | — | None declared | Everyone | Yes | unwhitelist, unwl | `bot/cogs/commands/automod.py` |
| automod unignore channel | `{prefix}automod unignore channel <channel>` or `/automod unignore channel` | Hybrid | Remove a channel from the whitelist. | channel | User: administrator | Administrator | Yes | — | `bot/cogs/commands/automod.py` |
| automod unignore role | `{prefix}automod unignore role <role>` or `/automod unignore role` | Hybrid | Remove a role from the whitelist. | role | User: administrator | Administrator | Yes | — | `bot/cogs/commands/automod.py` |
| blacklistword | `{prefix}blacklistword` (group) | Prefix | No description in source. | — | None declared | Everyone | No | blword | `bot/cogs/commands/blacklist.py` |
| blacklistword add | `{prefix}blacklistword add <word>` | Prefix | No description in source. | word | User: administrator | Administrator | No | — | `bot/cogs/commands/blacklist.py` |
| blacklistword bypass | `{prefix}blacklistword bypass` (group) | Prefix | No description in source. | — | User: administrator | Administrator | No | — | `bot/cogs/commands/blacklist.py` |
| blacklistword bypass add | `{prefix}blacklistword bypass add <target>` | Prefix | No description in source. | target | User: administrator | Administrator | No | — | `bot/cogs/commands/blacklist.py` |
| blacklistword bypass list | `{prefix}blacklistword bypass list` | Prefix | No description in source. | — | User: administrator | Administrator | No | — | `bot/cogs/commands/blacklist.py` |
| blacklistword bypass remove | `{prefix}blacklistword bypass remove <target>` | Prefix | No description in source. | target | User: administrator | Administrator | No | — | `bot/cogs/commands/blacklist.py` |
| blacklistword config | `{prefix}blacklistword config` | Prefix | No description in source. | — | User: administrator | Administrator | Yes | — | `bot/cogs/commands/blacklist.py` |
| blacklistword remove | `{prefix}blacklistword remove <word>` | Prefix | No description in source. | word | User: administrator | Administrator | No | — | `bot/cogs/commands/blacklist.py` |
| blacklistword reset | `{prefix}blacklistword reset` | Prefix | No description in source. | — | User: administrator | Administrator | Yes | — | `bot/cogs/commands/blacklist.py` |

## Antinuke

| Command | Syntax | Type | Description | Arguments | Permissions | Who | Setup first? | Aliases | Source |
|---|---|---|---|---|---|---|---|---|---|
| antinuke | `{prefix}antinuke <option>` or `/antinuke` | Hybrid | Enables/Disables Anti-Nuke Module in the server | option | User: administrator | Server Owner or extra owner | This command is the setup step | antiwizz, anti | `bot/cogs/commands/antinuke.py` |
| emergency | `{prefix}emergency` (group) | Prefix | No description in source. | — | None declared | Everyone | No | emg | `bot/cogs/commands/emergency.py` |
| emergency authorise | `{prefix}emergency authorise` (group) | Prefix | No description in source. | — | None declared | Everyone | No | ath | `bot/cogs/commands/emergency.py` |
| emergency authorise add | `{prefix}emergency authorise add <member>` | Prefix | No description in source. | member | Checked in the command body, not with a permission decorator | Server Owner | No | — | `bot/cogs/commands/emergency.py` |
| emergency authorise list | `{prefix}emergency authorise list` | Prefix | No description in source. | — | Checked in the command body, not with a permission decorator | Server Owner | No | view | `bot/cogs/commands/emergency.py` |
| emergency authorise remove | `{prefix}emergency authorise remove <member>` | Prefix | No description in source. | member | Checked in the command body, not with a permission decorator | Server Owner | No | — | `bot/cogs/commands/emergency.py` |
| emergency disable | `{prefix}emergency disable` | Prefix | No description in source. | — | Checked in the command body, not with a permission decorator | Server Owner or bot owner | Yes | — | `bot/cogs/commands/emergency.py` |
| emergency enable | `{prefix}emergency enable` | Prefix | No description in source. | — | Checked in the command body, not with a permission decorator | Server Owner or bot owner | This command is the setup step | — | `bot/cogs/commands/emergency.py` |
| emergency role | `{prefix}emergency role` (group) | Prefix | No description in source. | — | None declared | Everyone | No | — | `bot/cogs/commands/emergency.py` |
| emergency role add | `{prefix}emergency role add <role>` | Prefix | No description in source. | role | Checked in the command body, not with a permission decorator | Server Owner | No | — | `bot/cogs/commands/emergency.py` |
| emergency role list | `{prefix}emergency role list` | Prefix | No description in source. | — | Checked in the command body, not with a permission decorator | Server Owner, emergency authorised user, or bot owner | No | view | `bot/cogs/commands/emergency.py` |
| emergency role remove | `{prefix}emergency role remove <role>` | Prefix | No description in source. | role | Checked in the command body, not with a permission decorator | Server Owner | No | — | `bot/cogs/commands/emergency.py` |
| emergencyrestore | `{prefix}emergencyrestore` | Prefix | No description in source. | — | Bot: manage_roles | Server Owner or bot owner | No | emgrestore | `bot/cogs/commands/emergency.py` |
| emergencysituation | `{prefix}emergencysituation` | Prefix | No description in source. | — | Bot: manage_roles | Server Owner, emergency authorised user, or bot owner | No | emgs | `bot/cogs/commands/emergency.py` |
| extraowner | `{prefix}extraowner <option> <user>` or `/extraowner` | Hybrid | Adds Extraowner to the server | option, user | Checked in the command body, not with a permission decorator | Server Owner or bot owner | No | owner | `bot/cogs/commands/extraown.py` |
| nightmode | `{prefix}nightmode` or `/nightmode` (group) | Hybrid | Manages Nightmode feature | — | None declared | Everyone | No | — | `bot/cogs/commands/nightmode.py` |
| nightmode disable | `{prefix}nightmode disable` or `/nightmode disable` | Hybrid | Disable nightmode | — | User: administrator | Server Owner or extra owner | Yes | — | `bot/cogs/commands/nightmode.py` |
| nightmode enable | `{prefix}nightmode enable` or `/nightmode enable` | Hybrid | Enable nightmode | — | User: administrator | Server Owner or extra owner | This command is the setup step | — | `bot/cogs/commands/nightmode.py` |
| unwhitelist | `{prefix}unwhitelist <member>` or `/unwhitelist` | Hybrid | Unwhitelist a user from antinuke | member | User: administrator | Server Owner or extra owner | No | unwl | `bot/cogs/commands/anti_unwl.py` |
| whitelist | `{prefix}whitelist <member>` or `/whitelist` | Hybrid | Whitelists a user from antinuke for a specific action. | member | User: administrator | Server Owner or extra owner | No | wl | `bot/cogs/commands/anti_wl.py` |
| whitelisted | `{prefix}whitelisted` or `/whitelisted` | Hybrid | Shows the list of whitelisted users. | — | User: administrator | Server Owner or extra owner | No | wlist | `bot/cogs/commands/anti_wl.py` |
| whitelistreset | `{prefix}whitelistreset` or `/whitelistreset` | Hybrid | Resets the whitelisted users. | — | User: administrator | Server Owner or extra owner | No | wlreset | `bot/cogs/commands/anti_wl.py` |

## Tickets

| Command | Syntax | Type | Description | Arguments | Permissions | Who | Setup first? | Aliases | Source |
|---|---|---|---|---|---|---|---|---|---|
| ticket | `{prefix}ticket` or `/ticket` (group) | Hybrid | Main command group for the ticket system. | — | None declared | Everyone | No | — | `bot/cogs/commands/ticket.py` |
| ticket claim | `{prefix}ticket claim` or `/ticket claim` | Hybrid | Claim the ticket to notify others that you are handling it. | — | User: manage_channels | Moderator | Yes | — | `bot/cogs/commands/ticket.py` |
| ticket close | `{prefix}ticket close` or `/ticket close` | Hybrid | Close the current ticket channel. | — | User: manage_channels | Moderator | Yes | — | `bot/cogs/commands/ticket.py` |
| ticket lock | `{prefix}ticket lock` or `/ticket lock` | Hybrid | Lock the ticket, preventing the user from sending messages. | — | User: manage_channels | Moderator | Yes | — | `bot/cogs/commands/ticket.py` |
| ticket setup | `{prefix}ticket setup <style> <channel>` or `/ticket setup` | Hybrid | Start the interactive setup for the ticket panel. | style, channel | User: manage_guild | Moderator | This command is the setup step | — | `bot/cogs/commands/ticket.py` |
| ticket transcript | `{prefix}ticket transcript` or `/ticket transcript` | Hybrid | Generate a transcript of a closed ticket. | — | User: manage_channels | Moderator | Yes | — | `bot/cogs/commands/ticket.py` |
| ticket unlock | `{prefix}ticket unlock` or `/ticket unlock` | Hybrid | Unlock the ticket, allowing the user to send messages again. | — | User: manage_channels | Moderator | Yes | — | `bot/cogs/commands/ticket.py` |

## Verification

| Command | Syntax | Type | Description | Arguments | Permissions | Who | Setup first? | Aliases | Source |
|---|---|---|---|---|---|---|---|---|---|
| verification | `{prefix}verification` or `/verification` (group) | Hybrid | Advanced verification system management. | — | User: administrator | Administrator | This command is the setup step | — | `bot/cogs/commands/verification.py` |
| verification disable | `{prefix}verification disable` or `/verification disable` | Hybrid | Disable the verification system and reset all channel permissions. | — | User: administrator | Administrator | Yes | — | `bot/cogs/commands/verification.py` |
| verification enable | `{prefix}verification enable` or `/verification enable` | Hybrid | Enable the verification system. | — | User: administrator | Administrator | This command is the setup step | — | `bot/cogs/commands/verification.py` |
| verification fix | `{prefix}verification fix` or `/verification fix` | Hybrid | Auto-fix channel permissions for verification system. | — | User: administrator | Administrator | Yes | — | `bot/cogs/commands/verification.py` |
| verification logs | `{prefix}verification logs <limit>` or `/verification logs` | Hybrid | View recent verification logs. | limit | User: administrator | Administrator | Yes | — | `bot/cogs/commands/verification.py` |
| verification reset | `{prefix}verification reset` or `/verification reset` | Hybrid | Reset all channel permissions (remove verification restrictions). | — | User: administrator | Administrator | Yes | — | `bot/cogs/commands/verification.py` |
| verification setup | `{prefix}verification setup` or `/verification setup` | Hybrid | Set up the advanced verification system. | — | User: administrator | Administrator | This command is the setup step | — | `bot/cogs/commands/verification.py` |
| verification status | `{prefix}verification status` or `/verification status` | Hybrid | Check verification system status and analytics. | — | User: administrator | Administrator | Yes | — | `bot/cogs/commands/verification.py` |
| verification verify | `{prefix}verification verify <user>` or `/verification verify` | Hybrid | Manually verify a user (Admin only). | user | User: administrator | Administrator | Yes | — | `bot/cogs/commands/verification.py` |

## Roles

| Command | Syntax | Type | Description | Arguments | Permissions | Who | Setup first? | Aliases | Source |
|---|---|---|---|---|---|---|---|---|---|
| autorole | `{prefix}autorole` (group) | Prefix | No description in source. | — | User: administrator | Administrator | This command is the setup step | — | `bot/cogs/commands/autorole.py` |
| autorole bots | `{prefix}autorole bots` (group) | Prefix | Setup autoroles for bots | — | User: administrator | Administrator | Yes | — | `bot/cogs/commands/autorole.py` |
| autorole bots add | `{prefix}autorole bots add <role>` | Prefix | Add role to bot Autoroles. | role | User: administrator | Administrator | Yes | — | `bot/cogs/commands/autorole.py` |
| autorole bots remove | `{prefix}autorole bots remove <role>` | Prefix | Remove a role from bot Autoroles. | role | User: administrator | Administrator | Yes | — | `bot/cogs/commands/autorole.py` |
| autorole config | `{prefix}autorole config` | Prefix | Shows the current autorole configuration | — | User: administrator | Administrator | Yes | — | `bot/cogs/commands/autorole.py` |
| autorole humans | `{prefix}autorole humans` (group) | Prefix | Setup autoroles for human | — | User: administrator | Administrator | Yes | — | `bot/cogs/commands/autorole.py` |
| autorole humans add | `{prefix}autorole humans add <role>` | Prefix | Add role to list of human Autoroles. | role | User: administrator | Administrator | Yes | — | `bot/cogs/commands/autorole.py` |
| autorole humans remove | `{prefix}autorole humans remove <role>` | Prefix | Remove a role from human Autoroles. | role | User: administrator | Administrator | Yes | — | `bot/cogs/commands/autorole.py` |
| autorole reset | `{prefix}autorole reset` (group) | Prefix | Clear autorole config in the Guild | — | User: administrator | Administrator | Yes | — | `bot/cogs/commands/autorole.py` |
| autorole reset all | `{prefix}autorole reset all` | Prefix | Clear all autorole configuration in the Guild | — | User: administrator | Administrator | Yes | — | `bot/cogs/commands/autorole.py` |
| autorole reset bots | `{prefix}autorole reset bots` | Prefix | Clear autorole configuration for bots | — | User: administrator | Administrator | Yes | — | `bot/cogs/commands/autorole.py` |
| autorole reset humans | `{prefix}autorole reset humans` | Prefix | Clear autorole configuration for humans | — | User: administrator | Administrator | Yes | — | `bot/cogs/commands/autorole.py` |
| createrr | `{prefix}createrr <channel> <message_id> <emoji> <role>` or `/createrr` | Hybrid | Create a reaction role. | channel, message_id, emoji, role | User: manage_roles | Moderator | No | — | `bot/cogs/commands/reactionroles.py` |
| dmrr | `{prefix}dmrr <mode>` or `/dmrr` | Hybrid | Enable or disable DM messages for reaction roles. | mode | User: manage_guild | Moderator | No | — | `bot/cogs/commands/reactionroles.py` |
| friend | `{prefix}friend <member>` or `/friend` | Hybrid | Gives the friend role to the user. | member | None declared | Everyone | No | frnd | `bot/cogs/commands/customrole.py` |
| girl | `{prefix}girl <member>` or `/girl` | Hybrid | Gives the girl role to the user. | member | None declared | Everyone | No | qt | `bot/cogs/commands/customrole.py` |
| guest | `{prefix}guest <member>` or `/guest` | Hybrid | Gives the guest role to the user. | member | None declared | Everyone | No | — | `bot/cogs/commands/customrole.py` |
| setup | `{prefix}setup` or `/setup` (group) | Hybrid | Setups custom roles for the server. | — | User: administrator | Administrator | This command is the setup step | — | `bot/cogs/commands/customrole.py` |
| setup config | `{prefix}setup config` or `/setup config` | Hybrid | Shows the current custom role configuration in the Guild. | — | User: administrator | Administrator | Yes | — | `bot/cogs/commands/customrole.py` |
| setup create | `{prefix}setup create <name> <role>` or `/setup create` | Hybrid | Creates a custom role command | name, role | User: administrator | Administrator | No | — | `bot/cogs/commands/customrole.py` |
| setup delete | `{prefix}setup delete <name>` or `/setup delete` | Hybrid | Deletes a custom role command. | name | User: administrator | Administrator | No | remove | `bot/cogs/commands/customrole.py` |
| setup friend | `{prefix}setup friend <role>` or `/setup friend` | Hybrid | Setup friend role in the Guild | role | User: administrator | Administrator | No | — | `bot/cogs/commands/customrole.py` |
| setup girl | `{prefix}setup girl <role>` or `/setup girl` | Hybrid | Setup girl role in the Guild | role | User: administrator | Administrator | No | — | `bot/cogs/commands/customrole.py` |
| setup guest | `{prefix}setup guest <role>` or `/setup guest` | Hybrid | Setup guest role in the Guild | role | User: administrator | Administrator | No | — | `bot/cogs/commands/customrole.py` |
| setup list | `{prefix}setup list` or `/setup list` | Hybrid | List all the custom roles setup for the server. | — | User: administrator | Administrator | No | — | `bot/cogs/commands/customrole.py` |
| setup reqrole | `{prefix}setup reqrole <role>` or `/setup reqrole` | Hybrid | Setup required role for custom role commands | role | User: administrator | Administrator | No | — | `bot/cogs/commands/customrole.py` |
| setup reset | `{prefix}setup reset` or `/setup reset` | Hybrid | Resets custom role configuration for the server. | — | User: administrator | Administrator | Yes | — | `bot/cogs/commands/customrole.py` |
| setup staff | `{prefix}setup staff <role>` or `/setup staff` | Hybrid | Setup staff role in Guild | role | User: administrator | Administrator | No | — | `bot/cogs/commands/customrole.py` |
| setup vip | `{prefix}setup vip <role>` or `/setup vip` | Hybrid | Setups vip role in the Guild | role | User: administrator | Administrator | No | — | `bot/cogs/commands/customrole.py` |
| staff | `{prefix}staff <member>` or `/staff` | Hybrid | Gives the staff role to the user. | member | None declared | Everyone | No | official | `bot/cogs/commands/customrole.py` |
| vanityroles | `{prefix}vanityroles` (group) | Prefix | No description in source. | — | None declared | Everyone | No | — | `bot/cogs/commands/vanityroles.py` |
| vanityroles reset | `{prefix}vanityroles reset` | Prefix | No description in source. | — | None declared | Everyone | Yes | — | `bot/cogs/commands/vanityroles.py` |
| vanityroles setup | `{prefix}vanityroles setup <vanity> <role> <channel>` | Prefix | No description in source. | vanity, role, channel | None declared | Everyone | This command is the setup step | — | `bot/cogs/commands/vanityroles.py` |
| vanityroles show | `{prefix}vanityroles show` | Prefix | No description in source. | — | None declared | Everyone | No | — | `bot/cogs/commands/vanityroles.py` |
| vcrole | `{prefix}vcrole` (group) | Prefix | Vcrole Setup commands | — | User: administrator | Administrator | No | — | `bot/cogs/commands/Invc.py` |
| vcrole add | `{prefix}vcrole add <role>` | Prefix | Adds a role to the vcrole list | role | User: administrator | Administrator | No | — | `bot/cogs/commands/Invc.py` |
| vcrole config | `{prefix}vcrole config` | Prefix | Shows the Current vcrole in this Guild | — | User: administrator | Administrator | Yes | view, show | `bot/cogs/commands/Invc.py` |
| vcrole remove | `{prefix}vcrole remove <role>` | Prefix | Removes the role from vcrole list | role | User: administrator | Administrator | No | reset | `bot/cogs/commands/Invc.py` |
| vip | `{prefix}vip <member>` or `/vip` | Hybrid | Gives the VIP role to the user. | member | None declared | Everyone | No | — | `bot/cogs/commands/customrole.py` |

## Leveling

| Command | Syntax | Type | Description | Arguments | Permissions | Who | Setup first? | Aliases | Source |
|---|---|---|---|---|---|---|---|---|---|
| level | `{prefix}level` (group) | Prefix | Leveling system | — | None declared | Everyone | No | — | `bot/cogs/commands/leveling.py` |
| level blacklist | `{prefix}level blacklist` (group) | Prefix | Manage leveling blacklists | — | None declared | Everyone | Yes | — | `bot/cogs/commands/leveling.py` |
| level blacklist add | `{prefix}level blacklist add <target_type> <target>` | Prefix | Add to the leveling blacklist | target_type, target | User: administrator | Administrator | Yes | — | `bot/cogs/commands/leveling.py` |
| level blacklist list | `{prefix}level blacklist list` | Prefix | List the leveling blacklist | — | User: administrator | Administrator | Yes | — | `bot/cogs/commands/leveling.py` |
| level blacklist remove | `{prefix}level blacklist remove <target_type> <target>` | Prefix | Remove from the leveling blacklist | target_type, target | User: administrator | Administrator | Yes | — | `bot/cogs/commands/leveling.py` |
| level channel | `{prefix}level channel <channel>` | Prefix | Set the level-up announcement channel | channel | User: administrator | Administrator | Yes | — | `bot/cogs/commands/leveling.py` |
| level cooldown | `{prefix}level cooldown <seconds>` | Prefix | Set message cooldown in seconds | seconds | User: administrator | Administrator | Yes | — | `bot/cogs/commands/leveling.py` |
| level disable | `{prefix}level disable` | Prefix | Disable the leveling system | — | User: administrator | Administrator | Yes | — | `bot/cogs/commands/leveling.py` |
| level enable | `{prefix}level enable` | Prefix | Enable the leveling system | — | User: administrator | Administrator | This command is the setup step | — | `bot/cogs/commands/leveling.py` |
| level leaderboard | `{prefix}level leaderboard` | Prefix | View the server level leaderboard | — | None declared | Everyone | Yes | — | `bot/cogs/commands/leveling.py` |
| level multiplier | `{prefix}level multiplier` (group) | Prefix | Manage XP multipliers | — | None declared | Everyone | Yes | — | `bot/cogs/commands/leveling.py` |
| level multiplier add | `{prefix}level multiplier add <target_type> <target> <multiplier>` | Prefix | Add an XP multiplier | target_type, target, multiplier | User: administrator | Administrator | Yes | — | `bot/cogs/commands/leveling.py` |
| level multiplier list | `{prefix}level multiplier list` | Prefix | List all XP multipliers | — | User: administrator | Administrator | Yes | — | `bot/cogs/commands/leveling.py` |
| level multiplier remove | `{prefix}level multiplier remove <target_type> <target>` | Prefix | Remove an XP multiplier | target_type, target | User: administrator | Administrator | Yes | — | `bot/cogs/commands/leveling.py` |
| level placeholders | `{prefix}level placeholders` | Prefix | Show available placeholders for level-up messages | — | None declared | Everyone | Yes | — | `bot/cogs/commands/leveling.py` |
| level rank | `{prefix}level rank <member>` | Prefix | View your current rank and level | member | None declared | Everyone | Yes | — | `bot/cogs/commands/leveling.py` |
| level rewards | `{prefix}level rewards` (group) | Prefix | Manage level rewards | — | None declared | Everyone | Yes | — | `bot/cogs/commands/leveling.py` |
| level rewards add | `{prefix}level rewards add <level> <role> <remove_previous>` | Prefix | Add a level reward | level, role, remove_previous | User: administrator | Administrator | Yes | — | `bot/cogs/commands/leveling.py` |
| level rewards list | `{prefix}level rewards list` | Prefix | List all level rewards | — | User: administrator | Administrator | Yes | — | `bot/cogs/commands/leveling.py` |
| level rewards remove | `{prefix}level rewards remove <level>` | Prefix | Remove a level reward | level | User: administrator | Administrator | Yes | — | `bot/cogs/commands/leveling.py` |
| level setcolor | `{prefix}level setcolor <color>` | Prefix | Set embed color | color | User: administrator | Administrator | Yes | — | `bot/cogs/commands/leveling.py` |
| level setmessage | `{prefix}level setmessage <message>` | Prefix | Set level-up message | message | User: administrator | Administrator | Yes | — | `bot/cogs/commands/leveling.py` |
| level settings | `{prefix}level settings` | Prefix | Configure leveling settings | — | User: administrator | Administrator | Yes | config | `bot/cogs/commands/leveling.py` |
| level setxp | `{prefix}level setxp <amount>` | Prefix | Set XP amount per message | amount | User: administrator | Administrator | Yes | — | `bot/cogs/commands/leveling.py` |
| level stats | `{prefix}level stats <member>` | Prefix | View detailed level statistics | member | None declared | Everyone | Yes | — | `bot/cogs/commands/leveling.py` |
| level thumbnail | `{prefix}level thumbnail <setting>` | Prefix | Toggle user thumbnail in level-up messages | setting | User: administrator | Administrator | Yes | — | `bot/cogs/commands/leveling.py` |
| listlevelroles | `{prefix}listlevelroles` or `/listlevelroles` | Hybrid | List all level roles (admin only) | — | User: administrator | Administrator | No | — | `bot/cogs/commands/leveling.py` |
| removelevelrole | `{prefix}removelevelrole <level>` or `/removelevelrole` | Hybrid | Remove a level role (admin only) | level | User: administrator | Administrator | No | — | `bot/cogs/commands/leveling.py` |
| resetxp | `{prefix}resetxp <member>` or `/resetxp` | Hybrid | Reset a user's XP (admin only) | member | User: administrator | Administrator | No | — | `bot/cogs/commands/leveling.py` |
| setlevel | `{prefix}setlevel <member> <level>` or `/setlevel` | Hybrid | Set a user's level (admin only) | member, level | User: administrator | Administrator | No | — | `bot/cogs/commands/leveling.py` |
| setlevelrole | `{prefix}setlevelrole <level> <role>` or `/setlevelrole` | Hybrid | Set a role for a specific level (admin only) | level, role | User: administrator | Administrator | No | — | `bot/cogs/commands/leveling.py` |
| setxp | `{prefix}setxp <member> <xp>` or `/setxp` | Hybrid | Set a user's XP (admin only) | member, xp | User: administrator | Administrator | No | — | `bot/cogs/commands/leveling.py` |

## Welcome

| Command | Syntax | Type | Description | Arguments | Permissions | Who | Setup first? | Aliases | Source |
|---|---|---|---|---|---|---|---|---|---|
| boost | `{prefix}boost` (group) | Prefix | Boost message configuration commands | — | User: administrator | Administrator | No | bst | `bot/cogs/commands/booster.py` |
| boost autodel | `{prefix}boost autodel <seconds>` | Prefix | Set auto-delete timer for boost messages (0 to disable) | seconds | User: administrator | Administrator | No | — | `bot/cogs/commands/booster.py` |
| boost channel | `{prefix}boost channel` (group) | Prefix | Manage boost notification channels | — | User: administrator | Administrator | No | — | `bot/cogs/commands/booster.py` |
| boost channel add | `{prefix}boost channel add <channel>` | Prefix | Add a boost notification channel | channel | User: administrator | Administrator | No | — | `bot/cogs/commands/booster.py` |
| boost channel remove | `{prefix}boost channel remove <channel>` | Prefix | Remove a boost notification channel | channel | User: administrator | Administrator | No | — | `bot/cogs/commands/booster.py` |
| boost config | `{prefix}boost config` | Prefix | View current boost configuration | — | User: administrator | Administrator | Yes | — | `bot/cogs/commands/booster.py` |
| boost embed | `{prefix}boost embed` | Prefix | Toggle embed formatting for boost messages | — | User: administrator | Administrator | No | — | `bot/cogs/commands/booster.py` |
| boost image | `{prefix}boost image <image_url>` | Prefix | Set boost message image | image_url | User: administrator | Administrator | No | — | `bot/cogs/commands/booster.py` |
| boost message | `{prefix}boost message` | Prefix | Set boost message content | — | User: administrator | Administrator | No | — | `bot/cogs/commands/booster.py` |
| boost ping | `{prefix}boost ping` | Prefix | Toggle pinging the booster | — | User: administrator | Administrator | No | — | `bot/cogs/commands/booster.py` |
| boost reset | `{prefix}boost reset` | Prefix | Reset boost configuration | — | User: administrator | Administrator | Yes | — | `bot/cogs/commands/booster.py` |
| boost test | `{prefix}boost test` | Prefix | Test how the boost message will look | — | User: administrator | Administrator | Yes | — | `bot/cogs/commands/booster.py` |
| boost thumbnail | `{prefix}boost thumbnail <thumbnail_url>` | Prefix | Set boost message thumbnail | thumbnail_url | User: administrator | Administrator | No | — | `bot/cogs/commands/booster.py` |
| boostrole | `{prefix}boostrole` (group) | Prefix | Manage boost roles | — | User: administrator | Administrator | No | — | `bot/cogs/commands/booster.py` |
| boostrole add | `{prefix}boostrole add <role>` | Prefix | Add a boost role | role | User: administrator | Administrator | No | — | `bot/cogs/commands/booster.py` |
| boostrole config | `{prefix}boostrole config` | Prefix | View boost role configuration | — | User: administrator | Administrator | Yes | — | `bot/cogs/commands/booster.py` |
| boostrole remove | `{prefix}boostrole remove <role>` | Prefix | Remove a boost role | role | User: administrator | Administrator | No | — | `bot/cogs/commands/booster.py` |
| boostrole reset | `{prefix}boostrole reset` | Prefix | Reset boost role configuration | — | User: administrator | Administrator | Yes | — | `bot/cogs/commands/booster.py` |
| fastgreet_add | `{prefix}fastgreet_add <channel>` | Prefix | No description in source. | channel | User: administrator | Administrator | No | — | `bot/cogs/commands/fastgreet.py` |
| fastgreet_list | `{prefix}fastgreet_list` | Prefix | No description in source. | — | None declared | Everyone | No | — | `bot/cogs/commands/fastgreet.py` |
| fastgreet_remove | `{prefix}fastgreet_remove <channel>` | Prefix | No description in source. | channel | User: administrator | Administrator | No | — | `bot/cogs/commands/fastgreet.py` |
| greet | `{prefix}greet` or `/greet` (group) | Hybrid | Shows all the greet commands. | — | None declared | Everyone | No | — | `bot/cogs/commands/welcome.py` |
| greet autodelete | `{prefix}greet autodelete <time>` or `/greet autodelete` | Hybrid | Sets the auto-delete duration for the welcome message. | time | User: administrator | Administrator | Yes | autodel | `bot/cogs/commands/welcome.py` |
| greet channel | `{prefix}greet channel` or `/greet channel` | Hybrid | Sets the channel where welcome messages will be sent. | — | User: administrator | Administrator | Yes | — | `bot/cogs/commands/welcome.py` |
| greet config | `{prefix}greet config` or `/greet config` | Hybrid | Shows the current welcome configuration. | — | User: administrator | Administrator | Yes | — | `bot/cogs/commands/welcome.py` |
| greet edit | `{prefix}greet edit` or `/greet edit` | Hybrid | Edits the current welcome message settings for the server. | — | User: administrator | Administrator | Yes | — | `bot/cogs/commands/welcome.py` |
| greet reset | `{prefix}greet reset` or `/greet reset` | Hybrid | Resets and deletes the current welcome configuration for the server. | — | User: administrator | Administrator | Yes | disable | `bot/cogs/commands/welcome.py` |
| greet setup | `{prefix}greet setup` or `/greet setup` | Hybrid | Configures a welcome message for new members joining the server. | — | User: administrator | Administrator | This command is the setup step | — | `bot/cogs/commands/welcome.py` |
| greet test | `{prefix}greet test` or `/greet test` | Hybrid | Sends a test welcome message to preview the setup. | — | User: administrator | Administrator | Yes | — | `bot/cogs/commands/welcome.py` |
| joindm | `{prefix}joindm` (group) | Prefix | No description in source. | — | User: administrator | Administrator | No | — | `bot/cogs/commands/joindm.py` |
| joindm disable | `{prefix}joindm disable` | Prefix | No description in source. | — | User: administrator | Administrator | Yes | — | `bot/cogs/commands/joindm.py` |
| joindm enable | `{prefix}joindm enable` | Prefix | No description in source. | — | User: administrator | Administrator | This command is the setup step | — | `bot/cogs/commands/joindm.py` |
| joindm message | `{prefix}joindm message <message>` | Prefix | No description in source. | message | User: administrator | Administrator | No | — | `bot/cogs/commands/joindm.py` |
| joindm test | `{prefix}joindm test` | Prefix | No description in source. | — | None declared | Everyone | Yes | — | `bot/cogs/commands/joindm.py` |

## Logging

| Command | Syntax | Type | Description | Arguments | Permissions | Who | Setup first? | Aliases | Source |
|---|---|---|---|---|---|---|---|---|---|
| log | `{prefix}log` or `/log` (group) | Hybrid | Main logging command group. Works with both slash (/) and prefix (!) commands. | — | None declared | Everyone | No | — | `bot/cogs/commands/logging.py` |
| log config | `{prefix}log config` or `/log config` | Hybrid | Open interactive config menu for logging settings. | — | User: manage_guild | Moderator | Yes | — | `bot/cogs/commands/logging.py` |
| log export | `{prefix}log export <days>` or `/log export` | Hybrid | Export log data as a JSON file. | days | User: manage_guild | Moderator | Yes | — | `bot/cogs/commands/logging.py` |
| log ignore | `{prefix}log ignore <action> <target_type> <target>` or `/log ignore` | Hybrid | Manage ignored channels, roles, or users. | action, target_type, target | User: manage_guild | Moderator | Yes | — | `bot/cogs/commands/logging.py` |
| log reset | `{prefix}log reset` or `/log reset` | Hybrid | Reset all logging configuration. | — | User: manage_guild | Moderator | Yes | — | `bot/cogs/commands/logging.py` |
| log search | `{prefix}log search <user> <category> <hours>` or `/log search` | Hybrid | Search through logged events with filters. | user, category, hours | User: manage_guild | Moderator | Yes | — | `bot/cogs/commands/logging.py` |
| log setup | `{prefix}log setup` or `/log setup` | Hybrid | Run the interactive setup for logging channels. | — | User: manage_guild | Moderator | This command is the setup step | — | `bot/cogs/commands/logging.py` |
| log status | `{prefix}log status` or `/log status` | Hybrid | View the current logging configuration. | — | User: manage_guild | Moderator | Yes | — | `bot/cogs/commands/logging.py` |
| log test | `{prefix}log test <category>` or `/log test` | Hybrid | Send test log messages to configured channels. | category | User: manage_guild | Moderator | Yes | — | `bot/cogs/commands/logging.py` |
| log toggle | `{prefix}log toggle <category> <enabled>` or `/log toggle` | Hybrid | Enable or disable specific logging categories. | category, enabled | User: manage_guild | Moderator | Yes | — | `bot/cogs/commands/logging.py` |

## Music / Voice

| Command | Syntax | Type | Description | Arguments | Permissions | Who | Setup first? | Aliases | Source |
|---|---|---|---|---|---|---|---|---|---|
| autoplay | `{prefix}autoplay` | Prefix | Toggles autoplay mode. | — | None declared | Everyone | No | — | `bot/cogs/commands/music.py` |
| clearqueue | `{prefix}clearqueue` | Prefix | Clears the queue. | — | None declared | Everyone | No | — | `bot/cogs/commands/music.py` |
| disconnect | `{prefix}disconnect` or `/disconnect` | Hybrid | Disconnects the bot from the voice channel. | — | None declared | Everyone | No | dc, leave | `bot/cogs/commands/music.py` |
| filter | `{prefix}filter` or `/filter` (group) | Hybrid | No description in source. | — | None declared | Everyone | No | — | `bot/cogs/commands/filters.py` |
| filter disable | `{prefix}filter disable` or `/filter disable` | Hybrid | Disable the current filter. | — | None declared | Everyone | Yes | — | `bot/cogs/commands/filters.py` |
| filter enable | `{prefix}filter enable` or `/filter enable` | Hybrid | Enable a filter. | — | None declared | Everyone | This command is the setup step | — | `bot/cogs/commands/filters.py` |
| j2creset | `{prefix}j2creset` | Prefix | No description in source. | — | User: administrator | Administrator | No | — | `bot/cogs/commands/j2c.py` |
| j2csetup | `{prefix}j2csetup` | Prefix | No description in source. | — | User: administrator | Administrator | No | — | `bot/cogs/commands/j2c.py` |
| join | `{prefix}join` | Prefix | Joins the voice channel. | — | None declared | Everyone | No | connect | `bot/cogs/commands/music.py` |
| loop | `{prefix}loop` | Prefix | Toggles loop mode. | — | None declared | Everyone | No | — | `bot/cogs/commands/music.py` |
| nowplaying | `{prefix}nowplaying` | Prefix | Shows the info about current playing song. | — | None declared | Everyone | No | nop | `bot/cogs/commands/music.py` |
| pause | `{prefix}pause` | Prefix | Pauses the current song. | — | None declared | Everyone | No | — | `bot/cogs/commands/music.py` |
| play | `{prefix}play <query>` | Prefix | Plays a song or playlist. | query | None declared | Everyone | No | p | `bot/cogs/commands/music.py` |
| queue | `{prefix}queue` | Prefix | Shows the current queue. | — | None declared | Everyone | No | — | `bot/cogs/commands/music.py` |
| replay | `{prefix}replay` | Prefix | Replays the current song. | — | None declared | Everyone | No | — | `bot/cogs/commands/music.py` |
| resume | `{prefix}resume` | Prefix | Resumes the paused song. | — | None declared | Everyone | No | — | `bot/cogs/commands/music.py` |
| search | `{prefix}search <query>` | Prefix | Searches music from multiple platforms. | query | None declared | Everyone | No | — | `bot/cogs/commands/music.py` |
| seek | `{prefix}seek <percentage>` | Prefix | Seeks to a specific percentage of the song. | percentage | None declared | Everyone | No | — | `bot/cogs/commands/music.py` |
| shuffle | `{prefix}shuffle` | Prefix | Shuffles the queue. | — | None declared | Everyone | No | — | `bot/cogs/commands/music.py` |
| skip | `{prefix}skip` | Prefix | Skips the current song. | — | None declared | Everyone | No | — | `bot/cogs/commands/music.py` |
| stop | `{prefix}stop` | Prefix | Stops the current song and clears the queue. | — | None declared | Everyone | No | — | `bot/cogs/commands/music.py` |
| voice | `{prefix}voice` (group) | Prefix | No description in source. | — | None declared | Everyone | No | vc | `bot/cogs/commands/voice.py` |
| voice deafen | `{prefix}voice deafen <member>` | Prefix | Deafen a user in a voice channel. | member | User: deafen_members | Everyone | No | — | `bot/cogs/commands/voice.py` |
| voice deafenall | `{prefix}voice deafenall` | Prefix | Deafen all Ussr in a voice channel. | — | User: administrator | Administrator | No | — | `bot/cogs/commands/voice.py` |
| voice kick | `{prefix}voice kick <member>` | Prefix | Removes a user from the voice channel. | member | User: administrator | Administrator | No | — | `bot/cogs/commands/voice.py` |
| voice kickall | `{prefix}voice kickall` | Prefix | Disconnect all members from the voice channel. | — | User: administrator | Administrator | No | — | `bot/cogs/commands/voice.py` |
| voice lock | `{prefix}voice lock` | Prefix | Locks the voice channel so no one can join. | — | User: manage_roles; Bot: manage_roles | Moderator | No | — | `bot/cogs/commands/voice.py` |
| voice move | `{prefix}voice move <member> <channel>` | Prefix | Move a member from one voice channel to another. | member, channel | User: administrator | Administrator | No | — | `bot/cogs/commands/voice.py` |
| voice moveall | `{prefix}voice moveall <channel>` | Prefix | Move all members from the voice channel to the specified voice channel. | channel | User: administrator | Administrator | No | — | `bot/cogs/commands/voice.py` |
| voice mute | `{prefix}voice mute <member>` | Prefix | mute a member in voice channel . | member | User: mute_members | Everyone | No | — | `bot/cogs/commands/voice.py` |
| voice muteall | `{prefix}voice muteall` | Prefix | Mute all members in a voice channel. | — | User: administrator | Administrator | No | — | `bot/cogs/commands/voice.py` |
| voice private | `{prefix}voice private` | Prefix | Makes the voice channel private. | — | User: manage_roles; Bot: manage_roles | Moderator | No | — | `bot/cogs/commands/voice.py` |
| voice pull | `{prefix}voice pull <member>` | Prefix | Pull a member from one voice channel to yours. | member | User: administrator | Administrator | No | — | `bot/cogs/commands/voice.py` |
| voice pullall | `{prefix}voice pullall <channel>` | Prefix | Move all members of ALL voice channels to a specified voice channel. | channel | User: administrator | Administrator | No | — | `bot/cogs/commands/voice.py` |
| voice undeafen | `{prefix}voice undeafen <member>` | Prefix | Undeafen a User in a voice channel . | member | User: deafen_members | Everyone | No | — | `bot/cogs/commands/voice.py` |
| voice undeafenall | `{prefix}voice undeafenall` | Prefix | undeafen all member in a voice channel . | — | User: administrator | Administrator | No | — | `bot/cogs/commands/voice.py` |
| voice unlock | `{prefix}voice unlock` | Prefix | Unlocks the voice channel so anyone can join. | — | User: manage_roles; Bot: manage_roles | Moderator | No | — | `bot/cogs/commands/voice.py` |
| voice unmute | `{prefix}voice unmute <member>` | Prefix | Unmute a member in the voice channel. | member | User: mute_members | Everyone | No | — | `bot/cogs/commands/voice.py` |
| voice unmuteall | `{prefix}voice unmuteall` | Prefix | Unmute all members in a voice channel. | — | User: administrator | Administrator | No | — | `bot/cogs/commands/voice.py` |
| voice unprivate | `{prefix}voice unprivate` | Prefix | Makes the voice channel public. | — | User: manage_roles; Bot: manage_roles | Moderator | No | — | `bot/cogs/commands/voice.py` |
| volume | `{prefix}volume <level>` | Prefix | Sets the volume of the player. | level | None declared | Everyone | No | vol | `bot/cogs/commands/music.py` |

## Games

| Command | Syntax | Type | Description | Arguments | Permissions | Who | Setup first? | Aliases | Source |
|---|---|---|---|---|---|---|---|---|---|
| 2048 | `{prefix}2048` or `/2048` | Hybrid | Play 2048 game with bot. | — | None declared | Everyone | No | twenty48 | `bot/cogs/commands/Games.py` |
| battleship | `{prefix}battleship <player>` or `/battleship` | Hybrid | Play battleship game with your friend. | player | None declared | Everyone | No | battle-ship | `bot/cogs/commands/Games.py` |
| blackjack | `{prefix}blackjack` | Prefix | Play a simple game of blackjack. | — | None declared | Everyone | No | bj, blackjacks | `bot/cogs/commands/blackjack.py` |
| chess | `{prefix}chess <player>` or `/chess` | Hybrid | Play Chess with a user. | player | None declared | Everyone | No | — | `bot/cogs/commands/Games.py` |
| connectfour | `{prefix}connectfour <player>` or `/connectfour` | Hybrid | Play Connect Four game with user. | player | None declared | Everyone | No | c4, connect-four, connect4 | `bot/cogs/commands/Games.py` |
| counting | `{prefix}counting` (group) | Prefix | No description in source. | — | None declared | Everyone | No | — | `bot/cogs/commands/counting.py` |
| counting channel | `{prefix}counting channel <channel>` | Prefix | No description in source. | channel | User: manage_channels | Moderator | No | — | `bot/cogs/commands/counting.py` |
| counting config | `{prefix}counting config <mode>` | Prefix | No description in source. | mode | User: manage_channels | Moderator | Yes | — | `bot/cogs/commands/counting.py` |
| counting disable | `{prefix}counting disable` | Prefix | No description in source. | — | User: manage_channels | Moderator | Yes | — | `bot/cogs/commands/counting.py` |
| counting enable | `{prefix}counting enable` | Prefix | No description in source. | — | User: manage_channels | Moderator | This command is the setup step | — | `bot/cogs/commands/counting.py` |
| counting reset | `{prefix}counting reset` | Prefix | No description in source. | — | User: manage_channels | Moderator | Yes | — | `bot/cogs/commands/counting.py` |
| counting stats | `{prefix}counting stats` | Prefix | No description in source. | — | None declared | Everyone | No | — | `bot/cogs/commands/counting.py` |
| country-guesser | `{prefix}country-guesser` (group) | Prefix | Guess name of the country by flag. | — | None declared | Everyone | No | guess, guesser, countryguesser | `bot/cogs/commands/Games.py` |
| country-guesser start | `{prefix}country-guesser start` | Prefix | Starts the country guesser game. It's a 100 Seconds Game so suggested to play in a SPECIFIC CHANNEL. | — | None declared | Everyone | No | — | `bot/cogs/commands/Games.py` |
| lights-out | `{prefix}lights-out` or `/lights-out` | Hybrid | Play Lights Show game with bot. | — | None declared | Everyone | No | lightsout | `bot/cogs/commands/Games.py` |
| memory-game | `{prefix}memory-game` or `/memory-game` | Hybrid | How strong is your memory? | — | None declared | Everyone | No | memory | `bot/cogs/commands/Games.py` |
| number-slider | `{prefix}number-slider` or `/number-slider` | Hybrid | slide numbers with bot | — | None declared | Everyone | No | slider | `bot/cogs/commands/Games.py` |
| reaction | `{prefix}reaction` | Prefix | See how fast you can react to the correct emoji. | — | None declared | Everyone | No | — | `bot/CodeX.py` |
| rps | `{prefix}rps <player>` or `/rps` | Hybrid | Play Rock Paper Scissor with bot/user. | player | None declared | Everyone | No | rockpaperscissors | `bot/cogs/commands/Games.py` |
| slots | `{prefix}slots` | Prefix | No description in source. | — | None declared | Everyone | No | slot | `bot/cogs/commands/slots.py` |
| tic-tac-toe | `{prefix}tic-tac-toe <player>` or `/tic-tac-toe` | Hybrid | play tic-tac-toe game with a user. | player | None declared | Everyone | No | ttt, tictactoe | `bot/cogs/commands/Games.py` |
| wordle | `{prefix}wordle` or `/wordle` | Hybrid | Wordle Game / Play with bot. | — | None declared | Everyone | No | — | `bot/cogs/commands/Games.py` |

## Fun

| Command | Syntax | Type | Description | Arguments | Permissions | Who | Setup first? | Aliases | Source |
|---|---|---|---|---|---|---|---|---|---|
| 8ball | `{prefix}8ball <question>` | Prefix | No description in source. | question | None declared | Everyone | No | — | `bot/cogs/commands/fun.py` |
| anime | `{prefix}anime` | Prefix | No description in source. | — | None declared | Everyone | No | — | `bot/cogs/commands/image.py` |
| boy | `{prefix}boy` | Prefix | No description in source. | — | None declared | Everyone | No | — | `bot/cogs/commands/image.py` |
| brainrate | `{prefix}brainrate <user>` | Prefix | No description in source. | user | None declared | Everyone | No | — | `bot/cogs/commands/fun.py` |
| coinflip | `{prefix}coinflip` | Prefix | No description in source. | — | None declared | Everyone | No | — | `bot/cogs/commands/fun.py` |
| couple | `{prefix}couple` | Prefix | No description in source. | — | None declared | Everyone | No | — | `bot/cogs/commands/image.py` |
| dice | `{prefix}dice` | Prefix | No description in source. | — | None declared | Everyone | No | — | `bot/cogs/commands/fun.py` |
| dumb | `{prefix}dumb <user>` | Prefix | No description in source. | user | None declared | Everyone | No | — | `bot/cogs/commands/fun.py` |
| enlarge | `{prefix}enlarge <emoji>` | Prefix | No description in source. | emoji | None declared | Everyone | No | — | `bot/cogs/moderation/moderation.py` |
| gend | `{prefix}gend <message_id>` or `/gend` | Hybrid | Ends a giveaway before its ending time. | message_id | User: manage_guild | Moderator | No | — | `bot/cogs/commands/giveaway.py` |
| genius | `{prefix}genius <user>` | Prefix | No description in source. | user | None declared | Everyone | No | — | `bot/cogs/commands/fun.py` |
| glist | `{prefix}glist` or `/glist` | Hybrid | Lists all ongoing giveaways. | — | User: manage_guild | Moderator | No | — | `bot/cogs/commands/giveaway.py` |
| greroll | `{prefix}greroll <message_id>` or `/greroll` | Hybrid | Rerolls a giveaway on replying the giveaway message. | message_id | User: manage_guild | Moderator | No | — | `bot/cogs/commands/giveaway.py` |
| gstart | `{prefix}gstart <time> <winners> <prize>` or `/gstart` | Hybrid | Starts a new giveaway. | time, winners, prize | User: manage_guild | Moderator | No | — | `bot/cogs/commands/giveaway.py` |
| hack | `{prefix}hack <member>` | Prefix | hack someone's discord account | member | None declared | Everyone | No | — | `bot/cogs/commands/general.py` |
| hash | `{prefix}hash <algorithm> <message>` | Prefix | Hashes provided text with provided algorithm | algorithm, message | None declared | Everyone | No | — | `bot/cogs/commands/general.py` |
| howhot | `{prefix}howhot <user>` | Prefix | No description in source. | user | None declared | Everyone | No | — | `bot/cogs/commands/fun.py` |
| hug | `{prefix}hug <user>` | Prefix | No description in source. | user | None declared | Everyone | No | — | `bot/cogs/commands/fun.py` |
| intelligence | `{prefix}intelligence <user>` | Prefix | No description in source. | user | None declared | Everyone | No | — | `bot/cogs/commands/fun.py` |
| iq | `{prefix}iq <user>` | Prefix | No description in source. | user | None declared | Everyone | No | — | `bot/cogs/commands/fun.py` |
| kiss | `{prefix}kiss <user>` | Prefix | No description in source. | user | None declared | Everyone | No | — | `bot/cogs/commands/fun.py` |
| nitro | `{prefix}nitro` | Prefix | No description in source. | — | None declared | Everyone | No | — | `bot/cogs/commands/nitro.py` |
| pat | `{prefix}pat <user>` | Prefix | No description in source. | user | None declared | Everyone | No | — | `bot/cogs/commands/fun.py` |
| rickroll | `{prefix}rickroll <url>` | Prefix | Detects if provided url is a rick-roll | url | None declared | Everyone | No | — | `bot/cogs/commands/general.py` |
| roast | `{prefix}roast <user>` | Prefix | No description in source. | user | None declared | Everyone | No | — | `bot/cogs/commands/fun.py` |
| shipp | `{prefix}shipp <user1> <user2>` | Prefix | No description in source. | user1, user2 | None declared | Everyone | No | — | `bot/cogs/commands/fun.py` |
| simprate | `{prefix}simprate <user>` | Prefix | No description in source. | user | None declared | Everyone | No | — | `bot/cogs/commands/fun.py` |
| slap | `{prefix}slap <user>` | Prefix | No description in source. | user | None declared | Everyone | No | — | `bot/cogs/commands/fun.py` |
| spotify | `{prefix}spotify <user>` | Prefix | Shows what a user is listening to on Spotify. | user | None declared | Everyone | No | — | `bot/CodeX.py` |
| tickle | `{prefix}tickle <user>` | Prefix | No description in source. | user | None declared | Everyone | No | — | `bot/cogs/commands/fun.py` |
| token | `{prefix}token <user>` | Prefix | No description in source. | user | None declared | Everyone | No | — | `bot/cogs/commands/general.py` |
| toxic | `{prefix}toxic <user>` | Prefix | No description in source. | user | None declared | Everyone | No | — | `bot/cogs/commands/fun.py` |
| urban | `{prefix}urban <phrase>` or `/urban` | Hybrid | Get meaning of specified phrase | phrase | None declared | Everyone | No | — | `bot/cogs/commands/general.py` |
| wizz | `{prefix}wizz` | Prefix | No description in source. | — | None declared | Everyone | No | — | `bot/cogs/commands/general.py` |
| yt | `{prefix}yt <search_query>` | Prefix | No description in source. | search_query | None declared | Everyone | No | youtube | `bot/cogs/commands/youtube.py` |

## Utility

| Command | Syntax | Type | Description | Arguments | Permissions | Who | Setup first? | Aliases | Source |
|---|---|---|---|---|---|---|---|---|---|
| calculator | `{prefix}calculator` | Prefix | Starts a calculator session | — | None declared | Everyone | No | calc, calculate, math | `bot/cogs/commands/calc.py` |
| create_hook | `{prefix}create_hook` | Prefix | Creates a webhook in the current channel. | — | User: administrator | Administrator | No | makehook | `bot/CodeX.py` |
| decode | `{prefix}decode` (group) | Prefix | All decode methods | — | None declared | Everyone | No | — | `bot/cogs/commands/encryption.py` |
| decode ascii85 | `{prefix}decode ascii85 <txtinput>` | Prefix | Decode in ASCII85 | txtinput | None declared | Everyone | No | a85 | `bot/cogs/commands/encryption.py` |
| decode base32 | `{prefix}decode base32 <txtinput>` | Prefix | Decode in base32 | txtinput | None declared | Everyone | No | b32 | `bot/cogs/commands/encryption.py` |
| decode base64 | `{prefix}decode base64 <txtinput>` | Prefix | Decode in base64 | txtinput | None declared | Everyone | No | b64 | `bot/cogs/commands/encryption.py` |
| decode base85 | `{prefix}decode base85 <txtinput>` | Prefix | Decode in base85 | txtinput | None declared | Everyone | No | b85 | `bot/cogs/commands/encryption.py` |
| decode hex | `{prefix}decode hex <txtinput>` | Prefix | Decode in hex | txtinput | None declared | Everyone | No | — | `bot/cogs/commands/encryption.py` |
| decode rot13 | `{prefix}decode rot13 <txtinput>` | Prefix | Decode in rot13 | txtinput | None declared | Everyone | No | r13 | `bot/cogs/commands/encryption.py` |
| delete_hook | `{prefix}delete_hook <webhook_url>` | Prefix | Deletes a webhook using its URL. | webhook_url | User: administrator | Administrator | No | delhook | `bot/CodeX.py` |
| embed | `{prefix}embed` or `/embed` | Hybrid | No description in source. | — | User: manage_messages | Moderator | No | — | `bot/cogs/commands/Embed.py` |
| encode | `{prefix}encode` (group) | Prefix | All encode methods | — | None declared | Everyone | No | — | `bot/cogs/commands/encryption.py` |
| encode ascii85 | `{prefix}encode ascii85 <txtinput>` | Prefix | Encode in ASCII85 | txtinput | None declared | Everyone | No | a85 | `bot/cogs/commands/encryption.py` |
| encode base32 | `{prefix}encode base32 <txtinput>` | Prefix | Encode in base32 | txtinput | None declared | Everyone | No | b32 | `bot/cogs/commands/encryption.py` |
| encode base64 | `{prefix}encode base64 <txtinput>` | Prefix | Encode in base64 | txtinput | None declared | Everyone | No | b64 | `bot/cogs/commands/encryption.py` |
| encode base85 | `{prefix}encode base85 <txtinput>` | Prefix | Encode in base85 | txtinput | None declared | Everyone | No | b85 | `bot/cogs/commands/encryption.py` |
| encode hex | `{prefix}encode hex <txtinput>` | Prefix | Encode in hex | txtinput | None declared | Everyone | No | — | `bot/cogs/commands/encryption.py` |
| encode rot13 | `{prefix}encode rot13 <txtinput>` | Prefix | Encode in rot13 | txtinput | None declared | Everyone | No | r13 | `bot/cogs/commands/encryption.py` |
| hinglish | `{prefix}hinglish <text>` or `/hinglish` | Hybrid | Translate informal Hinglish to proper English. | text | None declared | Everyone | No | — | `bot/cogs/commands/translate.py` |
| list_hooks | `{prefix}list_hooks` | Prefix | Lists all webhooks in the current channel. | — | User: administrator | Administrator | No | hooks | `bot/CodeX.py` |
| messages | `{prefix}messages <member>` | Prefix | No description in source. | member | None declared | Everyone | No | msg | `bot/cogs/commands/messages.py` |
| minecraft reset | `/minecraft reset` | Slash | Remove the Minecraft server status setup. | — | User: manage_guild | Moderator | Yes | — | `bot/cogs/commands/minecraft.py` |
| minecraft setup | `/minecraft setup` | Slash | Set up the auto-updating Minecraft server status. | — | User: manage_guild | Moderator | This command is the setup step | — | `bot/cogs/commands/minecraft.py` |
| minecraft status | `/minecraft status` | Slash | Get a one-time status of the configured server. | — | None declared | Everyone | Yes | — | `bot/cogs/commands/minecraft.py` |
| password | `{prefix}password` | Prefix | Generates a random secure password for you | — | None declared | Everyone | No | — | `bot/cogs/commands/encryption.py` |
| qr | `{prefix}qr` | Prefix | Sends a QR code image. | — | User: administrator | Administrator | No | qrcode | `bot/cogs/commands/qr.py` |
| setnotif | `{prefix}setnotif` (group) | Prefix | No description in source. | — | None declared | Everyone | No | — | `bot/cogs/commands/notify.py` |
| setnotif list | `{prefix}setnotif list` | Prefix | No description in source. | — | None declared | Everyone | No | — | `bot/cogs/commands/notify.py` |
| setnotif reset | `{prefix}setnotif reset` | Prefix | No description in source. | — | None declared | Everyone | Yes | — | `bot/cogs/commands/notify.py` |
| setnotif twitch | `{prefix}setnotif twitch <role> <channel>` | Prefix | No description in source. | role, channel | User: administrator | Administrator | No | — | `bot/cogs/commands/notify.py` |
| setnotif youtube | `{prefix}setnotif youtube <role> <channel>` | Prefix | No description in source. | role, channel | User: administrator | Administrator | No | — | `bot/cogs/commands/notify.py` |
| steal | `{prefix}steal <emote>` or `/steal` | Hybrid | Steal an emoji or sticker | emote | User: manage_emojis | Moderator | No | eadd | `bot/cogs/commands/steal.py` |
| timer | `{prefix}timer <times> <title>` or `/timer` | Hybrid | Starts a timer | times, title | None declared | Everyone | No | tstart | `bot/cogs/commands/timer.py` |

## Owner / Developer

| Command | Syntax | Type | Description | Arguments | Permissions | Who | Setup first? | Aliases | Source |
|---|---|---|---|---|---|---|---|---|---|
| autonp | `{prefix}autonp` (group) | Prefix | Manage auto no-prefix for partner guilds. | — | Bot owner check | Bot Owner | No | — | `bot/cogs/commands/np.py` |
| autonp guild | `{prefix}autonp guild` (group) | Prefix | Manage partner guilds for auto no-prefix. | — | None declared | Everyone | No | — | `bot/cogs/commands/np.py` |
| autonp guild add | `{prefix}autonp guild add <guild_id>` | Prefix | Add a guild to auto no-prefix. | guild_id | None declared | Everyone | No | — | `bot/cogs/commands/np.py` |
| autonp guild list | `{prefix}autonp guild list` | Prefix | List all guilds with auto no-prefix. | — | Bot owner or staff-list check | Bot Owner or staff list | No | — | `bot/cogs/commands/np.py` |
| autonp guild remove | `{prefix}autonp guild remove <guild_id>` | Prefix | Remove a guild from auto no-prefix. | guild_id | None declared | Everyone | No | — | `bot/cogs/commands/np.py` |
| bdg | `{prefix}bdg` (group) | Prefix | No description in source. | — | Bot owner or staff-list check | Bot Owner or staff list | No | — | `bot/cogs/commands/owner.py` |
| bdg add | `{prefix}bdg add <member> <badge>` | Prefix | No description in source. | member, badge | Bot owner or staff-list check | Bot Owner or staff list | No | — | `bot/cogs/commands/owner.py` |
| bdg remove | `{prefix}bdg remove <member> <badge>` | Prefix | No description in source. | member, badge | Bot owner or staff-list check | Bot Owner or staff list | No | — | `bot/cogs/commands/owner.py` |
| blacklist | `{prefix}blacklist` (group) | Prefix | No description in source. | — | Bot owner check | Bot Owner | No | bl | `bot/cogs/commands/block.py` |
| blacklist guild | `{prefix}blacklist guild` (group) | Prefix | Add/Remove a guild to the blacklist. | — | Bot owner check | Bot Owner | No | — | `bot/cogs/commands/block.py` |
| blacklist guild add | `{prefix}blacklist guild add <guild_id>` | Prefix | Adds a guild to the blacklist. | guild_id | Bot owner check | Bot Owner | No | — | `bot/cogs/commands/block.py` |
| blacklist guild remove | `{prefix}blacklist guild remove <guild_id>` | Prefix | Remove a guild from the blacklist. | guild_id | Bot owner check | Bot Owner | No | — | `bot/cogs/commands/block.py` |
| blacklist guild show | `{prefix}blacklist guild show` | Prefix | Shows the list of blacklisted guilds | — | Bot owner check | Bot Owner | No | list | `bot/cogs/commands/block.py` |
| blacklist user | `{prefix}blacklist user` (group) | Prefix | Add/Remove a user to the blacklist. | — | Bot owner check | Bot Owner | No | — | `bot/cogs/commands/block.py` |
| blacklist user add | `{prefix}blacklist user add <user>` | Prefix | Adds a user to the blacklist. | user | Bot owner check | Bot Owner | No | — | `bot/cogs/commands/block.py` |
| blacklist user remove | `{prefix}blacklist user remove <user>` | Prefix | Remove a user from the blacklist. | user | Bot owner check | Bot Owner | No | — | `bot/cogs/commands/block.py` |
| blacklist user show | `{prefix}blacklist user show` | Prefix | Shows all Blacklisted users. | — | Bot owner check | Bot Owner | No | list | `bot/cogs/commands/block.py` |
| change | `{prefix}change` (group) | Prefix | No description in source. | — | Bot owner check | Bot Owner | No | — | `bot/cogs/commands/owner.py` |
| change nickname | `{prefix}change nickname <name>` | Prefix | Change nickname. | name | Bot owner check | Bot Owner | No | — | `bot/cogs/commands/owner.py` |
| dm | `{prefix}dm <user> <message>` | Prefix | DM the user of your choice | user, message | Bot owner check | Bot Owner | No | — | `bot/cogs/commands/owner.py` |
| dmstaff | `{prefix}dmstaff <member> <message>` | Prefix | No description in source. | member, message | None declared | Everyone | No | — | `bot/cogs/commands/dms.py` |
| forcepurgebots | `{prefix}forcepurgebots <prefix> <search>` | Prefix | Clear recently bot messages in channel (Bot owner only) | prefix, search | Bot: manage_messages; Bot owner check | Bot Owner | No | fpb | `bot/cogs/commands/owner.py` |
| forcepurgeuser | `{prefix}forcepurgeuser <member> <search>` | Prefix | Clear recent messages of a user in channel (Bot owner only) | member, search | Bot: manage_messages; Bot owner check | Bot Owner | No | fpu | `bot/cogs/commands/owner.py` |
| freezenick | `{prefix}freezenick <member> <nickname>` | Prefix | Freezes a member's nickname in the current server. | member, nickname | User: manage_nicknames | Moderator | No | — | `bot/cogs/commands/owner2.py` |
| GB | `{prefix}GB <user> <reason>` | Prefix | Bans the user from all mutual guilds. | user, reason | Bot owner check | Bot Owner | No | — | `bot/cogs/commands/owner2.py` |
| getinvite | `{prefix}getinvite <guild>` | Prefix | No description in source. | guild | Bot owner check | Bot Owner | No | gi, guildinvite | `bot/cogs/commands/owner.py` |
| global | `{prefix}global` (group) | Prefix | No description in source. | — | Bot owner check | Bot Owner | No | — | `bot/cogs/commands/owner2.py` |
| global clearnick | `{prefix}global clearnick <user>` | Prefix | Clears the nickname of a user in all mutual guilds. | user | Bot owner check | Bot Owner | No | — | `bot/cogs/commands/owner2.py` |
| global freezenick | `{prefix}global freezenick <user> <name>` | Prefix | Freezes a user's nickname in all mutual guilds. | user, name | Bot owner check | Bot Owner | No | — | `bot/cogs/commands/owner2.py` |
| global kick | `{prefix}global kick <user> <reason>` | Prefix | Kicks the user from all mutual guilds. | user, reason | Bot owner check | Bot Owner | No | — | `bot/cogs/commands/owner2.py` |
| global nick | `{prefix}global nick <user> <name>` | Prefix | Changes the nickname of a user in all mutual guilds. | user, name | Bot owner check | Bot Owner | No | — | `bot/cogs/commands/owner2.py` |
| global timeout | `{prefix}global timeout <user> <reason>` | Prefix | Timeouts the user for 28 days in all mutual guilds. | user, reason | Bot owner check | Bot Owner | No | — | `bot/cogs/commands/owner2.py` |
| global unfreezenick | `{prefix}global unfreezenick <user>` | Prefix | Unfreezes a user's nickname in all mutual guilds. | user | Bot owner check | Bot Owner | No | — | `bot/cogs/commands/owner2.py` |
| globalunban | `{prefix}globalunban <user>` | Prefix | No description in source. | user | Bot owner check | Bot Owner | No | — | `bot/cogs/commands/owner.py` |
| guildban | `{prefix}guildban <guild_id> <user_id> <reason>` | Prefix | No description in source. | guild_id, user_id, reason | Bot owner check | Bot Owner | No | — | `bot/cogs/commands/owner.py` |
| guildinfo | `{prefix}guildinfo <guild_id>` | Prefix | No description in source. | guild_id | Bot owner or staff-list check | Bot Owner or staff list | No | — | `bot/cogs/commands/owner.py` |
| guildunban | `{prefix}guildunban <guild_id> <user_id> <reason>` | Prefix | No description in source. | guild_id, user_id, reason | Bot owner check | Bot Owner | No | — | `bot/cogs/commands/owner.py` |
| leaveguild | `{prefix}leaveguild <guild_id>` | Prefix | No description in source. | guild_id | Bot owner check | Bot Owner | No | leavesv | `bot/cogs/commands/owner.py` |
| makeinvite | `{prefix}makeinvite <guild_id>` | Prefix | Creates an invite for a specified server (owner only). | guild_id | Bot owner check | Bot Owner | No | createinvite, makeinv | `bot/CodeX.py` |
| mutuals | `{prefix}mutuals <user>` | Prefix | No description in source. | user | Bot owner check | Bot Owner | No | mutual | `bot/cogs/commands/owner.py` |
| np | `{prefix}np` (group) | Prefix | Allows you to add someone to the no-prefix list (owner-only command) | — | Bot owner or staff-list check | Bot Owner or staff list | No | — | `bot/cogs/commands/np.py` |
| np add | `{prefix}np add <user>` | Prefix | Add user to no-prefix with time options | user | Bot owner or staff-list check | Bot Owner or staff list | No | — | `bot/cogs/commands/np.py` |
| np list | `{prefix}np list` | Prefix | List of no-prefix users | — | Bot owner or staff-list check | Bot Owner or staff list | No | — | `bot/cogs/commands/np.py` |
| np remove | `{prefix}np remove <user>` | Prefix | Remove user from no-prefix | user | Bot owner or staff-list check | Bot Owner or staff list | No | — | `bot/cogs/commands/np.py` |
| np reset | `{prefix}np reset` | Prefix | Reset/clear all users from the no-prefix list | — | Bot owner check | Bot Owner | Yes | — | `bot/cogs/commands/np.py` |
| np status | `{prefix}np status <user>` | Prefix | Check if a user is in the No Prefix list and show details. | user | Bot owner or staff-list check | Bot Owner or staff list | Yes | — | `bot/cogs/commands/np.py` |
| ownerban | `{prefix}ownerban <user_id> <reason>` | Prefix | No description in source. | user_id, reason | Bot owner check | Bot Owner | No | forceban, dna | `bot/cogs/commands/owner.py` |
| owners | `{prefix}owners` | Prefix | No description in source. | — | Bot owner check | Bot Owner | No | — | `bot/cogs/commands/owner.py` |
| ownerunban | `{prefix}ownerunban <user_id> <reason>` | Prefix | No description in source. | user_id, reason | Bot owner check | Bot Owner | No | forceunban | `bot/cogs/commands/owner.py` |
| profile | `{prefix}profile <member>` or `/profile` | Hybrid | No description in source. | member | None declared | Everyone | No | pr, badgesf | `bot/cogs/commands/owner.py` |
| reload | `{prefix}reload` | Prefix | Restarts the client. | — | Bot owner check | Bot Owner | No | — | `bot/cogs/commands/owner.py` |
| servertour | `{prefix}servertour <time_in_seconds> <member>` | Prefix | No description in source. | time_in_seconds, member | Bot owner check | Bot Owner | No | — | `bot/cogs/commands/owner.py` |
| slist | `{prefix}slist` | Prefix | No description in source. | — | Bot owner or staff-list check | Bot Owner or staff list | No | — | `bot/cogs/commands/owner.py` |
| staff_add | `{prefix}staff_add <user>` | Prefix | Adds a user to the staff list. | user | Bot owner check | Bot Owner | No | staffadd, addstaff | `bot/cogs/commands/owner.py` |
| staff_list | `{prefix}staff_list` | Prefix | Lists all staff members. | — | Bot owner check | Bot Owner | No | stafflist, liststaff, staffs | `bot/cogs/commands/owner.py` |
| staff_remove | `{prefix}staff_remove <user>` | Prefix | Removes a user from the staff list. | user | Bot owner check | Bot Owner | No | staffremove, removestaff | `bot/cogs/commands/owner.py` |
| sync | `{prefix}sync` | Prefix | Syncs all database. | — | Bot owner check | Bot Owner | No | — | `bot/cogs/commands/owner.py` |
| unfreezenick | `{prefix}unfreezenick <member>` | Prefix | Unfreezes a member's nickname in the current server. | member | User: manage_nicknames | Moderator | No | — | `bot/cogs/commands/owner2.py` |

## AI

| Command | Syntax | Type | Description | Arguments | Permissions | Who | Setup first? | Aliases | Source |
|---|---|---|---|---|---|---|---|---|---|
| ai | `{prefix}ai` (group) | Prefix | AI chatbot and utility commands | — | None declared | Everyone | No | — | `bot/cogs/commands/ai.py` |
| ai activate | `{prefix}ai activate <channel>` | Prefix | Enable the AI chatbot in a channel | channel | None declared | Everyone | No | — | `bot/cogs/commands/ai.py` |
| ai analyse | `{prefix}ai analyse <image_url>` | Prefix | Analyze an image or text and provide a description | image_url | None declared | Everyone | No | — | `bot/cogs/commands/ai.py` |
| ai analyze | `{prefix}ai analyze <image> <text>` | Prefix | Analyze an image or text and provide a description | image, text | None declared | Everyone | No | — | `bot/cogs/commands/ai.py` |
| ai ask | `{prefix}ai ask <question>` | Prefix | Ask the AI a question | question | None declared | Everyone | No | — | `bot/cogs/commands/ai.py` |
| ai code | `{prefix}ai code <language> <description>` | Prefix | Generate code in any programming language | language, description | None declared | Everyone | No | — | `bot/cogs/commands/ai.py` |
| ai conversation-clear | `{prefix}ai conversation-clear` | Prefix | Clear your conversation history | — | None declared | Everyone | No | — | `bot/cogs/commands/ai.py` |
| ai conversation-stats | `{prefix}ai conversation-stats` | Prefix | View your conversation statistics | — | None declared | Everyone | No | — | `bot/cogs/commands/ai.py` |
| ai database-clear | `{prefix}ai database-clear` | Prefix | Clear your AI conversation data and personality | — | None declared | Everyone | No | — | `bot/cogs/commands/ai.py` |
| ai deactivate | `{prefix}ai deactivate` | Prefix | Disable the AI chatbot in the channel | — | None declared | Everyone | No | — | `bot/cogs/commands/ai.py` |
| ai explain | `{prefix}ai explain <topic> <level>` | Prefix | Explain a concept or topic in detail | topic, level | None declared | Everyone | No | — | `bot/cogs/commands/ai.py` |
| ai fact | `{prefix}ai fact <topic>` | Prefix | Get a random fact or fact on a specific topic | topic | None declared | Everyone | No | — | `bot/cogs/commands/ai.py` |
| ai mood-analyzer | `{prefix}ai mood-analyzer <text>` | Prefix | Analyze the mood/sentiment of text | text | None declared | Everyone | No | — | `bot/cogs/commands/ai.py` |
| ai personality | `{prefix}ai personality` | Prefix | Set your personal AI personality (Slash command only) | — | None declared | Everyone | No | — | `bot/cogs/commands/ai.py` |
| ai roleplay-disable | `{prefix}ai roleplay-disable` | Prefix | Disable roleplay mode in the current channel | — | None declared | Everyone | No | — | `bot/cogs/commands/ai.py` |
| ai roleplay-enable | `{prefix}ai roleplay-enable` | Prefix | Enable roleplay mode in the current channel | — | None declared | Everyone | No | — | `bot/cogs/commands/ai.py` |
| ai summarize | `{prefix}ai summarize <text>` | Prefix | Summarize a long text | text | None declared | Everyone | No | — | `bot/cogs/commands/ai.py` |

## Other

These rows are help-index cogs under `bot/cogs/zyrox/`. They register real prefix commands, but most of them only print a list of other commands. They are not a second copy of the feature.

| Command | Syntax | Type | Description | Arguments | Permissions | Who | Setup first? | Aliases | Source |
|---|---|---|---|---|---|---|---|---|---|
| __AI__ | `{prefix}__AI__` (group) | Prefix | `ai activate`, `ai deactivate`, `ai analyze`, `ai analyse`, `ai code`, `ai explain`, `ai conversation-clear`, `ai mood-analyzer`, `ai personality`, `ai conversa | — | None declared | Everyone | No | — | `bot/cogs/zyrox/ai.py` |
| __Antinuke__ | `{prefix}__Antinuke__` (group) | Prefix | `antinuke` , `antinuke enable` , `antinuke disable` , `whitelist` , `whitelist @user` , `unwhitelist` , `whitelisted` , `whitelist reset` , `extraowner` , `extr | — | None declared | Everyone | No | — | `bot/cogs/zyrox/antinuke.py` |
| __Automod__ | `{prefix}__Automod__` (group) | Prefix | `automod` , `automod enable` , `automod disable` , `automod punishment` , `autmod config` , `automod logging` `automod ignore` , `automod ignore channel` , `aut | — | None declared | Everyone | No | — | `bot/cogs/zyrox/automod.py` |
| __Birthday__ | `{prefix}__Birthday__` (group) | Prefix | `birthdaysetup` , `setbirthday` , `removebirthday` , `listbirthdays` , `birthday` | — | None declared | Everyone | No | — | `bot/cogs/zyrox/birth.py` |
| __Boost__ | `{prefix}__Boost__` (group) | Prefix | `boost setup` , `boost message` , `boost channel` , `boostrole` , `boost config` | — | None declared | Everyone | No | — | `bot/cogs/zyrox/booster.py` |
| __Counting__ | `{prefix}__Counting__` (group) | Prefix | `>counting`, `>counting enable/disable`, `>counting channel #channel`, `>counting stats`, `>counting config continue/reset` | — | None declared | Everyone | No | — | `bot/cogs/zyrox/counting.py` |
| __Fun__ | `{prefix}__Fun__` (group) | Prefix | `/imagine` , `ship` , `mydog` , `chat` , `translate` , `howgay` , `lesbian` , `cute` , `intelligence`, `chutiya` , `horny` , `tharki` , `gif` , `iplookup` , `we | — | None declared | Everyone | No | — | `bot/cogs/zyrox/fun.py` |
| __Games__ | `{prefix}__Games__` (group) | Prefix | `blackjack` , `chess` , `tic-tac-toe` , `country-guesser` , `rps` , `lights-out` , `wordle` , `2048` , `memory-game` , `number-slider` , `battleship` , `connect | — | None declared | Everyone | No | — | `bot/cogs/zyrox/games.py` |
| __General__ | `{prefix}__General__` (group) | Prefix | `status` , `afk` , `avatar` , `banner` , `servericon` , `membercount` , `poll` , `hack` , `token` , `users` , `wizz` , `urban` , `rickroll` , `hash` , `snipe` , | — | None declared | Everyone | No | — | `bot/cogs/zyrox/general.py` |
| __Giveaway__ | `{prefix}__Giveaway__` (group) | Prefix | `gstart`, `gend`, `greroll` , `glist` | — | None declared | Everyone | No | — | `bot/cogs/zyrox/giveaway.py` |
| __Ignore__ | `{prefix}__Ignore__` (group) | Prefix | `ignore` , `ignore command add` , `ignore command remove` , `ignore command show` , `ignore channel add` , `ignore channel remove` , `ignore channel show` , `ig | — | None declared | Everyone | No | — | `bot/cogs/zyrox/ignore.py` |
| __InviteTracker__ | `{prefix}__InviteTracker__` (group) | Prefix | `>invites`, `>addinvites`, `>inviteleaderboard`, `>invitelogging` | — | None declared | Everyone | No | — | `bot/cogs/zyrox/inviteTracker.py` |
| __J2C__ | `{prefix}__J2C__` (group) | Prefix | `>j2csetup`, `>j2creset` | — | None declared | Everyone | No | — | `bot/cogs/zyrox/j2c.py` |
| __Joindm__ | `{prefix}__Joindm__` (group) | Prefix | `joindm enable` , `joindm disable` , `joindm message` , `joindm test` | — | None declared | Everyone | No | — | `bot/cogs/zyrox/joindm.py` |
| __Leveling__ | `{prefix}__Leveling__` (group) | Prefix | `level status`, `level channel`, `level message`, `level desc`, `level color`, `level thumbnail`, `level image`, `level clearimage`, `level xprange`, `level mul | — | None declared | Everyone | No | — | `bot/cogs/zyrox/leveling.py` |
| __Logging__ | `{prefix}__Logging__` (group) | Prefix | `log`, `log enable`, `log disable`, `log config`, `log ignore`, `log status`, `log toggle` | — | None declared | Everyone | No | — | `bot/cogs/zyrox/logging.py` |
| __Minecraft__ | `{prefix}__Minecraft__` (group) | Prefix | `minecraft setup` , `minecraft reset` , `minecraft status` | — | None declared | Everyone | No | — | `bot/cogs/zyrox/mc.py` |
| __Moderation__ | `{prefix}__Moderation__` (group) | Prefix | `audit` , `warn` , `clearwarns` , `ban` , `clone` , `snipe` , `hide` , `hideall` , `kick` , `lock` , `mute` , `nick` , `nuke` , `role` , `roleicon` , `role all` | — | None declared | Everyone | No | — | `bot/cogs/zyrox/moderation.py` |
| __Music__ | `{prefix}__Music__` (group) | Prefix | `play` , `search` , `loop` , `autoplay` , `nowplaying` , `shuffle` , `stop` , `skip` , `seek` , `join` , `disconnect` , `replay` , `queue` , `clearqueue` , `pau | — | None declared | Everyone | No | — | `bot/cogs/zyrox/music.py` |
| __Setup__ | `{prefix}__Setup__` (group) | Prefix | `setup` , `setup create <name>` , `setup delete <name>`  , `setup list` , `setup staff` , `setup girl` , `setup friend` , `setup vip` , `setup guest` , `setup c | — | None declared | Everyone | No | — | `bot/cogs/zyrox/server.py` |
| __Sticky__ | `{prefix}__Sticky__` (group) | Prefix | `sticky setup` , `sticky edit` , `sticky list` , `sticky remove` | — | None declared | Everyone | No | — | `bot/cogs/zyrox/sticky.py` |
| __Ticket__ | `{prefix}__Ticket__` (group) | Prefix | `/ticket setup`, `/ticket close`, `/ticket lock`, `/ticket claim`, `/ticket unlock`, `/ticket transcript` | — | None declared | Everyone | No | — | `bot/cogs/zyrox/ticket.py` |
| __Utility__ | `{prefix}__Utility__` (group) | Prefix | `botinfo` , `stats` , `invite` , `serverinfo` , `userinfo` , `roleinfo` , `boostcount` , `unbanall` ,  `joined-at` , `ping` , `github` , `vcinfo` , `channelinfo | — | None declared | Everyone | No | — | `bot/cogs/zyrox/extra.py` |
| __Vanity__ | `{prefix}__Vanity__` (group) | Prefix | `>vanityroles setup` , `>vanityroles reset `, `>vanityroles show` , | — | None declared | Everyone | No | — | `bot/cogs/zyrox/vanity.py` |
| __Verification__ | `{prefix}__Verification__` (group) | Prefix | `verification setup`, `verification status`, `verification enable`, `verification disable`, `verification logs`, `verification reset`, `verification verify`, `v | — | None declared | Everyone | No | — | `bot/cogs/zyrox/verify.py` |
| __Voice__ | `{prefix}__Voice__` (group) | Prefix | `voice` , `voice kick` , `voice kickall` , `voice mute` , `voice muteall` , `voice unmute` , `voice unmuteall` , `voice deafen` , `voice deafenall` , `voice und | — | None declared | Everyone | No | — | `bot/cogs/zyrox/voice.py` |
| __Welcomer__ | `{prefix}__Welcomer__` (group) | Prefix | `greet setup` , `greet reset`, `greet channel` , `greet edit` , `greet test` , `greet config` , `greet autodeletete` , `greet` | — | None declared | Everyone | No | — | `bot/cogs/zyrox/welcome.py` |
| encryption | `{prefix}encryption` (group) | Prefix | Show all available encryption commands | — | None declared | Everyone | No | encrypt | `bot/cogs/zyrox/encryption.py` |
| jail | `{prefix}jail <member> <duration> <reason>` | Prefix | Help-index command. Prints a list of related commands. | member, duration, reason | User: manage_roles | Moderator | No | — | `bot/cogs/commands/jail.py` |
| jailhistory | `{prefix}jailhistory <member>` | Prefix | Help-index command. Prints a list of related commands. | member | None declared | Everyone | No | — | `bot/cogs/commands/jail.py` |
| react | `{prefix}react` (group) | Prefix | Lists all subcommands of autoreact group. | — | User: administrator | Administrator | No | autoreact | `bot/cogs/commands/autoreact.py` |
| react add | `{prefix}react add <trigger> <emojis>` | Prefix | Adds a trigger and its emojis to the autoreact. | trigger, emojis | User: administrator | Administrator | No | set, create | `bot/cogs/commands/autoreact.py` |
| react list | `{prefix}react list` | Prefix | Lists all the triggers and their emojis in the autoreact module. | — | User: administrator | Administrator | No | show, config | `bot/cogs/commands/autoreact.py` |
| react remove | `{prefix}react remove <trigger>` | Prefix | Removes a trigger and its emojis from the autoreact. | trigger | User: administrator | Administrator | No | clear, delete | `bot/cogs/commands/autoreact.py` |
| react reset | `{prefix}react reset` | Prefix | Resets all the triggers and their emojis in the autoreact module. | — | User: administrator | Administrator | Yes | — | `bot/cogs/commands/autoreact.py` |
| unjail | `{prefix}unjail <member>` | Prefix | Help-index command. Prints a list of related commands. | member | User: manage_roles | Moderator | No | — | `bot/cogs/commands/jail.py` |

## Testing Plan

Use a private test server and a bot that is not in any server you care about. Give the bot a role below your own role. Do the phases in order. Stay inside a phase until the safe commands in it behave as the table describes.

### Phase 1 — Safe Smoke Tests

These read information, play a local game, or send a harmless message. They should not change roles, channels, or moderation state.

Suggested order:

1. `{prefix}ping`, `{prefix}uptime`, `{prefix}stats`, `{prefix}botinfo`, `{prefix}users`, `{prefix}invite`
2. `{prefix}serverinfo`, `{prefix}userinfo`, `{prefix}roleinfo`, `{prefix}channelinfo`, `{prefix}vcinfo`, `{prefix}membercount`, `{prefix}boostcount`
3. `{prefix}help` and one help-index command such as `{prefix}__general__` so you can see that those stubs only print text
4. `{prefix}avatar`, `{prefix}banner user`, `{prefix}servericon`, `{prefix}permissions`, `{prefix}joined-at`, `{prefix}status`
5. `{prefix}afk`, `{prefix}coinflip`, `{prefix}dice`, `{prefix}8ball`, `{prefix}calculator`, `{prefix}timer`, `{prefix}qr`
6. Games that only need two people in the same channel: `{prefix}rps`, `{prefix}wordle`, `{prefix}2048`, `{prefix}chess`, `{prefix}tic-tac-toe`
7. `{prefix}spotify` and `{prefix}reaction` from `bot/CodeX.py`

Skip `{prefix}hack`, `{prefix}token`, and `{prefix}wizz` until you have read them. They are jokes, but the names look like account theft.

### Phase 2 — Configuration Tests

These create roles, channels, panels, or database rows. Make them in the test server only. Turn each feature off, or reset it, before you leave the phase.

Suggested order:

1. `{prefix}prefix` — set a test prefix, then set it back
2. `{prefix}autorole` and its `humans` / `bots` add and remove subcommands, then `{prefix}autorole reset`
3. `{prefix}setup` custom-role commands, then the matching reset
4. `{prefix}greet setup`, `{prefix}greet test`, `{prefix}greet config`, `{prefix}greet reset`
5. `{prefix}joindm`, `{prefix}fastgreet_add` / `fastgreet_remove`, booster `boost` setup, then reset
6. `{prefix}log setup`, `{prefix}log test`, `{prefix}log status`, `{prefix}log reset`
7. `{prefix}verification setup`, `{prefix}verification status`, `{prefix}verification disable`
8. `{prefix}ticket` panel setup in a throwaway category, then close or reset it
9. `{prefix}level` enable, check config, then disable
10. `{prefix}media setup` in an empty channel, `{prefix}stickymessage` / `{prefix}sticky` setup, `{prefix}autoresponder`, `{prefix}react`
11. `{prefix}counting`, `{prefix}j2csetup` (creates voice channels), `{prefix}vcrole`, vanity roles, reaction roles
12. `{prefix}ignore` and `{prefix}blacklistword` on a test word you can remove

### Phase 3 — Moderation Tests

Use a second Discord account that has a role below the bot. Do not test these on the server owner or on your only admin account.

Suggested order:

1. `{prefix}warn` and `{prefix}clearwarns` on the second account
2. `{prefix}mute` for one minute, then `{prefix}unmute`
3. `{prefix}nick`, then clear the nickname
4. `{prefix}slowmode 5`, then `{prefix}unslowmode`
5. `{prefix}lock` and `{prefix}unlock` on one empty test channel
6. `{prefix}hide` and `{prefix}unhide` on that same channel
7. `{prefix}clear` / `{prefix}purge` of your own test messages
8. `{prefix}kick` the second account, then invite them back
9. `{prefix}ban` the second account, then `{prefix}unban`
10. `{prefix}jail` / `{prefix}unjail` only after you know which role it will assign
11. `{prefix}snipe` after you delete one of your own messages

Leave `{prefix}lockall`, `{prefix}unlockall`, `{prefix}hideall`, `{prefix}unhideall`, `{prefix}nuke`, and `{prefix}unbanall` until the end of this phase, and only in the empty test server. `nuke` deletes and clones a channel. `unbanall` removes every ban.

### Phase 4 — Security / Antinuke Tests

Higher risk. These commands change who is allowed to moderate, or they turn on automatic bans. Use the test server. Do not enable antinuke on a server that already has admins you need.

Suggested order:

1. Read `{prefix}antinuke` with no option so you only see the status text
2. `{prefix}extraowner view`, then `set` a second test account, then `reset`
3. `{prefix}whitelist` / `{prefix}whitelisted` / `{prefix}unwhitelist` / `{prefix}whitelistreset`
4. `{prefix}antinuke enable`, perform one harmless protected action with the second account only if you are ready to be banned by the bot, then `{prefix}antinuke disable`
5. `{prefix}automod` enable, punishment, config, then disable
6. `{prefix}nightmode` enable and disable
7. `{prefix}emergency` enable, list, then disable. Do not run `{prefix}emergencysituation` until you have `{prefix}emergencyrestore` ready. That pair strips and restores dangerous permissions.
8. `{prefix}topcheck` enable and disable (server owner only)

The antinuke listeners under `bot/cogs/antinuke/` are not commands. They ban members automatically when the module is on. Treat that as part of this phase.

### Phase 5 — External Service Tests

Skip a command if its API key, Lavalink node, or other service is not configured. A failure here usually means the outside service, not the test server.

Suggested order:

1. `{prefix}translate` with a short phrase
2. `{prefix}urban` with a harmless word
3. `{prefix}github` with a public repository name
4. `{prefix}yt` / `{prefix}youtube`
5. `{prefix}ai` with no arguments (help), then `{prefix}ai ask` with a short question. Image, code, and chat subcommands need `GROQ_API_KEY` or `GOOGLE_API_KEY`.
6. Music, in a voice channel, only if Lavalink is set: `{prefix}join`, `{prefix}play`, `{prefix}nowplaying`, `{prefix}pause`, `{prefix}resume`, `{prefix}skip`, `{prefix}queue`, `{prefix}stop`, `{prefix}disconnect`. Then `{prefix}filter enable`.
7. `{prefix}minecraft status` only after `/minecraft setup` against a public server address you are allowed to query

`/imagine` and `{prefix}map` are not in this list because those cogs are not loaded. See Findings.

### Phase 6 — Owner / Developer Tests

Run these only as the Discord user in `OWNER_IDS`, in the test server. Do not use them in a production server.

Suggested order:

1. `{prefix}owners`, `{prefix}staff_list`, `{prefix}slist`, `{prefix}guildinfo`
2. `{prefix}np list` and badge commands, which do not change a server
3. `{prefix}reload` only when you can watch the console
4. `{prefix}dm` to yourself
5. `{prefix}makeinvite` for the test server only
6. Global moderation (`{prefix}global`, `{prefix}ownerban`, `{prefix}guildban`, `{prefix}leaveguild`) last, and only against the test server and the second account

Jishaku is not loaded unless `JISHAKU_ENABLED` is `true`. Leave it false for these tests.

## Findings

Nothing in this section was changed. These are notes from the source.

### Duplicate or easy-to-confuse commands

- `setup` is a hybrid group in `bot/cogs/commands/customrole.py` (custom self-roles). `/minecraft setup` is a different slash subcommand in `bot/cogs/commands/minecraft.py`. They do not share a prefix name.
- `{prefix}status` shows a user's Discord status (`bot/cogs/commands/status.py`). `/minecraft status` is the Minecraft panel. Different command trees.
- `extraowner` also registers the alias `owner` (`bot/cogs/commands/extraown.py`). That alias is not the bot-owner system.
- `bot/cogs/zyrox/` loads a second set of prefix commands whose job is to print help text. Most are named after the Python function, for example `__antinuke__` and `__moderation__`. The encryption help cog registers a real command named `encryption`, while the working encode/decode commands live on `encode` and `decode` in `bot/cogs/commands/encryption.py`.
- `girl` is a custom-role command. A `girl` image command in `bot/cogs/commands/image.py` is commented out, so only the role command is registered.
- `blacklist` (`bot/cogs/commands/block.py`) is a bot-owner block list. `blacklistword` (`bot/cogs/commands/blacklist.py`) is a per-server word filter. They are different commands with similar names.

### Unclear descriptions

- **125** loaded commands have no `help` or `description` in the decorator and no docstring. The table shows "No description in source." Many of those are fun meters (`hug`, `iq`, `roast`) and help-index stubs.
- `{prefix}hack`, `{prefix}token`, and `{prefix}wizz` in `bot/cogs/commands/general.py` are joke commands. The names do not describe that.
- `ban` aliases include `fuckban`, `hackban`, and `kuttaban`. `mute` aliases include `stfu` and `chup`. The behavior is still ban or timeout.
- Several help-index commands have an empty body (`pass`) and no text, so invoking them does nothing visible. Examples include the sticky, birthday, and Minecraft help cogs.

### Missing or weak permission checks

No loaded Moderation, Antinuke, Tickets, or Verification command was left marked Everyone after decorator and body checks. That does not prove every branch is safe. `give`, `nuke`, `role`, and mass channel commands still deserve a manual read because they also use `top_check()` or confirm buttons.

- `warn` asks for `moderate_members` even though a warning does not time anyone out. The bot's own `manage_messages` check on that command is commented out.
- `unlock` asks for `manage_roles`, while `lock` and `hide` ask for `manage_channels`.
- `blacklist_check` and `ignore_check` in `bot/cogs/commands/owner.py` are defined as checks that always return true. They do not block anyone.

### Suspicious or dangerous commands

- `{prefix}nuke` deletes a channel and clones it.
- `{prefix}unbanall` / `massunban` removes every ban in the server.
- `{prefix}lockall`, `{prefix}unlockall`, `{prefix}hideall`, and `{prefix}unhideall` rewrite permissions on every channel.
- `{prefix}emergencysituation` and `{prefix}emergencyrestore` change high-impact roles. Server owner or bot owner only, but easy to fire in the wrong server.
- Bot-owner commands can ban, kick, nick, or purge across every mutual server (`global`, `ownerban`, `guildban`), create a permanent invite (`makeinvite`), or DM an arbitrary user (`dm`).
- `{prefix}create_hook` creates a webhook and sends the URL. It requires administrator, and it is still a secret-bearing command.
- Jishaku, when `JISHAKU_ENABLED` is true, lets a bot owner run Python in the bot process. It is off unless that setting is exactly `true`.

### Broken, incomplete, or not loaded

- `bot/cogs/commands/imagine.py` defines slash command `/imagine`, but that cog is never added in `bot/cogs/__init__.py`.
- `bot/cogs/commands/map.py` defines hybrid `map`, and its `add_cog` line is commented out.
- `bot/cogs/commands/msgpack.py` defines `addmessages`, `removemessages`, and `clearmessage`, and the cog is not loaded.
- `bot/cogs/commands/leveling_original.py` contains null bytes, so Python cannot parse it. The live leveling cog is `bot/cogs/commands/leveling.py`.
- The country-guesser `end` subcommand is commented out inside a string in `bot/cogs/commands/Games.py`. Only `country-guesser start` is registered.
- Antinuke files for emoji, sticker, and unban events are commented out in `bot/cogs/__init__.py`, so those protections are not active.
- `bot/cogs/commands/ai.py` is syntactically valid, but many lines contain spaces around dots (`commands .group`). It still loads. Several AI subcommands call each other in ways that do not match their arguments (`analyze` calls `analyse`). Treat AI results as unreliable until you test them.
- Some `bot/cogs/zyrox/` help commands are empty `pass` bodies, so they register and then do nothing.

### Hardcoded IDs

- The three startup channel IDs that used to live in `bot/CodeX.py` are gone. No loaded command still edits those channels.
- `{prefix}stats` and the mention reply in `bot/cogs/events/mention.py` still link to Discord user IDs `870179991462236170` and `767979794411028491` as credits. Those links do not grant owner access. The mention handler is not a command.
- Help text and footers often link to `https://discord.gg/codexdev`. That is a support invite, not a permission bypass.

### External APIs

- Music and `{prefix}filter` need a Lavalink node (`LAVALINK_HOST` and related variables in `bot/cogs/commands/music.py`). If those variables are missing, the music cog falls back to a built-in public node.
- `{prefix}ai` subcommands call Groq or Gemini when `GROQ_API_KEY` or `GOOGLE_API_KEY` is set (`bot/cogs/commands/ai.py`).
- `{prefix}translate` uses a translation library (`bot/cogs/commands/translate.py`).
- `{prefix}urban` calls a dictionary API (`bot/cogs/commands/general.py`).
- `{prefix}github` and `{prefix}yt` call external sites.
- Fun GIF actions use a Giphy key written in `bot/cogs/commands/fun.py`.
- `/minecraft` uses the Minecraft server-status protocol (`bot/cogs/commands/minecraft.py`).
- `{prefix}map` would call OpenStreetMap and MapQuest, but that cog is not loaded.
- `/imagine` would call an image API, but that cog is not loaded.

### Commands that appear unused

Defined in source, not registered because the cog is not added:

- `addmessages` (Prefix) in `bot/cogs/commands/msgpack.py`
- `clearmessage` (Prefix) in `bot/cogs/commands/msgpack.py`
- `imagine` (Slash) in `bot/cogs/commands/imagine.py`
- `map` (Hybrid) in `bot/cogs/commands/map.py`
- `removemessages` (Prefix) in `bot/cogs/commands/msgpack.py`

Files that could not be parsed:

- `cogs/commands/leveling_original.py: file contains null bytes and cannot be parsed`

Also not loaded, and therefore not commands you can run: Top.gg webhook cog, auto-blacklist event, and the extra antinuke event files. Their imports are commented out in `bot/cogs/__init__.py`.

## Registration notes

- One cog package is loaded: `cogs`, from `bot/core/zyrox.py`. `bot/cogs/__init__.py` `setup()` calls `add_cog` for each feature. A class that is only imported, or only listed in the unused `cogs_to_load` print loop, is not a command by itself. This reference follows the `add_cog` calls.
- `bot/cogs/zyrox/` cogs are loaded. They add extra prefix commands. They were not dropped as duplicates, because the registered names are different from the real feature commands, except `encryption` as noted above.
- Hybrid parent commands register both a prefix command and a slash command. Each subcommand is one row, not two.
- Jishaku is optional and is not part of the counts.

