import * as React from "react";
import { cn } from "@/lib/utils";

export function SettingRow({
  label,
  description,
  children,
  htmlFor,
  selected = false,
  id,
}: {
  label: string;
  description?: string;
  children: React.ReactNode;
  htmlFor?: string;
  selected?: boolean;
  id?: string;
}) {
  return (
    <div
      id={id}
      className={cn(
        "relative grid gap-2 border-b border-line-subtle py-3 last:border-b-0 sm:grid-cols-[minmax(0,1fr)_minmax(12rem,18rem)] sm:items-center sm:gap-6",
        selected && "bg-brand-500/[0.06]",
      )}
    >
      {selected ? <span aria-hidden="true" className="absolute inset-y-2 start-0 w-0.5 bg-brand-500" /> : null}
      <div className="min-w-0 ps-3">
        <label htmlFor={htmlFor} className="text-body font-medium text-fg-1">
          {label}
        </label>
        {description ? (
          <p className="mt-0.5 text-small text-fg-3" dir="auto">
            {description}
          </p>
        ) : null}
      </div>
      <div className="min-w-0 ps-3 sm:ps-0">{children}</div>
    </div>
  );
}
