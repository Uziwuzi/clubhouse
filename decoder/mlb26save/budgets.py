"""Salary cap via the game's own team budgets: set AI teams' D_STRATEGIES.BUDGET to the cap, and put them back.

The save is the only place budgets live (the game builds them when a franchise is created), so this is a save
edit, never a change to the game's files. It is opt-in and reversible:
  * the first write stores the franchise's original budgets in <store>/<franchise>.json; restore() writes them back;
  * every write refuses while the game or an emulator runs, backs up the save first (SaveSlot.write), and reads
    the save back to check that only the budget bytes changed and the checksum is valid.
Layout (save): D_STRATEGIES row 0, BUDGET = 30 x u32 dollars, one per MLB team in team-index order.
UNTESTED IN-GAME: whether, and how strictly, the AI keeps payroll under its budget.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from .container import SaveSlot
from .discover import game_running

MLB_TEAMS = 30


def _offsets(slot: SaveSlot):
    db = slot.db
    t = db.largest("D_STRATEGIES")
    st = db.structs["D_STRATEGIES"]
    base = t.row_offsets[0] + st.offsets["BUDGET"]
    return [base + 4 * k for k in range(MLB_TEAMS)], list(t.rows[0]["BUDGET"][:MLB_TEAMS])


def read(save: Path, info: Path) -> list[int]:
    return _offsets(SaveSlot(Path(save), Path(info)))[1]


def _write(save: Path, info: Path, new: dict[int, int], backup_dir: Path) -> dict:
    g = game_running()
    if g:
        return {"ok": False, "error": f"Close the game first ({g} is running). Nothing was written."}
    slot = SaveSlot(Path(save), Path(info))
    if not slot.checksum_ok:
        return {"ok": False, "error": "The save looks half-written (checksum mismatch). Nothing was written."}
    offs, cur = _offsets(slot)
    raw = bytearray(slot.raw)
    changed = 0
    for team, val in new.items():
        val = int(max(0, min(val, 0xFFFFFFFF)))
        if cur[team] != val:
            raw[offs[team]:offs[team] + 4] = val.to_bytes(4, "little")
            changed += 1
    if not changed:
        return {"ok": True, "written": 0}
    backup = slot.write(bytes(raw), backup_dir=backup_dir)
    check = SaveSlot(Path(save), Path(info))
    _, after = _offsets(check)
    diff = sum(a != b for a, b in zip(check.raw, slot.raw))
    expect = {t: int(v) for t, v in new.items()}
    if not check.checksum_ok or any(after[t] != v for t, v in expect.items()) or diff > 4 * changed or len(check.raw) != len(slot.raw):
        return {"ok": False, "error": f"The save didn't read back as expected. Your backup is in {backup}.", "backup": str(backup)}
    return {"ok": True, "written": changed, "backup": str(backup)}


def apply_cap(save: Path, info: Path, franchise: str, cap: int, teams: list[int], store: Path, backup_dir: Path) -> dict:
    """Lower every team in `teams` whose budget is above `cap` to `cap`; clubs under it keep theirs. (Setting them
    all to the cap raised 13 small budgets in the White Sox 2028 save, e.g. MIN $138M -> $252.7M, Nov 21, 2026.)
    Remembers the season's originals the first time, and always works from them, so re-applying never compounds."""
    store = Path(store); store.mkdir(parents=True, exist_ok=True)
    keep = store / f"{franchise}.json"
    orig = read(save, info)
    if keep.exists() and not _same_season(orig, json.loads(keep.read_text(encoding="utf-8"))):
        keep.unlink()                                  # the game rebuilt budgets since: that record is stale
    base = json.loads(keep.read_text(encoding="utf-8"))["budgets"] if keep.exists() else orig
    res = _write(save, info, {t: min(int(base[t]), int(cap)) for t in teams if 0 <= t < MLB_TEAMS}, backup_dir)
    if res.get("ok") and res.get("written"):
        rec = json.loads(keep.read_text(encoding="utf-8")) if keep.exists() else {"budgets": orig}
        rec["cap"] = int(cap)
        tmp = keep.with_suffix(".tmp")
        tmp.write_text(json.dumps(rec), encoding="utf-8")
        os.replace(tmp, keep)
    if keep.exists():
        res["original"] = json.loads(keep.read_text(encoding="utf-8"))["budgets"]
    return res


def restore(save: Path, info: Path, franchise: str, store: Path, backup_dir: Path) -> dict:
    """Write the franchise's original budgets back (the ones saved before the first apply_cap)."""
    keep = Path(store) / f"{franchise}.json"
    if not keep.exists():
        return {"ok": False, "error": "No original budgets on file for this franchise: Clubhouse never changed them."}
    if not _same_season(read(save, info), json.loads(keep.read_text(encoding="utf-8"))):
        keep.unlink()
        return {"ok": False, "error": "The game has already rebuilt every club's budget (it does each new season), so they're at their normal values. Nothing was written."}
    orig = json.loads(keep.read_text(encoding="utf-8"))["budgets"]
    res = _write(save, info, {t: v for t, v in enumerate(orig[:MLB_TEAMS])}, backup_dir)
    if res.get("ok"):
        keep.unlink()
    return res


def has_original(franchise: str, store: Path) -> bool:
    return (Path(store) / f"{franchise}.json").exists()


def applied(save: Path, info: Path, franchise: str, store: Path) -> bool:
    """Are the cap budgets still in this save? The game rebuilds every budget at the new season (the White Sox
    2028 Opening Day save was back to LAD $481M after 2027's $245.3M cap, Nov 21, 2026), and restoring a stale
    record would then write last season's budgets over this season's. Records from before `cap` was kept: the
    cap is the value 10+ clubs share."""
    keep = Path(store) / f"{franchise}.json"
    if not keep.exists():
        return False
    cur = read(save, info)
    rec = json.loads(keep.read_text(encoding="utf-8"))
    cap = rec.get("cap")
    if cap is None:
        from collections import Counter
        val, n = Counter(cur).most_common(1)[0]
        return n >= 10
    above = [t for t, o in enumerate(rec["budgets"][:MLB_TEAMS]) if o > cap]
    return bool(above) and _same_season(cur, rec) and sum(cur[t] == cap for t in above) >= len(above) - 1


def _same_season(cur: list, rec: dict) -> bool:
    """Is this record from the budgets now in the save? Every club is either at its recorded original or at the
    cap (a club or two may differ: the user's own club isn't touched and the game may nudge one); after the game
    rebuilds budgets for a new season most clubs match neither."""
    cap, orig = rec.get("cap"), rec["budgets"]
    ok = sum(c == o or (cap is not None and c == cap) for c, o in zip(cur, orig))
    return ok >= MLB_TEAMS - 2
