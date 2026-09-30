import test from "node:test";
import assert from "node:assert/strict";
import {
  assertSameOriginProxy,
  isBlockedProxyPath,
  sanitizeInboundHeaders,
} from "./proxyUtils.ts";

test("blocks internal proxy paths", () => {
  assert.equal(isBlockedProxyPath("internal/v1/sessions"), true);
  assert.equal(isBlockedProxyPath("guilds/1"), false);
  assert.equal(isBlockedProxyPath("../secrets"), true);
});

test("same-origin enforcement for mutations", () => {
  assert.equal(assertSameOriginProxy("GET", "localhost:3000", null), true);
  assert.equal(
    assertSameOriginProxy("POST", "localhost:3000", "http://localhost:3000"),
    true
  );
  assert.equal(
    assertSameOriginProxy("POST", "localhost:3000", "http://evil.example"),
    false
  );
});

test("strips inbound auth and internal headers", () => {
  const h = new Headers();
  h.set("Authorization", "Bearer browser-trust");
  h.set("X-Internal-Service-Key", "secret");
  h.set("X-Forwarded-Host", "evil");
  h.set("Content-Type", "application/json");
  const out = sanitizeInboundHeaders(h);
  assert.equal(out.has("Authorization"), false);
  assert.equal(out.has("X-Internal-Service-Key"), false);
  assert.equal(out.get("Content-Type"), "application/json");
});
