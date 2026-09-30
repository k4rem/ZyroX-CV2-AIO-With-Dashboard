import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { mintInternalIdentityToken } from "@/lib/internalIdentity";
import { botApiOrigin } from "@/lib/botInternal";
import { ApiError } from "@/lib/api";

export async function serverBotRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const session = await getServerSession(authOptions);
  const dashboardSessionId = (session as { dashboardSessionId?: string } | null)
    ?.dashboardSessionId;
  const userId = session?.user?.id;
  if (!session || !dashboardSessionId || !userId) {
    throw new ApiError(401, "Authentication required");
  }

  const token = mintInternalIdentityToken({ userId, sessionId: dashboardSessionId });
  const url = `${botApiOrigin()}/api/v1${endpoint}`;
  const headers = new Headers(options.headers);
  headers.set("Authorization", `Bearer ${token}`);
  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(url, {
    ...options,
    headers,
    cache: "no-store",
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const data = await response.json();
      detail = data.detail || detail;
    } catch {
      /* ignore */
    }
    throw new ApiError(response.status, detail);
  }

  return response.json();
}
