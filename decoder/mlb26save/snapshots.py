"""Stat snapshots per save day, so the app can show what happened *between* two saves.

The save keeps only season totals (plus month and current-series splits), not box scores. Clubhouse stores
a compact copy of every player's totals each time it reads a new save day, and the difference against the
previous stored day is "since your last save". Save after every game day and that is game by game.

Stored in <folder>/<franchise>.json, keeping the last KEEP save days of the current season.
"""
from __future__ import annotations

import json
from pathlib import Path

KEEP = 14
BAT = ("g", "ab", "h", "2b", "3b", "hr", "rbi", "r", "bb", "so", "sb")
PIT = ("g", "gs", "outs", "h", "er", "bb", "so", "w", "l", "sv", "hr")
BUCKETS = (("season", "MLB"), ("aaa", "AAA"), ("aa", "AA"))


def _take(data: dict) -> dict:
    snap = {}
    for p in data["players"]:
        keys = PIT if p["pos"] == "P" else BAT
        for bucket, lvl in BUCKETS:
            s = p["stats"].get(bucket)
            if s and s.get("g"):
                snap[f"{p['id']}:{lvl}"] = [s.get(k, 0) or 0 for k in keys]
    return snap


def attach_recent(data: dict, folder: Path, franchise: str | None) -> None:
    """Add data["recent"] = {"fromDay", "toDay", "lines": [[pid, level, {stat: delta}], ...]} and store today."""
    if not franchise:
        return
    year, day = data["season"]["year"], data["season"]["day"]
    path = Path(folder) / f"{franchise}.json"
    try:
        store = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        store = {}
    if data["season"].get("phase") == "spring":   # spring totals aren't season totals: don't store or diff them
        data["recent"] = None
        return
    if store.get("year") != year:
        store = {"year": year, "days": {}}
    from .history import label_before_opening
    store["days"] = {d: v for d, v in store["days"].items() if not label_before_opening(v.get("label"), data)}
    days = store["days"]
    now = _take(data)
    earlier = sorted(int(d) for d in days if int(d) < day)
    recent = None
    if earlier:
        prev_day = earlier[-1]
        prev = days[str(prev_day)]["p"]
        pos = {p["id"]: p["pos"] for p in data["players"]}
        lines = []
        for key, cur in now.items():
            old = prev.get(key, [0] * len(cur))
            if cur[0] <= old[0]:
                continue
            pid, lvl = key.split(":")
            keys = PIT if pos.get(int(pid)) == "P" else BAT
            lines.append([int(pid), lvl, {k: c - o for k, c, o in zip(keys, cur, old) if c != o}])
        recent = {"fromDay": prev_day, "fromLabel": days[str(prev_day)].get("label"), "toDay": day, "lines": lines}
    data["recent"] = recent
    days[str(day)] = {"label": data.get("slot", {}).get("label"), "p": now}
    for d in sorted(days, key=int)[:-KEEP]:
        del days[d]
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(store, separators=(",", ":")), encoding="utf-8")
    except OSError:
        pass
