"""Draft results and the franchise history file.

MLB26_SAVE: any franchise slot (pre-draft is fine). MLB26_DRAFT_SAVE: a slot from after the draft (optional).
"""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "decoder"))
from mlb26save import open_save                       # noqa: E402
from mlb26save.history import update_history          # noqa: E402

SAVE = os.environ.get("MLB26_SAVE")
DRAFT_SAVE = os.environ.get("MLB26_DRAFT_SAVE")


@pytest.mark.skipif(not DRAFT_SAVE, reason="set MLB26_DRAFT_SAVE to a post-draft save")
def test_draft_results_link_teams_and_prospects():
    d = open_save(DRAFT_SAVE).export()
    res = d["draftResults"]
    assert len(res) >= 150
    assert [r["pick"] for r in res] == sorted(r["pick"] for r in res)
    pros = {p["id"]: p for p in d["draft"]["prospects"]}
    assert all((pros[r["prospect"]]["first"], pros[r["prospect"]]["last"]) == (r["first"], r["last"]) for r in res)
    first_team = d["draft"]["order"][0]
    assert res[0]["pick"] == 1 and res[0]["team"] == first_team
    assert any(r["team"] == d["season"]["userTeam"] for r in res)


@pytest.mark.skipif(not SAVE, reason="set MLB26_SAVE")
def test_history_never_rewinds(tmp_path):
    d = open_save(SAVE).export()
    d["slot"] = {"label": "later"}
    update_history(d, tmp_path, "fr")
    y = str(d["season"]["year"])
    assert d["history"][y]["label"] == "later"
    older = {**d, "season": {**d["season"], "day": d["season"]["day"] - 1}, "slot": {"label": "older"}}
    update_history(older, tmp_path, "fr")
    assert older["history"][y]["label"] == "later"   # an older save of the same season doesn't overwrite it
