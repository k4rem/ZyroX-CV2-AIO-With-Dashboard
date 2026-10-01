import * as React from "react";
import { SectionRule } from "@/components/ui/section-rule";

export function SettingGroup({
  label,
  meta,
  children,
  id,
}: {
  label: string;
  meta?: React.ReactNode;
  children: React.ReactNode;
  id?: string;
}) {
  return (
    <section aria-labelledby={id} className="mt-6">
      <SectionRule id={id} label={label} meta={meta} />
      <div className="mt-1">{children}</div>
    </section>
  );
}
