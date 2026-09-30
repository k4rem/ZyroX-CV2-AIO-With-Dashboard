/**
 * Discord snowflakes must stay decimal strings in JS (never Number / parseInt).
 */

export const SNOWFLAKE_PATTERN = /^\d{17,20}$/;

export function isSnowflakeString(value: unknown): value is string {
  return typeof value === "string" && SNOWFLAKE_PATTERN.test(value);
}

/** Normalize user/API input to a snowflake string or null if invalid. */
export function normalizeSnowflakeInput(raw: string): string | null {
  const s = raw.trim();
  return SNOWFLAKE_PATTERN.test(s) ? s : null;
}

/** Comma-separated role/channel IDs → unique valid snowflake strings. */
export function parseCommaSeparatedSnowflakes(raw: string): string[] {
  const out: string[] = [];
  for (const part of raw.split(",")) {
    const id = normalizeSnowflakeInput(part);
    if (id && !out.includes(id)) out.push(id);
  }
  return out;
}

export function compareSnowflakes(a: string, b: string): boolean {
  return a.trim() === b.trim();
}

/** Coerce JSON values that may have been numbers (legacy) — prefer backend string fixes. */
export function coerceIdToString(value: unknown): string | null {
  if (value == null || value === "") return null;
  if (typeof value === "string") return normalizeSnowflakeInput(value) ?? value;
  if (typeof value === "number" && Number.isSafeInteger(value)) return String(value);
  return String(value);
}
