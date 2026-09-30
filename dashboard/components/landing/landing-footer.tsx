import Link from "next/link";
import { ClsMark } from "@/components/brand/cls-mark";
import { CLS_DISCORD_INVITE_URL } from "@/lib/publicLinks";

export function LandingFooter() {
  return (
    <footer className="border-t border-line-subtle bg-chrome/40">
      <div className="mx-auto flex min-h-12 max-w-6xl flex-col items-start justify-between gap-4 px-4 py-4 text-caption text-fg-3 md:flex-row md:items-center md:px-6">
        <div className="flex items-center gap-2">
          <ClsMark height={16} />
          <span className="cls-wordmark text-fg-2">CLS OS</span>
        </div>
        <nav className="flex flex-wrap items-center gap-x-5 gap-y-2">
          <Link href="/privacy" className="text-fg-2 hover:text-fg-1">
            Privacy
          </Link>
          <Link href="/terms" className="text-fg-2 hover:text-fg-1">
            Terms
          </Link>
          <a
            href={CLS_DISCORD_INVITE_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="text-fg-2 hover:text-fg-1"
          >
            CLS Discord
          </a>
        </nav>
        <p className="text-fg-3">Private system. Access by grant only.</p>
      </div>
    </footer>
  );
}
