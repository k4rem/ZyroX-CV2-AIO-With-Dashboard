"""Rasterize the small CLS tab mark from a 16px grid. No font files."""

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT / "public" / "brand"
APP = ROOT / "app"
PURPLE = (118, 70, 242, 255)
CANVAS = (9, 8, 13, 255)

# 16×16. C on the left, S on the right, 2px strokes, 1px margin.
GRID = (
    "................",
    ".######.#######.",
    ".######.#######.",
    ".##.....##......",
    ".##.....##......",
    ".##.....##......",
    ".##.....##......",
    ".##.....#######.",
    ".##.....#######.",
    ".##..........##.",
    ".##..........##.",
    ".##..........##.",
    ".##..........##.",
    ".######.#######.",
    ".######.#######.",
    "................",
)


def mark(scale: int) -> Image.Image:
    size = 16 * scale
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    for y, row in enumerate(GRID):
        if len(row) != 16:
            raise SystemExit(f"row {y} is {len(row)}")
        for x, cell in enumerate(row):
            if cell == "#":
                draw.rectangle((x * scale, y * scale, (x + 1) * scale - 1, (y + 1) * scale - 1), fill=PURPLE)
    return image


def svg() -> str:
    rects = []
    for y, row in enumerate(GRID):
        for x, cell in enumerate(row):
            if cell == "#":
                rects.append(f'<rect x="{x}" y="{y}" width="1" height="1"/>')
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" shape-rendering="crispEdges" role="img" aria-label="CLS">'
        '<g fill="#7646F2">' + "".join(rects) + "</g></svg>\n"
    )


def on_canvas(size: int, mark_size: int) -> Image.Image:
    image = Image.new("RGBA", (size, size), CANVAS)
    glyph = mark(mark_size // 16)
    offset = (size - glyph.size[0]) // 2
    image.paste(glyph, (offset, offset), glyph)
    return image


def main() -> None:
    BRAND.mkdir(parents=True, exist_ok=True)
    text = svg()
    (BRAND / "cls-icon.svg").write_text(text, encoding="utf-8")
    (APP / "icon.svg").write_text(text, encoding="utf-8")
    icon16 = mark(1)
    icon32 = mark(2)
    icon16.save(BRAND / "cls-icon-16.png")
    icon32.save(BRAND / "cls-icon-32.png")
    mark(12).save(BRAND / "cls-icon-192.png")
    mark(32).save(BRAND / "cls-icon-512.png")
    on_canvas(180, 144).save(BRAND / "cls-apple-icon.png")
    on_canvas(180, 144).save(APP / "apple-icon.png")
    on_canvas(512, 384).save(BRAND / "cls-icon-maskable-512.png")
    icon32.save(APP / "favicon.ico", format="ICO", sizes=[(16, 16), (32, 32)])
    icon32.save(ROOT / "public" / "favicon.ico", format="ICO", sizes=[(16, 16), (32, 32)])
    (ROOT / "public" / "manifest.webmanifest").write_text(
        """{
  "name": "CLS OS",
  "short_name": "CLS OS",
  "display": "standalone",
  "background_color": "#09080d",
  "theme_color": "#040306",
  "icons": [
    { "src": "/brand/cls-icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/brand/cls-icon-512.png", "sizes": "512x512", "type": "image/png" },
    { "src": "/brand/cls-icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }
  ]
}
""",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
