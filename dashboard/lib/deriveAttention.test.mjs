import test from "node:test";
import assert from "node:assert/strict";
import {
  deriveAttention,
  countLoggingEnabledWithoutChannel,
  countTicketCategoriesMissingStaff,
} from "./deriveAttention.ts";

test("deriveAttention: required module failure", () => {
  const items = deriveAttention({
    guildId: "1000000000000000001",
    health: {
      modules: { required_failed: [{ name: "scheduler", error: "timeout" }] },
    },
    antinukeStatus: null,
    loggingPartial: null,
    ticketsGap: null,
  });
  assert.equal(items.length, 1);
  assert.match(items[0].message, /scheduler/);
  assert.equal(items[0].severity, "critical");
});

test("deriveAttention: permission gaps for guild", () => {
  const items = deriveAttention({
    guildId: "1000000000000000001",
    health: {
      permissions: {
        guilds: [
          {
            guild_id: "1000000000000000001",
            missing_by_module: { Logging: ["View Audit Log"] },
          },
        ],
      },
    },
    antinukeStatus: null,
    loggingPartial: null,
    ticketsGap: null,
  });
  assert.equal(items.length, 1);
  assert.match(items[0].message, /Logging/);
  assert.ok(items[0].href.endsWith("/logging"));
});

test("deriveAttention: antinuke disabled", () => {
  const items = deriveAttention({
    guildId: "1",
    health: null,
    antinukeStatus: false,
    loggingPartial: null,
    ticketsGap: null,
  });
  assert.equal(items.length, 1);
  assert.match(items[0].message, /Antinuke is disabled/);
});

test("deriveAttention: logging and tickets gaps", () => {
  const items = deriveAttention({
    guildId: "1",
    health: null,
    antinukeStatus: true,
    loggingPartial: { enabledWithoutChannel: 2 },
    ticketsGap: { categoriesMissingStaff: 1 },
  });
  assert.equal(items.length, 2);
});

test("deriveAttention: empty when nothing to report", () => {
  assert.deepEqual(
    deriveAttention({
      guildId: "1",
      health: { modules: { required_failed: [] } },
      antinukeStatus: true,
      loggingPartial: { enabledWithoutChannel: 0 },
      ticketsGap: { categoriesMissingStaff: 0 },
    }),
    [],
  );
});

test("countLoggingEnabledWithoutChannel", () => {
  assert.equal(
    countLoggingEnabledWithoutChannel(
      { messages: true, joins: false, bans: true },
      { messages: "123", bans: "0" },
    ),
    1,
  );
});

test("countTicketCategoriesMissingStaff", () => {
  assert.equal(
    countTicketCategoriesMissingStaff([
      { staff_roles: [1] },
      { staff_roles: [] },
      {},
    ]),
    2,
  );
});
