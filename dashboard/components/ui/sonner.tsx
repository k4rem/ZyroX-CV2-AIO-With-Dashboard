/**
 * ╔══════════════════════════════════════════════════════════════════╗
 * ║                                                                  ║
 * ║   ░█▀▀░█▀█░█▀▄░█▀▀░█░█   ░█▀▄░█▀▀░█░█░█▀▀                     ║
 * ║   ░█░░░█░█░█░█░█▀▀░▄▀▄   ░█░█░█▀▀░▀▄▀░▀▀█                     ║
 * ║   ░▀▀▀░▀▀▀░▀▀░░▀▀▀░▀░▀   ░▀▀░░▀▀▀░░▀░░▀▀▀                     ║
 * ║                                                                  ║
 * ║           © 2026 CodeX Devs — All Rights Reserved               ║
 * ║                                                                  ║
 * ║   discord  ──  https://discord.gg/codexdev                      ║
 * ║   youtube  ──  https://youtube.com/@CodeXDevs                   ║
 * ║   github   ──  https://github.com/RayExo                        ║
 * ║                                                                  ║
 * ╚══════════════════════════════════════════════════════════════════╝
 */

import { Toaster as Sonner } from "sonner";

type ToasterProps = React.ComponentProps<typeof Sonner>;

/** Toast theme (DS §29.5): surface-2, line-strong, radius-md. Semantic colour only as a thin border tint. */
const Toaster = ({ ...props }: ToasterProps) => {
  return (
    <Sonner
      theme="dark"
      className="toaster group"
      toastOptions={{
        classNames: {
          toast:
            "group toast group-[.toaster]:bg-surface-2 group-[.toaster]:text-fg-1 group-[.toaster]:border-line-strong group-[.toaster]:shadow-elev-1 group-[.toaster]:rounded-md group-[.toaster]:px-3 group-[.toaster]:py-2.5 group-[.toaster]:text-body",
          description: "group-[.toast]:text-fg-3 group-[.toast]:text-small",
          actionButton: "group-[.toast]:bg-brand-600 group-[.toast]:text-white",
          cancelButton: "group-[.toast]:bg-surface-3 group-[.toast]:text-fg-2",
          success: "group-[.toaster]:border-ok/40",
          error: "group-[.toaster]:border-danger/40",
          warning: "group-[.toaster]:border-warn/40",
          info: "group-[.toaster]:border-info/40",
          loading: "group-[.toaster]:border-line-strong",
        },
      }}
      {...props}
    />
  );
};

export { Toaster };
