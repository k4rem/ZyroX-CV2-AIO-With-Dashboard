import test from "node:test";
import assert from "node:assert/strict";
import { actionSummary, exclusionSummary, thresholdSummary } from "./automodModel.ts";

const flood = {
  id: "flood",
  name: "Message flood",
  enabled: true,
  engine: "cls",
  mode: "enforce",
  trigger: { count: 5, window_seconds: 5 },
  scope: {
    include_channels: [],
    exclude_channels: ["1", "2"],
    include_categories: [],
    exclude_categories: [],
    exclude_roles: [],
  },
  message_action: "delete",
  member_action: "timeout",
  timeout_seconds: 600,
  notify_action: "none",
  points: 1,
  last_triggered_at: null,
};

test("rule summary shows the real threshold and actions", () => {
  assert.equal(thresholdSummary(flood), "5 messages / 5 sec");
  assert.equal(actionSummary(flood), "Delete + Timeout 10m");
  assert.equal(exclusionSummary(flood), 2);
});
