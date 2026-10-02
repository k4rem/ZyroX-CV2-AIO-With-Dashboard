/** A failed load is an error with a retry. It is not an empty collection. */

export function loadFailure(error: unknown, title: string) {
  const technical = error instanceof Error && error.message ? error.message : null;
  return {
    title,
    message: "This could not be loaded. Retry, or check that CLS is online.",
    reference: technical,
    action: "retry" as const,
    pretendEmpty: false,
  };
}
