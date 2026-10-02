import { actionResultView, type ActionResult } from "@/lib/actionResult";
import { TONE_CLASS, toneForOutcome } from "@/lib/statusTone";
import { cn } from "@/lib/utils";

export function ActionResultView({ result }: { result: ActionResult }) {
  const view = actionResultView(result);
  const tone = TONE_CLASS[toneForOutcome(result.outcome)];
  return (
    <article className={cn("border px-3 py-2", tone.tint)}>
      <p className="text-small text-fg-1">
        <span className={cn("font-medium", tone.text)}>{view.label}</span>
        <span className="text-fg-2"> · {view.reason}</span>
      </p>
      {view.discordError ? <p className="mt-1 font-mono text-caption text-danger">{view.discordError}</p> : null}
      {view.context || view.at ? (
        <p className="mt-1 text-caption text-fg-3">
          {[view.context, view.at].filter(Boolean).join(" · ")}
        </p>
      ) : null}
    </article>
  );
}
