import assert from "node:assert/strict";
import test from "node:test";
import { evaluateLegacyDirectBotApi } from "./legacyDirectApi.mjs";

test("production blocks legacy flag even when true", () => {
  const r = evaluateLegacyDirectBotApi({
    NODE_ENV: "production",
    NEXT_PUBLIC_LEGACY_DIRECT_BOT_API: "true",
  });
  assert.equal(r.allowed, false);
  assert.match(r.reason, /Phase 1/);
});

test("development requires explicit legacy flag", () => {
  const r = evaluateLegacyDirectBotApi({
    NODE_ENV: "development",
    NEXT_PUBLIC_LEGACY_DIRECT_BOT_API: "false",
  });
  assert.equal(r.allowed, false);
});

test("development allows explicit opt-in", () => {
  const r = evaluateLegacyDirectBotApi({
    NODE_ENV: "development",
    NEXT_PUBLIC_LEGACY_DIRECT_BOT_API: "true",
  });
  assert.equal(r.allowed, true);
});
