export type ActionOutcome = "succeeded" | "failed" | "skipped";

export type ActionResult = {
  outcome: ActionOutcome;
  reason: string;
  discordError?: string | null;
  at?: string | null;
  context?: string | null;
};

export const OUTCOME_LABEL: Record<ActionOutcome, string> = {
  succeeded: "Succeeded",
  failed: "Failed",
  skipped: "Skipped",
};

export function actionResultView(result: ActionResult) {
  if (!result.reason?.trim()) {
    throw new Error("Action result requires a reason");
  }
  return {
    label: OUTCOME_LABEL[result.outcome],
    reason: result.reason.trim(),
    discordError: result.discordError?.trim() || null,
    at: result.at ?? null,
    context: result.context ?? null,
    succeeded: result.outcome === "succeeded",
  };
}
