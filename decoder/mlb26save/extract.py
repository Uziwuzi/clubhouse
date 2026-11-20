"""Turn the raw tables into one clean, app-friendly dict.

Every field mapping here is tagged in docs/SAVE_FORMAT.md as VERIFIED or GUESS.
"""
from __future__ import annotations

import datetime as dt

from .database import Database

MLB_TEAMS = 30
DIVISIONS = ["AL East", "AL Central", "AL West", "NL East", "NL Central", "NL West"]
POSITIONS = {0: "P", 1: "C", 2: "1B", 3: "2B", 4: "3B", 5: "SS", 6: "LF", 7: "CF", 8: "RF", 9: "DH"}
OPENING_DAY = (3, 25)   # SEASONDATE 0 == March 25 (matches both test saves' slot labels)

# PITCH_TYPE_n codes. LIKELY: matched against real arsenals (Sale 3, Crochet 9, Senga 12,
# Cole 13, Valdez/Yamamoto 2, Wheeler/Webb 17, Yamamoto/Chapman 5, ...). Codes 4, 6, 8, 14, 15 UNKNOWN.
PITCH_NAMES = {0: "Four-seam", 1: "Sinker", 2: "Curveball", 3: "Slider", 5: "Splitter", 9: "Cutter",
               10: "Changeup", 12: "Forkball", 13: "Knuckle curve", 17: "Sweeper"}


def _bats(p):    # VERIFIED: UNSIGNED_PACK[0] bits 23-24, 0 = R, 1 = L, 2 = S (28 known hitters)
    return "RLS?"[(p["UNSIGNED_PACK"][0] >> 23) & 3]


def _age(p):     # VERIFIED: UNSIGNED_PACK[0] bits 16-22, exact for 25 players with known birthdays
    return (p["UNSIGNED_PACK"][0] >> 16) & 127


def _service_years(p):  # VERIFIED: UNSIGNED_PACK[1] bits 10-15, 17 of 19 known players exact (other 2 off by one)
    return (p["UNSIGNED_PACK"][1] >> 10) & 63


def _throws(p):  # VERIFIED: SIGNED_PACK bit 30, 1 = L (26 known pitchers; 31% of MLB arms are LHP)
    return "L" if (p["SIGNED_PACK"] >> 30) & 1 else "R"


def _number(p):  # VERIFIED: UNSIGNED_PACK[4] bits 7-13 = jersey number (1175 of 1178 MLB players match real numbers)
    return (p["UNSIGNED_PACK"][4] >> 7) & 127


def _height(p):  # VERIFIED: UNSIGNED_PACK[0] bits 9-15 = height in inches (1178 of 1178)
    return (p["UNSIGNED_PACK"][0] >> 9) & 127


def _weight(p):  # LIKELY: UNSIGNED_PACK[0] bits 0-8 = weight in lb (15 of 16 known players exact)
    return p["UNSIGNED_PACK"][0] & 511


# D_QUIRKS.DATA is a 32-bit little-endian flag set. Names and descriptions come from the game's
# romfs/NSW/UI/QUIRKS.NSW_EN. The bit for each name is LIKELY, not VERIFIED: matched by who carries it
# (home/road/day/night are the only bits shared by hitters and pitchers; bit 16 is the 100 mph arms;
# bit 17 is high-stamina starters; bit 18 is leadoff types). See docs/SAVE_FORMAT.md.
QUIRKS = {
    0: ("Homebody", "Performs better when playing at home."),
    1: ("Road Warrior", "Performs better when playing on the road."),
    2: ("First-Pitch Hitter", "Excels at hitting the first pitch of an at-bat."),
    3: ("Dead Red", "Excels at hitting fastballs."),
    4: ("Breaking Ball Hitter", "Excels at hitting breaking balls."),
    5: ("Unfazed", "Excels when hitting with 2 strikes."),
    6: ("Fighter", "Performs better in the 9th inning or later."),
    7: ("Stopper", "Performs better when his team is behind."),
    8: ("Rally Monkey", "Performs better when his team is behind."),
    9: ("Pickoff Artist", "Increases success rate of pickoffs."),
    10: ("Situational Hitter", "Excels at driving in a runner from third with less than 2 outs."),
    11: ("Pinch Hitter", "Excels at pinch hitting."),
    12: ("Bad Ball Hitter", "Excels at hitting pitches outside the strike zone."),
    13: ("Day Player", "Performs better when playing day games."),
    14: ("Night Player", "Performs better when playing night games."),
    15: ("Outlier II", "Secondary pitch exceeds the max velocity limit."),
    16: ("Outlier I", "Primary pitch exceeds the max velocity limit."),
    17: ("Break Outlier", "Loses less break when tired."),
    18: ("Table Setter", "Performs better when no runners are on."),
}


