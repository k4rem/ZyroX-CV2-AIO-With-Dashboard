const BOT_INTERNAL_BASE =
  process.env.BOT_INTERNAL_URL || "http://127.0.0.1:8000";

export async function createDashboardSession(discordAccessToken: string): Promise<{
  sessionId: string;
  discordUserId: string;
}> {
  const key = process.env.INTERNAL_SERVICE_KEY;
  if (!key) {
    throw new Error("INTERNAL_SERVICE_KEY is not configured");
  }
  const res = await fetch(`${BOT_INTERNAL_BASE}/api/internal/v1/sessions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Internal-Service-Key": key,
    },
    body: JSON.stringify({ discord_access_token: discordAccessToken }),
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error("Failed to create dashboard session");
  }
  const data = await res.json();
  return { sessionId: data.session_id, discordUserId: data.discord_user_id };
}

export async function revokeDashboardSession(sessionId: string): Promise<void> {
  const key = process.env.INTERNAL_SERVICE_KEY;
  if (!key) return;
  try {
    await fetch(`${BOT_INTERNAL_BASE}/api/internal/v1/sessions/revoke`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Internal-Service-Key": key,
      },
      body: JSON.stringify({ session_id: sessionId }),
    });
  } catch {
    /* logout must not crash */
  }
}

export function botApiOrigin(): string {
  return BOT_INTERNAL_BASE.replace(/\/$/, "");
}
