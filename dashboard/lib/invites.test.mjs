import test from "node:test";
import assert from "node:assert/strict";
import { inviteTotal, uncreditedCount } from "./invites.ts";

test("valid and left stay separate from uncredited joins", () => {
  assert.equal(inviteTotal({ valid: 2, left: 1 }), 3);
  assert.equal(uncreditedCount({ uncredited: { ambiguous: 1, unknown: 2, no_inviter: 1 } }), 4);
});
