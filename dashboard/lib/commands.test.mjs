import assert from "node:assert/strict";
import test from "node:test";
import { commandCategories, filterCommands, restrictionSummary } from "./commands.ts";

const ping = {
  name: "ping",
  module: "Extra",
  category: "Utility",
  description: "Checks latency",
  usage: "ping",
  aliases: ["latency"],
  cooldown: null,
  permissions: [],
  dangerous: false,
  protected: false,
  enabled: true,
  allowed_role_ids: [],
  blocked_role_ids: [],
  allowed_channel_ids: [],
  blocked_channel_ids: [],
};

test("restriction summary stays human", () => {
  assert.equal(restrictionSummary(ping), "Everyone");
  assert.equal(restrictionSummary({ ...ping, enabled: false }), "Off");
  assert.equal(restrictionSummary({ ...ping, protected: true, enabled: false }), "Protected");
  assert.equal(
    restrictionSummary({ ...ping, allowed_role_ids: ["1"], allowed_channel_ids: ["2", "3"] }),
    "1 allowed roles · 2 channels",
  );
});

test("filters by category, search, and enabled state", () => {
  const ban = { ...ping, name: "ban", category: "Moderation", description: "Ban a member", enabled: false, aliases: [] };
  const rows = [ping, ban];
  assert.deepEqual(commandCategories(rows), ["Moderation", "Utility"]);
  assert.deepEqual(filterCommands(rows, "lat", "all", "all").map((row) => row.name), ["ping"]);
  assert.deepEqual(filterCommands(rows, "", "Moderation", "all").map((row) => row.name), ["ban"]);
  assert.deepEqual(filterCommands(rows, "", "all", "off").map((row) => row.name), ["ban"]);
});