def _quirks(kids) -> list[int]:
    q = kids.get("D_QUIRKS")
    if not q or not q.rows:
        return []
    v = int.from_bytes(bytes(q.rows[0]["DATA"]), "little")
    return [b for b in range(32) if v >> b & 1]


def _rgb(c):
    return "#%02x%02x%02x" % tuple(c[:3])


def _ratings(a: dict, pos: str) -> dict:
    bat = {
        "conR": a["CONTACT_RIGHT"], "conL": a["CONTACT_LEFT"],
        "powR": a["POWER_RIGHT"], "powL": a["POWER_LEFT"],
        "vision": a["PLATE_VISION"], "discipline": a["PLATE_DISCIPLINE"],
        "clutch": a["BATTING_CLUTCH"], "bunt": a["BUNTING_ABILITY"], "dragBunt": a["DRG_BUNTING_ABLT"],
    }
    fld = {
        "fielding": a["FIELDING_ABILITY"], "armStr": a["ARM_STRENGTH"], "armAcc": a["ARM_ACCURACY"],
        "reaction": a["REACTION_TIME"], "blocking": a["BLOCKING"],
    }
    run = {"speed": a["SPEED"], "stealing": a["BASE_STEALING"], "aggression": a["BASERUNNING_AGG"]}
    out = {"batting": bat, "fielding": fld, "running": run, "durability": a["DURABILITY"]}
    if pos == "P":
        out["pitching"] = {
            "stamina": a["STAMINA"], "h9": a["HITS_PER_BF"], "k9": a["K_PER_BF_RIGHT"],
            "k9L": a["K_PER_BF_LEFT"], "bb9": a["BB_PER_BF"], "hr9": a["HR_PER_BF"],
            "clutch": a["PITCHING_CLUTCH"],
        }
        out["arsenal"] = [
            {"type": a[f"PITCH_TYPE_{i}"], "name": PITCH_NAMES.get(a[f"PITCH_TYPE_{i}"]), "velocity": a[f"VELOCITY_{i}"],
             "movement": a[f"PITCH_MOVEMENT_{i}"], "usage": a[f"PITCH_USAGE_{i}"]}
            for i in range(6) if a[f"PITCH_TYPE_{i}"] != 255
        ]
    return out


def _bat_line(s: dict) -> dict:
    ab, h = s["AT_BATS"], s["HITS"]
    bb, hbp, sf = s["BASE_on_BALLS"], s.get("HIT_BY_PITCH", 0), s.get("SAC_FLY", 0)
    tb = h + s["DOUBLES"] + 2 * s["TRIPLES"] + 3 * s["HR"]
    pa = ab + bb + hbp + sf
    return {
        "g": s["GAMES"], "ab": ab, "h": h, "2b": s["DOUBLES"], "3b": s["TRIPLES"], "hr": s["HR"], "r": s["RUNS"],
        "rbi": s["RBI"], "bb": bb, "so": s["STRIKEOUTS"], "sb": s["STOLEN_BASES"],
        "hitStreak": s.get("HIT_STRK_GAMES", 0),   # LIKELY: current hitting streak in games
        "avg": round(h / ab, 3) if ab else None,
        "obp": round((h + bb + hbp) / pa, 3) if pa else None,
        "slg": round(tb / ab, 3) if ab else None,
        # splits vs right- / left-handed pitchers, and this month (hot / cold)
        "vsR": {"ab": s.get("AT_BATS_RHP", 0), "h": s.get("HITS_RHP", 0), "hr": s.get("HR_RHP", 0), "so": s.get("STRIKEOUTS_RHP", 0)},
        "vsL": {"ab": s.get("AT_BATS_LHP", 0), "h": s.get("HITS_LHP", 0), "hr": s.get("HR_LHP", 0), "so": s.get("STRIKEOUTS_LHP", 0)},
        "month": {"ab": s.get("AT_BATS_TMON", 0), "h": s.get("HITS_TMON", 0), "hr": s.get("HR_TMON", 0),
                  "bb": s.get("BB_TMON", 0)},
        # the current (or just finished) series. VERIFIED: Soto 6-for-13, 2 HR vs CIN in the Mets save
        "series": {"ab": s.get("AT_BATS_SERIES", 0), "h": s.get("HITS_SERIES", 0), "hr": s.get("HR_SERIES", 0),
                   "rbi": s.get("RBI_SERIES", 0), "2b": s.get("DOUBLES_SERIES", 0), "sb": s.get("SB_SERIES", 0)},
    }


