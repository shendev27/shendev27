"""
make_info_card.py

Hand-authors a neofetch-style SVG panel: a title bar, then colored
key/value rows. Each line fades and slides in on a short stagger.

Set STATIC=1 to emit a frozen (fully-visible, no animation) frame for
local Quick Look previews.

Usage:
    python scripts/make_info_card.py
    STATIC=1 python scripts/make_info_card.py
"""
import os

USERNAME = "shendev27"
HOSTNAME = "github"

FIELDS = [
    ("Now", "Software Engineer"),
    ("Stack", "Next.js, TypeScript, Python, PostgreSQL"),
    ("Interests", "AI/ML, Cybersecurity, OSINT"),
    ("Projects", "Vibe Check, Opensourcerer, Mentory"),
]

WIDTH = 490
LINE_H = 30
PAD_TOP = 56
FONT_SIZE = 14
TITLE_FONT_SIZE = 16
ACCENT = "#39d353"     # GitHub-green accent for keys
FG = "#c9d1d9"          # value text
BG = "#0d1117"
BORDER = "#30363d"
STAGGER = 0.12
DURATION = 0.35

STATIC = os.environ.get("STATIC") == "1"


def build_svg(out_path="info-card.svg"):
    height = PAD_TOP + LINE_H * len(FIELDS) + 24

    parts = []
    parts.append(
        f'<svg viewBox="0 0 {WIDTH} {height}" xmlns="http://www.w3.org/2000/svg" '
        f'font-family="monospace">'
    )
    parts.append(
        f'<rect x="0.5" y="0.5" width="{WIDTH-1}" height="{height-1}" rx="8" '
        f'fill="{BG}" stroke="{BORDER}" />'
    )
    # fake title bar dots
    for i, c in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        parts.append(f'<circle cx="{20 + i*18}" cy="20" r="6" fill="{c}" />')

    parts.append(
        f'<text x="{WIDTH/2}" y="25" text-anchor="middle" '
        f'font-size="{TITLE_FONT_SIZE}" fill="{FG}" opacity="0.85">'
        f'{USERNAME}@{HOSTNAME}</text>'
    )
    parts.append(
        f'<line x1="16" y1="40" x2="{WIDTH-16}" y2="40" stroke="{BORDER}" />'
    )

    for i, (key, value) in enumerate(FIELDS):
        y = PAD_TOP + i * LINE_H
        begin = i * STAGGER

        if STATIC:
            opacity_attr = 'opacity="1"'
            transform_attr = ''
            anim = ''
        else:
            opacity_attr = 'opacity="0"'
            transform_attr = f'transform="translate(-12,0)"'
            anim = (
                f'<animate attributeName="opacity" from="0" to="1" '
                f'begin="{begin:.2f}s" dur="{DURATION}s" fill="freeze" />'
                f'<animateTransform attributeName="transform" type="translate" '
                f'from="-12,0" to="0,0" begin="{begin:.2f}s" dur="{DURATION}s" '
                f'fill="freeze" additive="replace" />'
            )

        parts.append(f'<g {opacity_attr} {transform_attr}>{anim}')
        parts.append(
            f'  <text x="24" y="{y}" font-size="{FONT_SIZE}" fill="{ACCENT}" '
            f'font-weight="bold">{key}</text>'
        )
        parts.append(
            f'  <text x="140" y="{y}" font-size="{FONT_SIZE}" fill="{FG}">'
            f'{value}</text>'
        )
        parts.append('</g>')

    parts.append('</svg>')

    with open(out_path, "w") as f:
        f.write("\n".join(parts))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    build_svg()
