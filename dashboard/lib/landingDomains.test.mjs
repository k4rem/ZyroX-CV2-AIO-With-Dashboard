import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { DISCORD_ENTRY, LANDING_DOMAINS, PERIMETER_DOMAINS, neighborDomain } from "./landingDomains.ts";
import { LANDING_DEPTH, motionPolicy } from "./landingMotion.ts";

test("landing domains are the six real modules", () => {
  assert.deepEqual(PERIMETER_DOMAINS, ["Security", "Tickets", "Logging", "Messaging", "Roles", "Automation"]);
  assert.equal(LANDING_DOMAINS.length, 6);
  for (const domain of LANDING_DOMAINS) {
    assert.ok(domain.capabilities.length >= 2 && domain.capabilities.length <= 4);
    assert.equal(domain.surface.length, domain.capabilities.length);
    const text = `${domain.summary} ${domain.capabilities.join(" ")}`.toLowerCase();
    assert.equal(text.includes("uptime"), false);
    assert.equal(text.includes("testimonial"), false);
    assert.equal(text.includes("99.9"), false);
  }
});

test("domain keyboard movement wraps", () => {
  assert.equal(neighborDomain("Security", 1), "Tickets");
  assert.equal(neighborDomain("Security", -1), "Automation");
  assert.equal(neighborDomain("Automation", 1), "Security");
});

test("discord entry stays the only sign-in route", () => {
  assert.equal(DISCORD_ENTRY.provider, "discord");
  assert.equal(DISCORD_ENTRY.callbackUrl, "/auth/continue");
  assert.equal(DISCORD_ENTRY.label, "Sign in with Discord");
});

test("domain index stacks on small screens and splits beside the detail on desktop", () => {
  const source = readFileSync(new URL("../components/landing/domain-list.tsx", import.meta.url), "utf8");
  assert.match(source, /grid-cols-1/);
  assert.match(source, /lg:grid-cols-\[minmax\(16rem,22rem\)_minmax\(0,1fr\)\]/);
  assert.match(source, /role="tablist"/);
  assert.match(source, /role="tabpanel"/);
});

test("reduced motion removes parallax and the sweep", () => {
  const reduced = motionPolicy({ reduce: true, finePointer: true, tablet: false });
  assert.equal(reduced.pointer, false);
  assert.equal(reduced.sweep, false);
  assert.equal(reduced.entry, false);
  assert.equal(reduced.scroll, false);
  assert.equal(reduced.scale, 0);
});

test("touch keeps a simpler scroll settle and no cursor depth", () => {
  const touch = motionPolicy({ reduce: false, finePointer: false, tablet: true });
  assert.equal(touch.pointer, false);
  assert.equal(touch.scale, 0);
  assert.equal(touch.scroll, true);
});

test("desktop depth stays inside the brief", () => {
  const desktop = motionPolicy({ reduce: false, finePointer: true, tablet: false });
  assert.equal(desktop.scale, 1);
  assert.equal(LANDING_DEPTH.foreground, 24);
  assert.equal(LANDING_DEPTH.primary, 16);
  assert.equal(LANDING_DEPTH.secondary, 10);
  assert.equal(LANDING_DEPTH.background, 4);
  const tablet = motionPolicy({ reduce: false, finePointer: true, tablet: true });
  assert.equal(tablet.scale, 0.5);
});