def _pit_line(s: dict) -> dict:
    outs = s["P_IP"]                    # stored as outs recorded
    ip = outs / 3
    return {
        "g": s["P_GAMES"], "gs": s["P_G_STARTED"], "w": s["P_WINS"], "l": s["P_LOSSES"],
        "sv": s["P_SAVES"], "ip": f"{outs // 3}.{outs % 3}", "outs": outs,
        "h": s["P_HITS"], "er": s["P_EARNEDRUNS"], "bb": s["P_BASEONBALLS"],
        "so": s["P_STRIKEOUTS"], "hld": s["P_HOLDS"],
        "hr": s["P_HOMERUNS"],
        "era": round(9 * s["P_EARNEDRUNS"] / ip, 2) if outs else None,
        "whip": round((s["P_HITS"] + s["P_BASEONBALLS"]) / ip, 2) if outs else None,
        # opponents' results vs right- / left-handed batters
        "vsR": {"ab": s.get("P_AB_RHB", 0), "h": s.get("P_H_RHB", 0), "so": s.get("P_SO_RHB", 0)},
        "vsL": {"ab": s.get("P_AB_LHB", 0), "h": s.get("P_H_LHB", 0), "so": s.get("P_SO_LHB", 0)},
        # pitches thrown on each of the last 7 game days, most recent first (this season's copy only)
        "series": {"outs": s.get("P_IP_SERIES", 0), "so": s.get("P_SO_SRS", 0), "er": s.get("P_ER_SER", 0),
                   "g": s.get("P_G_SERIES", 0), "sv": s.get("P_SV_SER", 0)},
        "pitches7": [s.get(k, 0) for k in ("PITCHES_TODAY", "PITCHES_1D_AGO", "PITCHES_2D_AGO", "PITCHES_3D_AGO",
                                            "PITCHES_4D_AGO", "PITCHES_5D_AGO", "PITCHES_6D_AGO")],
    }


SCHED_STRIDE = 255   # D_SCHEDULE_DATA: one row per team per day; row = team * 255 + day

# Minor leagues: D_TEAM_PROF LEAGUE_INX / DIVISION_INX of the AAA and AA clubs. VERIFIED by the clubs in each.
MINOR_LEAGUES = {2: "International League", 3: "Pacific Coast League", 4: "Eastern League", 5: "Southern League", 6: "Texas League"}
MINOR_DIVS = {6: "East", 7: "West", 8: "East", 9: "West", 10: "Northeast", 11: "Southwest", 12: "North", 13: "South", 14: "North", 15: "South"}

# D_CAREER_STATS: 28 season slots per player, row = player * 28 + slot, newest season first. Empty slots read
# YEAR 2025 / ORG 31 with no games. ORG = MLB team index, 30 = more than one team that year. MLB seasons only.
# VERIFIED: Judge 2017 52 HR / 2022 62 HR, Trout back to 2011, Verlander back to 2005 (no 2021), Soto 2022 ORG 30.
CAREER_SLOTS = 28


def _career(t, pid: int, pos: str) -> list:
    """Every MLB season on file for a player, oldest first, as compact rows.
    Hitters: [year, org, g, ab, r, h, 2b, 3b, hr, rbi, bb, so, sb, cs, hbp, sf]
    Pitchers: [year, org, g, gs, w, l, sv, hld, outs, h, er, hr, bb, so, cg, sho, qs, bf]
    (pitchers who also hit, like Ohtani, get "bat" rows too)."""
    out = []
    for k in range(CAREER_SLOTS):
        r = t.rows[pid * CAREER_SLOTS + k]
        if not r["GAMES_PLAYED"] and not r["GAMES_PITCHED"]:
            continue
        row = {"y": r["YEAR"], "org": r["ORG"]}
        if r["GAMES_PITCHED"]:
            row["p"] = [r["GAMES_PITCHED"], r["GAMES_STARTED"], r["WINS"], r["LOSSES"], r["SAVES"], r["HOLDS"],
                        r["INNINGS_PITCHED"], r["HITS_ALLOWED"], r["EARNED_RUNS"], r["HOMERUNS_ALLOWED"],
                        r["WALKS_ALLOWED"], r["P_STRIKEOUTS"], r["COMPLETE_GAMES"], r["SHUTOUTS"], r["QUALITY_STARTS"],
                        r["BATTERS_FACED"]]
        if r["AT_BATS"] or (pos != "P" and r["GAMES_PLAYED"]):
            row["b"] = [r["GAMES_PLAYED"], r["AT_BATS"], r["RUNS"], r["HITS"], r["DOUBLES"], r["TRIPLES"], r["HOME_RUNS"],
                        r["RBIS"], r["WALKS"], r["B_STRIKEOUTS"], r["STOLEN_BASES"], r["CAUGHT_STEALING"],
                        r["HIT_BY_PITCH"], r["SAC_FLIES"]]
        out.append(row)
    return sorted(out, key=lambda x: x["y"])


