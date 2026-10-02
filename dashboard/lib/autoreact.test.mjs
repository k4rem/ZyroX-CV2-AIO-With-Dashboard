import test from "node:test";
import assert from "node:assert/strict";
import { triggerSummary } from "./autoreact.ts";

test("trigger summary stays readable", () => {
  assert.equal(triggerSummary({ mode: "contains", pattern: "hello r10" }), "Contains “hello r10”");
  assert.equal(triggerSummary({ mode: "starts", pattern: "" }), "Starts with “…”");
});
