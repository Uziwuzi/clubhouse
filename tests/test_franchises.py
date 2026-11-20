"""Franchise grouping and the upcoming-games owner check.

Set MLB26_FOLDER to a copy of a profile folder holding several FRAN slots (for example one with a White Sox franchise and two Mets franchises). Never point it at the live saves.
"""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "decoder"))
from mlb26save.container import SaveSlot, label_date   # noqa: E402
from mlb26save.franchises import profile_root, scan    # noqa: E402

FOLDER = os.environ.get("MLB26_FOLDER")
needs = pytest.mark.skipif(not FOLDER, reason="set MLB26_FOLDER to a copy of a profile folder")


def test_label_date():
    assert label_date("Mets May 29, 2026") == "2026-05-29"
    assert label_date("White Sox April 21, 2026") == "2026-04-21"
    assert label_date("Uzis final roster") is None


def test_slot_folder_widens_to_profile(tmp_path):
    slot = tmp_path / "FRAN00000000ABCDEF12"
    assert profile_root(slot) == tmp_path
    assert profile_root(tmp_path) == tmp_path


@needs
def test_saves_group_by_franchise_and_newest_first():
    fs = scan(FOLDER)
    assert fs, "no franchises found"
    ids = [f["id"] for f in fs]
    assert len(ids) == len(set(ids))
    for f in fs:
        ts = [s["ts"] for s in f["slots"]]
        assert ts == sorted(ts, reverse=True)          # newest slot first
        assert f["latest"] is f["slots"][0]
        assert len({s["team"] for s in f["slots"]}) == 1  # one franchise = one user team


@needs
def test_schedule_is_complete_and_mirrored():
    for f in scan(FOLDER):
        s = f["latest"]
        x = SaveSlot(Path(s["save"]), Path(s["info"])).export()
        S = x["schedule"]
        assert S and len(S) == 30
        for t in range(30):
            assert [g[1] for g in S[t]] == list(range(1, 163)), f"team {t} game numbers"
        idx = {(t, g[0], g[4]): g for t in range(30) for g in S[t]}
        for t in range(30):
            for day, num, opp, home, tm in S[t]:
                m = idx[(opp, day, tm)]          # the opponent has the same game, same day and time
                assert m[2] == t and m[3] != home


@needs
def test_white_sox_known_games():
    for f in scan(FOLDER):
        if f["abbr"] != "CWS":
            continue
        s = f["latest"]
        S = SaveSlot(Path(s["save"]), Path(s["info"])).export()["schedule"][5]
        # game 24-25 at AZ on days 28-29, 26-28 vs WSH on days 30-32 (from the game's own upcoming list)
        assert [(g[0], g[2], g[3]) for g in S[23:28]] == [(28, 25, 0), (29, 25, 0), (30, 19, 1), (31, 19, 1), (32, 19, 1)]


@needs
def test_upcoming_only_for_the_users_team():
    for f in scan(FOLDER):
        s = f["latest"]
        x = SaveSlot(Path(s["save"]), Path(s["info"])).export()
        up = x["upcoming"]
        if up is None:
            continue
        assert all(g["opp"] < 30 for g in up["games"])     # real MLB opponents only
        assert up["games"] and up["games"][0]["game"] == len(x["teams"][x["season"]["userTeam"]]["games"]) + 1
