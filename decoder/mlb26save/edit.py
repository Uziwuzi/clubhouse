"""Player edits, patched in place into a copy of the decompressed save.

Only fields whose meaning is VERIFIED in docs/SAVE_FORMAT.md can be edited:
first and last name, jersey number, primary position, bats and throws.
Every write keeps the decompressed size the same, and SaveSlot.write() backs up first.

UNTESTED IN-GAME until the write test in docs/SAVE_FORMAT.md passes.
"""
from __future__ import annotations

import subprocess

from .extract import POSITIONS

# Processes that mean the game (or a Switch emulator) may have the save open.
GAME_PROCESSES = {"mlb.exe", "yuzu.exe", "suyu.exe", "sudachi.exe", "citron.exe", "eden.exe",
                  "ryujinx.exe", "torzu.exe"}

POS_CODES = {v: k for k, v in POSITIONS.items()}
HITTER_POS = [p for p in POSITIONS.values() if p != "P"]
NAME_BYTES = 16           # FIRST_NAME / LAST_NAME are char[16], NUL padded


def game_running() -> str | None:
    """The name of a running game or emulator process, or None."""
    try:
        out = subprocess.run(["tasklist", "/FO", "CSV", "/NH"], capture_output=True, text=True,
                             timeout=10, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)).stdout
    except (OSError, subprocess.SubprocessError):
        return "unknown (couldn't list running programs)"
    for line in out.splitlines():
        name = line.split(",")[0].strip('"').lower()
        if name in GAME_PROCESSES:
            return name
    return None


class EditError(ValueError):
    pass


def _set_bits(word: int, shift: int, width: int, value: int) -> int:
    mask = ((1 << width) - 1) << shift
    return (word & ~mask) | ((value << shift) & mask)


def _encode_name(s: str, label: str) -> bytes:
    s = " ".join(str(s).split())
    if not s:
        raise EditError(f"{label} can't be empty.")
    try:
        b = s.encode("latin-1")
    except UnicodeEncodeError:
        raise EditError(f"{label} has a character the game can't store.") from None
    if len(b) > NAME_BYTES - 1:
        raise EditError(f"{label} can be at most {NAME_BYTES - 1} characters.")
    return b.ljust(NAME_BYTES, b"\0")


def apply_player_edits(db, raw: bytearray, pid: int, changes: dict) -> dict:
    """Patch `changes` for player row `pid` into `raw` (a bytearray of the decompressed save).

    changes may hold: first, last (str), num (0-99), pos ("C".."DH"; pitchers stay "P"),
    bats ("R"/"L"/"S"), throws ("R"/"L"). Returns the fields actually changed {field: [old, new]}.
    """
    prof = db.largest("D_PLR_PROFILE")
    if not 0 <= pid < len(prof.rows) or not prof.rows[pid]["LAST_NAME"]:
        raise EditError("That player isn't in this save.")
    row = prof.rows[pid]
    st = db.structs[prof.name]
    base = prof.row_offsets[pid]
    off = lambda f: base + st.offsets[f]
    done = {}

    for key, field in (("first", "FIRST_NAME"), ("last", "LAST_NAME")):
        if key in changes and changes[key] is not None:
            new = _encode_name(changes[key], "First name" if key == "first" else "Last name")
            if new.split(b"\0")[0].decode("latin-1") != row[field]:
                o = off(field)
                raw[o:o + NAME_BYTES] = new
                done[key] = [row[field], new.split(b"\0")[0].decode("latin-1")]

    up = list(row["UNSIGNED_PACK"])
    sp = row["SIGNED_PACK"]
    up0, up4, sp0 = up[0], up[4], sp

    if changes.get("num") is not None:
        n = int(changes["num"])
        if not 0 <= n <= 99:
            raise EditError("Numbers go from 0 to 99.")
        old = (up[4] >> 7) & 127
        if n != old:
            # Bits 0-6 hold the same number for 99% of players (meaning UNKNOWN); keep them in step when they match.
            if up[4] & 127 == old:
                up[4] = _set_bits(up[4], 0, 7, n)
            up[4] = _set_bits(up[4], 7, 7, n)
            done["num"] = [old, n]

    if changes.get("bats"):
        b = str(changes["bats"]).upper()
        if b not in ("R", "L", "S"):
            raise EditError("Bats must be R, L or S.")
        old = "RLS?"[(up[0] >> 23) & 3]
        if b != old:
            up[0] = _set_bits(up[0], 23, 2, "RLS".index(b))
            done["bats"] = [old, b]

    if changes.get("throws"):
        t = str(changes["throws"]).upper()
        if t not in ("R", "L"):
            raise EditError("Throws must be R or L.")
        old = "L" if (sp >> 30) & 1 else "R"
        if t != old:
            sp = _set_bits(sp, 30, 1, 1 if t == "L" else 0)
            done["throws"] = [old, t]

    if changes.get("pos"):
        p = str(changes["pos"]).upper()
        old = POSITIONS.get(row["POSITION"], "?")
        if p not in POS_CODES:
            raise EditError("Unknown position.")
        if (p == "P") != (old == "P"):
            raise EditError("Pitchers and position players can't switch: their ratings are built differently.")
        if p != old:
            o = off("POSITION")
            raw[o] = POS_CODES[p]
            done["pos"] = [old, p]

    if up[0] != up0 or up[4] != up4:
        o = off("UNSIGNED_PACK")
        for i in (0, 4):
            raw[o + 4 * i:o + 4 * i + 4] = up[i].to_bytes(4, "little")
    if sp != sp0:
        o = off("SIGNED_PACK")
        raw[o:o + 4] = sp.to_bytes(4, "little")
    return done
