import assert from "node:assert/strict";
import test from "node:test";
import { eventLabel, filterTickets, questionKindLabel, ticketStatusLabel } from "./ticketsModel.ts";

const rows = [
  { id: "a", number: 12, status: "claimed", opener_name: "Aero", assignee_name: "Karim", category_id: "bill", category_name: "Billing", close_reason: "" },
  { id: "b", number: 4, status: "closed", opener_name: "Mina", assignee_name: "", category_id: "tech", category_name: "Technical", close_reason: "Resolved from dashboard" },
  { id: "c", number: 9007199254740993, status: "open", opener_name: "Guest", assignee_name: "", category_id: "bill", category_name: "Billing", close_reason: "" },
];

test("queue filters use names, status, and category, not raw ids", () => {
  assert.equal(filterTickets(rows, { status: "claimed", categoryId: "all", assignee: "all", query: "" }).length, 1);
  assert.equal(filterTickets(rows, { status: "all", categoryId: "bill", assignee: "unassigned", query: "" }).map((row) => row.number)[0], 9007199254740993);
  assert.equal(filterTickets(rows, { status: "all", categoryId: "all", assignee: "Karim", query: "" })[0].opener_name, "Aero");
  assert.equal(filterTickets(rows, { status: "all", categoryId: "all", assignee: "all", query: "resolved from dashboard" })[0].id, "b");
  assert.equal(filterTickets(rows, { status: "all", categoryId: "all", assignee: "all", query: "12" })[0].id, "a");
});

test("status and question labels stay human", () => {
  assert.equal(ticketStatusLabel("claimed"), "Claimed");
  assert.equal(ticketStatusLabel("error"), "Needs attention");
  assert.equal(questionKindLabel("paragraph"), "Paragraph");
  assert.equal(questionKindLabel("short"), "Short");
});

test("priority and tag filters keep the existing queue filters", () => {
  const tagged = rows.map((row, index) => ({ ...row, priority: index === 0 ? "high" : "normal", tags: index === 0 ? [{ id: "1", name: "Billing" }] : [] }));
  assert.equal(filterTickets(tagged, { status: "all", categoryId: "all", assignee: "all", query: "", priority: "high" }).length, 1);
  assert.equal(filterTickets(tagged, { status: "claimed", categoryId: "bill", assignee: "all", query: "", tag: "Billing" })[0].id, "a");
  assert.equal(eventLabel({ kind: "priority_changed", payload: { label: "Normal → High" } }), "Priority changed: Normal → High");
  assert.equal(eventLabel({ kind: "routing_fallback" }), "Routing fallback");
});

test("timeline reads actors and transfer names", () => {
  assert.equal(eventLabel({ kind: "claimed", actor_name: "Karim" }), "Claimed by Karim");
  assert.equal(eventLabel({ kind: "transferred", payload: { from: "Billing", to: "Technical" } }), "Transferred Billing → Technical");
  assert.equal(eventLabel({ kind: "closed", payload: { reason: "Resolved" } }), "Closed: Resolved");
});
