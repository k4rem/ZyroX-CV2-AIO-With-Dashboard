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

import os
from dotenv import load_dotenv

load_dotenv()

TOKEN      = os.environ.get("TOKEN")
BRAND_NAME = os.environ.get("brand_name", "Zyrox X")
NAME       = BRAND_NAME
BotName    = BRAND_NAME

server     = "https://discord.gg/codexdev"
serverLink = "https://discord.gg/codexdev"
ch         = "https://discord.com/channels/699587669059174461/1271825678710476911"

CMD_WEBHOOK_URL = os.getenv("CMD_WEBHOOK_URL")

# ── Owner / Staff IDs ─────────────────────────────────────────────────────────
# OWNER_IDS must be set in .env as comma-separated numeric Discord user IDs.

def _parse_owner_ids() -> list[int]:
    raw = os.getenv("OWNER_IDS", "").strip()
    if not raw:
        raise SystemExit(
            "Startup stopped: OWNER_IDS is missing in .env. "
            "Set OWNER_IDS to one or more comma-separated Discord user IDs."
        )
    parts = [part.strip() for part in raw.split(",") if part.strip()]
    if not parts or any(not part.isdigit() for part in parts):
        raise SystemExit(
            "Startup stopped: OWNER_IDS is invalid. "
            "Use comma-separated numeric Discord user IDs only."
        )
    return [int(part) for part in parts]

OWNER_IDS:     list[int] = _parse_owner_ids()
OWNER_IDS_STR: list[str] = [str(i) for i in OWNER_IDS]

# Aliases kept for backwards compatibility with files that import these names
BOT_OWNER_IDS     = OWNER_IDS
BOT_OWNER_IDS_STR = OWNER_IDS_STR
STAFF_IDS         = OWNER_IDS
STAFF_IDS_STR     = OWNER_IDS_STR