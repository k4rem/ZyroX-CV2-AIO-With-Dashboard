# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                  ║
# ║   ░█▀▀░█▀█░█▀▄░█▀▀░█░█   ░█▀▄░█▀▀░█░█░█▀▀                     ║
# ║   ░█░░░█░█░█░█░█▀▀░▄▀▄   ░█░█░█▀▀░▀▄▀░▀▀█                     ║
# ║   ░▀▀▀░▀▀▀░▀▀░░▀▀▀░▀░▀   ░▀▀░░▀▀▀░░▀░░▀▀▀                     ║
# ║                                                                  ║
# ║            © 2026 CodeX Devs — All Rights Reserved              ║
# ║                                                                  ║
# ║   discord  ──  https://discord.gg/codexdev                      ║
# ║   youtube  ──  https://youtube.com/@CodeXDevs                   ║
# ║   github   ──  https://github.com/RayExo                        ║
# ║                                                                  ║
# ╚══════════════════════════════════════════════════════════════════╝

"""
HTTPS Tunnel for the ZyroX API using a preinstalled Cloudflare binary.

The bot never installs packages or downloads executables at runtime.
Install ``cloudflared`` during deployment and make it available on PATH.

──────────────────────────────────────────────────────────────────────────────
How to get your CF_TUNNEL_TOKEN (browser only, no CLI needed)
──────────────────────────────────────────────────────────────────────────────
1. Go to https://one.dash.cloudflare.com
2. Networks → Tunnels → Create a tunnel
3. Choose "Cloudflared" as connector type
4. Give it a name (e.g. zyrox-api) and click Save
5. On the "Install connector" step, find the token in the command shown:
      cloudflared tunnel run --token <YOUR_TOKEN_HERE>
   Copy just the token string.
6. Go to "Published Application Routes" tab → Add a Published Application Routes:
      Subdomain: zyrox-api   Domain: yourdomain.com   Service: http://localhost:8000
   (Or use any domain you have on Cloudflare)
7. Paste the token into your .env:
      CF_TUNNEL_TOKEN = "eyJhIjoiX..."
      CF_TUNNEL_URL   = "https://zyrox-api.yourdomain.com"

That's the permanent URL — never changes between restarts.
Unlimited bandwidth, unlimited requests, free.
──────────────────────────────────────────────────────────────────────────────
"""

import os
import time
import threading
import subprocess
import shutil

# ── env vars ──────────────────────────────────────────────────────────────────
TUNNEL_ENABLED = os.getenv("TUNNEL_ENABLED", "false").strip().lower() == "true"
CF_TUNNEL_TOKEN = os.getenv("CF_TUNNEL_TOKEN", "").strip()   # token from Cloudflare dashboard
CF_TUNNEL_URL   = os.getenv("CF_TUNNEL_URL", "").strip()     # e.g. https://api.yourdomain.com
API_PORT        = int(os.getenv("API_PORT", "8000"))

# ── colours ───────────────────────────────────────────────────────────────────
_CYAN   = "\033[36m"
_GREEN  = "\033[32m"
_YELLOW = "\033[33m"
_RED    = "\033[31m"
_RESET  = "\033[0m"


def _get_binary() -> str | None:
    """Return the preinstalled cloudflared executable from PATH."""
    return shutil.which("cloudflared")


def _run_tunnel(binary: str, token: str, port: int, public_url: str) -> None:
    """
    Blocking loop — runs:
      cloudflared tunnel --no-autoupdate run --token <token>
    Restarts automatically if the process exits.
    """
    cmd = [
        binary,
        "tunnel",
        "--no-autoupdate",
        "--url", f"http://localhost:{port}",
        "run",
        "--token", token,
    ]

    first_run = True
    while True:
        if first_run:
            print(f"{_CYAN}◈ Tunnel: connecting to Cloudflare…{_RESET}")
            first_run = False
        else:
            print(f"{_YELLOW}◈ Tunnel: reconnecting…{_RESET}")

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )

            announced = False
            for line in proc.stdout:
                line = line.rstrip()
                if not line:
                    continue

                # Only surface important lines — suppress the noisy info spam
                low = line.lower()
                if any(k in low for k in ("error", "warn", "registered", "connected", "failed", "unable")):
                    print(f"{_CYAN}  [cloudflared] {line}{_RESET}")

                # Announce the live URL once the tunnel is up
                if not announced and ("registered tunnel connection" in low or "connection registered" in low):
                    announced = True
                    if public_url:
                        print(f"{_GREEN}◈ Tunnel: API is live at  {public_url}{_RESET}")
                        print(f"{_CYAN}  ↳ NEXT_PUBLIC_API_URL = {public_url}/api/v1{_RESET}")
                    else:
                        print(f"{_GREEN}◈ Tunnel: connected — check CF_TUNNEL_URL in .env for your public URL{_RESET}")

            proc.wait()
            code = proc.returncode

        except (FileNotFoundError, PermissionError) as exc:
            print(f"{_RED}◈ Tunnel: failed to execute binary at '{binary}' — {exc}{_RESET}")
            print(f"{_RED}  Check: file exists, has execute permission, and matches the server OS/arch.{_RESET}")
            return
        except Exception as exc:
            print(f"{_RED}◈ Tunnel: unexpected error — {exc}{_RESET}")
            code = -1

        print(f"{_YELLOW}◈ Tunnel: exited (code {code}), restarting in 5 s…{_RESET}")
        time.sleep(5)


def start_tunnel() -> None:
    """
    Start the Cloudflare Tunnel in a background daemon thread.
    Called from CodeX.py after keep_alive().
    """
    if not TUNNEL_ENABLED:
        print(f"{_YELLOW}◈ Tunnel: disabled (TUNNEL_ENABLED is not true){_RESET}")
        return

    if not CF_TUNNEL_TOKEN:
        print(
            f"{_YELLOW}◈ Tunnel: CF_TUNNEL_TOKEN is not set — tunnel skipped.\n"
            f"  Get your token from https://one.dash.cloudflare.com → Networks → Tunnels{_RESET}"
        )
        return

    binary = _get_binary()
    if not binary:
        print(
            f"{_RED}◈ Tunnel: cloudflared is not installed or is not on PATH.\n"
            f"  Tunnel skipped. Install a reviewed cloudflared binary during deployment; "
            f"the bot will not download or install it.{_RESET}"
        )
        return

    print(f"{_CYAN}◈ Tunnel: cloudflared binary ready — starting tunnel on port {API_PORT}…{_RESET}")
    t = threading.Thread(target=_run_tunnel, args=(binary, CF_TUNNEL_TOKEN, API_PORT, CF_TUNNEL_URL), daemon=True)
    t.start()
