import assert from "node:assert/strict";
import test from "node:test";
import { isSafeDashboardCallback, resolvePostAuthDestination } from "./authRouting.ts";

test("rejects open-redirect callback URLs", () => {
  assert.equal(isSafeDashboardCallback("https://evil.test/dashboard"), false);
  assert.equal(isSafeDashboardCallback("//evil/dashboard"), false);
  assert.equal(isSafeDashboardCallback("/dashboard/../admin"), false);
  assert.equal(isSafeDashboardCallback("/dashboard/guilds"), true);
});

test("routes by grant count and root", () => {
  assert.equal(
    resolvePostAuthDestination({ guildIds: [], isRoot: false }),
    "/auth/no-access",
  );
  assert.equal(
    resolvePostAuthDestination({ guildIds: [], isRoot: true }),
    "/dashboard/admin",
  );
  assert.equal(
    resolvePostAuthDestination({ guildIds: ["1000000000000000001"], isRoot: false }),
    "/dashboard/guild/1000000000000000001",
  );
  assert.equal(
    resolvePostAuthDestination({ guildIds: ["1", "2"], isRoot: false }),
    "/dashboard/guilds",
  );
});

test("honours safe in-app callback when guild is authorized", () => {
  const dest = resolvePostAuthDestination({
    guildIds: ["1000000000000000099"],
    isRoot: false,
    callbackUrl: "/dashboard/guild/1000000000000000099/antinuke",
  });
  assert.equal(dest, "/dashboard/guild/1000000000000000099/antinuke");
});

test("ignores callback for a guild the user cannot access", () => {
  const dest = resolvePostAuthDestination({
    guildIds: ["1000000000000000001"],
    isRoot: false,
    callbackUrl: "/dashboard/guild/1000000000000000002/antinuke",
  });
  assert.equal(dest, "/dashboard/guild/1000000000000000001");
});
