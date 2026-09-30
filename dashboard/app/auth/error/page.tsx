import { AuthErrorClient } from "./auth-error-client";

export default function AuthErrorPage({
  searchParams,
}: {
  searchParams: { error?: string };
}) {
  return <AuthErrorClient code={searchParams.error ?? null} />;
}