def _draft_results(db: Database):
    """This year's draft, once it has happened. VERIFIED on the Mets Aug 2, 2026 save:
    - D_DRAFT_PICKS (200 rows, empty before the draft): name, AMATEUR_INX_16BT = row in D_AMATUER_PLAYER
      (200 of 200 names match), PICK_SELECTED = overall pick (CWS picked first: A.J. Klein = 1; 0 = not taken),
      BONUS_OFFER = bonus in dollars (LIKELY), SALARY > 0 once he has signed (LIKELY: 11 drafted players have 0).
    - D_DRAFTPICKLIST: 30 rows, row = MLB team, PICKS = that team's D_DRAFT_PICKS rows (255 = empty).
      Mets: picks 26, 73, 95, 125, 155, 185, matching their spots in DRAFT_ORDER.
    Drafted players stay in D_AMATUER_PLAYER (club 255) after signing; they are not in the league
    D_PLR_PROFILE table during the season."""
    if not db.find("D_DRAFT_PICKS"):
        return []
    rows = db.largest("D_DRAFT_PICKS").rows
    team_of = {}
    if db.find("D_DRAFTPICKLIST"):
        for t, r in enumerate(db.read(db.find("D_DRAFTPICKLIST")[0][0]).rows[:MLB_TEAMS]):
            for i in r["PICKS"]:
                if i != 255:
                    team_of[i] = t
    # After a season rolls over the amateur class is regenerated; picks that no longer point at the same names
    # belong to last year's draft (kept by Clubhouse's history file), so don't report them as this year's.
    amt = db.largest("D_AMATUER_PLAYER") if db.find("D_AMATUER_PLAYER") else None
    def same(r):
        i = r["AMATEUR_INX_16BT"]
        if amt is None or i == 0xFFFF or i >= len(amt.children) or "D_PLR_PROFILE" not in amt.children[i]:
            return False
        p = amt.children[i]["D_PLR_PROFILE"].rows[0]
        return (p["FIRST_NAME"], p["LAST_NAME"]) == (r["FIRST_NAME"], r["LAST_NAME"])
    named = [r for r in rows if r["LAST_NAME"] and r["PICK_SELECTED"]]
    if not named or sum(map(same, named)) < len(named) * .8:
        return []
    out = []
    for i, r in enumerate(rows):
        if not r["LAST_NAME"] or not r["PICK_SELECTED"]:
            continue
        am = r["AMATEUR_INX_16BT"] if r["AMATEUR_INX_16BT"] != 0xFFFF else None
        out.append({"first": r["FIRST_NAME"], "last": r["LAST_NAME"], "pick": r["PICK_SELECTED"], "team": team_of.get(i),
                    "signed": r["SALARY"] > 0, "salary": r["SALARY"], "bonus": r["BONUS_OFFER"],
                    "prospect": 100000 + am if am is not None else None})
    return sorted(out, key=lambda x: x["pick"])


def _schedule(db: Database) -> list[list[list[int]]] | None:
    """Every MLB team's full season: [day, game number, opponent, home(1/0), time hhmm] per game.

    D_SCHEDULE_DATA (24,450 rows) is a grid of 255 days per team in team-index order (MLB clubs
    0-29 first, then minor-league clubs). Empty rows are off days. PACKED_DATA:
    bits 0-7 = opponent team index, bits 8-15 = this team's game number (1-162),
    bit 23 = home (0xC0... = home, 0x40... = away). DATE_TIME = start time as hhmm.
    `day` counts from March 25 like SEASONDATE.
    VERIFIED: White Sox games 24-30 (at AZ, vs WSH, vs LAA) land on days 28-34 exactly as the game's
    own upcoming list says, and every MLB club has games 1-162.
    """
    if not db.find("D_SCHEDULE_DATA"):
        return None
    rows = db.largest("D_SCHEDULE_DATA").rows
    out = []
    for t in range(MLB_TEAMS):
        games = []
        for day in range(SCHED_STRIDE):
            i = t * SCHED_STRIDE + day
            if i >= len(rows):
                break
            p = rows[i]["PACKED_DATA"]
            if p:
                games.append([day, (p >> 8) & 0xFF, p & 0xFF, 1 if (p >> 16) & 0x80 else 0, rows[i]["DATE_TIME"]])
        out.append(games)
    return out


