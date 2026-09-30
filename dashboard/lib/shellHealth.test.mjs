import assert from "node:assert/strict";
import test from "node:test";
import { deriveHealth, permissionSummaryForGuild } from "./shellHealth.ts";

test("no data yet is loading, never online", () => {
  const h = deriveHealth({ status: null, statusFailed: false, health: null });
  assert.equal(h.level, "loading");
  assert.equal(h.latencyMs, null);
});

test("failed status call is offline", () => {
  const h = deriveHealth({ status: null, statusFailed: true, health: null });
  assert.equal(h.level, "offline");
});

test("online with real latency", () => {
  const h = deriveHealth({ status: { latency: 41.6 }, statusFailed: false, health: null });
  assert.equal(h.level, "online");
  assert.equal(h.latencyMs, 42);
  assert.deepEqual(h.reasons, []);
});

test("latency over 400 ms degrades", () => {
  const h = deriveHealth({ status: { latency: 512 }, statusFailed: false, health: null });
  assert.equal(h.level, "degraded");
  assert.match(h.reasons[0], /400 ms/);
});

test("required module failure degrades even with good latency", () => {
  const h = deriveHealth({
    status: { latency: 30 },
    statusFailed: false,
    health: { modules: { required_failed: [{ name: "antinuke", error: "boom" }] } },
  });
  assert.equal(h.level, "degraded");
  assert.match(h.reasons[0], /antinuke/);
});

test("non-finite latency is unknown, not a fake number", () => {
  const h = deriveHealth({ status: { latency: Number.NaN }, statusFailed: false, health: null });
  assert.equal(h.latencyMs, null);
});

test("permission summary reads only the requested guild", () => {
  const health = {
    permissions: {
      guilds: [
        { guild_id: "1", guild_name: "Mine", missing_by_module: { logging: ["view_audit_log"] } },
        { guild_id: "2", guild_name: "Not mine", missing_by_module: { antinuke: ["ban_members"] } },
      ],
    },
  };
  const mine = permissionSummaryForGuild(health, "1");
  assert.equal(mine.known, true);
  assert.deepEqual(mine.missingModules, [{ module: "logging", missing: ["view_audit_log"] }]);
  assert.equal(permissionSummaryForGuild(health, "3").known, false);
  assert.equal(permissionSummaryForGuild(null, "1").known, false);
});
