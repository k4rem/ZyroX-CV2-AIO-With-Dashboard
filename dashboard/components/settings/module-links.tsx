import Link from "next/link";
import { cn } from "@/lib/utils";

export function ModuleLinks({
  label,
  links,
}: {
  label: string;
  links: { href: string; label: string; current?: boolean }[];
}) {
  return (
    <nav aria-label={label} className="mb-4 flex flex-wrap gap-1">
      {links.map((link) => (
        <Link
          key={link.href}
          href={link.href}
          aria-current={link.current ? "page" : undefined}
          className={cn(
            "inline-flex h-8 items-center rounded-sm px-3 text-small",
            link.current ? "border-s-2 border-brand-500 bg-surface-3 ps-2.5 text-fg-1" : "text-fg-3 hover:bg-surface-3 hover:text-fg-2",
          )}
        >
          {link.label}
        </Link>
      ))}
    </nav>
  );
}
