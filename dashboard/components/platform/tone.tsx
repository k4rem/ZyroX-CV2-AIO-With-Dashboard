import { CircleMinus, CircleCheck, Info, Lock, OctagonAlert, TriangleAlert } from "lucide-react";
import { cn } from "@/lib/utils";
import { TONE_CLASS, TONE_LABEL, type StatusTone } from "@/lib/statusTone";

const GLYPH = {
  check: CircleCheck,
  alert: TriangleAlert,
  octagon: OctagonAlert,
  info: Info,
  lock: Lock,
  minus: CircleMinus,
} as const;

export function StatusToneMark({ tone, className }: { tone: StatusTone; className?: string }) {
  const style = TONE_CLASS[tone];
  const Glyph = GLYPH[style.glyph];
  return (
    <span className={cn("inline-flex h-5 items-center gap-1 rounded-xs border px-1.5 text-[11px] font-medium", style.tint, style.text, className)}>
      <Glyph className="size-3" strokeWidth={1.75} aria-hidden="true" />
      {TONE_LABEL[tone]}
    </span>
  );
}
