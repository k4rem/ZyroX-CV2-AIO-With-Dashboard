"use client";

import { cn } from "@/lib/utils";

export function Segmented<T extends string>({
  value,
  onChange,
  options,
  label,
}: {
  value: T;
  onChange: (value: T) => void;
  options: { value: T; label: string }[];
  label: string;
}) {
  const index = Math.max(0, options.findIndex((option) => option.value === value));
  return (
    <div
      role="radiogroup"
      aria-label={label}
      className="relative inline-grid h-8 rounded-sm border border-line bg-surface-1 p-0.5"
      style={{ gridTemplateColumns: `repeat(${options.length}, minmax(0, 1fr))` }}
    >
      <span
        aria-hidden="true"
        className="pointer-events-none absolute bottom-0.5 top-0.5 rounded-xs bg-surface-4 transition-[inset-inline-start] duration-standard ease-cls-out motion-reduce:transition-none"
        style={{
          width: `calc((100% - 4px) / ${options.length})`,
          insetInlineStart: `calc(2px + (${index} * (100% - 4px) / ${options.length}))`,
        }}
      />
      {options.map((option) => {
        const selected = option.value === value;
        return (
          <button
            key={option.value}
            type="button"
            role="radio"
            aria-checked={selected}
            className={cn(
              "relative z-[1] px-3 text-small font-medium transition-colors duration-micro",
              selected ? "text-fg-1" : "text-fg-3 hover:text-fg-2",
            )}
            onClick={() => onChange(option.value)}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
