import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { actionResultView } from "./actionResult.ts";
import { activitySentence } from "./activitySentence.ts";
import { labelFor } from "./labels.ts";
import { loadFailure } from "./loadFailure.ts";
import { channelChecks, moduleHealth, roleChecks } from "./platformHealth.ts";
import { DEFAULT_PAGE_SIZE, PAGE_SIZES, pageCount, serverPage } from "./pagination.ts";
import { fieldErrorSummary, shouldConfirmInAppLeave, shouldGuardLeave, LEAVE_MESSAGE } from "./saveGuard.ts";
import { isSaveShortcut } from "./modulePayloads.ts";
import { STATUS_TONES, toneForHealth, toneForOutcome } from "./statusTone.ts";

const root = new URL("..", import.meta.url);

test("role hierarchy and channel capability health", () => {
  const above = roleChecks({
    managed: false,
    position: 12,
    roleId: "1543105121913802823",
    botPosition: 4,
    botRoleId: "1543105121804615781",
    manageRoles: true,
  });
  assert.equal(moduleHealth(above).status, "warning");
  assert.equal(above.find((row) => row.id === "role_hierarchy").label, "Role above CLS");
  const managed = roleChecks({ managed: true, manageRoles: true, position: 1, roleId: "3", botPosition: 4, botRoleId: "9" });
  assert.equal(managed.find((row) => row.id === "role_managed").ok, false);
  const channel = channelChecks({ view_channel: true, send_messages: false, embed_links: true }, ["send_messages", "embed_links"]);
  assert.equal(channel[0].label, "Cannot send");
  assert.equal(moduleHealth(channel).status, "error");
});

test("status tones stay distinct and info is not the locked tone", () => {
  assert.deepEqual(STATUS_TONES, ["ok", "warning", "danger", "info", "locked", "neutral"]);
  assert.equal(toneForHealth("healthy"), "ok");
  assert.equal(toneForHealth("locked"), "locked");
  assert.notEqual(toneForHealth("error"), "info");
  assert.equal(toneForOutcome("failed"), "danger");
  assert.equal(toneForOutcome("skipped"), "neutral");
  const css = readFileSync(new URL("./app/globals.css", root), "utf8");
  assert.match(css, /--cls-info: 156 148 188/);
  assert.match(css, /--cls-locked: 120 132 148/);
  assert.doesNotMatch(css, /--cls-info: 77 179 240/);
});

test("action result refuses a blank reason and does not invent success", () => {
  const failed = actionResultView({ outcome: "failed", reason: "Missing Permissions", discordError: "50013" });
  assert.equal(failed.label, "Failed");
  assert.equal(failed.succeeded, false);
  assert.throws(() => actionResultView({ outcome: "succeeded", reason: "  " }));
});

test("label registry hides raw ids from the title", () => {
  const label = labelFor("aggregate.destructive");
  assert.equal(label.title, "Destructive burst");
  assert.equal(label.title.includes("aggregate"), false);
  assert.equal(labelFor("sequence.cls_impairment").tone, "warning");
  assert.equal(labelFor("DEVELOPMENT_PROPOSAL").title, "Development proposal");
});

test("data table pagination contract", () => {
  assert.deepEqual(PAGE_SIZES, [25, 50, 100]);
  assert.equal(DEFAULT_PAGE_SIZE, 25);
  const items = Array.from({ length: 120 }, (_, index) => index + 1);
  const first = serverPage(items, 1, 25);
  assert.equal(first.rows.length, 25);
  assert.equal(first.total, 120);
  assert.equal(pageCount(120, 50), 3);
  const last = serverPage(items, 3, 50);
  assert.deepEqual(last.rows, items.slice(100));
  const hundred = serverPage(items, 2, 100);
  assert.equal(hundred.page, 2);
  assert.equal(hundred.rows.length, 20);
});

test("save bar dirty leave and field errors", () => {
  assert.equal(shouldGuardLeave(false, false), false);
  assert.equal(shouldGuardLeave(true, false), true);
  const current = new URL("http://127.0.0.1:3000/dashboard/guild/1/settings");
  assert.equal(
    shouldConfirmInAppLeave({
      dirty: true,
      href: "/dashboard/guilds",
      target: null,
      button: 0,
      modified: false,
      current,
    }),
    true,
  );
  assert.equal(
    shouldConfirmInAppLeave({
      dirty: false,
      href: "/dashboard/guilds",
      target: null,
      button: 0,
      modified: false,
      current,
    }),
    false,
  );
  assert.equal(isSaveShortcut({ key: "s", metaKey: true, ctrlKey: false, altKey: false }), true);
  assert.equal(fieldErrorSummary({ prefix: "Prefix must be between 1 and 10 characters." }), "Prefix must be between 1 and 10 characters.");
  assert.match(LEAVE_MESSAGE, /Unsaved changes/);
});

test("error state retries instead of pretending the collection is empty", () => {
  const failure = loadFailure(new Error("upstream timeout"), "Welcome could not be loaded");
  assert.equal(failure.action, "retry");
  assert.equal(failure.pretendEmpty, false);
  assert.equal(failure.reference, "upstream timeout");
  const welcome = readFileSync(new URL("./app/dashboard/guild/[guildId]/welcome/page.tsx", root), "utf8");
  assert.equal(welcome.includes("getWelcomeHome(params.guildId).catch(() => null)"), false);
  assert.match(welcome, /LoadError/);
});

test("decorative drag is suppressed and the drop zone stays a drop target", () => {
  const css = readFileSync(new URL("./app/globals.css", root), "utf8");
  assert.match(css, /-webkit-user-drag: none/);
  assert.match(css, /\[draggable="true"\]/);
  assert.match(css, /\[data-drag-handle\]/);
  const transfer = readFileSync(new URL("./components/dashboard/config-transfer.tsx", root), "utf8");
  assert.match(transfer, /data-dropzone/);
  assert.match(transfer, /onDrop/);
});

test("shared button exposes a visible focus ring", () => {
  const button = readFileSync(new URL("./components/ui/button.tsx", root), "utf8");
  assert.match(button, /focus-visible:outline/);
  assert.match(button, /disabled:opacity-60/);
});

test("activity sentence keeps actor verb target and attribution", () => {
  const added = activitySentence(
    {
      actor: "AERO",
      verb: "added",
      object: "R7 Extra",
      target: "+EVO+",
      source: "CLS SYSTEM",
      module: "Role Automation",
      at: Date.now() - 3 * 60 * 60 * 1000,
    },
    Date.now(),
  );
  assert.equal(added.sentence, "AERO added R7 Extra to +EVO+");
  assert.match(added.meta, /CLS SYSTEM · Role Automation · 3h ago/);
  const deleted = activitySentence({ actor: "AERO", verb: "deleted", object: "Message", form: "event", confidence: "certain" });
  assert.equal(deleted.sentence, "Message deleted by AERO");
  assert.equal(deleted.confidence, "Certain");
});
