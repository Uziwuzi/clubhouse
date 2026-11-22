"""Road to the Show careers (CARR<hash> slots): the player's stats and equipped gear, and equipping gear.

The career save is the same LE90 database as a franchise. The player is the D_PLR_PROFILE row whose name starts the
slot label ("First Last, Club POS Month D, YYYY"); in the test career he is the last row (3334 of 3335).

Gear (VERIFIED Nov 22, 2026 in-game on that career): D_PLAYER_ACC has one row per player, aligned with D_PLR_PROFILE,
and each slot holds the catalog item's `style` within its equipment `type` (FRONTEND/EQUIPMENT/MLBEQUIPMENT.JSON).
BAT 37 showed in-game as "Chandler AJ99 Pro Hard Maple XP" (type 0, style 37); GLOVE 3 = Rawlings Pro Preferred
(type 3), BATTING_GLOVES 62 = Jordan Fly Elite (type 1), SHOES 37 = Jordan 1 MCS (type 2), ELBOW_GUARD 21 = Jordan
Diamond Elite (type 9). Grip, glasses, sleeves, wrist guard, leg guard and catcher gear: see SLOTS (VERIFIED Nov 22, 2026). Offline, the game's own Edit Player screen only offers the generic
"Style 1" items; the Equipment tab is the online package inventory.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

from .container import SaveSlot
from .discover import game_running
from .extract import OPENING_DAY, _bat_line, _calendar, _pit_line, _stat_tables, export_league

# slot key -> (D_PLAYER_ACC field, catalog type). The catalog types for the second group come from the game's own
# model names (Eyeglasses_*, CatcherMask*, ChestProt_*, shinGuard_*, CompSleevePad_*, wristGuard_*, LegGuards_*, grip
# tape textures) and each slot's highest value in the save fits its type. equip() writes only slots in VERIFIED
# (hard rule: only VERIFIED fields are written).
SLOTS = {
    "bat": ("BAT", 0),
    "batgloves": ("BATTING_GLOVES", 1),
    "cleats": ("SHOES", 2),
    "glove": ("GLOVE", 3),
    "elbow": ("ELBOW_GUARD", 9),
    "grip": ("BAT_GRIP", 8),
    "glasses": ("GLASSES", 7),
    "sleeves": ("COMP_SLEEVES", 13),
    "wrist": ("WRIST_BRACES", 14),
    "shin": ("SHIN_GUARD", 12),
    "cmask": ("CATCHER_MASK", 10),
    "cshin": ("CATCHER_SHN_GRD", 15),
    "chest": ("CHEST_PROTECTOR", 11),
}
# The second group was confirmed in-game on Nov 22, 2026 (test items in all eight slots showed in Edit Player).
VERIFIED = {"bat", "batgloves", "cleats", "glove", "elbow", "grip", "glasses", "sleeves", "wrist", "shin", "cmask", "cshin", "chest"}
BAT_KEYS = ("g", "ab", "h", "2b", "3b", "hr", "r", "rbi", "bb", "so", "sb", "po", "a", "e")   # po/a/e: fielding (PUTOUTS, ASSISTS, ERRORS)
PIT_KEYS = ("g", "gs", "w", "l", "sv", "outs", "h", "er", "bb", "so", "hr", "hld")


SKIP_DIRS = ("backup", "-tx", "temp", "cache")   # the game's own save-backup / save-tx copies and scratch folders


def career_dirs(folder: str | Path, depth: int = 2) -> list[Path]:
    """CARR slot folders in `folder` or up to `depth` levels below it (the profile id folder, the save folder, ...),
    skipping the game's backup and transaction copies."""
    folder, out = Path(folder), []

    def walk(d: Path, left: int):
        try:
            kids = [k for k in d.iterdir() if k.is_dir()]
        except OSError:
            return
        for k in kids:
            n = k.name.lower()
            if n.startswith("carr"):
                out.append(k)
            elif left > 0 and not any(x in n for x in SKIP_DIRS) and not n.startswith(("fran", "rost", "plya", "sett")):
                walk(k, left - 1)
    if folder.name.lower().startswith("carr"):
        return [folder]
    walk(folder, depth)
    return out


def careers(profile: Path) -> list[dict]:
    """Every Road to the Show slot in or below a save folder, newest first."""
    out = []
    for d in career_dirs(profile):
        s, i = d / "SAVE_000", d / "SAVEINFO"
        if s.exists() and i.exists():
            out.append({"key": d.name, "dir": str(d), "mtime": s.stat().st_mtime})
    return sorted(out, key=lambda c: -c["mtime"])


def _player_row(db, label: str) -> int:
    rows = db.largest("D_PLR_PROFILE").rows
    name = (label or "").split(",")[0].strip().lower()
    hits = [i for i, r in enumerate(rows) if f"{r['FIRST_NAME']} {r['LAST_NAME']}".strip().lower() == name]
    if hits:
        return hits[-1]
    named = [i for i, r in enumerate(rows) if r["LAST_NAME"]]
    return named[-1]


def _sum(lines: list[dict], keys) -> dict:
    return {k: sum(int(l.get(k) or 0) for l in lines) for k in keys}


