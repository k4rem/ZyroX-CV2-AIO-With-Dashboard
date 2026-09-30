"""Phase 0 module load health tracking."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Type

from colorama import Fore, Style


@dataclass
class ModuleHealth:
    required_ok: list[str] = field(default_factory=list)
    required_failed: list[tuple[str, str]] = field(default_factory=list)
    optional_ok: list[str] = field(default_factory=list)
    optional_failed: list[tuple[str, str]] = field(default_factory=list)
    optional_skipped: list[str] = field(default_factory=list)

    @property
    def healthy(self) -> bool:
        return len(self.required_failed) == 0

    def record_ok(self, name: str, required: bool) -> None:
        if required:
            self.required_ok.append(name)
        else:
            self.optional_ok.append(name)

    def record_fail(self, name: str, required: bool, error: Exception) -> None:
        msg = f"{type(error).__name__}: {error}"
        if required:
            self.required_failed.append((name, msg))
        else:
            self.optional_failed.append((name, msg))

    def record_skipped(self, name: str, reason: str) -> None:
        self.optional_skipped.append(f"{name} ({reason})")

    def print_summary(self) -> None:
        print(Fore.CYAN + Style.BRIGHT + "\n=== Module health summary ===")
        print("Required:")
        for name in self.required_ok:
            print(Fore.GREEN + f"  {name} ✅")
        for name, err in self.required_failed:
            print(Fore.RED + Style.BRIGHT + f"  {name} ❌ — {err}")
        print("Optional:")
        for name in self.optional_ok:
            print(Fore.GREEN + f"  {name} ✅")
        for name, err in self.optional_failed:
            print(Fore.YELLOW + f"  {name} ⚠ — {err}")
        for line in self.optional_skipped:
            print(Fore.YELLOW + f"  {line}")
        if not self.healthy:
            print(
                Fore.RED
                + Style.BRIGHT
                + "BOT UNHEALTHY: one or more required modules failed to load."
            )
        print(Fore.CYAN + Style.BRIGHT + "=============================\n")


async def add_cog_safe(
    bot,
    cog_cls: Type,
    health: ModuleHealth,
    *,
    required: bool = False,
    skip: bool = False,
    skip_reason: str = "",
) -> None:
    name = cog_cls.__name__
    if skip:
        health.record_skipped(name, skip_reason or "disabled")
        return
    try:
        await bot.add_cog(cog_cls(bot))
        health.record_ok(name, required)
    except Exception as exc:
        health.record_fail(name, required, exc)
        if required:
            print(Fore.RED + Style.BRIGHT + f"Required cog failed: {name} — {exc}")


def required_modules_report(bot) -> dict:
    """Dashboard-safe module health snapshot (no secrets)."""
    health: ModuleHealth | None = getattr(bot, "module_health", None)
    if health is None:
        return {
            "healthy": True,
            "required_ok": [],
            "required_failed": [],
            "optional_ok": [],
            "optional_failed": [],
        }
    return {
        "healthy": health.healthy,
        "required_ok": list(health.required_ok),
        "required_failed": [{"name": n, "error": e} for n, e in health.required_failed],
        "optional_ok": list(health.optional_ok),
        "optional_failed": [{"name": n, "error": e} for n, e in health.optional_failed],
    }
