export const LEAVE_MESSAGE = "Leave this page? Unsaved changes will be lost.";

export function shouldGuardLeave(dirty: boolean, saving: boolean): boolean {
  return dirty && !saving;
}

export function shouldConfirmInAppLeave(input: {
  dirty: boolean;
  href: string | null;
  target: string | null;
  button: number;
  modified: boolean;
  current: URL;
}): boolean {
  if (!input.dirty || input.button !== 0 || input.modified) return false;
  if (!input.href || input.href.startsWith("#") || input.target === "_blank") return false;
  let next: URL;
  try {
    next = new URL(input.href, input.current);
  } catch {
    return false;
  }
  if (next.origin !== input.current.origin) return false;
  if (next.pathname === input.current.pathname && next.search === input.current.search) return false;
  return true;
}

export function fieldErrorSummary(fieldErrors: Record<string, string | null | undefined> | null | undefined): string | null {
  if (!fieldErrors) return null;
  const messages = Object.values(fieldErrors).map((value) => value?.trim()).filter((value): value is string => Boolean(value));
  return messages.length ? messages.join(" ") : null;
}
