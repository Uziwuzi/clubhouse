"""Discover in game: make prospects that Clubhouse's scouts found appear on the game's draft list.

D_AMATUER_PLAYER.SCOUTED_CERT[team] (one byte per club) is how far that club has scouted a prospect.
VERIFIED Nov 21, 2026 on the Astros May 5 save:
  - 0 = the club hasn't discovered him, and he's missing from that club's draft list (Mateo, Trujillo, Amoros
    and Dan Smith were 0 and hidden; Beam at 5 and Beau at 10 were listed, as NR).
  - Setting Eric Mateo 0 -> 5 (Beam's value, the game's usual starting value) made him appear in-game as NR.
    The save loaded normally.

So the only write is 0 -> 5, for the user's own club, and only where the value is 0 now. The decompressed
size never changes, the current save is backed up first (SaveSlot.write), and nothing is written while the
game or an emulator is running.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from .container import SaveSlot

DISCOVERED = 5
GAME_PROCESSES = {"mlb.exe", "yuzu.exe", "suyu.exe", "sudachi.exe", "citron.exe", "eden.exe",
                  "ryujinx.exe", "torzu.exe"}


def game_running() -> str | None:
    """The name of a running game or emulator process, or None (or a reason if the list can't be read)."""
    try:
        out = subprocess.run(["tasklist", "/FO", "CSV", "/NH"], capture_output=True, text=True, timeout=10,
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)).stdout
    except (OSError, subprocess.SubprocessError):
        return "unknown (couldn't list running programs)"
    for line in out.splitlines():
        name = line.split(",")[0].strip('"').lower()
        if name in GAME_PROCESSES:
            return name
    return None


def _name(t, i):
    kids = t.children[i] if i < len(t.children) else {}
    p = kids["D_PLR_PROFILE"].rows[0] if "D_PLR_PROFILE" in kids else {}
    return f"{p.get('FIRST_NAME', '')} {p.get('LAST_NAME', '')}".strip()


def plan(slot: SaveSlot, team: int, players: list[dict]) -> tuple[list[dict], bytearray]:
    """What would change. `players` = [{"row": amateur row, "name": "First Last"}]; the name must match the
    save's row (so a regenerated class never gets the wrong player)."""
    db = slot.db
    t = db.largest("D_AMATUER_PLAYER")
    off = db.structs["D_AMATUER_PLAYER"].offsets["SCOUTED_CERT"]
    raw = bytearray(slot.raw)
    out = []
    for p in players:
        row = int(p["row"])
        res = {"row": row, "name": p.get("name", "")}
        if not 0 <= row < len(t.rows):
            res["skip"] = "not in this draft class"
        elif _name(t, row).lower() != str(p.get("name", "")).strip().lower():
            res["skip"] = f"row {row} is {_name(t, row) or 'empty'} in this save"
        else:
            cert = t.rows[row]["SCOUTED_CERT"]
            o = t.row_offsets[row] + off + team
            if raw[o] != cert[team]:
                res["skip"] = "unexpected save layout"
            elif cert[team] != 0:
                res["skip"] = "already on the game's list"
            else:
                raw[o] = DISCOVERED
                res["ok"] = True
        out.append(res)
    return out, raw


def discover(save: Path, info: Path, team: int, players: list[dict], backup_dir: Path) -> dict:
    g = game_running()
    if g:
        return {"ok": False, "error": f"Close the game first ({g} is running). Nothing was written."}
    slot = SaveSlot(Path(save), Path(info))
    if not slot.checksum_ok:
        return {"ok": False, "error": "The save looks half-written (checksum mismatch). Nothing was written."}
    results, raw = plan(slot, team, players)
    todo = [r for r in results if r.get("ok")]
    if not todo:
        return {"ok": True, "written": 0, "results": results}
    assert len(raw) == len(slot.raw)
    backup = slot.write(bytes(raw), backup_dir=backup_dir)
    check = SaveSlot(Path(save), Path(info))
    t = check.db.largest("D_AMATUER_PLAYER")
    bad = [r for r in todo if t.rows[r["row"]]["SCOUTED_CERT"][team] != DISCOVERED]
    changed = sum(a != b for a, b in zip(check.raw, slot.raw))
    if not check.checksum_ok or bad or changed != len(todo) or len(check.raw) != len(slot.raw):
        return {"ok": False, "error": f"The save didn't read back as expected. Your backup is in {backup}.",
                "backup": str(backup)}
    return {"ok": True, "written": len(todo), "results": results, "backup": str(backup)}
