"use client";

import { useMemo, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { SaveBar } from "@/components/settings/save-bar";
import { Button } from "@/components/ui/button";
import { ChannelPicker, RolePicker } from "@/components/discord/channel-picker";
import { ActionResultView } from "@/components/platform/action-result";
import { ActivitySentence } from "@/components/platform/activity-sentence";
import { DataTable } from "@/components/platform/data-table";
import { DetailsDrawer } from "@/components/platform/details-drawer";
import { HealthBadge, HealthPanel } from "@/components/platform/health";
import { ErrorState } from "@/components/ui/state";
import { StatusToneMark } from "@/components/platform/tone";
import { labelFor } from "@/lib/labels";
import { channelChecks, moduleHealth, roleChecks } from "@/lib/platformHealth";
import { parsePage, parsePageSize, serverPage, tableQuery, type PageSize } from "@/lib/pagination";
import { STATUS_TONES } from "@/lib/statusTone";
import type { ActionResult } from "@/lib/actionResult";

const ROWS = Array.from({ length: 120 }, (_, index) => ({
  id: String(index + 1),
  name: `Row ${index + 1}`,
}));

const BOT = "1543105121804615781";
const ABOVE = "1543105121913802823";

function Lab() {
  const router = useRouter();
  const pathname = usePathname();
  const search = useSearchParams();
  const page = parsePage(search.get("page"));
  const pageSize = parsePageSize(search.get("size"));
  const query = (search.get("q") ?? "").trim().toLowerCase();
  const filtered = ROWS.filter((row) => !query || row.name.toLowerCase().includes(query));
  const slice = serverPage(filtered, page, pageSize);
  const [selected, setSelected] = useState<string | null>(null);
  const [drawer, setDrawer] = useState(false);
  const [role, setRole] = useState(ABOVE);
  const [channel, setChannel] = useState("locked");
  const [showError, setShowError] = useState(true);
  const [tableError, setTableError] = useState<string | null>(null);
  const [prefix, setPrefix] = useState(">");

  const roleHealth = useMemo(
    () =>
      roleChecks({
        managed: role === "managed",
        position: role === ABOVE ? 20 : 1,
        roleId: role,
        botPosition: 10,
        botRoleId: BOT,
        manageRoles: role !== "missing-perm",
      }),
    [role],
  );
  const channelHealth = channelChecks(
    { view_channel: channel !== "hidden", send_messages: channel !== "locked", embed_links: channel !== "no-embed", attach_files: true, manage_channels: true },
    ["view_channel", "send_messages", "embed_links"],
  );

  function push(patch: { page?: number; size?: PageSize; q?: string | null }) {
    const next = tableQuery(new URLSearchParams(search.toString()), patch);
    router.replace(`${pathname}?${next.toString()}`);
  }

  const results: ActionResult[] = [
    { outcome: "succeeded", reason: "Role assigned.", at: "2026-10-02T12:00:00Z", context: "Role Automation" },
    { outcome: "failed", reason: "Discord rejected the role update.", discordError: "Missing Permissions", at: "2026-10-02T12:01:00Z" },
    { outcome: "skipped", reason: "Member already holds the role.", context: "Welcome" },
  ];

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-section text-fg-1">Platform primitives</h1>
        <p className="text-small text-fg-3">Shared contracts for later modules. This page is the foundation example.</p>
      </header>

      <section className="space-y-2">
        <h2 className="text-small text-fg-2">Button</h2>
        <div className="flex gap-2">
          <Button type="button">Save changes</Button>
          <Button type="button" variant="secondary">Discard</Button>
          <Button type="button" disabled>Disabled</Button>
        </div>
      </section>

      <section className="flex flex-wrap gap-2">
        {STATUS_TONES.map((tone) => (
          <StatusToneMark key={tone} tone={tone} />
        ))}
        <HealthBadge status="healthy" />
        <HealthBadge status="warning" />
        <HealthBadge status="error" />
        <HealthBadge status="locked" />
        <HealthBadge status="unavailable" />
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <div>
          <h2 className="mb-2 text-small text-fg-2">Role</h2>
          <RolePicker
            roles={[
              { id: "safe", name: "Member", position: 1, managed: false },
              { id: "managed", name: "Integration", position: 1, managed: true },
              { id: ABOVE, name: "Above CLS", position: 20, managed: false },
              { id: "missing-perm", name: "Needs Manage Roles", position: 1, managed: false },
            ]}
            value={role}
            onChange={setRole}
            botPosition={10}
            botRoleId={BOT}
            manageRoles={role !== "missing-perm"}
            intent="mutate"
          />
          <HealthPanel health={moduleHealth(roleHealth)} className="mt-3" />
        </div>
        <div>
          <h2 className="mb-2 text-small text-fg-2">Channel</h2>
          <ChannelPicker
            channels={[
              { id: "general", name: "general", type: "0" },
              { id: "locked", name: "staff-only", type: "0" },
              { id: "hidden", name: "hidden", type: "0" },
              { id: "no-embed", name: "no-embeds", type: "0" },
            ]}
            value={channel}
            onChange={setChannel}
            capabilities={{
              general: { view_channel: true, send_messages: true, embed_links: true, attach_files: true, manage_channels: true },
              locked: { view_channel: true, send_messages: false, embed_links: true, attach_files: true, manage_channels: false },
              hidden: { view_channel: false, send_messages: false, embed_links: false, attach_files: false, manage_channels: false },
              "no-embed": { view_channel: true, send_messages: true, embed_links: false, attach_files: true, manage_channels: true },
            }}
            required={["view_channel", "send_messages", "embed_links"]}
            intent="mutate"
          />
          <HealthPanel health={moduleHealth(channelHealth)} className="mt-3" />
        </div>
      </section>

      <section className="space-y-2">
        <h2 className="text-small text-fg-2">Labels</h2>
        {["aggregate.destructive", "sequence.cls_impairment", "DEVELOPMENT_PROPOSAL"].map((id) => {
          const label = labelFor(id);
          return (
            <p key={id} className="text-small text-fg-1">
              {label.title}
              <span className="ms-2 text-caption text-fg-3">{label.description}</span>
            </p>
          );
        })}
      </section>

      <section className="space-y-2">
        {results.map((result) => (
          <ActionResultView key={result.outcome} result={result} />
        ))}
        <ActivitySentence
          event={{ actor: "AERO", verb: "added", object: "R7 Extra", target: "+EVO+", source: "CLS SYSTEM", module: "Role Automation", at: Date.now() - 3 * 60 * 60 * 1000 }}
        />
        <ActivitySentence
          event={{ actor: "AERO", verb: "deleted", object: "Message", form: "event", confidence: "certain", source: "CLS SYSTEM", module: "Logging", at: Date.now() - 5 * 60 * 1000 }}
        />
      </section>

      <section className="space-y-2">
        <h2 className="text-small text-fg-2">Save</h2>
        <label className="block text-small text-fg-2">
          Prefix
          <input
            value={prefix}
            onChange={(event) => setPrefix(event.target.value)}
            className="ms-2 h-8 border border-line-input bg-surface-well px-2 text-fg-1"
          />
        </label>
        <a href="/" className="text-small text-brand-400">Leave to home</a>
        <SaveBar
          dirty={prefix !== ">"}
          saving={false}
          error={null}
          fieldErrors={prefix.length > 10 ? { prefix: "Prefix must be between 1 and 10 characters." } : undefined}
          onSave={() => setPrefix(">")}
          onDiscard={() => setPrefix(">")}
        />
      </section>

      <section>
        {/* Native image so the drag-ghost check hits the browser, not the image optimizer. */}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img data-decorative src="/brand/cls-icon-32.png" alt="" width={16} height={16} draggable={false} />
      </section>

      <section className="space-y-2">
        <div className="flex gap-2">
          <Button type="button" variant="secondary" onClick={() => setDrawer(true)}>Open details</Button>
          <Button type="button" variant="ghost" onClick={() => setShowError((value) => !value)}>Toggle error</Button>
        </div>
        {showError ? (
          <ErrorState
            title="Example could not be loaded"
            description="This could not be loaded. Retry, or check that CLS is online."
            reference="preview-ref"
            actions={<Button type="button" onClick={() => setShowError(false)}>Retry</Button>}
          />
        ) : null}
        <DetailsDrawer
          open={drawer}
          onOpenChange={setDrawer}
          title="Example record"
          summary={<p>Summary of the record. Human wording stays here.</p>}
          evidence={<p>Evidence captured with the event.</p>}
          ids={{ guild_id: "1543105121804615781", record_id: "row-1" }}
          raw={{ id: "row-1", source: "platform" }}
        />
      </section>

      <section className="space-y-2">
        <label className="block text-small text-fg-3">
          Filter
          <input
            value={search.get("q") ?? ""}
            onChange={(event) => push({ q: event.target.value, page: 1 })}
            className="ms-2 h-8 border border-line-input bg-surface-well px-2 text-fg-1"
          />
        </label>
        <DataTable
          rows={tableError ? [] : slice.rows}
          columns={[
            { key: "id", header: "ID", cell: (row) => row.id },
            { key: "name", header: "Name", cell: (row) => row.name },
          ]}
          getRowId={(row) => row.id}
          page={slice.page}
          pages={slice.pages}
          pageSize={slice.pageSize}
          total={slice.total}
          error={tableError}
          onRetry={() => setTableError(null)}
          onPageChange={(next) => push({ page: next })}
          onPageSizeChange={(size) => push({ size, page: 1 })}
          selectedId={selected}
          onSelect={setSelected}
        />
        <Button type="button" variant="ghost" onClick={() => setTableError("The page request failed.")}>Simulate table error</Button>
      </section>
    </div>
  );
}

export default function PrimitivesPage() {
  return (
    <Suspense fallback={<p className="text-small text-fg-3">Loading…</p>}>
      <Lab />
    </Suspense>
  );
}
