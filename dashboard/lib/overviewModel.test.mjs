import test from "node:test";
import assert from "node:assert/strict";
import {
  channelComposition,
  j2cEnabled,
  j2cSteps,
  loggingRouting,
  permissionCoverage,
  rankAttention,
  stepsDone,
  summarizeCoverage,
  ticketSteps,
  welcomeSteps,
} from "./overviewModel.ts";
import { ACTIVITY_WIDGETS, availableActivityWidgets } from "./overviewWidgets.ts";

test("j2c: state comes from join_channel_id (the API has no enabled field)", () => {
  const unset = { guild_id: "1", join_channel_id: null, control_channel_id: null, category_id: null };
  assert.equal(j2cEnabled(unset), false);
  assert.equal(j2cEnabled({ ...unset, enabled: true }), false);
  assert.equal(j2cEnabled({ ...unset, join_channel_id: "1543105121804615999" }), true);
  assert.equal(j2cEnabled(null), false);
  assert.equal(stepsDone(j2cSteps({ join_channel_id: "1", control_channel_id: null })), 1);
});

test("welcome: channel and content are separate steps; embed content counts", () => {
  assert.equal(stepsDone(welcomeSteps({ channel_id: null, welcome_message: null })), 0);
  assert.equal(stepsDone(welcomeSteps({ channel_id: "1", welcome_message: "  " })), 1);
  assert.equal(stepsDone(welcomeSteps({ channel_id: "1", welcome_message: "hi {user}" })), 2);
  const embed = welcomeSteps({ channel_id: "1", welcome_type: "embed", embed_data: { title: "Hi" } });
  assert.equal(stepsDone(embed), 2);
  assert.equal(embed[1].label, "Embed content");
});

test("tickets: every category needs staff for the third step", () => {
  assert.equal(stepsDone(ticketSteps({ panel_channel: null, categories: [] })), 0);
  assert.equal(
    stepsDone(ticketSteps({ panel_channel: "1", categories: [{ staff_roles: ["2"] }, { staff_roles: [] }] })),
    2,
  );
  assert.equal(
    stepsDone(ticketSteps({ panel_channel: "1", categories: [{ staff_roles: ["2"] }, { staff_roles: ["3"] }] })),
    3,
  );
});

test("logging: routed counts only enabled categories with a real channel", () => {
  assert.deepEqual(
    loggingRouting({ a: true, b: true, c: false, d: true }, { a: "123", b: "0", c: "456" }),
    { enabled: 3, routed: 1 },
  );
  assert.deepEqual(loggingRouting({}, {}), { enabled: 0, routed: 0 });
});

test("coverage buckets sum to the module count", () => {
  const c = summarizeCoverage(["on", "on", "off", "partial", "unavailable", "off"]);
  assert.deepEqual(c, { on: 2, partial: 1, off: 2, unavailable: 1 });
});

test("channel composition groups Discord types and drops empty kinds", () => {
  const comp = channelComposition([{ type: "0" }, { type: "5" }, { type: "2" }, { type: "4" }, { type: 4 }]);
  assert.deepEqual(
    comp.map((c) => [c.kind, c.count]),
    [
      ["text", 2],
      ["voice", 1],
      ["category", 2],
    ],
  );
  assert.deepEqual(channelComposition(null), []);
});

test("permission coverage uses module_requirements and this guild's missing list", () => {
  const health = {
    permissions: {
      module_requirements: { Logging: ["View Audit Log"], Tickets: ["Manage Channels"], Welcome: [] },
      guilds: [{ guild_id: "9", missing_by_module: { Logging: ["View Audit Log"], Tickets: [] } }],
    },
  };
  assert.deepEqual(permissionCoverage(health, "9"), {
    known: true,
    total: 3,
    satisfied: 2,
    missingModules: ["Logging"],
  });
  assert.equal(permissionCoverage(health, "10").known, false);
  assert.equal(permissionCoverage(null, "9").known, false);
});

test("attention ranking is critical → warning → info and stable within a severity", () => {
  const ranked = rankAttention([
    { id: "a", severity: "info" },
    { id: "b", severity: "warning" },
    { id: "c", severity: "critical" },
    { id: "d", severity: "warning" },
  ]);
  assert.deepEqual(
    ranked.map((i) => i.id),
    ["c", "b", "d", "a"],
  );
});

test("activity band ships with no widgets and filters by available sources", () => {
  assert.equal(ACTIVITY_WIDGETS.length, 0);
  assert.deepEqual(availableActivityWidgets(new Set(["tickets.activity"])), []);
  const registry = [
    { id: "t", source: "tickets.activity", title: "Tickets" },
    { id: "s", source: "security.events", title: "Security" },
  ];
  assert.deepEqual(
    availableActivityWidgets(new Set(["security.events"]), registry).map((w) => w.id),
    ["s"],
  );
});
