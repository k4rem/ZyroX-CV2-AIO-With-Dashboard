import assert from "node:assert/strict";
import test from "node:test";
import { TRANSFER_STEPS, modeLabel, resultLabel, whenLabel } from "./configTransfer.ts";

test("import uses a five-step review before apply", () => {
  assert.deepEqual(TRANSFER_STEPS, ["Upload", "Review", "Map resources", "Changes", "Apply"]);
  assert.equal(modeLabel("restore"), "Restore into this server");
  assert.equal(modeLabel("transfer"), "Transfer into this server");
  assert.equal(resultLabel("rolled_back"), "Failed. Rolled back");
  assert.match(whenLabel("2026-10-02T12:30:43.743500+00:00"), /2026/);
  assert.equal(whenLabel("not-a-date"), "not-a-date");
});
