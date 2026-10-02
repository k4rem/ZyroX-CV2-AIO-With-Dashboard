import test from "node:test";
import assert from "node:assert/strict";
import { filterGiveaways, giveawayPreview, giveawayView } from "./giveaways.ts";

test("views follow stored status", () => {
  assert.equal(giveawayView("open"), "live");
  assert.equal(giveawayView("scheduled"), "scheduled");
  assert.equal(giveawayView("ended"), "ended");
  const rows = [
    { status: "open" },
    { status: "scheduled" },
    { status: "archived" },
  ];
  assert.equal(filterGiveaways(rows, "live").length, 1);
  assert.equal(filterGiveaways(rows, "ended").length, 1);
});

test("preview names the prize and end", () => {
  const text = giveawayPreview({
    prize: "R10 Test Prize",
    description: "Disposable",
    winnerCount: 1,
    endsAt: "2026-10-02T16:00:00.000Z",
    host: "eerr00",
  });
  assert.match(text, /R10 Test Prize/);
  assert.match(text, /Winners: 1/);
  assert.match(text, /Host: eerr00/);
});
