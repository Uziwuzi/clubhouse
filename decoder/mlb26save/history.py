"""Franchise history that outlives the save: one JSON file per franchise, one entry per season.

The game overwrites last season's draft results, standings and so on as the franchise moves on. Each time
Clubhouse reads a save it records the season's latest state here, so earlier seasons stay available:
standings, your team, your affiliates' records, and the full draft (who went where, signed or not).

Rules: an entry is only replaced by a save from the same season that is at least as far along (loading an
older save never rewinds history), and a season's draft is kept once seen even if a later save drops it.
"""
from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path

_MONTHS = {m: i for i, m in enumerate(("January", "February", "March", "April", "May", "June", "July", "August",
                                       "September", "October", "November", "December"), 1)}


def label_before_opening(label: str | None, data: dict) -> bool:
    """True when a stored slot label ("Royals March 13, 2026") is from spring training of this save's season.
    Clubhouse 1.7 recorded spring saves as the regular season; this lets later loads drop those entries."""
    od = ((data.get("season") or {}).get("calendar") or {}).get("openingDay")
    m = re.search(r"([A-Z][a-z]+) (\d{1,2}), (\d{4})", label or "")
    if not od or not m or m.group(1) not in _MONTHS:
        return False
    d = dt.date(int(m.group(3)), _MONTHS[m.group(1)], int(m.group(2))).isoformat()
    return d[:4] == od[:4] and d < od


def update_history(data: dict, folder: Path, franchise: str | None) -> None:
    data["history"] = {}
    if not franchise:
        return
    path = Path(folder) / f"{franchise}.json"
    try:
        store = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        store = {}
    seasons = store.setdefault("seasons", {})
    year, day = str(data["season"]["year"]), data["season"]["day"]
    if data["season"].get("phase") == "spring":   # spring games aren't the season: record nothing
        data["history"] = {y: e for y, e in seasons.items() if not label_before_opening(e.get("label"), data)}
        return
    cur = seasons.get(year, {})
    if cur and label_before_opening(cur.get("label"), data):
        cur = {"draft": cur.get("draft")}          # an entry written from a spring save by Clubhouse 1.7
    if cur.get("day", -1) <= day:
        me = data["season"]["userTeam"]
        clubs = [c for c in data["clubs"] if c.get("org") == me and c.get("record")]
        entry = {
            "day": day,
            "label": (data.get("slot") or {}).get("label"),
            "userTeam": me,
            "standings": [[t["id"], t["record"]["w"], t["record"]["l"], t["record"]["rs"], t["record"]["ra"]] for t in data["teams"]],
            "farm": [[c["id"], c["level"], c["record"]["w"], c["record"]["l"]] for c in clubs],
            "draft": cur.get("draft") or [],
        }
        if data.get("draftResults"):
            pros = {p["id"]: p for p in ((data.get("draft") or {}).get("prospects") or [])}
            entry["draft"] = [{**{k: r[k] for k in ("first", "last", "pick", "team", "signed", "bonus")},
                               "pos": (pros.get(r["prospect"]) or {}).get("pos"), "age": (pros.get(r["prospect"]) or {}).get("age"),
                               "rank": (pros.get(r["prospect"]) or {}).get("rank")} for r in data["draftResults"]]
        seasons[year] = entry
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(store, separators=(",", ":")), encoding="utf-8")
        except OSError:
            pass
    data["history"] = seasons
