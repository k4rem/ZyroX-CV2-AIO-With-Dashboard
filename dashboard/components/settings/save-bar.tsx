"use client";

import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { isSaveShortcut } from "@/lib/modulePayloads";
import { fieldErrorSummary, LEAVE_MESSAGE, shouldConfirmInAppLeave, shouldGuardLeave } from "@/lib/saveGuard";

export function SaveBar({
  dirty,
  saving,
  error,
  fieldErrors,
  onSave,
  onDiscard,
}: {
  dirty: boolean;
  saving: boolean;
  error: string | null;
  fieldErrors?: Record<string, string | null | undefined>;
  onSave: () => void;
  onDiscard: () => void;
}) {
  const fieldSummary = fieldErrorSummary(fieldErrors);

  useEffect(() => {
    if (!shouldGuardLeave(dirty, false)) return;
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
      const anchor = (event.target as Element | null)?.closest("a");
      if (!anchor) return;
      if (
        !shouldConfirmInAppLeave({
          dirty: true,
          href: anchor.getAttribute("href"),
          target: anchor.getAttribute("target"),
          button: event.button,
          modified: event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.defaultPrevented,
          current: new URL(window.location.href),
        })
      ) {
        return;
      }
      if (!window.confirm(LEAVE_MESSAGE)) event.preventDefault();
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

  if (!dirty && !saving && !error && !fieldSummary) return null;

  return (
    <div className="sticky bottom-3 z-20 mt-6" data-save-bar={dirty ? "dirty" : "clean"}>
      <div className="flex flex-wrap items-center justify-between gap-3 border border-line bg-surface-2 px-3 py-2">
        <p className="text-small text-fg-2" role={error || fieldSummary ? "alert" : undefined}>
          {error ?? fieldSummary ?? (saving ? "Saving…" : "Unsaved changes")}
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