def _all_star(db: Database, year: int) -> dict | None:
    """All-Star Game date, host and result. The save does NOT store fan voting (no such field)."""
    sc, asg = db.find("D_SCHED_CONST"), db.find("D_ALL_STAR_INFO")
    if not sc:
        return None
    c = db.read(sc[0][0]).rows[0]
    out = {"date": dt.date(year, c["ALLSTAR_MONTH"] + 1, c["ALLSTAR_DATE"]).isoformat()}   # months are 0-based
    if asg:
        g = db.read(asg[0][0]).rows[0]
        out["host"] = g["HOST"]
        played = g["WINNING_PIT"] != 0xFFFF
        out["played"] = played
        if played:
            out.update(homeScore=g["HOME_SCORE"], awayScore=g["AWAY_SCORE"], homeHits=g["HOME_HITS"], awayHits=g["AWAY_HITS"],
                       win=g["WINNING_PIT"], loss=g["LOSING_PIT"], save=g["SAVING_PIT"] if g["SAVING_PIT"] != 0xFFFF else None)
    return out


def _draft(db: Database, user_team: int | None = None):
    """This year's amateur draft class and the draft order.

    D_AMATUER_PLAYER (sic, 540 rows): each row carries its own child D_PLR_PROFILE / D_PLAYER_ATTS
    (one row each) holding the prospect's name and ratings. VERIFIED.
    DRAFT_RANK: 0 = top of the game's board, 65535 = unranked (200 are ranked). VERIFIED.
    BONUS_DEMAND: dollars (No. 1 asks ~$10.6M, like a real No. 1 slot). LIKELY.
    CLASS, REGION, SCOUTED_* / PERCEIVED_*: UNKNOWN, not exported.
    D_DRAFT_DATA.DRAFT_ORDER: 150 team indexes, pick by pick (5 rounds incl. comp picks). LIKELY.
    """
    am = db.find("D_AMATUER_PLAYER")
    if not am:
        return None
    t = db.largest("D_AMATUER_PLAYER")
    prospects = []
    for i, r in enumerate(t.rows):
        kids = t.children[i] if i < len(t.children) else {}
        if "D_PLR_PROFILE" not in kids or "D_PLAYER_ATTS" not in kids:
            continue
        p, a = kids["D_PLR_PROFILE"].rows[0], kids["D_PLAYER_ATTS"].rows[0]
        if not p["LAST_NAME"]:
            continue
        pos = POSITIONS.get(p["POSITION"], "?")
        prospects.append({
            "id": 100000 + i, "prospect": True, "first": p["FIRST_NAME"], "last": p["LAST_NAME"],
            "pos": pos, "role": pos,   # not SP/RP: that split comes from stamina, a hidden rating
            "bats": _bats(p), "throws": _throws(p), "ovr": a["RANK"], "pot": a["POTENTIAL"], "age": _age(p),
            "height": _height(p), "weight": _weight(p),
            "rank": r["DRAFT_RANK"] + 1 if r["DRAFT_RANK"] != 0xFFFF else None,
            "bonus": r["BONUS_DEMAND"], "ratings": _ratings(a, pos),
            # SCOUTED_CERT[team] (5-100): how well that club has scouted him. LIKELY: 100 for the few each club
            # has fully scouted, 5 for most. Clubhouse narrows its fog-of-war ranges with it.
            "cert": (r["SCOUTED_CERT"][user_team] if user_team is not None and user_team < len(r.get("SCOUTED_CERT") or []) else None),
            "team": None, "club": None, "injury": None, "contract": None, "stats": {},
        })
    order = []
    dd = db.find("D_DRAFT_DATA")
    if dd:
        order = [x for x in db.read(dd[0][0]).rows[0]["DRAFT_ORDER"] if x < MLB_TEAMS]
    return {"prospects": prospects, "order": order}


