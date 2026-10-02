export type ActivityConfidence = "certain" | "likely" | "unknown";

export type ActivityEvent = {
  actor: string;
  verb: string;
  target?: string | null;
  object?: string | null;
  source?: string | null;
  module?: string | null;
  confidence?: ActivityConfidence | null;
  at?: string | number | Date | null;
  /** action: "AERO added Role to Member". event: "Message deleted by AERO". */
  form?: "action" | "event";
};

const CONFIDENCE_LABEL: Record<ActivityConfidence, string> = {
  certain: "Certain",
  likely: "Likely",
  unknown: "Unknown",
};

export function relativeTime(at: ActivityEvent["at"], now = Date.now()): string | null {
  if (at == null || at === "") return null;
  const then = at instanceof Date ? at.getTime() : typeof at === "number" ? at : Date.parse(at);
  if (Number.isNaN(then)) return null;
  const delta = Math.max(0, now - then);
  const minutes = Math.floor(delta / 60000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export function activitySentence(event: ActivityEvent, now = Date.now()) {
  const actor = event.actor.trim();
  const verb = event.verb.trim();
  const object = event.object?.trim() || "";
  const target = event.target?.trim() || "";
  let sentence: string;
  if (event.form === "event") {
    sentence = [object, verb, "by", actor].filter(Boolean).join(" ");
  } else if (object && target) {
    sentence = `${actor} ${verb} ${object} to ${target}`;
  } else if (object) {
    sentence = `${actor} ${verb} ${object}`;
  } else {
    sentence = `${actor} ${verb}`;
  }
  const meta = [event.source, event.module, relativeTime(event.at, now)].filter(Boolean).join(" · ");
  return {
    sentence,
    meta,
    confidence: event.confidence ? CONFIDENCE_LABEL[event.confidence] : null,
  };
}
