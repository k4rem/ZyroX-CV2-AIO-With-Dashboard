import assert from "node:assert/strict";
import test from "node:test";

/** Mirrors access-management grant payload (strings only). */
function buildGrantPayload(guildId, userId, templateKey) {
  return {
    guild_id: guildId.trim(),
    discord_user_id: userId.trim(),
    template_key: templateKey,
  };
}

test("access grant payload keeps snowflake strings", () => {
  const guild = "100000000000000001";
  const user = "1543105121804615781";
  const body = buildGrantPayload(guild, user, "admin");
  assert.equal(typeof body.guild_id, "string");
  assert.equal(typeof body.discord_user_id, "string");
  assert.equal(body.guild_id, guild);
  assert.equal(body.discord_user_id, user);
  assert.equal(JSON.parse(JSON.stringify(body)).guild_id, guild);
});
