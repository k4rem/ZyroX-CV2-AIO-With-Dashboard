"use client";

import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { isSaveShortcut } from "@/lib/modulePayloads";

export function SaveBar({
  dirty,
  saving,
  error,
  onSave,
  onDiscard,
}: {
  dirty: boolean;
  saving: boolean;
  error: string | null;
  onSave: () => void;
  onDiscard: () => void;
}) {
  useEffect(() => {
    if (!dirty) return;
    const onKey = (event: KeyboardEvent) => {
      if (!isSaveShortcut(event) || saving) return;
      event.preventDefault();
      onSave();
    };
    const onLeave = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = "";
    };
    const onClick = (event: MouseEvent) => {
      if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      const anchor = (event.target as Element | null)?.closest("a");
      if (!anchor) return;
      const href = anchor.getAttribute("href");
      if (!href || href.startsWith("#") || anchor.getAttribute("target") === "_blank") return;
      const next = new URL(anchor.href, window.location.href);
      if (next.origin !== window.location.origin) return;
      if (next.pathname === window.location.pathname && next.search === window.location.search) return;
      if (!window.confirm("Leave this page? Unsaved changes will be lost.")) event.preventDefault();
    };
    window.addEventListener("keydown", onKey);
    window.addEventListener("beforeunload", onLeave);
    document.addEventListener("click", onClick, true);
    return () => {
      window.removeEventListener("keydown", onKey);
      window.removeEventListener("beforeunload", onLeave);
      document.removeEventListener("click", onClick, true);
    };
  }, [dirty, onSave, saving]);

  if (!dirty && !saving && !error) return null;

  return (
    <div className="sticky bottom-3 z-20 mt-6">
      <div className="flex flex-wrap items-center justify-between gap-3 border border-line bg-surface-2 px-3 py-2">
        <p className="text-small text-fg-2" role={error ? "alert" : undefined}>
          {error ?? (saving ? "Saving…" : "Unsaved changes")}
        </p>
        <div className="flex items-center gap-2">
          <Button type="button" variant="ghost" className="max-sm:h-10" onClick={onDiscard} disabled={saving}>
            Discard
          </Button>
          <Button type="button" className="max-sm:h-10" onClick={onSave} disabled={saving} aria-busy={saving}>
            {saving ? "Saving…" : "Save changes"}
          </Button>
        </div>
      </div>
    </div>
  );
}
