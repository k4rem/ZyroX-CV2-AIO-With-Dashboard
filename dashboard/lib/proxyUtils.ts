export const BLOCKED_PROXY_PREFIXES = ["internal/"];

export function isBlockedProxyPath(relPath: string): boolean {
  if (relPath.includes("..")) return true;
  return BLOCKED_PROXY_PREFIXES.some((p) => relPath.startsWith(p));
}

export function assertSameOriginProxy(
  method: string,
  host: string | null,
  origin: string | null
): boolean {
  if (method === "GET" || method === "HEAD") return true;
  if (!origin || !host) return false;
  try {
    return new URL(origin).host === host;
  } catch {
    return false;
  }
}

export const STRIPPED_INBOUND_HEADERS = [
  "x-internal-service-key",
  "x-forwarded-host",
  "x-forwarded-for",
  "forwarded",
  "host",
] as const;

export function sanitizeInboundHeaders(inbound: Headers): Headers {
  const out = new Headers();
  inbound.forEach((value, key) => {
    const lk = key.toLowerCase();
    if (lk === "authorization") return;
    if (STRIPPED_INBOUND_HEADERS.includes(lk as (typeof STRIPPED_INBOUND_HEADERS)[number])) return;
    out.set(key, value);
  });
  return out;
}
