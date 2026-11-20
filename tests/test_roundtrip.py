"""Run:  python -m pytest tests  (set MLB26_SAVE to a profile save folder)

Read-only checks plus an in-memory write round trip. Never touches the real save.
"""
import hashlib
import os
import sys
import zlib
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "decoder"))
from mlb26save import open_save            # noqa: E402
from mlb26save.database import Database    # noqa: E402

SAVE = os.environ.get("MLB26_SAVE")
pytestmark = pytest.mark.skipif(not SAVE, reason="set MLB26_SAVE to a save folder")


def test_checksum_matches():
    assert open_save(SAVE).checksum_ok


def test_export_shape():
    d = open_save(SAVE).export()
    assert len(d["teams"]) == 30
    assert all(len(t["roster"]) >= 26 for t in d["teams"])
    assert len(d["players"]) > 3000


def test_profile_folder_finds_franchise_slot():
    # MLB26_SAVE may be a FRAN slot folder or the profile folder above it.
    from mlb26save.container import find_franchise_slots
    p = Path(SAVE)
    profile = p.parent if p.name.upper().startswith("FRAN") else p
    slots = find_franchise_slots(profile)
    assert slots and slots[0][0].parent.name.upper().startswith("FRAN")
    assert open_save(profile).save_path == slots[0][0]


def test_patch_roundtrip():
    s = open_save(SAVE)
    t = s.db.largest("D_PLAYER_ATTS")
    raw = bytearray(s.raw)
    s.db.patch(raw, t, 0, "SPEED", 77)
    comp = zlib.compress(bytes(raw), 9)
    again = Database(zlib.decompress(comp))
    assert again.largest("D_PLAYER_ATTS").rows[0]["SPEED"] == 77
    assert len(hashlib.sha256(comp).digest()) == 32


def test_career_history_and_farm():
    d = open_save(SAVE).export()
    judge = next(p for p in d["players"] if p["first"] == "Aaron" and p["last"] == "Judge")
    by_year = {r["y"]: r for r in judge["career"]}
    assert by_year[2022]["b"][6] == 62 and by_year[2017]["b"][6] == 52   # HR column
    levels = {c["level"] for c in d["clubs"] if c.get("level")}
    assert levels == {"AAA", "AA", "A"}
    me = d["season"]["userTeam"]
    assert sorted(c["level"] for c in d["clubs"] if c.get("org") == me) == ["A", "AA", "AAA"]
    assert any(p["stats"].get("aaa") for p in d["players"] if p["level"] == "AAA")
