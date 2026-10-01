"use client";

import { useEffect, useState, type ReactNode } from "react";
import { cn } from "@/lib/utils";

export interface FlowNodeModel {
  id: string;
  kicker: string;
  title: string;
  detail: string;
  tone: "set" | "missing" | "neutral";
}

export function FlowLane({
  nodes,
  selected,
  onSelect,
  armed,
  animate,
  vertical,
  caption,
  extra,
}: {
  nodes: FlowNodeModel[];
  selected: string | null;
  onSelect: (id: string) => void;
  armed: boolean;
  animate: boolean;
  vertical: boolean;
  caption?: string;
  extra?: ReactNode;
}) {
  const [reduce, setReduce] = useState(false);
  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const apply = () => setReduce(media.matches);
    apply();
    media.addEventListener("change", apply);
    return () => media.removeEventListener("change", apply);
  }, []);

  return (
    <div className="cls-cut bg-stage p-3 sm:p-4">
      <div className="relative">
        {armed ? (
          <span
            className={cn(
              "pointer-events-none absolute start-2 end-2 top-0 h-px bg-brand-400",
              vertical && "bottom-0 start-0 end-auto top-2 w-px",
              animate && !reduce && !vertical && "cls-signal",
            )}
          />
        ) : null}
        <ol className={cn("flex gap-2", vertical ? "flex-col ps-3" : "items-stretch")}>
          {nodes.map((node, index) => (
            <li key={node.id} className={cn("flex min-w-0", vertical ? "flex-col" : "flex-1 items-stretch")}>
              {index > 0 ? (
                <span
                  aria-hidden="true"
                  className={cn(
                    "shrink-0 self-center border-line",
                    vertical ? "ms-5 h-3 border-s" : "mx-1 w-4 border-t",
                    node.tone === "missing" ? "border-dashed" : "border-line-strong",
                  )}
                />
              ) : null}
              <button
                type="button"
                onClick={() => onSelect(node.id)}
                aria-pressed={selected === node.id}
                className={cn(
                  "relative flex min-h-11 w-full flex-col justify-center rounded-sm border px-2 py-1.5 text-start",
                  selected === node.id && "bg-brand-500/[0.06]",
                  node.tone === "missing" ? "border-dashed border-warn" : "border-line",
                )}
              >
                {selected === node.id ? <span aria-hidden="true" className="absolute inset-y-1 start-0 w-0.5 bg-brand-500" /> : null}
                <span className="flex items-center gap-1.5 text-caption text-fg-3">
                  <span
                    aria-hidden="true"
                    className={cn(
                      "inline-block size-1.5 rotate-45 border",
                      node.tone === "set" ? "border-fg-1 bg-fg-1" : "border-fg-3",
                    )}
                  />
                  {node.kicker}
                </span>
                <span className="truncate text-small font-medium text-fg-1">{node.title}</span>
                <span className="truncate text-caption text-fg-3">{node.detail}</span>
              </button>
            </li>
          ))}
        </ol>
      </div>
      {extra}
      {caption ? <p className="mt-3 text-small text-fg-2">{caption}</p> : null}
    </div>
  );
}
