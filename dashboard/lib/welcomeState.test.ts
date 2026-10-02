import assert from "node:assert/strict";
import test from "node:test";
import { GOODBYE_MESSAGE_VARIABLES, WELCOME_MESSAGE_VARIABLES, asMessageDraft, sameWelcomeState } from "./welcomeState.ts";

test("goodbye hides the mention and welcome keeps the member variables", () => {
  assert.equal(WELCOME_MESSAGE_VARIABLES.some((item) => item.id === "user"), true);
  assert.equal(GOODBYE_MESSAGE_VARIABLES.some((item) => item.id === "user"), false);
  assert.equal(GOODBYE_MESSAGE_VARIABLES.some((item) => item.id === "user_name"), true);
});

test("discard restores the saved draft and a media reference survives", () => {
  const saved = asMessageDraft({
    content: "Hi {user}",
    embeds: [{ title: "Welcome", image: { kind: "media", value: "a".repeat(32) + ".png" }, fields: [{ name: "One", value: "A", inline: false }] }],
    buttons: [],
  });
  const edited = { ...saved, content: "changed" };
  assert.equal(sameWelcomeState(saved, edited), false);
  assert.equal(sameWelcomeState(saved, JSON.parse(JSON.stringify(saved))), true);
  assert.equal(saved.embeds[0].image?.kind, "media");
  assert.equal(saved.embeds[0].fields[0].name, "One");
});
