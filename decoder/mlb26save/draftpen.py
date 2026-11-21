"""The draft order Clubhouse writes into the save (lottery result and salary-cap penalties), and put back.

D_DRAFT_DATA row 0 (VERIFIED layout on the Mets Aug 2 and White Sox Apr 1 saves): DRAFT_ORDER = 150 bytes,
5 rounds x 30 slots of team indexes; COMP_PICKS = 30 bytes (qualifying-offer compensation picks: in the White Sox save they're exactly the clubs that
lost QO free agents; the game builds Competitive Balance A/B itself, not from the save);
PPI_PICKS = 30 bytes; 255 = empty. The game blanks picks itself (255) when a club loses one for signing a
qualifying-offer free agent, and keeps the order fixed from the start of the season until the July draft.
UNTESTED IN-GAME: drafting from an order Clubhouse changed (a forfeited slot, a competitive balance pick moved up).

Opt-in and reversible: the first write stores the season's original arrays in <store>/<franchise>.json;
restore() writes them back. Refuses while the game runs, once the draft has started, and on any change other
than clubs removed (forfeits) or reordered within a row (lottery, standings), packed with 255 at the end. Backs up the save first and reads
it back to check that only these bytes changed.
"""
from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path

from .container import SaveSlot
from .discover import game_running

FIELDS = (("DRAFT_ORDER", 150), ("COMP_PICKS", 30), ("PPI_PICKS", 30))


def _layout(slot: SaveSlot):
    db = slot.db
    loc = db.find("D_DRAFT_DATA")
    if not loc:
        return None, None
    t = db.read(loc[0][0])
    st = db.structs["D_DRAFT_DATA"]
    offs = {f: t.row_offsets[0] + st.offsets[f] for f, _ in FIELDS}
    vals = {f: list(slot.raw[offs[f]:offs[f] + n]) for f, n in FIELDS}
    return offs, vals


def _before_draft(db) -> bool:
    """Spring, or the regular season before the All-Star date: this season's draft (held at the All-Star break)
    can't have started. Needed because the game keeps last year's class and picks in the save until then: the
    2028 Opening Day save still had the 2027 class with all 198 picks matching it (Nov 21, 2026).
    MODESTATE 2 = spring, 4 = regular season (VERIFIED); SEASONDATE counts days from Opening Day."""
    import datetime as dt
    try:
        g = db.largest("D_GAME_OPTIONS").rows[0]
        if g["MODESTATE"] == 2:
            return True
        if g["MODESTATE"] != 4:
            return False
        c = db.largest("D_SCHED_CONST").rows[0]
        od = dt.date(2001, c["SEAS_START_MONTH"] + 1, c["SEAS_START_DATE"])
        asg = dt.date(2001, c["ALLSTAR_MONTH"] + 1, c["ALLSTAR_DATE"])
        return g["SEASONDATE"] < (asg - od).days
    except (KeyError, IndexError, ValueError, AttributeError):
        return False


def _draft_started(slot: SaveSlot) -> bool:
    """True once this season's class has picks. D_DRAFT_PICKS keeps LAST year's picks until the next draft (the
    2028 Opening Day save still had all 198 from 2027, Nov 21, 2026), so a pick only counts when its
    AMATEUR_INX_16BT row in the current class still carries the same name (the same test as extract._draft)."""
    db = slot.db
    if not db.find("D_DRAFT_PICKS") or not db.find("D_AMATUER_PLAYER"):
        return False
    if _before_draft(db):
        return False
    amt = db.largest("D_AMATUER_PLAYER")

    def same(r):
        i = r["AMATEUR_INX_16BT"]
        if i == 0xFFFF or i >= len(amt.children) or "D_PLR_PROFILE" not in amt.children[i]:
            return False
        p = amt.children[i]["D_PLR_PROFILE"].rows[0]
        return (p["FIRST_NAME"], p["LAST_NAME"]) == (r["FIRST_NAME"], r["LAST_NAME"])
    return any(r["LAST_NAME"] and r["PICK_SELECTED"] and same(r) for r in db.largest("D_DRAFT_PICKS").rows)

def read(save: Path, info: Path) -> dict | None:
    _, vals = _layout(SaveSlot(Path(save), Path(info)))
    return vals


