"use client";

import { useEffect, useState, type ReactNode } from "react";
import { X } from "lucide-react";
import { Drawer, DrawerClose, DrawerContent } from "@/components/ui/drawer";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type Tab = "summary" | "evidence" | "developer" | string;

export function DetailsDrawer({
  open,
  onOpenChange,
  title,
  summary,
  evidence,
  ids,
  raw,
  sections,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  summary: ReactNode;
  evidence?: ReactNode;
  ids?: Record<string, string>;
  raw?: unknown;
  sections?: Array<{ id: string; label: string; content: ReactNode }>;
}) {
  const [tab, setTab] = useState<Tab>(sections?.[0]?.id || "summary");
  useEffect(() => {
    if (sections?.length && !sections.some((section) => section.id === tab)) {
      setTab(sections[0].id);
    }
  }, [sections, tab]);
  const tabs: Array<{ id: Tab; label: string }> = sections
    ? sections.map((section) => ({ id: section.id, label: section.label }))
    : [
        { id: "summary", label: "Summary" },
        { id: "evidence", label: "Evidence" },
        { id: "developer", label: "Developer" },
      ];
  return (
    <Drawer open={open} onOpenChange={onOpenChange}>
      <DrawerContent side="end" title={title} width="min(440px, 100vw)" className="bg-canvas">
        <header className="flex items-center justify-between gap-3 border-b border-line px-3 py-2">
          <h2 className="text-section text-fg-1">{title}</h2>
          <DrawerClose asChild>
            <Button type="button" variant="ghost" size="icon" aria-label="Close">
              <X className="size-4" />
            </Button>
          </DrawerClose>
        </header>
        <div className="flex gap-1 border-b border-line px-3 py-2" role="tablist">
          {tabs.map((item) => (
            <button
              key={item.id}
              type="button"
              role="tab"
              aria-selected={tab === item.id}
              className={cn(
                "h-7 rounded-xs px-2 text-small",
                tab === item.id ? "bg-surface-3 text-fg-1" : "text-fg-3 hover:text-fg-1",
              )}
              onClick={() => setTab(item.id)}
            >
              {item.label}
            </button>
          ))}
        </div>
        <div className="min-h-0 flex-1 overflow-auto px-3 py-3 text-small text-fg-2" role="tabpanel">
          {sections ? sections.find((section) => section.id === tab)?.content : null}
          {!sections && tab === "summary" ? summary : null}
          {!sections && tab === "evidence" ? evidence ?? <p className="text-fg-3">No evidence recorded.</p> : null}
          {!sections && tab === "developer" ? (
            <div className="space-y-3">
              {ids ? (
                <dl className="space-y-1 font-mono text-caption">
                  {Object.entries(ids).map(([key, value]) => (
                    <div key={key} className="flex justify-between gap-3">
                      <dt className="text-fg-3">{key}</dt>
                      <dd className="text-fg-1" dir="ltr">{value}</dd>
                    </div>
                  ))}
                </dl>
              ) : null}
              <pre className="overflow-auto border border-line bg-surface-well p-2 text-caption text-fg-2" dir="ltr">
                {JSON.stringify(raw ?? {}, null, 2)}
              </pre>
              <Button
                type="button"
                variant="secondary"
                onClick={() => void navigator.clipboard.writeText(JSON.stringify(raw ?? {}, null, 2))}
              >
                Copy JSON
              </Button>
            </div>
          ) : null}
        </div>
      </DrawerContent>
    </Drawer>
  );
}
