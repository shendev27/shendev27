"""
fetch_contributions.py

Fetches the public contribution calendar HTML fragment GitHub serves at
https://github.com/users/<username>/contributions -- the same fragment
the profile page itself uses. No GraphQL API, no personal access token.

Writes data/contributions.json with raw days plus derived stats
(current streak, longest streak, best day, monthly totals).

Usage:
    python scripts/fetch_contributions.py [username]
"""
import sys
import json
import os
from datetime import datetime, date, timezone
import requests
from bs4 import BeautifulSoup

USERNAME = "shendev27"
OUT_PATH = "data/contributions.json"


def fetch_html(username: str) -> str:
    url = f"https://github.com/users/{username}/contributions"
    headers = {"User-Agent": "Mozilla/5.0 (profile-readme-bot)"}
    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    return resp.text


def parse_days(html: str):
    import re

    soup = BeautifulSoup(html, "html.parser")
    days = []

    # GitHub renders each day as a <td data-date data-level id=...>. The
    # actual contribution count isn't an attribute -- it's spelled out in
    # a matching <tool-tip for="...">N contributions on Month Day.</tool-tip>
    cells = soup.select("td[data-date]")

    tooltip_text_by_id = {}
    for tip in soup.find_all("tool-tip"):
        target = tip.get("for")
        if target:
            tooltip_text_by_id[target] = tip.get_text(strip=True)

    for cell in cells:
        d = cell.get("data-date")
        if not d:
            continue
        level = cell.get("data-level", "0")
        cell_id = cell.get("id")

        count = None
        tip_text = tooltip_text_by_id.get(cell_id, "")
        if tip_text:
            if tip_text.lower().startswith("no contributions"):
                count = 0
            else:
                m = re.match(r"(\d+)\s+contribution", tip_text)
                if m:
                    count = int(m.group(1))

        days.append({"date": d, "level": int(level), "count": count})

    days.sort(key=lambda x: x["date"])
    return days


def derive_stats(days):
    total = sum(d["count"] or 0 for d in days)

    # current streak: consecutive days with count > 0, walking back from
    # the most recent day that has data.
    current_streak = 0
    longest_streak = 0
    running = 0
    best_day = {"date": None, "count": -1}

    for d in days:
        c = d["count"] or 0
        if c > 0:
            running += 1
            longest_streak = max(longest_streak, running)
        else:
            running = 0
        if c > best_day["count"]:
            best_day = {"date": d["date"], "count": c}

    for d in reversed(days):
        c = d["count"] or 0
        if c > 0:
            current_streak += 1
        else:
            break

    monthly = {}
    for d in days:
        month = d["date"][:7]  # YYYY-MM
        monthly[month] = monthly.get(month, 0) + (d["count"] or 0)

    return {
        "total": total,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "best_day": best_day,
        "monthly": monthly,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


def main():
    username = sys.argv[1] if len(sys.argv) > 1 else USERNAME
    html = fetch_html(username)
    days = parse_days(html)

    if not days:
        print("Warning: no contribution cells parsed -- GitHub markup may have "
              "changed, or the profile has no public activity.", file=sys.stderr)

    stats = derive_stats(days)

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump({"username": username, "days": days, "stats": stats}, f, indent=2)

    print(f"Wrote {OUT_PATH}: {len(days)} days, {stats['total']} total contributions")


if __name__ == "__main__":
    main()
