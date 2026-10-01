# Phase 2S recovery feasibility

No production recovery was attempted. This is a code and platform reading, not a drill.

| Capability | Verdict | Why |
| --- | --- | --- |
| Empty replacement guild | CONDITIONAL | A new empty guild can receive a planned restore. The bot must already be in that guild with Manage Roles and Manage Channels. |
| Structure recreation | GO | The Phase 2B document has roles, channels, categories, overwrites, and positions. Phase 6 can create them. It cannot copy message history. |
| Role and channel ordering | CONDITIONAL | Positions are stored. Discord will not place a role above the bot, and category creation has to happen before its children. |
| Member recovery | NO-GO | Members cannot be forced back. There is no stored OAuth grant that can re-add the current member list. |
| Ban restoration | GO | The ban list is user IDs only. `create_ban` can replay it when Ban Members is present. Reasons and message-delete windows are not in the snapshot. |
| OAuth rejoin | CONDITIONAL | A future join needs each member to authorize `guilds.join` again. Existing Discord sessions do not transfer to a replacement guild. |

Prototype: `capture_snapshot` already round-trips the structure a restore planner needs. No live guild was restored.
