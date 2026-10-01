"""Image uploads: magic bytes, Pillow re-encode, size cap, safe keys."""

from __future__ import annotations

import io
import re
import uuid

from PIL import Image, UnidentifiedImageError

MAX_BYTES = 4 * 1024 * 1024
KEY_RE = re.compile(r"^[a-f0-9]{32}\.png$")


class MediaError(ValueError):
    pass


def inspect_image(data: bytes) -> bytes:
    if not data:
        raise MediaError("Choose an image file")
    if len(data) > MAX_BYTES:
        raise MediaError("Images must be 4 MB or smaller")
    if data.startswith(b"<") or data.startswith(b"<?xml") or b"<svg" in data[:200].lower():
        raise MediaError("SVG images are not allowed")
    try:
        with Image.open(io.BytesIO(data)) as image:
            image.verify()
        with Image.open(io.BytesIO(data)) as image:
            if image.format not in {"PNG", "JPEG", "GIF", "WEBP"}:
                raise MediaError("Use a PNG, JPEG, GIF, or WebP image")
            converted = image.convert("RGBA")
            out = io.BytesIO()
            converted.save(out, format="PNG")
    except MediaError:
        raise
    except (UnidentifiedImageError, OSError) as exc:
        raise MediaError("That file is not a valid image") from exc
    encoded = out.getvalue()
    if len(encoded) > MAX_BYTES:
        raise MediaError("Images must be 4 MB or smaller")
    return encoded


def new_key() -> str:
    return uuid.uuid4().hex + ".png"


def valid_key(key: str) -> bool:
    return bool(KEY_RE.fullmatch(key or ""))
