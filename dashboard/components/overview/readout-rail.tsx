import * as React from "react";
import type { OverviewPayload } from "@/lib/loadOverview";
import { Avatar } from "@/components/ui/avatar";
import { StatusDot, StatusLabel, type Status } from "@/components/ui/status";
import { Tooltip } from "@/components/ui/tooltip";
import { ChangeMark, Readout } from "@/components/ui/readout";
import { CheckedReadout } from "./checked-readout";
import { LiveLatency } from "./live-latency";

const TONE_STATUS: Record<"ok" | "warn" | "danger", Status> = { ok: "online", warn: "degraded", danger: "offline" };

function botState(data: OverviewPayload): { status: Status; label: string } {
  if (data.healthLevel === "offline") return { status: "offline", label: "Offline" };
  if (data.healthLevel === "degraded") return { status: "degraded", label: "Degraded" };
  if (data.botOnline) return { status: "online", label: "Online" };
  return { status: "unknown", label: "Unknown" };
}

function RatioValue({
  ok,
  total,
  tone,
  srLabel,
  tip,
}: {
  ok: number;
  total: number;
  tone: "ok" | "warn" | "danger";
  srLabel: string;
  tip: React.ReactNode;
}) {
  return (
    <Tooltip content={tip} side="bottom" align="start">
      <span tabIndex={0} className="inline-flex items-center gap-2 rounded-xs">
        <StatusDot status={TONE_STATUS[tone]} />
        <ChangeMark watch={`${ok}/${total}`}>
          <span className="font-mono tabular-nums" dir="ltr" aria-hidden="true">
            {ok}/{total}
          </span>
          <span className="sr-only">{srLabel}</span>
        </ChangeMark>
      </span>
    </Tooltip>
  );
}

/**
 * Readout rail (RP §1.1): one instrument strip for the server and the bot's state
 * in it. Carries the cut; the signal edge belongs to the instrument deck below.
 */
export function ReadoutRail({ data, className, style }: { data: OverviewPayload; className?: string; style?: React.CSSProperties }) {
  const bot = botState(data);
  const reqOk = data.requiredOkNames.length;
  const reqTotal = reqOk + data.requiredFailedNames.length;
  const perm = data.permissions;
  const g = data.guild;

  return (
    <section aria-label="Server and bot status" className={className} style={style}>
      <dl className="cls-cut grid grid-cols-2 gap-px overflow-hidden rounded-md border border-line bg-line-subtle shadow-hl-1 md:grid-cols-3 xl:grid-cols-[minmax(0,1.2fr)_repeat(6,minmax(0,1fr))] [&>div]:bg-surface-1">
        <Readout label="Server" className="col-span-2 md:col-span-3 xl:col-span-1">
          <Avatar src={data.guildIconUrl} name={g?.name} size={24} />
          <span className="min-w-0 truncate" dir="auto">
            {g?.name ?? "Server unavailable"}
          </span>
        </Readout>

        <Readout label="Bot">
          <ChangeMark watch={bot.status}>
            <StatusLabel status={bot.status} className="text-readout">
              <span className="text-fg-1">{bot.label}</span>
            </StatusLabel>
          </ChangeMark>
          <LiveLatency initialMs={data.botLatencyMs} />
        </Readout>

        <Readout label="Required modules">
          {reqTotal > 0 ? (
            <RatioValue
              ok={reqOk}
              total={reqTotal}
              tone={reqOk === reqTotal ? "ok" : "danger"}
              srLabel={`${reqOk} of ${reqTotal} required modules loaded`}
              tip={
                <span className="block space-y-0.5">
                  {data.requiredOkNames.map((n) => (
                    <span key={n} className="block">
                      {n} · loaded
                    </span>
                  ))}
                  {data.requiredFailedNames.map((n) => (
                    <span key={n} className="block text-danger">
                      {n} · failed
                    </span>
                  ))}
                </span>
              }
            />
          ) : (
            <span className="text-body font-normal text-fg-3">Not reported</span>
          )}
        </Readout>

        <Readout label="Permissions">
          {perm.known ? (
            <RatioValue
              ok={perm.satisfied}
              total={perm.total}
              tone={perm.satisfied === perm.total ? "ok" : "warn"}
              srLabel={`Bot has the permissions ${perm.satisfied} of ${perm.total} modules need`}
              tip={
                perm.missingModules.length === 0
                  ? `The bot has every permission its ${perm.total} modules need here.`
                  : `Missing permissions for ${perm.missingModules.join(", ")}.`
              }
            />
          ) : (
            <span className="text-body font-normal text-fg-3">Not reported</span>
          )}
        </Readout>

        <Readout label="Postgres">
          {data.postgresEnabled === false ? (
            <span className="text-body font-normal text-fg-3">Not enabled</span>
          ) : data.postgresConnected == null ? (
            <span className="text-body font-normal text-fg-3">Not reported</span>
          ) : (
            <ChangeMark watch={data.postgresConnected}>
              <StatusLabel status={data.postgresConnected ? "online" : "offline"} className="text-readout">
                <span className="text-fg-1">{data.postgresConnected ? "Connected" : "Disconnected"}</span>
              </StatusLabel>
            </ChangeMark>
          )}
        </Readout>

        <Readout label="Scheduler">
          {data.schedulerRunning == null ? (
            <span className="text-body font-normal text-fg-3">Not reported</span>
          ) : (
            <ChangeMark watch={data.schedulerRunning}>
              <StatusLabel status={data.schedulerRunning ? "online" : "offline"} className="text-readout">
                <span className="text-fg-1">{data.schedulerRunning ? "Running" : "Stopped"}</span>
              </StatusLabel>
            </ChangeMark>
          )}
        </Readout>

        <Readout label="Checked">
          <CheckedReadout checkedAt={data.checkedAt} />
        </Readout>
      </dl>
    </section>
  );
}
