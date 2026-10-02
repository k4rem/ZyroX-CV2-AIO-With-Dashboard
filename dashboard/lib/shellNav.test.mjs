import assert from "node:assert/strict";
import test from "node:test";
import {
  NAV_ITEMS,
  buildNav,
  isFluidRoute,
  parseDashboardPath,
  resolveBreadcrumbs,
  switchGuildHref,
} from "./shellNav.ts";

const flat = (groups) => groups.flatMap((g) => g.items);

test("root-only items are emitted only when the server says isRoot", () => {
  const asUser = flat(buildNav({ pathname: "/dashboard/guilds", guildId: null, isRoot: false }));
  assert.equal(asUser.some((i) => i.id === "access"), false);
  assert.equal(asUser.some((i) => i.id === "platform"), false);

  const asRoot = flat(buildNav({ pathname: "/dashboard/guilds", guildId: null, isRoot: true }));
  assert.deepEqual(
    asRoot.filter((i) => ["access", "platform"].includes(i.id)).map((i) => i.href),
    ["/dashboard/access", "/dashboard/admin"],
  );
});

test("verification and leveling stay routable but are never surfaced", () => {
  const items = flat(buildNav({ pathname: "/dashboard/guild/1", guildId: "1", isRoot: true }));
  assert.equal(items.some((i) => i.id === "verification"), false);
  assert.equal(items.some((i) => i.id === "leveling"), false);
  assert.ok(NAV_ITEMS.find((i) => i.id === "verification")?.hidden);
  assert.ok(NAV_ITEMS.find((i) => i.id === "leveling")?.hidden);
  // Hidden routes still resolve breadcrumbs so the page does not look orphaned.
  const crumbs = resolveBreadcrumbs({ pathname: "/dashboard/guild/1/verification", guildId: "1", guildName: "Main" });
  assert.equal(crumbs.at(-1)?.label, "Verification");
});

test("guild-scoped groups appear only inside a guild; servers only outside", () => {
  const outside = buildNav({ pathname: "/dashboard/guilds", guildId: null, isRoot: false });
  assert.deepEqual(flat(outside).map((i) => i.id), ["servers"]);

  const inside = buildNav({ pathname: "/dashboard/guild/42/antinuke", guildId: "42", isRoot: false });
  const ids = flat(inside).map((i) => i.id);
  assert.ok(ids.includes("antinuke"));
  assert.equal(ids.includes("servers"), false);
  assert.deepEqual(
    inside.map((g) => g.id),
    ["overview", "management", "tickets", "engagement", "moderation", "security", "system"],
  );
});

test("active detection: exact for overview, prefix for modules, grouped routes share one item", () => {
  const at = (pathname) =>
    flat(buildNav({ pathname, guildId: "7", isRoot: false })).filter((i) => i.active).map((i) => i.id);
  assert.deepEqual(at("/dashboard/guild/7"), ["overview"]);
  assert.deepEqual(at("/dashboard/guild/7/antinuke"), ["antinuke"]);
  assert.deepEqual(at("/dashboard/guild/7/welcome"), ["welcome"]);
  assert.deepEqual(at("/dashboard/guild/7/invcrole"), ["roles"]);
  assert.deepEqual(at("/dashboard/guild/7/tracking"), ["invites"]);
  assert.deepEqual(at("/dashboard/guild/7/verification"), []);
});

test("nav hrefs never contain a server-only root id and always include the guild id", () => {
  const items = flat(buildNav({ pathname: "/dashboard/guild/99", guildId: "99", isRoot: true }));
  for (const item of items.filter((i) => !["access", "platform"].includes(i.id))) {
    assert.ok(item.href.startsWith("/dashboard/guild/99"), item.href);
  }
});

test("breadcrumbs: guild / group / page, with tab label for grouped routes", () => {
  const crumbs = resolveBreadcrumbs({ pathname: "/dashboard/guild/5/antinuke", guildId: "5", guildName: "CLS Main" });
  assert.deepEqual(crumbs.map((c) => c.label), ["CLS Main", "Security", "Protection"]);
  assert.equal(crumbs[0].userContent, true);

  const grouped = resolveBreadcrumbs({ pathname: "/dashboard/guild/5/welcome", guildId: "5", guildName: "CLS Main" });
  assert.deepEqual(grouped.map((c) => c.label), ["CLS Main", "Engagement", "Welcome"]);

  const access = resolveBreadcrumbs({ pathname: "/dashboard/access", guildId: null });
  assert.deepEqual(access.map((c) => c.label), ["CLS OS", "System", "Access"]);

  const unknownName = resolveBreadcrumbs({ pathname: "/dashboard/guild/5", guildId: "5", guildName: null });
  assert.equal(unknownName[0].label, "Server 5");
  assert.equal(unknownName[0].userContent, false);
});

test("switching server keeps the same module", () => {
  assert.equal(switchGuildHref("/dashboard/guild/1/automod", "2"), "/dashboard/guild/2/automod");
  assert.equal(switchGuildHref("/dashboard/guild/1", "2"), "/dashboard/guild/2");
  assert.equal(switchGuildHref("/dashboard/guilds", "2"), "/dashboard/guild/2");
});

test("parseDashboardPath handles trailing slashes and non-guild routes", () => {
  assert.deepEqual(parseDashboardPath("/dashboard/guild/3/j2c/"), { guildId: "3", subpath: "/j2c" });
  assert.deepEqual(parseDashboardPath("/dashboard/access"), { guildId: null, subpath: "" });
});

test("overview and tickets use the full workspace width", () => {
  assert.equal(isFluidRoute("/dashboard/guild/1543105121804615781"), true);
  assert.equal(isFluidRoute("/dashboard/guild/1543105121804615781/"), true);
  assert.equal(isFluidRoute("/dashboard/guild/1543105121804615781/tickets"), true);
  assert.equal(isFluidRoute("/dashboard/guild/1543105121804615781/tickets/panels"), true);
  assert.equal(isFluidRoute("/dashboard/guild/1543105121804615781/reactionroles/new"), true);
  assert.equal(isFluidRoute("/dashboard/guild/1543105121804615781/autorole"), true);
  assert.equal(isFluidRoute("/dashboard/guild/1543105121804615781/config-transfer"), true);
  assert.equal(isFluidRoute("/dashboard/guilds"), false);
  assert.equal(isFluidRoute("/dashboard/access"), false);
});