def _upcoming(db: Database, prof_t, year: int, user_team: int, away: int, home: int, day0: dt.date | None = None):
    """The next 7 games for the user's team and for its next opponent, with probable starters.

    These tables describe the two teams of the game the save is set up to play next
    (D_GAME_OPTIONS.AWAYTEAM / HOMETEAM), not necessarily the user's team:
    D_SCHED_INFO (14 rows): rows 0-6 = AWAYTEAM's next games, rows 7-13 = HOMETEAM's.
    D_UPCOMING_PI (28 rows): row i = the starter for the team owning schedule row i,
    row 14+i = the opposing starter in that game. PLAYER_ID matches D_PLR_PROFILE.PLAYER_ID.
    D_GAMEINFO.UPCMG_GM_DATES: season day of each schedule row.
    VERIFIED on two saves: White Sox (AWAYTEAM = CWS at AZ) and Mets May 29 (AWAYTEAM / HOMETEAM were
    the Portland / Binghamton minor-league clubs, so the rows said nothing about the Mets).
    Returns None unless the user's team is one of the two.
    """
    if user_team not in (away, home):
        return None
    si, up, gi = db.find("D_SCHED_INFO"), db.find("D_UPCOMING_PI"), db.find("D_GAMEINFO")
    if not si or not up:
        return None
    si, up = db.read(si[0][0]).rows, db.read(up[0][0]).rows
    if len(si) != 14 or len(up) != 28:
        return None
    days = db.read(gi[0][0]).rows[0].get("UPCMG_GM_DATES") if gi else None
    by_pid = {}
    for i, p in enumerate(prof_t.rows):
        if p["LAST_NAME"] and p["PLAYER_ID"]:
            by_pid.setdefault(p["PLAYER_ID"], i)

    def games(lo):
        out = []
        for i in range(lo, lo + 7):
            r = si[i]
            if not r["ACTIVE"]:
                continue
            d = days[i] if days else None
            out.append({
                "game": r["GAME"], "opp": r["OPPONENT"], "home": bool(r["HOME"]), "time": r["TIME"],
                "day": d, "date": ((day0 or dt.date(year, *OPENING_DAY)) + dt.timedelta(days=d)).isoformat() if d is not None else None,
                "sp": by_pid.get(up[i]["PLAYER_ID"]) if up[i]["PLAYER_ID"] else None,
                "oppSp": by_pid.get(up[14 + i]["PLAYER_ID"]) if up[14 + i]["PLAYER_ID"] else None,
            })
        return out

    a, h = games(0), games(7)
    mine, theirs = (a, h) if user_team == away else (h, a)
    mine = [g for g in mine if g["opp"] < MLB_TEAMS]   # only real MLB games
    if not mine:
        return None
    return {"games": mine, "opp": mine[0]["opp"], "oppGames": theirs}


def _calendar(db: Database, year: int):
    """Spring training and season dates from D_SCHED_CONST (months are 0-based). VERIFIED on the Royals
    Feb 20, 2026 save: spring training Feb 20 - Mar 24, Opening Day Mar 25 (matches SEASONDATE 0), All-Star
    July 14. The save's own date during spring comes from the slot label; SEASONDATE stays 0 and
    TIME_OF_YEAR reads 3, as in the regular season, so neither tells spring apart."""
    if not db.find("D_SCHED_CONST"):
        return None
    c = db.largest("D_SCHED_CONST").rows[0]
    d = lambda m, k: dt.date(year, c[m] + 1, c[k]).isoformat()
    try:
        return {"springStart": d("ST_START_MONTH", "ST_START_DATE"), "springEnd": d("ST_END_MONTH", "ST_END_DATE"),
                "openingDay": d("SEAS_START_MONTH", "SEAS_START_DATE"), "seasonEnd": d("SEAS_END_MONTH", "SEAS_END_DATE")}
    except (KeyError, ValueError):
        return None


def _stat_tables(db: Database, name: str):
    """The four league-wide copies of a stats table, in file order.
    In both test saves: [0] = last season, [1] = current season, [2],[3] = empty
    (probably postseason / spring). Treat [2],[3] as unknown."""
    offs = sorted(o for o, c in db.find(name) if c > 1000)
    return [db.read(o) for o in offs]


