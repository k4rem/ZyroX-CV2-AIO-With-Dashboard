import { activitySentence, type ActivityEvent } from "@/lib/activitySentence";

export function ActivitySentence({ event }: { event: ActivityEvent }) {
  const view = activitySentence(event);
  return (
    <p className="text-small text-fg-1">
      <span>{view.sentence}</span>
      {view.meta ? <span className="mt-0.5 block text-caption text-fg-3">{view.meta}</span> : null}
      {view.confidence ? <span className="mt-0.5 block text-caption text-fg-3">Attribution: {view.confidence}</span> : null}
    </p>
  );
}