def _packed(new: list) -> list | None:
    """The clubs in a row if it's packed (clubs first, 255 only at the end), else None. The game reads a row as
    its first N slots (N = clubs in it): a 255 in the middle showed up in-game as a blank Baltimore pick and
    pushed the last clubs out (Nov 21, 2026)."""
    kept = [v for v in new if v != 255]
    return kept if new == kept + [255] * (len(new) - len(kept)) else None


def _check(orig: dict, new: dict) -> str | None:
    """Each row may only lose clubs (forfeits) and be reordered (a lottery, the standings); it never gains a club
    or a second pick, and stays packed. Compensation and prospect promotion picks may only lose clubs."""
    for f, n in FIELDS:
        if len(new[f]) != n or any(not (0 <= v < 30 or v == 255) for v in new[f]):
            return f"{f} has the wrong length or a value that isn't a club."
    rows = [("DRAFT_ORDER", r * 30, (r + 1) * 30, f"Row {r + 1} of the draft order") for r in range(5)]
    rows += [("COMP_PICKS", 0, 30, "The compensation picks"), ("PPI_PICKS", 0, 30, "The prospect promotion picks")]
    for f, a, b, name in rows:
        kept = _packed(new[f][a:b])
        if kept is None:
            return f"{name} would have an empty slot before its last pick."
        base = Counter(v for v in orig[f][a:b] if v != 255)
        # A club may legitimately hold two picks in a list (the game gave TB two compensation picks in a 2028
        # save, Nov 21, 2026): only refuse a club getting more picks than the game's order gave it.
        if any(n > base[v] for v, n in Counter(kept).items()):
            return f"{name} would give a club a pick it didn't have."
    return None


def _write(save, info, new: dict, backup_dir) -> dict:
    g = game_running()
    if g:
        return {"ok": False, "error": f"Close the game first ({g} is running). Nothing was written."}
    slot = SaveSlot(Path(save), Path(info))
    if not slot.checksum_ok:
        return {"ok": False, "error": "The save looks half-written (checksum mismatch). Nothing was written."}
    if _draft_started(slot):
        return {"ok": False, "error": "This season's draft has already started in your save. Nothing was written."}
    offs, cur = _layout(slot)
    if offs is None:
        return {"ok": False, "error": "This save has no draft order."}
    raw = bytearray(slot.raw)
    changed = 0
    for f, n in FIELDS:
        for k in range(n):
            if raw[offs[f] + k] != new[f][k]:
                raw[offs[f] + k] = new[f][k]
                changed += 1
    if not changed:
        return {"ok": True, "written": 0}
    backup = slot.write(bytes(raw), backup_dir=backup_dir)
    check = SaveSlot(Path(save), Path(info))
    _, after = _layout(check)
    diff = sum(a != b for a, b in zip(check.raw, slot.raw))
    if not check.checksum_ok or after != new or diff != changed or len(check.raw) != len(slot.raw):
        return {"ok": False, "error": f"The save didn't read back as expected. Your backup is in {backup}.", "backup": str(backup)}
    return {"ok": True, "written": changed, "backup": str(backup)}


def originals(franchise: str, store: Path) -> dict | None:
    p = Path(store) / f"{franchise}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def apply(save, info, franchise: str, season: int, new: dict, store: Path, backup_dir: Path) -> dict:
    store = Path(store); store.mkdir(parents=True, exist_ok=True)
    keep = store / f"{franchise}.json"
    cur = read(save, info)
    if cur is None:
        return {"ok": False, "error": "This save has no draft order."}
    kept = originals(franchise, store)
    if kept and kept.get("season") != season:
        kept = None                                # last season's record: this season's order is new
    base = kept["order"] if kept else cur
    err = _check(base, new)
    if err:
        return {"ok": False, "error": err + " Nothing was written."}
    res = _write(save, info, new, backup_dir)
    # File the original only once a write went through: a refused write (game running, draft started) used to
    # leave a record behind, and the page then said the penalties were in the save (Nov 21, 2026).
    if res.get("ok") and res.get("written") and not kept:
        tmp = keep.with_suffix(".tmp")
        tmp.write_text(json.dumps({"season": season, "order": cur}), encoding="utf-8")
        os.replace(tmp, keep)
    return res


def restore(save, info, franchise: str, store: Path, backup_dir: Path) -> dict:
    kept = originals(franchise, store)
    if not kept:
        return {"ok": False, "error": "Clubhouse hasn't changed this franchise's draft order."}
    res = _write(save, info, kept["order"], backup_dir)
    if res.get("ok"):
        (Path(store) / f"{franchise}.json").unlink()
    return res
