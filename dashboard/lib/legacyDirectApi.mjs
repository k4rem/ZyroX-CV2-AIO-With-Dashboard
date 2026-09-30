/**
 * Phase 0: legacy browser → FastAPI gate (testable without Next.js build).
 */

export function evaluateLegacyDirectBotApi(env) {
  const nodeEnv = env.NODE_ENV || "";
  if (nodeEnv === "production") {
    return {
      allowed: false,
      reason:
        "Legacy direct bot API is disabled in production. Phase 1 requires an authenticated Next.js server-side proxy.",
    };
  }
  if (env.NEXT_PUBLIC_LEGACY_DIRECT_BOT_API !== "true") {
    return {
      allowed: false,
      reason:
        "Dashboard bot API access is disabled for Phase 0. Set NEXT_PUBLIC_LEGACY_DIRECT_BOT_API=true only for local development.",
    };
  }
  return { allowed: true };
}
