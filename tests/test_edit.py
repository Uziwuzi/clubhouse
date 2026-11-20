"""Player edits on a temp copy of the save (set MLB26_SAVE). Never touches the real save."""
import os
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "decoder"))
from mlb26save import open_save                              # noqa: E402
from mlb26save.container import SaveSlot                     # noqa: E402
from mlb26save.edit import EditError, apply_player_edits     # noqa: E402

SAVE = os.environ.get("MLB26_SAVE")
pytestmark = pytest.mark.skipif(not SAVE, reason="set MLB26_SAVE to a save folder")


@pytest.fixture()
def copy(tmp_path):
    src = open_save(SAVE)
    d = tmp_path / "FRAN_TEST"
    d.mkdir()
    shutil.copy2(src.save_path, d / src.save_path.name)
    shutil.copy2(src.info_path, d / "SAVEINFO")
    return SaveSlot(d / src.save_path.name, d / "SAVEINFO")


def _hitter(data):
    return next(p for p in data["players"] if p["team"] is not None and p["pos"] not in ("P", "C"))


def test_edit_round_trip(copy, tmp_path):
    before = copy.export()
    p = _hitter(before)
    raw = bytearray(copy.raw)
    new_pos = "C" if p["pos"] != "C" else "1B"
    done = apply_player_edits(copy.db, raw, p["id"], {
        "first": "Testy", "last": "McTestface", "num": (p["num"] + 1) % 100, "pos": new_pos,
        "bats": "S", "throws": "L" if p["throws"] == "R" else "R"})
    assert set(done) == {"first", "last", "num", "pos", "bats", "throws"}
    assert len(raw) == len(copy.raw)
    backup = copy.write(bytes(raw), backup_dir=tmp_path / "bk")
    assert (backup / copy.save_path.name).exists()
    again = SaveSlot(copy.save_path, copy.info_path)
    assert again.checksum_ok
    q = next(x for x in again.export()["players"] if x["id"] == p["id"])
    assert (q["first"], q["last"], q["num"], q["pos"], q["bats"]) == ("Testy", "McTestface", (p["num"] + 1) % 100, new_pos, "S")
    assert q["throws"] != p["throws"]
    # Nothing else moved: ratings, age, height and the other players are untouched.
    assert (q["age"], q["height"], q["ovr"], q["ratings"]) == (p["age"], p["height"], p["ovr"], p["ratings"])
    diff = [i for i, (a, b) in enumerate(zip(copy.raw, again.raw)) if a != b]
    row = copy.db.largest("D_PLR_PROFILE").row_offsets[p["id"]]
    assert diff and all(row <= i < row + 120 for i in diff)


def test_edit_rejects_bad_values(copy):
    p = _hitter(copy.export())
    raw = bytearray(copy.raw)
    for bad in ({"last": "x" * 16}, {"num": 100}, {"pos": "P"}, {"bats": "Q"}, {"first": "  "}, {"last": "李"}):
        with pytest.raises(EditError):
            apply_player_edits(copy.db, raw, p["id"], bad)
    assert raw == copy.raw
