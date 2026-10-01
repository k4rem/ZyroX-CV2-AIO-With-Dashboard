import test from "node:test";
import assert from "node:assert/strict";
import { parseDiscordMarkdown } from "./discordMarkdown.ts";
import {
  BOT_DEFAULT_EMBED_COLOR,
  defaultWelcomeEmbed,
  interpretWelcomeColor,
  substituteWelcome,
  welcomeUpdatePayload,
  welcomeValueMap,
} from "./welcomeFormat.ts";
import {
  buildCustomRolesUpdate,
  buildJ2CUpdate,
  customRolesDraftFromApi,
  draftsDiffer,
  isSaveShortcut,
  nextComboboxIndex,
  roleIdFromApi,
  rolePlace,
} from "./modulePayloads.ts";

const SNOWFLAKE = "1234567890123456789";

test("default welcome colour includes # so greet2 will not ignore it", () => {
  const embed = defaultWelcomeEmbed();
  assert.match(embed.color, /^#[0-9A-F]{6}$/);
  assert.equal(embed.color.startsWith("#"), true);
  const payload = welcomeUpdatePayload({
    welcome_type: "embed",
    welcome_message: "",
    channel_id: null,
    auto_delete_duration: null,
    embed,
  });
  assert.equal(payload.embed_data.color, "#2F3136");
});

test("a colour without # is invalid and previews as the bot default grey", () => {
  const bare = interpretWelcomeColor("2f3136");
  assert.equal(bare.valid, false);
  assert.equal(bare.stored, null);
  assert.equal(bare.preview, BOT_DEFAULT_EMBED_COLOR);
  assert.match(bare.error ?? "", /# colour/);
  const ok = interpretWelcomeColor("#6025e2");
  assert.equal(ok.valid, true);
  assert.equal(ok.stored, "#6025E2");
  assert.equal(interpretWelcomeColor("").preview, BOT_DEFAULT_EMBED_COLOR);
});

test("welcome variables resolve known tokens and keep unknown ones", () => {
  const values = welcomeValueMap({
    userId: SNOWFLAKE,
    userName: "Aero",
    userAvatar: "https://cdn.example/a.png",
    userNick: "Aero",
    userJoinDate: null,
    userCreateDate: null,
    serverName: "CLS",
    serverId: "1543105121804615999",
    serverMemberCount: 42,
    serverIcon: "https://cdn.example/s.png",
    timestamp: "today at 03:30",
  });
  const result = substituteWelcome("Hi {user} in {server_name}. {not_a_var} joined {user_joindate}", values);
  assert.equal(result.text.includes(`<@${SNOWFLAKE}>`), true);
  assert.equal(result.text.includes("CLS"), true);
  assert.deepEqual(result.unknown, ["not_a_var"]);
  assert.deepEqual(result.unresolved, ["user_joindate"]);
  assert.equal(result.text.includes("{user_joindate}"), true);
});

test("discord markdown never produces HTML and keeps injection as text", () => {
  const blocks = parseDiscordMarkdown(
    '**bold** *italic* __under__ ~~gone~~ `code`\n# Title\n- item\n[ok](https://example.com) [bad](javascript:alert(1))\n||secret||\n`<img src=x onerror=alert(1)>`\n<script>alert(1)</script>\n```\nalert(1)\n```',
  );
  const dumped = JSON.stringify(blocks);
  assert.equal(dumped.includes('"type":"html"'), false);
  assert.equal(dumped.includes("<script>alert(1)</script>"), true);
  assert.equal(dumped.includes("javascript:alert"), true);
  assert.equal(blocks.some((block) => block.type === "heading" && block.level === 1), true);
  assert.equal(blocks.some((block) => block.type === "list"), true);
  assert.equal(blocks.some((block) => block.type === "code" && block.text.includes("alert(1)")), true);
  const link = dumped.includes("https://example.com");
  assert.equal(link, true);
});

test("draft dirty tracking resets when the saved value is restored", () => {
  const saved = { enabled: true, join_channel_id: "1" };
  assert.equal(draftsDiffer(saved, saved), false);
  assert.equal(draftsDiffer(saved, { ...saved, enabled: false }), true);
});

test("save shortcut is Ctrl or Meta S without modifiers", () => {
  assert.equal(isSaveShortcut({ key: "s", ctrlKey: true, metaKey: false, altKey: false }), true);
  assert.equal(isSaveShortcut({ key: "s", ctrlKey: false, metaKey: true, altKey: false }), true);
  assert.equal(isSaveShortcut({ key: "s", ctrlKey: true, metaKey: false, altKey: true }), false);
  assert.equal(isSaveShortcut({ key: "k", ctrlKey: true, metaKey: false, altKey: false }), false);
});

test("combobox keyboard moves, selects and closes", () => {
  assert.equal(nextComboboxIndex(-1, 3, "ArrowDown"), 0);
  assert.equal(nextComboboxIndex(0, 3, "ArrowDown"), 1);
  assert.equal(nextComboboxIndex(0, 3, "ArrowUp"), 2);
  assert.equal(nextComboboxIndex(1, 3, "Home"), 0);
  assert.equal(nextComboboxIndex(1, 3, "End"), 2);
  assert.equal(nextComboboxIndex(1, 3, "Enter"), "select");
  assert.equal(nextComboboxIndex(1, 3, "Escape"), "close");
});

test("turning Join to Create off keeps the saved channel ids", () => {
  const payload = buildJ2CUpdate({
    enabled: false,
    join_channel_id: SNOWFLAKE,
    control_channel_id: "1543105121804615999",
    category_id: "1543105121804615700",
  });
  assert.equal(payload.enabled, false);
  assert.equal(payload.join_channel_id, SNOWFLAKE);
  assert.equal(payload.control_channel_id, "1543105121804615999");
  assert.equal(payload.category_id, "1543105121804615700");
  assert.notEqual(payload.join_channel_id, null);
});

test("custom role ids stay full-precision strings above 2^53", () => {
  assert.ok(Number(SNOWFLAKE) > Number.MAX_SAFE_INTEGER - 1 || String(Number(SNOWFLAKE)) !== SNOWFLAKE);
  assert.notEqual(String(Number(SNOWFLAKE)), SNOWFLAKE);
  assert.notEqual(String(parseInt(SNOWFLAKE, 10)), SNOWFLAKE);
  assert.equal(roleIdFromApi(SNOWFLAKE), SNOWFLAKE);
  assert.equal(roleIdFromApi(Number(SNOWFLAKE)), null);
  const draft = customRolesDraftFromApi({
    staff: SNOWFLAKE,
    girl: null,
    vip: 9007199254740993,
    guest: "nope",
    frnd: null,
    reqrole: "2234567890123456789",
  });
  assert.equal(draft.staff, SNOWFLAKE);
  assert.equal(draft.vip, null);
  const payload = buildCustomRolesUpdate(draft);
  assert.equal(typeof payload.staff, "string");
  assert.equal(payload.staff, SNOWFLAKE);
  assert.equal(JSON.parse(JSON.stringify(payload)).staff, SNOWFLAKE);
});

test("role position is only shown when the API provides it", () => {
  const roles = [
    { id: "a", position: 10 },
    { id: "b", position: 4 },
    { id: "c", position: 1 },
  ];
  assert.deepEqual(rolePlace("b", roles), { rank: 2, total: 3 });
  assert.equal(rolePlace("missing", roles), null);
  assert.equal(rolePlace("a", [{ id: "a" }]), null);
});