def read(slot_dir: str | Path) -> dict:
    d = Path(slot_dir)
    slot = SaveSlot(d / "SAVE_000", d / "SAVEINFO")
    db = slot.db
    label = slot.info.label
    row = _player_row(db, label)
    p = db.largest("D_PLR_PROFILE").rows[row]
    go = db.largest("D_GAME_OPTIONS").rows[0]
    year = go["START_YEAR"] + go["SEASONYEAR"]
    phase = {2: "spring", 4: "season", 7: "postseason"}.get(go.get("MODESTATE"))
    cal = _calendar(db, year)
    if phase == "spring" and cal:
        date = dt.date.fromisoformat(cal["springStart"]) + dt.timedelta(days=go["SEASONDATE"])
    else:
        date = dt.date(year, *OPENING_DAY) + dt.timedelta(days=go["SEASONDATE"])
    # Stats copies: [1] this MLB season, [2] this season in AAA, [3] in AA (as in extract.export_league)
    bt, pt = _stat_tables(db, "D_PLAYER_STATS"), _stat_tables(db, "D_PITCHER_STATS")
    lvls = (("mlb", 1), ("aaa", 2), ("aa", 3))
    bat = {k: {**_bat_line(bt[i].rows[row]), "po": bt[i].rows[row].get("PUTOUTS", 0), "a": bt[i].rows[row].get("ASSISTS", 0),
               "e": bt[i].rows[row].get("ERRORS", 0)} for k, i in lvls if i < len(bt)}
    pit = {k: _pit_line(pt[i].rows[row]) for k, i in lvls if i < len(pt)}
    acc = db.largest("D_PLAYER_ACC").rows[row]
    lg = export_league(db)                      # the player's ratings, club and organization (about 3 s; cached by the app)
    pl = next((x for x in lg["players"] if x["id"] == row), {}) or {}
    club = next((c for c in lg.get("clubs", []) if c.get("id") == pl.get("club")), None)
    keep = ("pos", "role", "bats", "throws", "num", "height", "weight", "age", "ovr", "pot", "level", "org", "team",
            "club", "contract", "ratings", "injury", "serviceYears", "serviceDays")
    return {
        "player": {k: pl.get(k) for k in keep},
        "clubInfo": {k: club.get(k) for k in ("abbr", "city", "name", "level", "league", "division")} if club else None,
        # the MLB organization, for logos and colours when no franchise is loaded (Road to the Show only)
        "teamInfo": next(({k: t.get(k) for k in ("id", "abbr", "city", "name", "league", "division", "colors")}
                          for t in lg.get("teams", []) if t.get("id") == pl.get("org")), None),
        "key": d.name, "label": label, "row": row,
        "first": p["FIRST_NAME"], "last": p["LAST_NAME"],
        "year": year, "date": date.isoformat(), "phase": phase,
        "seasonEnd": (cal or {}).get("seasonEnd"),
        "bat": {"levels": {k: {x: v.get(x, 0) for x in BAT_KEYS} for k, v in bat.items()}, "total": _sum(list(bat.values()), BAT_KEYS)},
        "pit": {"levels": {k: {x: v.get(x, 0) for x in PIT_KEYS} for k, v in pit.items()}, "total": _sum(list(pit.values()), PIT_KEYS)},
        "gear": {k: acc[f] for k, (f, _) in SLOTS.items()},
        "slotsOk": sorted(VERIFIED),
    }


def equip(slot_dir: str | Path, row: int, gear: dict, backup_dir: Path, test: bool = False) -> dict:
    """Write {slot key: catalog style} for the career's player. Refuses while the game runs, backs up first,
    and reads the save back to check that only those bytes changed."""
    g = game_running()
    if g:
        return {"ok": False, "error": f"Close the game first ({g} is running). Nothing was written."}
    d = Path(slot_dir)
    slot = SaveSlot(d / "SAVE_000", d / "SAVEINFO")
    if not slot.checksum_ok:
        return {"ok": False, "error": "The save looks half-written (checksum mismatch). Nothing was written."}
    db = slot.db
    if _player_row(db, slot.info.label) != row:
        return {"ok": False, "error": "That career's save changed since Clubhouse read it. Reload and try again."}
    t = db.largest("D_PLAYER_ACC")
    raw = bytearray(slot.raw)
    want = {}
    for k, v in gear.items():
        if k not in SLOTS or (k not in VERIFIED and not test):
            return {"ok": False, "error": f"The {k} slot isn't confirmed in-game yet. Nothing was written."}
        v = int(v)
        f = SLOTS[k][0]
        size = next((x.elem_size for x in db.structs["D_PLAYER_ACC"].fields if x.name == f), 1)   # BAT is 2 bytes
        if not 0 <= v < 256 ** size:
            return {"ok": False, "error": "That item isn't a valid gear style. Nothing was written."}
        want[f] = v
        db.patch(raw, t, row, f, v)
    changed = sum(a != b for a, b in zip(raw, slot.raw))
    if not changed:
        return {"ok": True, "written": 0}
    backup = slot.write(bytes(raw), backup_dir=backup_dir)
    check = SaveSlot(d / "SAVE_000", d / "SAVEINFO")
    after = check.db.largest("D_PLAYER_ACC").rows[row]
    diff = sum(a != b for a, b in zip(check.raw, slot.raw))
    if not check.checksum_ok or any(after[f] != v for f, v in want.items()) or diff != changed:
        return {"ok": False, "error": f"The save didn't read back as expected. Your backup is in {backup}.", "backup": str(backup)}
    return {"ok": True, "written": changed, "backup": str(backup)}
