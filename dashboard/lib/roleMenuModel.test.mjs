import assert from "node:assert/strict";
import test from "node:test";
import { menuModeLabel, menuTypeLabel } from "./roleMenuModel.ts";

test("menu types and modes stay human", () => {
  assert.equal(menuTypeLabel("button"), "Buttons");
  assert.equal(menuTypeLabel("select"), "Select menu");
  assert.equal(menuModeLabel("unique"), "Unique");
  assert.equal(menuModeLabel("add"), "Add only");
  assert.equal(menuModeLabel("remove"), "Remove only");
  assert.equal(menuTypeLabel("nope"), "Reaction");
});
