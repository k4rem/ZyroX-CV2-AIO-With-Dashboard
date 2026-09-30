# Legacy privilege state cleanup

This file records the privilege rows present during the September 30, 2026 security stabilization. No database rows were changed by the patch.

## Rows currently present

### `bot/db/np.db`

`staff` is empty.

`np` contains four global no-prefix users:

- `767979794411028491` — no expiry
- `858677845987164170` — no expiry
- `1258831252748894436` — no expiry
- `1383717676202987551` — no expiry

No-prefix status is global convenience access, not bot ownership. Normal command permission checks still apply.

### `bot/db/anti.db`

`extraowners` contains:

- Guild `1448947999123308687` → user `1258831252748894436`
- Guild `1448948375658565662` → user `1258831252748894436`

`whitelisted_users` contains:

- Guild `1419729237480575070` → user `767979794411028491`, with every recorded antinuke bypass flag enabled

The two `144894...` guild IDs also appear across current leveling, message, and prefix runtime data; `1448948375658565662` also has ticket data. That correlation makes them likely current test guilds, so this patch did not delete their extra-owner rows.

Guild `1419729237480575070` is tied to the old project state and the original-project user ID identified in the audit. It also appears in old logging/counting and other runtime data. Static repository data cannot prove who currently owns any Discord guild, so verify IDs in Discord before cleanup.

## Rows to remove before production

Remove these confirmed legacy original-project privileges:

```sql
DELETE FROM np
WHERE id = 767979794411028491;
```

```sql
DELETE FROM whitelisted_users
WHERE guild_id = 1419729237480575070
  AND user_id = 767979794411028491;
```

Review the other three no-prefix users individually. Remove every user who is not explicitly approved by the current root owner:

```sql
DELETE FROM np
WHERE id IN (
  858677845987164170,
  1258831252748894436,
  1383717676202987551
);
```

Do not run that statement if any listed user is intentionally approved.

Treat the two extra-owner rows as test data. Keep them while those test guilds are in use, but remove them before a clean production deployment unless the guild and user are deliberately re-approved:

```sql
DELETE FROM extraowners
WHERE (guild_id = 1448947999123308687 AND owner_id = 1258831252748894436)
   OR (guild_id = 1448948375658565662 AND owner_id = 1258831252748894436);
```

## Safe manual procedure

1. Stop the bot so SQLite is not being written.
2. Back up both files before changing them:
   - `bot/db/np.db`
   - `bot/db/anti.db`
3. Open each database with a trusted SQLite client.
4. Run `BEGIN IMMEDIATE;`.
5. Run only the relevant `DELETE` statement above.
6. Verify the remaining rows before committing:

```sql
SELECT id, expiry_time FROM np ORDER BY id;
SELECT guild_id, owner_id FROM extraowners ORDER BY guild_id, owner_id;
SELECT * FROM whitelisted_users ORDER BY guild_id, user_id;
```

7. Run `COMMIT;` only if the remaining rows are correct; otherwise run `ROLLBACK;`.
8. Restart the bot and verify no-prefix and antinuke configuration in the test guild.

For production, the safer approach is to initialize clean runtime databases and manually recreate only approved configuration. Do not copy the repository's tracked test databases into production unchanged.
