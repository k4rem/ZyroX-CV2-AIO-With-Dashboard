import Link from "next/link";
import { ClsMark } from "@/components/brand/cls-mark";
import { CLS_DISCORD_INVITE_URL, hasClsDiscordInvite } from "@/lib/publicLinks";

const footerLinkClass =
  "inline-flex min-h-11 items-center text-fg-2 hover:text-fg-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-400 focus-visible:ring-offset-2 focus-visible:ring-offset-void rounded-sm px-1";

export function LandingFooter() {
  return (
    <footer className="border-t border-line-subtle bg-chrome/40">
      <div className="cls-public-container flex min-h-12 flex-col items-start justify-between gap-4 py-4 text-caption text-fg-3 md:flex-row md:items-center">
        <div className="flex items-center gap-2">
          <ClsMark height={16} />
          <span className="cls-wordmark text-fg-2">CLS OS</span>
        </div>
        <nav className="flex flex-wrap items-center gap-x-3 gap-y-1">
          <Link href="/privacy" className={footerLinkClass}>
            Privacy
          </Link>
          <Link href="/terms" className={footerLinkClass}>
            Terms
          </Link>
          {hasClsDiscordInvite() ? (
            <a href={CLS_DISCORD_INVITE_URL} target="_blank" rel="noopener noreferrer" className={footerLinkClass}>
              CLS Discord
            </a>
          ) : null}
        </nav>
        <p className="text-fg-3">Private system. Access by grant only.</p>
      </div>
    </footer>
  );
}