def export_league(db: Database) -> dict:
    go = db.read(db.find("D_GAME_OPTIONS")[0][0]).rows[0]
    year = go["START_YEAR"] + go["SEASONYEAR"]
    day = go["SEASONDATE"]
    # MODESTATE: 2 = spring training, 4 = regular season. VERIFIED on 8 saves (3 spring: Royals Feb 20 and Mar 13,
    # Mets Feb 20; 5 in season). In spring, SEASONDATE counts days from the start of camp (Royals Mar 13 = 21), and
    # the "this season" stats copy and D_SEASON_RECORD hold spring games (the Royals were 12-8 after 20).
    phase = {2: "spring", 4: "season"}.get(go.get("MODESTATE"))
    cal = _calendar(db, year)
    if phase == "spring" and cal:
        date = dt.date.fromisoformat(cal["springStart"]) + dt.timedelta(days=day)
    else:
        date = dt.date(year, *OPENING_DAY) + dt.timedelta(days=day)
    user_team = go["CURRENTTEAM"]

    teams_t = db.largest("D_TEAM_PROF")
    prof_t = db.largest("D_PLR_PROFILE")
    atts_t = db.largest("D_PLAYER_ATTS")
    season_t = db.largest("D_SEASON_INFO")
    bat_tables = _stat_tables(db, "D_PLAYER_STATS")
    pit_tables = _stat_tables(db, "D_PITCHER_STATS")

    # Club (team) of every player: low byte of D_PLR_PROFILE.SIGNED_PACK. VERIFIED
    # against 10 known players and team at-bat totals. 0-29 = MLB, 30/31 = All-Star
    # squads, 32-34 = custom teams, 35+ = minor league affiliates.
    # NOTE: D_ROSTER_HLPR is NOT the live roster (it disagrees with the stats).
    club_of = {pid: p["SIGNED_PACK"] & 0xFF for pid, p in enumerate(prof_t.rows) if p["LAST_NAME"]}
    clubs = [{"id": k, "abbr": r["SHORT_NAME"], "city": r["CITY_NAME"], "name": r["TEAM_NAME"]}
             for k, r in enumerate(teams_t.rows)]

    # ---- farm systems ------------------------------------------------------------
    # D_AFFILIATIONS: AAA_/AA_/A_AFFILIATES[mlb team] = club index. VERIFIED (Toronto -> Buffalo Bisons,
    # New Hampshire Fisher Cats, Vancouver Canadians; Mets -> Syracuse, Binghamton, Brooklyn).
    level_of = {}
    if db.find("D_AFFILIATIONS"):
        aff = db.largest("D_AFFILIATIONS").rows[0]
        for lvl, key in (("AAA", "AAA_AFFILIATES"), ("AA", "AA_AFFILIATES"), ("A", "A_AFFILIATES")):
            for t, c in enumerate(aff[key][:MLB_TEAMS]):
                level_of[c] = (lvl, t)
    for c, (lvl, t) in level_of.items():
        if c >= len(clubs):
            continue
        r = teams_t.rows[c]
        clubs[c].update(level=lvl, org=t, league=MINOR_LEAGUES.get(r["LEAGUE_INX"]),
                        division=MINOR_DIVS.get(r["DIVISION_INX"]))
        # D_SEASON_INFO rows 35-94 are the AAA and AA clubs (same layout as MLB rows). VERIFIED: ~54 games by late May.
        if c < len(season_t.rows) and "D_SEASON_RECORD" in season_t.children[c]:
            rec = season_t.children[c]["D_SEASON_RECORD"].rows[0]
            sc = season_t.children[c]["D_SEASON_SCORES"].rows[: rec["GAMES"]] if "D_SEASON_SCORES" in season_t.children[c] else []
            clubs[c]["record"] = {"w": rec["WINS"], "l": rec["GAMES"] - rec["WINS"], "streakRaw": rec["STREAK"],
                                  "last10": [x for x in rec["LAST_10"] if x != 255],
                                  "rs": sum(g["US"] for g in sc), "ra": sum(g["OPPONENT"] for g in sc)}
            clubs[c]["games"] = [[g["US"], g["OPPONENT"]] for g in sc]
    career_t = db.largest("D_CAREER_STATS") if db.find("D_CAREER_STATS") else None
    if career_t and len(career_t.rows) != CAREER_SLOTS * len(prof_t.rows):
        career_t = None   # layout differs from the verified one: leave history out rather than misread it

    # ---- teams --------------------------------------------------------------
    teams = []
    for i in range(MLB_TEAMS):
        t = teams_t.rows[i]
        colors = [_rgb(r["COLORS"]) for r in teams_t.children[i].get("D_TEAM_COLORS").rows] \
            if "D_TEAM_COLORS" in teams_t.children[i] else []
        kids = season_t.children[i]
        rec = kids["D_SEASON_RECORD"].rows[0]
        games = kids["D_SEASON_SCORES"].rows[: rec["GAMES"]]
        # D_SEAS_PIT_INFO: winning / losing / saving pitcher per game, as D_PLR_PROFILE row numbers (65535 = none). VERIFIED
        pit = kids["D_SEAS_PIT_INFO"].rows if "D_SEAS_PIT_INFO" in kids else []
        nopit = lambda v: None if v == 0xFFFF else v
        rs, ra = sum(g["US"] for g in games), sum(g["OPPONENT"] for g in games)
        last10 = [x for x in rec["LAST_10"] if x != 255]
        teams.append({
            "id": i, "abbr": t["SHORT_NAME"], "city": t["CITY_NAME"], "name": t["TEAM_NAME"],
            "league": "AL" if t["LEAGUE_INX"] == 0 else "NL",
            "division": DIVISIONS[t["DIVISION_INX"]] if t["DIVISION_INX"] < 6 else None,
            "colors": colors,
            "record": {
                "w": rec["WINS"], "l": rec["GAMES"] - rec["WINS"],
                "homeW": rec["WINSHOME"], "homeL": rec["GAMESHOME"] - rec["WINSHOME"],
                "divW": rec["WINSDIV"], "divL": rec["GAMESDIV"] - rec["WINSDIV"],
                "oneRunW": rec["WINSONE"], "oneRunL": rec["GAMESONE"] - rec["WINSONE"],
                "xtraW": rec["WINSEXTRA"], "xtraL": rec["GAMESEXTRA"] - rec["WINSEXTRA"],
                "streakRaw": rec["STREAK"], "last10": last10, "rs": rs, "ra": ra,
            },
            "games": [{"us": g["US"], "them": g["OPPONENT"], "h": g["US_HITS"], "oh": g["OPPONENT_HITS"],
                       "e": g.get("US_ERR", 0), "oe": g.get("OPPONENT_ERR", 0),
                       "w": nopit(pit[k]["WIN"]) if k < len(pit) else None,
                       "l": nopit(pit[k]["LOSS"]) if k < len(pit) else None,
                       "sv": nopit(pit[k]["SAVE"]) if k < len(pit) else None}
                      for k, g in enumerate(games)],
            "roster": [pid for pid, c in club_of.items() if c == i],
        })

    # ---- players --------------------------------------------------------------
    players = []
    for pid, (p, a) in enumerate(zip(prof_t.rows, atts_t.rows)):
        if not p["LAST_NAME"]:
            continue
        pos = POSITIONS.get(p["POSITION"], "?")
        kids = prof_t.children[pid]
        con = kids.get("D_PLYR_CONTRACT")
        contract = None
        if con and con.rows:
            c = con.rows[0]
            # DATA low 4 bits = years left including this season. VERIFIED (Judge 6, Soto 14, Witt 11, Ohtani 8, ...).
            # The upper bits vary by contract but their meaning is UNKNOWN.
            contract = {"salary": c["CURR_SALARY"], "total": c["TOTAL_SAL"], "years": c["DATA"] & 15}
        club = club_of.get(pid)
        team = club if club is not None and club < MLB_TEAMS else None
        role = pos
        if pos == "P":
            role = "SP" if a["STAMINA"] >= 60 else "RP"
        stats = {}
        # Stats copies: [0] last MLB season, [1] this MLB season, [2] this season in AAA, [3] this season in AA.
        # VERIFIED: 429 of 806 AAA-club hitters have copy-2 lines, 430 of 812 AA-club hitters copy-3 lines; the
        # A level isn't simulated (16 of 375 A-club hitters have any line, all from earlier AA time).
        tabs = pit_tables if pos == "P" else bat_tables
        line = _pit_line if pos == "P" else _bat_line
        for label, idx in (("last", 0), ("season", 1), ("aaa", 2), ("aa", 3)):
            if idx < len(tabs):
                st = line(tabs[idx].rows[pid])
                if label in ("last", "season") or st["g"]:
                    stats[label] = st
        players.append({
            "id": pid, "first": p["FIRST_NAME"], "last": p["LAST_NAME"],
            "pos": pos, "role": role, "team": team, "club": club,
            "level": "MLB" if team is not None else level_of.get(club, (None, None))[0],
            "org": team if team is not None else level_of.get(club, (None, None))[1],
            "career": _career(career_t, pid, pos) if career_t else [],
            "bats": _bats(p), "throws": _throws(p),
            "num": _number(p), "height": _height(p), "weight": _weight(p),
            "quirks": _quirks(kids),
            "ovr": a["RANK"], "pot": a["POTENTIAL"],
            "injury": {"days": p["INJURY_DUR"], "il": p["DL_TIME"]} if p["INJURY_DUR"] else None,
            "age": _age(p),
            # MLB service time = serviceYears + serviceDays/172; seasonServiceDays = days credited this season
            "serviceYears": _service_years(p), "serviceDays": p["MLB_SERVICE_DAYS"], "seasonServiceDays": p["MLB_SD_SEASON"],
            "contract": contract,
            "ratings": _ratings(a, pos), "stats": stats,
        })

    return {
        "format": "mlb26save/0.2",
        "season": {"year": year, "day": day, "date": date.isoformat(), "userTeam": user_team,
                   "calendar": cal, "phase": phase},
        "upcoming": _upcoming(db, prof_t, year, user_team, go.get("AWAYTEAM"), go.get("HOMETEAM"), date - dt.timedelta(days=day)),
        "schedule": _schedule(db),
        "allStar": _all_star(db, year),
        "draft": _draft(db, user_team),
        "draftResults": _draft_results(db),
        "quirks": {str(k): {"name": n, "desc": d} for k, (n, d) in QUIRKS.items()},
        "teams": teams,
        "clubs": clubs,
        "players": players,
    }
