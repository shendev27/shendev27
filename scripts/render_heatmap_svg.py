"""
render_heatmap_svg.py

Renders data/contributions.json as the classic 53-week x 7-day
contribution calendar of rounded, colored boxes using a GitHub-ish
green ramp. Reveals once with a diagonal, line-after-line slide-down
(plays on load, then freezes -- no looping). Adds a Less->More legend
and a stats footer.

Usage:
    python scripts/render_heatmap_svg.py
"""
import json
from datetime import datetime, timedelta

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
#          none ->                                          brightest (neon top end)

DATA_PATH = "data/contributions.json"
OUT_PATH = "contrib-heatmap.svg"

BOX = 11
GAP = 3
LEFT_PAD = 30
TOP_PAD = 30
FONT = "monospace"
FG = "#8b949e"
STAGGER = 0.012   # per-column stagger (diagonal reveal)
DURATION = 0.35

WEEKDAY_LABELS = {1: "Mon", 3: "Wed", 5: "Fri"}  # Mon=0 .. Sun=6 (Python weekday)
MONTH_ABBR = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]


def level_to_color(level: int) -> str:
    level = max(0, min(level, len(PALETTE) - 1))
    return PALETTE[level]


def build_weeks(days):
    """Group days into GitHub-style weeks (columns), each column Sun-Sat."""
    by_date = {d["date"]: d for d in days}
    if not days:
        return []

    all_dates = sorted(by_date.keys())
    start = datetime.strptime(all_dates[0], "%Y-%m-%d")
    end = datetime.strptime(all_dates[-1], "%Y-%m-%d")

    # back up to the most recent Sunday on/before start
    start -= timedelta(days=(start.weekday() + 1) % 7)

    weeks = []
    cur = start
    while cur <= end:
        week = []
        for i in range(7):
            day_str = cur.strftime("%Y-%m-%d")
            entry = by_date.get(day_str)
            week.append(entry if entry else {"date": day_str, "level": 0, "count": 0})
            cur += timedelta(days=1)
        weeks.append(week)
    return weeks


def build_svg(data, out_path=OUT_PATH):
    days = data["days"]
    stats = data["stats"]
    username = data.get("username", "")

    weeks = build_weeks(days)
    n_weeks = len(weeks)

    grid_w = n_weeks * (BOX + GAP)
    grid_h = 7 * (BOX + GAP)
    width = LEFT_PAD + grid_w + 20
    height = TOP_PAD + grid_h + 60  # extra for legend + footer

    parts = []
    parts.append(
        f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" '
        f'font-family="{FONT}">'
    )
    parts.append(f'<style>text{{fill:{FG};}}</style>')

    # month labels along the top
    last_month = None
    for wi, week in enumerate(weeks):
        first_day = datetime.strptime(week[0]["date"], "%Y-%m-%d")
        month = first_day.month
        if month != last_month:
            x = LEFT_PAD + wi * (BOX + GAP)
            parts.append(
                f'<text x="{x}" y="{TOP_PAD - 10}" font-size="10">'
                f'{MONTH_ABBR[month-1]}</text>'
            )
            last_month = month

    # weekday labels down the left
    for wd, label in WEEKDAY_LABELS.items():
        y = TOP_PAD + wd * (BOX + GAP) + BOX - 2
        parts.append(f'<text x="0" y="{y}" font-size="9">{label}</text>')

    # grid of boxes, diagonal reveal (stagger by col+row)
    for wi, week in enumerate(weeks):
        for di, day in enumerate(week):
            x = LEFT_PAD + wi * (BOX + GAP)
            y = TOP_PAD + di * (BOX + GAP)
            color = level_to_color(day["level"])
            begin = (wi + di) * STAGGER
            count = day.get("count")
            title = f'{day["date"]}: {count if count is not None else "?"} contributions'

            parts.append(
                f'<rect x="{x}" y="{y}" width="{BOX}" height="{BOX}" rx="2" ry="2" '
                f'fill="{color}" opacity="0">'
                f'<title>{title}</title>'
                f'<animate attributeName="opacity" from="0" to="1" '
                f'begin="{begin:.3f}s" dur="{DURATION}s" fill="freeze" />'
                f'<animateTransform attributeName="transform" type="translate" '
                f'from="0,-6" to="0,0" begin="{begin:.3f}s" dur="{DURATION}s" '
                f'fill="freeze" additive="sum" />'
                f'</rect>'
            )

    # legend: Less -> More
    legend_y = TOP_PAD + grid_h + 24
    legend_x = LEFT_PAD
    parts.append(f'<text x="{legend_x}" y="{legend_y+9}" font-size="10">Less</text>')
    lx = legend_x + 34
    for i, color in enumerate(PALETTE):
        parts.append(
            f'<rect x="{lx + i*(BOX+3)}" y="{legend_y}" width="{BOX}" height="{BOX}" '
            f'rx="2" ry="2" fill="{color}" />'
        )
    parts.append(
        f'<text x="{lx + len(PALETTE)*(BOX+3) + 6}" y="{legend_y+9}" font-size="10">'
        f'More</text>'
    )

    # stats footer
    footer_y = legend_y + 26
    footer = f'{stats["total"]:,} contributions in the last year'
    if stats.get("longest_streak"):
        footer += f"  \u00b7  longest streak {stats['longest_streak']}d"
    parts.append(f'<text x="{LEFT_PAD}" y="{footer_y}" font-size="11">{footer}</text>')

    parts.append('</svg>')

    with open(out_path, "w") as f:
        f.write("\n".join(parts))
    print(f"Wrote {out_path} ({n_weeks} weeks)")


if __name__ == "__main__":
    with open(DATA_PATH) as f:
        data = json.load(f)
    build_svg(data)
