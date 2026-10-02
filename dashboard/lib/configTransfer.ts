export const TRANSFER_STEPS = ["Upload", "Review", "Map resources", "Changes", "Apply"] as const;

export function modeLabel(mode: string) {
  return mode === "restore" ? "Restore into this server" : "Transfer into this server";
}

export function resultLabel(result: string) {
  if (result === "applied") return "Applied";
  if (result === "rolled_back") return "Failed. Rolled back";
  return result;
}

export function whenLabel(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}
