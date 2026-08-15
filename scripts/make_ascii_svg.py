"""
make_ascii_svg.py

Converts a prepped grayscale photo into a monochrome, self-typing ASCII
art SVG. Each row wipes in left-to-right (a small block cursor rides the
wipe edge), staggered top to bottom. Prints once and freezes -- no loop.

Usage:
    python scripts/make_ascii_svg.py [prepped.png] [output.svg]
"""
import sys
from xml.sax.saxutils import escape
from PIL import Image

RAMP = " .`:-=+*cs#%@"  # bright (sparse) -> dark (dense); leading space = blank
COLS = 100
CHAR_W = 6.0
CHAR_H = 11.0
FONT_SIZE = 11
FILL_COLOR = "#c9d1d9"   # light gray, monochrome (no per-char rainbow)
BG_COLOR = "transparent"
ROW_STAGGER = 0.045       # seconds between each row starting its wipe
WIPE_DURATION = 0.5       # seconds for a single row's wipe animation


def image_to_ascii_rows(path: str, cols: int = COLS):
    img = Image.open(path).convert("L")
    w, h = img.size
    # characters are taller than wide, so compress rows accordingly
    aspect_correct = 0.5
    rows = max(1, round((h / w) * cols * aspect_correct))
    small = img.resize((cols, rows))
    pixels = small.load()

    ramp_len = len(RAMP)
    ascii_rows = []
    for y in range(rows):
        line = []
        for x in range(cols):
            brightness = pixels[x, y]  # 0 (dark) - 255 (bright)
            idx = int((255 - brightness) / 255 * (ramp_len - 1))
            line.append(RAMP[idx])
        ascii_rows.append("".join(line))
    return ascii_rows


def build_svg(ascii_rows, out_path: str):
    n_rows = len(ascii_rows)
    n_cols = max(len(r) for r in ascii_rows) if ascii_rows else 0
    width = n_cols * CHAR_W
    height = n_rows * CHAR_H + 10

    parts = []
    parts.append(
        f'<svg viewBox="0 0 {width:.0f} {height:.0f}" '
        f'xmlns="http://www.w3.org/2000/svg" font-family="monospace" '
        f'font-size="{FONT_SIZE}">'
    )
    parts.append(f'<style>text{{fill:{FILL_COLOR};white-space:pre;}}</style>')

    for i, row in enumerate(ascii_rows):
        row_width = len(row) * CHAR_W
        y = (i + 1) * CHAR_H
        begin = i * ROW_STAGGER
        clip_id = f"clip{i}"

        parts.append(f'<clipPath id="{clip_id}">')
        parts.append(
            f'  <rect x="0" y="{y - CHAR_H:.1f}" width="0" height="{CHAR_H:.1f}">'
        )
        parts.append(
            f'    <animate attributeName="width" from="0" to="{row_width:.1f}" '
            f'begin="{begin:.3f}s" dur="{WIPE_DURATION}s" fill="freeze" '
            f'calcMode="linear" />'
        )
        parts.append('  </rect>')
        parts.append('</clipPath>')

        parts.append(f'<g clip-path="url(#{clip_id})">')
        parts.append(f'  <text x="0" y="{y:.1f}">{escape(row)}</text>')
        parts.append('</g>')

        # small cursor block riding the wipe edge, disappears when the row is done
        parts.append(
            f'<rect x="0" y="{y - CHAR_H:.1f}" width="{CHAR_W:.1f}" '
            f'height="{CHAR_H:.1f}" fill="{FILL_COLOR}" opacity="0.85">'
        )
        parts.append(
            f'  <animate attributeName="x" from="0" to="{row_width:.1f}" '
            f'begin="{begin:.3f}s" dur="{WIPE_DURATION}s" fill="freeze" '
            f'calcMode="linear" />'
        )
        parts.append(
            f'  <animate attributeName="opacity" from="0.85" to="0" '
            f'begin="{begin + WIPE_DURATION:.3f}s" dur="0.15s" fill="freeze" />'
        )
        parts.append('</rect>')

    parts.append('</svg>')

    with open(out_path, "w") as f:
        f.write("\n".join(parts))
    print(f"Wrote {out_path} ({n_cols}x{n_rows} chars, {width:.0f}x{height:.0f}px)")


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "prepped.png"
    out = sys.argv[2] if len(sys.argv) > 2 else "ascii-portrait.svg"
    rows = image_to_ascii_rows(src)
    build_svg(rows, out)
