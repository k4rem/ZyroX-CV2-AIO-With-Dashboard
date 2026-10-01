import assert from "node:assert/strict";
import test from "node:test";
import {
  LIMITS,
  applyVariables,
  emptyMessage,
  insertAt,
  parseMessageJson,
  validateMessage,
  variableQuery,
} from "./messagePayload.ts";

test("inserts a variable at the cursor and leaves unknown tokens", () => {
  const inserted = insertAt("Hello ", 6, 6, "{server_name}");
  assert.equal(inserted.value, "Hello {server_name}");
  assert.equal(applyVariables(inserted.value, { server_name: "CLS" }), "Hello CLS");
  assert.equal(applyVariables("{user}", { server_name: "CLS" }), "{user}");
  const query = variableQuery("Rules for {serv", 15);
  assert.equal(query?.query, "serv");
});

test("rejects discord limit breaches and accepts a multi-embed payload", () => {
  const message = emptyMessage();
  message.content = "Intro";
  message.embeds[0].title = "Server Rules";
  message.embeds[0].description = "{server_name}";
  message.embeds[0].fields = [
    { name: "One", value: "A", inline: true },
    { name: "Two", value: "B", inline: false },
  ];
  message.embeds.push({ ...message.embeds[0], title: "Second", fields: [] });
  message.buttons = [{ label: "Rules", url: "https://example.com", emoji: "" }];
  assert.deepEqual(validateMessage(message), []);
  const exported = JSON.stringify(message);
  const imported = parseMessageJson(exported);
  assert.equal(imported.errors.length, 0);
  assert.equal(imported.message?.embeds[1].title, "Second");
  assert.equal(imported.message?.buttons[0].label, "Rules");
  message.content = "x".repeat(LIMITS.content + 1);
  assert.ok(validateMessage(message).some((error) => error.includes("2000")));
  const junk = parseMessageJson('{"content":"hi","token":"no"}');
  assert.ok(junk.errors[0].includes("Unknown"));
});
