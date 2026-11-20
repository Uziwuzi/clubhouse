"""Find every franchise in a save folder and group its save slots.

Each franchise save carries its own id: D_GAME_OPTIONS.UUID_STR. VERIFIED: the Mets saves of
March 25 and May 29 share one id; a separately started Mets franchise and the White Sox one
each have their own. The game may write a new save into a new FRAN<hash> slot folder, so the
newest slot of a franchise (by the SAVEINFO timestamp) is the one to read.
"""
from __future__ import annotations

import zlib
from pathlib import Path

from .container import SaveInfo, find_franchise_slots, label_date
from .database import Database

_cache: dict[tuple, dict] = {}   # (path, mtime_ns, size) -> slot summary


def _text(v) -> str:
    return v if isinstance(v, str) else bytes(v).split(b"\0")[0].decode("latin-1")


def slot_summary(save: Path, info: Path) -> dict | None:
    """Cheap facts about one slot (about 0.1 s, cached until the file changes)."""
    try:
        st = save.stat()
    except OSError:
        return None
    key = (str(save), st.st_mtime_ns, st.st_size)
    if key in _cache:
        return _cache[key]
    try:
        si = SaveInfo.parse(info.read_bytes())
        db = Database(zlib.decompress(save.read_bytes()))
        go = db.read(db.find("D_GAME_OPTIONS")[0][0]).rows[0]
        team = go["CURRENTTEAM"]
        teams = db.largest("D_TEAM_PROF").rows
        t = teams[team] if team < len(teams) else {}
        out = {
            "id": _text(go["UUID_STR"]) or str(save.parent.name),
            "slot": str(save.parent), "save": str(save), "info": str(info),
            "label": si.label, "labelDate": label_date(si.label), "savedAt": si.saved_at.isoformat(), "ts": si.timestamp,
            "team": team, "abbr": t.get("SHORT_NAME", ""), "city": t.get("CITY_NAME", ""), "name": t.get("TEAM_NAME", ""),
            "year": go["START_YEAR"] + go["SEASONYEAR"], "day": go["SEASONDATE"],
        }
    except Exception as e:   # half-written or unreadable slot: skip it this round
        out = {"error": str(e), "slot": str(save.parent)}
    _cache[key] = out
    return out


def scan(root: str | Path) -> list[dict]:
    """Franchises under `root`, newest first. Each has its slots newest first; `latest` is the one to read."""
    groups: dict[str, list[dict]] = {}
    for save, info in find_franchise_slots(root):
        s = slot_summary(save, info)
        if s and "id" in s:
            groups.setdefault(s["id"], []).append(s)
    out = []
    for fid, slots in groups.items():
        slots.sort(key=lambda s: (s["ts"], s["save"]), reverse=True)
        latest = slots[0]
        out.append({"id": fid, "latest": latest, "slots": slots,
                    "abbr": latest["abbr"], "city": latest["city"], "name": latest["name"], "team": latest["team"]})
    out.sort(key=lambda f: f["latest"]["ts"], reverse=True)
    return out


def profile_root(folder: str | Path) -> Path:
    """A FRAN<hash> slot folder widens to its profile folder, so every franchise is found."""
    folder = Path(folder)
    return folder.parent if folder.name.upper().startswith("FRAN") else folder
