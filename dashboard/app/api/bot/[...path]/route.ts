import { getServerSession } from "next-auth";
import { NextRequest, NextResponse } from "next/server";
import { authOptions } from "@/lib/auth";
import { mintInternalIdentityToken } from "@/lib/internalIdentity";
import { botApiOrigin } from "@/lib/botInternal";
import {
  assertSameOriginProxy,
  isBlockedProxyPath,
  sanitizeInboundHeaders,
} from "@/lib/proxyUtils";

const UPSTREAM_PREFIX = "/api/v1";

async function proxy(request: NextRequest, pathSegments: string[]) {
  if (
    !assertSameOriginProxy(
      request.method,
      request.headers.get("host"),
      request.headers.get("origin")
    )
  ) {
    return NextResponse.json({ detail: "Forbidden" }, { status: 403 });
  }

  const rel = pathSegments.join("/");
  if (isBlockedProxyPath(rel)) {
    return NextResponse.json({ detail: "Forbidden" }, { status: 403 });
  }

  const session = await getServerSession(authOptions);
  const dashboardSessionId = (session as { dashboardSessionId?: string } | null)
    ?.dashboardSessionId;
  const userId = session?.user?.id;
  if (!session || !dashboardSessionId || !userId) {
    return NextResponse.json({ detail: "Authentication required" }, { status: 401 });
  }

  let identityToken: string;
  try {
    identityToken = mintInternalIdentityToken({
      userId,
      sessionId: dashboardSessionId,
    });
  } catch {
    return NextResponse.json({ detail: "Server misconfigured" }, { status: 503 });
  }

  const upstreamPath = `${UPSTREAM_PREFIX}/${rel}`.replace(/\/+/g, "/");
  const url = new URL(upstreamPath, botApiOrigin());
  request.nextUrl.searchParams.forEach((v, k) => url.searchParams.set(k, v));

  const headers = sanitizeInboundHeaders(request.headers);
  headers.set("Authorization", `Bearer ${identityToken}`);
  const contentType = request.headers.get("content-type");
  if (contentType) {
    headers.set("Content-Type", contentType);
  }

  const init: RequestInit = {
    method: request.method,
    headers,
    cache: "no-store",
  };
  if (request.method !== "GET" && request.method !== "HEAD") {
    init.body = await request.arrayBuffer();
  }

  let upstream: Response;
  try {
    upstream = await fetch(url.toString(), init);
  } catch {
    return NextResponse.json({ detail: "Upstream unavailable" }, { status: 502 });
  }

  const body = await upstream.arrayBuffer();
  return new NextResponse(body, {
    status: upstream.status,
    headers: {
      "Content-Type": upstream.headers.get("content-type") || "application/json",
    },
  });
}

type Ctx = { params: Promise<{ path: string[] }> };

export async function GET(request: NextRequest, ctx: Ctx) {
  const { path } = await ctx.params;
  return proxy(request, path);
}

export async function POST(request: NextRequest, ctx: Ctx) {
  const { path } = await ctx.params;
  return proxy(request, path);
}

export async function PATCH(request: NextRequest, ctx: Ctx) {
  const { path } = await ctx.params;
  return proxy(request, path);
}

export async function DELETE(request: NextRequest, ctx: Ctx) {
  const { path } = await ctx.params;
  return proxy(request, path);
}

export async function PUT(request: NextRequest, ctx: Ctx) {
  const { path } = await ctx.params;
  return proxy(request, path);
}
