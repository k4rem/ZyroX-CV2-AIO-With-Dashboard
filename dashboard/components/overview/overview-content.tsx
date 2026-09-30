import Link from "next/link";
import { ChevronRight } from "lucide-react";
import type { OverviewPayload } from "@/lib/loadOverview";
import { PageHeader } from "@/components/dashboard/page-header";
import { StatusLabel } from "@/components/ui/status";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";

function SystemLine({ data }: { data: OverviewPayload }) {
  const botStatus =
    data.healthLevel === "offline"
      ? "offline"
      : data.healthLevel === "degraded"
        ? "degraded"
        : data.botOnline
          ? "online"
          : "unknown";

  const modulesLabel =
    data.requiredTotal > 0
      ? `${data.requiredOk}/${data.requiredTotal} required modules`
      : data.systemHealth?.modules
        ? "Modules checked"
        : null;

  const permGuild = data.systemHealth?.permissions?.guilds?.find(
    (g) => g.guild_id && data.guild?.id && String(g.guild_id) === String(data.guild.id),
  );
  const permMissing = permGuild
    ? Object.keys(permGuild.missing_by_module ?? {}).filter(
        (k) => (permGuild.missing_by_module?.[k]?.length ?? 0) > 0,
      ).length
    : 0;

  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-2 rounded-md border border-line bg-surface-1 px-3 py-2 text-caption text-fg-2">
      <span className="inline-flex items-center gap-2">
        <StatusLabel status={botStatus} />
        {data.botLatencyMs != null && (
          <span className="tabular-nums text-fg-3" dir="ltr">
            {data.botLatencyMs} ms
          </span>
        )}
      </span>
      {modulesLabel && (
        <>
          <span className="hidden text-fg-4 sm:inline" aria-hidden="true">
            │
          </span>
          <span>{modulesLabel}</span>
        </>
      )}
      {permMissing > 0 && (
        <>
          <span className="hidden text-fg-4 sm:inline" aria-hidden="true">
            │
          </span>
          <span className="text-warn">
            Permissions · {permMissing} module{permMissing === 1 ? "" : "s"} missing
          </span>
        </>
      )}
      {data.postgresEnabled && (
        <>
          <span className="hidden text-fg-4 sm:inline" aria-hidden="true">
            │
          </span>
          <span className="inline-flex items-center gap-1.5">
            Postgres
            <StatusLabel status={data.postgresConnected ? "online" : "offline"} />
          </span>
        </>
      )}
      {data.schedulerRunning != null && (
        <>
          <span className="hidden text-fg-4 sm:inline" aria-hidden="true">
            │
          </span>
          <span className="inline-flex items-center gap-1.5">
            Scheduler
            <StatusLabel status={data.schedulerRunning ? "online" : "offline"} />
          </span>
        </>
      )}
    </div>
  );
}

function NeedsAttention({ data }: { data: OverviewPayload }) {
  return (
    <section className="rounded-md border border-line bg-surface-1 p-4">
      <h2 className="text-section-title text-fg-1">Needs attention</h2>
      {data.attention.length === 0 ? (
        <p className="mt-2 text-body text-fg-2">Nothing needs attention.</p>
      ) : (
        <ul className="mt-3 space-y-2">
          {data.attention.map((item) => (
            <li key={item.id}>
              <Link
                href={item.href}
                className={cn(
                  "flex items-center justify-between gap-3 rounded-md border border-line px-3 py-2 text-body transition-colors duration-row hover:bg-surface-2",
                  item.severity === "critical" && "border-danger/30",
                  item.severity === "warning" && "border-warn/30",
                )}
              >
                <span className="min-w-0 text-fg-1">{item.message}</span>
                <span className="inline-flex shrink-0 items-center gap-1 text-caption text-brand">
                  Open
                  <ChevronRight className="size-3.5 rtl:rotate-180" aria-hidden="true" />
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function ServerFacts({ data }: { data: OverviewPayload }) {
  const g = data.guild;
  return (
    <section className="rounded-md border border-line bg-surface-1 p-4">
      <h2 className="text-section-title text-fg-1">Server</h2>
      {g ? (
        <dl className="mt-3 grid grid-cols-2 gap-x-4 gap-y-2 text-body">
          <div>
            <dt className="text-caption text-fg-3">Members</dt>
            <dd className="tabular-nums text-fg-1">{g.member_count.toLocaleString()}</dd>
          </div>
          <div>
            <dt className="text-caption text-fg-3">Roles</dt>
            <dd className="tabular-nums text-fg-1">{g.role_count.toLocaleString()}</dd>
          </div>
          <div>
            <dt className="text-caption text-fg-3">Channels</dt>
            <dd className="tabular-nums text-fg-1">{g.channel_count.toLocaleString()}</dd>
          </div>
        </dl>
      ) : (
        <p className="mt-2 text-body text-fg-2">{data.guildError ?? "Server details unavailable."}</p>
      )}
    </section>
  );
}

function AccessFacts({ data }: { data: OverviewPayload }) {
  return (
    <section className="rounded-md border border-line bg-surface-1 p-4">
      <h2 className="text-section-title text-fg-1">Your access</h2>
      <p className="mt-2 text-body text-fg-1">{data.accessLabel}</p>
      {data.grantsCount != null && (
        <p className="mt-1 text-caption text-fg-3">
          {data.grantsCount} active grant{data.grantsCount === 1 ? "" : "s"} on this server
        </p>
      )}
    </section>
  );
}

function ModulesTable({ data }: { data: OverviewPayload }) {
  return (
    <section className="rounded-md border border-line bg-surface-1 p-4">
      <h2 className="text-section-title text-fg-1">Modules</h2>
      <div className="mt-3 overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Module</TableHead>
              <TableHead>State</TableHead>
              <TableHead className="hidden sm:table-cell">Detail</TableHead>
              <TableHead className="w-10">
                <span className="sr-only">Configure</span>
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.modules.map((row) => (
              <TableRow key={row.key}>
                <TableCell className="font-medium text-fg-1">{row.name}</TableCell>
                <TableCell>
                  <StatusLabel status={row.status}>{row.statusLabel}</StatusLabel>
                </TableCell>
                <TableCell className="hidden max-w-[32ch] truncate text-fg-2 sm:table-cell">
                  {row.detail}
                </TableCell>
                <TableCell>
                  <Link
                    href={row.href}
                    className="text-caption text-brand hover:underline"
                  >
                    Configure
                  </Link>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </section>
  );
}

export function OverviewContent({ data, guildId }: { data: OverviewPayload; guildId: string }) {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Overview"
        description="Operational summary for this server. All values come from live configuration and health checks."
      />
      <SystemLine data={data} />
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_min(280px,100%)]">
        <div className="space-y-6">
          <NeedsAttention data={data} />
          <ModulesTable data={data} />
        </div>
        <div className="space-y-4">
          <ServerFacts data={data} />
          <AccessFacts data={data} />
        </div>
      </div>
    </div>
  );
}
