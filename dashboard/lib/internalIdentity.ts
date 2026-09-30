import jwt from "jsonwebtoken";
import { randomUUID } from "crypto";

const TTL_SECONDS = parseInt(process.env.INTERNAL_IDENTITY_TTL_SECONDS || "60", 10);

export function mintInternalIdentityToken(params: {
  userId: string;
  sessionId: string;
}): string {
  const secret = process.env.INTERNAL_IDENTITY_SIGNING_KEY;
  const audience = process.env.INTERNAL_IDENTITY_AUDIENCE || "cls-fastapi";
  if (!secret) {
    throw new Error("INTERNAL_IDENTITY_SIGNING_KEY is not configured");
  }
  const now = Math.floor(Date.now() / 1000);
  return jwt.sign(
    {
      sub: params.userId,
      sid: params.sessionId,
      aud: audience,
      jti: randomUUID(),
      iat: now,
      exp: now + TTL_SECONDS,
    },
    secret,
    { algorithm: "HS256" }
  );
}
