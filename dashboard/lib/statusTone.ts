/** Semantic tones. Info is violet-steel. Locked is its own slate treatment. */

export const STATUS_TONES = ["ok", "warning", "danger", "info", "locked", "neutral"] as const;

export type StatusTone = (typeof STATUS_TONES)[number];

export const TONE_LABEL: Record<StatusTone, string> = {
  ok: "OK",
  warning: "Warning",
  danger: "Danger",
  info: "Info",
  locked: "Locked",
  neutral: "Neutral",
};

export const TONE_CLASS: Record<StatusTone, { text: string; tint: string; glyph: "check" | "alert" | "octagon" | "info" | "lock" | "minus" }> = {
  ok: { text: "text-ok", tint: "border-ok/30 bg-ok/10", glyph: "check" },
  warning: { text: "text-warn", tint: "border-warn/30 bg-warn/10", glyph: "alert" },
  danger: { text: "text-danger", tint: "border-danger/30 bg-danger/10", glyph: "octagon" },
  info: { text: "text-info", tint: "border-info/30 bg-info/10", glyph: "info" },
  locked: { text: "text-locked", tint: "border-locked/40 bg-locked/10", glyph: "lock" },
  neutral: { text: "text-neutral", tint: "border-neutral/30 bg-neutral/10", glyph: "minus" },
};

const HEALTH_TONE = {
  healthy: "ok",
  warning: "warning",
  error: "danger",
  locked: "locked",
  unavailable: "neutral",
} as const;

export function toneForHealth(status: keyof typeof HEALTH_TONE): StatusTone {
  return HEALTH_TONE[status];
}

const OUTCOME_TONE = {
  succeeded: "ok",
  failed: "danger",
  skipped: "neutral",
} as const;

export function toneForOutcome(outcome: keyof typeof OUTCOME_TONE): StatusTone {
  return OUTCOME_TONE[outcome];
}
