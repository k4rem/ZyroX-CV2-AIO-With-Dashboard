"use client";

import { useCallback, useState } from "react";
import { draftsDiffer } from "@/lib/modulePayloads";

export function useDraft<T>(initial: T) {
  const [saved, setSaved] = useState(initial);
  const [draft, setDraft] = useState(initial);
  const dirty = draftsDiffer(saved, draft);
  const reset = useCallback(() => setDraft(saved), [saved]);
  const commit = useCallback((next: T) => {
    setSaved(next);
    setDraft(next);
  }, []);
  return { draft, setDraft, saved, dirty, reset, commit };
}
