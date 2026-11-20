# MLB The Show 26 (Switch) franchise save format

Worked out from two saves of the same White Sox franchise: March 25, 2026 (day 0) and April 21, 2026 (day 27). Each finding below is tagged:

- **VERIFIED**: checked against real data in both saves.
- **LIKELY**: consistent with the data but not proven.
- **UNKNOWN**: not worked out yet.

## Files

The profile folder is `<emulator>\profile\save\<profile-id>\`. **Each save type has its own slot folder inside it**, and each slot folder holds one `SAVE_000` + `SAVEINFO` pair. **VERIFIED** on one PC's saves:

| Slot folder | Contents (label seen) |
|---|---|
| `FRAN<hash>` | Franchise ("White Sox April 21, 2026") |
| `CARR<hash>` | Road to the Show ("<Player Name>, Blue Wahoos SP/2B May 24, 2026") |
| `ROST<hash>` | Saved roster ("Uzis final roster") |
| `SETT<hash>`, `PLYA<hash>` | Settings, audio |

All five use the same zlib + SAVEINFO SHA-256 container. `open_save()` accepts the slot folder, the profile folder, or `profile\save`, and picks the newest `FRAN*` slot. The game writes `SAVE_000` first and `SAVEINFO` up to ~17 s later, so the checksum briefly mismatches mid-save. **UNKNOWN:** whether a second franchise gets a second `FRAN<hash>` folder (likely).

| File | What it is |
|---|---|
| `SAVE_000` | The franchise, zlib-compressed (header `78 9C`). About 1.7–2.5 MB on disk, 52,359,168 bytes unpacked. The unpacked size was identical in both saves. **VERIFIED** |
| `SAVEINFO` | 168 bytes, described below. **VERIFIED** |

`SAVEINFO` layout:

| Offset | Type | Meaning |
|---|---|---|
| 0x00 | char[128] | Slot label, e.g. `White Sox April 21, 2026`, NUL padded |
| 0x80 | u32 LE | Unix timestamp of the save |
| 0x84 | u32 | 0 |
| 0x88 | u8[32] | **SHA-256 of the compressed `SAVE_000` bytes.** VERIFIED: matched in both saves. |

## Inside SAVE_000: three self-describing databases

The unpacked file contains three databases back to back:

| Offset | Contents (by table names) |
|---|---|
| `0x000000` | Current game state: game options, box score, in-game data |
| `0x0AF000` | Player-appearance and custom-content database (logos, uniforms, GM goals) |
| `0x12AF000` | **The franchise:** players, ratings, stats, schedule, standings, inbox, draft, trades and more |

Each database has this layout:

```
"LE90"  u32 desc_len
"[DESC]"  struct definitions ...
"[DATA]"  table blocks ...
```

**Struct definition** (VERIFIED):

```
char[16] name    u32 desc_len (= 4 + 32*n)    u32 n_fields
n_fields x { char[22] name; u16 index; u16 elem_size; u16 count; u16 total_size; u16 0 }
```

**Table block** (VERIFIED):

```
char[16] struct_name   u32 row_count
row_count x {
    fields packed back to back in DESCRIPTOR ORDER (not `index` order), no padding
    then this row's child table blocks (same format, recursive)
}
```

- **Children are not declared anywhere.** The decoder learns them from the data: the blocks sitting between row 0 and row 1 are row 0's children. A repeated name ends the list. This matters for zero-field structs like `D_SEASON_INFO`, whose rows are made only of children.
- **Many tables appear several times.** For example, `D_PLR_PROFILE` has small copies with 1 row each for box-score context, and one league-wide copy with 3,335 rows. Use `Database.largest(name)` to get the league-wide copy.
- **Strings are Latin-1** (Domínguez, Acuña). VERIFIED
- **Integers are little-endian.**
- **Every table has a fixed size**, so editing values never moves anything. Writes are patch-in-place.

`docs/SCHEMA.txt` lists every struct with its field offsets.

## Field meanings

### Season and calendar: `D_GAME_OPTIONS` (database 0)

| Field | Meaning | Status |
|---|---|---|
| `SEASONDATE` | Days since Opening Day: 0 on Mar 25, 27 on Apr 21 | VERIFIED |
| `START_YEAR` + `SEASONYEAR` | Franchise year (2026 + 0) | LIKELY |
| `CURRENTTEAM`, `USER_TEAM_FLAGS` | The user's team index (5 = CWS, 17 = NYM; flags `1<<5`) | VERIFIED for two teams |
| `UUID_STR` | **Franchise id.** All saves of one franchise share it; separately started franchises differ. A franchise's saves can be spread over several `FRAN<hash>` slots, so read the newest by the `SAVEINFO` timestamp | VERIFIED (3 franchises, 4 slots) |
| `AWAYTEAM`, `HOMETEAM` | The two teams of the game the save is set up to play next (can be minor-league clubs) | VERIFIED |
| `TIME_OF_YEAR` | Phase of the season. Reads 3 in the regular season and also on the first day of spring training (Royals Feb 20 save), so it doesn't tell spring apart | UNKNOWN for other phases |

Opening Day = March 25 is inferred from the slot labels. Confirm it for later seasons.

### Teams: `D_TEAM_PROF` (154 rows)

- **Rows 0–29 are the MLB teams**, in division order: AL East, AL Central, AL West, NL East, NL Central, NL West. **VERIFIED**
- **Other rows:** 30–31 are the All-Star squads, 32–34 are custom teams, and 35+ are minor-league affiliates.
- **Fields:** `CITY_NAME`, `TEAM_NAME`, `SHORT_NAME`, `LEAGUE_INX` (0 = AL, 1 = NL) and `DIVISION_INX` (0–5). **VERIFIED**
- **Team colors:** the child table `D_TEAM_COLORS` holds 3 RGBA colors.

### Players

All three of these tables have 3,335 rows, and the row index is the player id.

**`D_PLR_PROFILE`** (VERIFIED)
- `FIRST_NAME`, `LAST_NAME`, `POSITION` (0 P, 1 C, 2 1B, 3 2B, 4 3B, 5 SS, 6 LF, 7 CF, 8 RF)
- `INJURY_DUR`, `DL_TIME` and `MLB_SERVICE_DAYS`
- **Team: `SIGNED_PACK & 0xFF`.** VERIFIED against 10 known players, and the White Sox players' summed at-bats match their games played.
- `UNSIGNED_PACK` (7 × u32) is a bitfield. **Bats = word 0, bits 23–24** (0 = R, 1 = L, 2 = switch). VERIFIED against 28 known hitters; 40% of MLB hitters bat L and 12% switch. Options are still **UNKNOWN**.
- **Throws = `SIGNED_PACK` bit 30** (1 = L). VERIFIED against 26 known pitchers plus the whole White Sox staff; 31% of MLB pitchers throw L.
- **Age = `UNSIGNED_PACK[0]` bits 16–22.** VERIFIED: exact for 25 players with known birthdays. Prospects come out 18–23.
- **Service years = `UNSIGNED_PACK[1]` bits 10–15**; `MLB_SERVICE_DAYS` = the days part (0–171); `MLB_SD_SEASON` = days credited this season. VERIFIED: 17 of 19 known players exact, the other two off by one. Service time reads as years.days, like 6.086.
- **Contract years left = `D_PLYR_CONTRACT.DATA` low 4 bits**, counting this season. VERIFIED: Judge 6, Soto 14, Witt 11, Ohtani 8, Betts 7. Bit 4 always set; bits 10–15 vary by contract but don't match arbitration or no-trade status: **UNKNOWN**.
- Unsigned players (the free-agent pool) have club `SIGNED_PACK & 0xFF == 255`: 557 in the April save.
- `D_FREE_AGENTS` (asking `CONTRACT_TERM` / `CONTRACT_AAV`, `MOTIV_CAP`, ...) and `D_CONTRACT_OFFER` (`INTEREST`, `TEAM`, `AGE`) are empty during the season. Their fields need an offseason save to verify: **UNKNOWN**. The 30-row first copy of `D_FREE_AGENTS` is a misparse.
- `PLAYER_ID` is the game's stable player id, used by other tables such as `D_UPCOMING_PI`. It is not the row index.
- **Jersey number = `UNSIGNED_PACK[4]` bits 7–13.** VERIFIED: 1,175 of 1,178 MLB players match their real numbers. Bits 0–6 hold the same number for 1,163 players: meaning **UNKNOWN** (perhaps a preferred number). The editor writes bits 7–13, and bits 0–6 too when they matched the old number.
- **Height in inches = `UNSIGNED_PACK[0]` bits 9–15.** VERIFIED: 1,178 of 1,178.
- **Weight in lb = `UNSIGNED_PACK[0]` bits 0–8.** LIKELY: 15 of 16 known players exact.
- `FIRST_NAME` / `LAST_NAME` are char[16], Latin-1, NUL padded (15 characters max). `FIRST_NAME_ID` / `LAST_NAME_ID` are 0 for the sample checked; probably the announcer-audio name ids: **UNKNOWN**.
- There are about 670 more one-row copies of `D_PLR_PROFILE`: 52 match league players by `PLAYER_ID` and name, and the rest are draft prospects (`PLAYER_ID` 65533). What owns them is **UNKNOWN**; the editor only patches the league table.

**Children of `D_PLR_PROFILE`**
- `D_PLYR_CONTRACT`: `CURR_SALARY` and `TOTAL_SAL` (VERIFIED: Shane Baz $13.6M of $68M)
- `D_PLYR_ANIMS`, `D_PLYR_AUDIO` (walk-up music handles), `D_PLYR_FLAGS`, `D_STANCE_DATA`
- **`D_QUIRKS.DATA`** (4 bytes) is a 32-bit little-endian flag set of the player's abilities. VERIFIED that it is a flag set (bits 0–18 used; stars carry up to 10). The names and descriptions come from the game's `romfs/NSW/UI/QUIRKS.NSW_EN`, but its list order is not the bit order. The bit-to-name map is **LIKELY**, from who carries each bit:
  - Bits 0, 1, 13 and 14 are the only ones shared by hitters and pitchers: Homebody, Road Warrior, Day Player, Night Player.
  - Bits 7, 9, 15, 16 and 17 are pitcher-only. Bit 16 is exactly the 100 mph arms (Chapman, Duran, Helsley, Doval, Misiorowski): Outlier I (primary pitch over the velocity cap). Bit 15 has fast secondary pitches: Outlier II. Bit 17 is high-stamina starters (average stamina 76): Break Outlier (loses less break when tired). Bit 7 is Stopper and bit 9 Pickoff Artist (both lean left-handed; the weakest pair in this map).
  - Bits 2–6, 8, 10–12 and 18 are hitter-only. Bit 18 is leadoff types (Table Setter); bit 5 is the most elite group, with the best clutch ratings (Unfazed).
  - Confirm against the game's player card for a few players before calling this VERIFIED.

**Career history: `D_CAREER_STATS`** (93,380 rows = 3,335 players × 28). VERIFIED.
- Row = player × 28 + slot, newest season first. Empty slots read `YEAR` 2025 / `ORG` 31 with no games.
- `ORG` = MLB team index; 30 = more than one team that season (Soto 2022, Verlander 2017 and 2023).
- MLB seasons only. Checked: Judge 2017 52 HR and 2022 62 HR, Trout back to 2011, Verlander back to 2005 with no 2021, Ohtani 2024 batting only.
- `INNINGS_PITCHED` is in outs (Verlander 2011: 753 = 251 IP).
- Exported per player as `career`; the app shows it in the player card's Statistics tab. `D_CAREER_TOTALS` (3,335 rows) is not used.

**Farm systems.** VERIFIED.
- `D_AFFILIATIONS.AAA_/AA_/A_AFFILIATES[team]` = club index. Toronto → Buffalo, New Hampshire, Vancouver; Mets → Syracuse, Binghamton, Brooklyn.
- AAA clubs are 35–64, AA clubs 65–94, A clubs 95–124.
- Minor leagues by `LEAGUE_INX` / `DIVISION_INX`: 2 International League (6 East, 7 West); 3 Pacific Coast League (8, 9); 4 Eastern League (10 Northeast, 11 Southwest); 5 Southern League (12 North, 13 South); 6 Texas League (14 North, 15 South). The A clubs have 255 / 255.
- Standings: `D_SEASON_INFO` rows 35–94 are the AAA and AA clubs, in the same layout as the MLB rows.
- Stats copies: copy 2 is AAA, copy 3 is AA. In the May save, 429 of 806 AAA-club hitters have copy-2 lines and 430 of 812 AA-club hitters have copy-3 lines.
- The A level isn't simulated: 16 of 375 A-club hitters have any line, all from earlier AA time.
- No minor-league box scores are stored. The app's "performance watch" diffs its own per-save snapshots (`mlb26save/snapshots.py`, kept in `%APPDATA%\Clubhouse\snapshots`).
- `HIT_STRK_GAMES` = current hitting streak (LIKELY).

**Draft results.** VERIFIED on the Mets Aug 2, 2026 save.
- **`D_DRAFT_PICKS`** (200 rows) is empty before the draft. Afterwards:
  - `AMATEUR_INX_16BT` = the row in `D_AMATUER_PLAYER`; 200 of 200 names match.
  - `PICK_SELECTED` = overall pick. CWS picked first and A.J. Klein = 1; 0 = not taken (2 rows).
  - `BONUS_OFFER` = bonus in dollars (LIKELY). `SALARY` > 0 once signed (LIKELY: 11 picks have 0).
- **`D_DRAFTPICKLIST`** (30 rows): row = MLB team, `PICKS` = that team's `D_DRAFT_PICKS` rows (255 = empty). The Mets have picks 26, 73, 95, 125, 155 and 185, matching their spots in `DRAFT_ORDER`.
- **Signed picks stay in `D_AMATUER_PLAYER`** (club 255) for the rest of the season. They are not in the league `D_PLR_PROFILE` table. The app uses the prospect record until a name match appears in the league table.
- **`D_AMATUER_PLAYER.SCOUTED_CERT[team]`** (5–100) is how well each club has scouted him (LIKELY). `PERCEIVED_OFFSET` / `PERCEIVED_RANGE` per team look like the game's own fog of war: **UNKNOWN**.
- **Season rollover:** the class regenerates, so `_draft_results` drops picks whose names no longer match their amateur row (stale, last year's draft). The franchise history file (`mlb26save/history.py`, `%APPDATA%\Clubhouse\history\<franchise>.json`) keeps each season's standings, affiliate records and full draft. An older save of the same season never overwrites a newer entry.

**`D_PLAYER_ATTS`: ratings, 0–99**
- `RANK` = overall (LIKELY)
- `POTENTIAL`
- `CONTACT_RIGHT/LEFT`, `POWER_RIGHT/LEFT`, `PLATE_VISION`, `PLATE_DISCIPLINE`, `BATTING_CLUTCH`, `BUNTING_ABILITY`, `DRG_BUNTING_ABLT`
- `SPEED`, `BASE_STEALING`, `BASERUNNING_AGG`
- `FIELDING_ABILITY`, `ARM_STRENGTH`, `ARM_ACCURACY`, `REACTION_*`, `BLOCKING`
- `STAMINA`, `HITS_PER_BF` (H/9), `K_PER_BF_RIGHT/LEFT`, `BB_PER_BF`, `HR_PER_BF`, `PITCHING_CLUTCH`, `DURABILITY`
- **Arsenal:** `PITCH_TYPE_n`, `VELOCITY_n`, `PITCH_MOVEMENT_n`, `PITCH_USAGE_n` for n = 0–5; 255 = no pitch.
- **Pitch-type code → name (LIKELY):** matched against real arsenals. 0 four-seam, 1 sinker, 2 curveball, 3 slider, 5 splitter, 9 cutter, 10 changeup, 12 forkball, 13 knuckle curve, 17 sweeper. Codes 4, 6, 8, 14 (Devin Williams' only pitch besides his fastball) and 15 are **UNKNOWN**. `VELOCITY_n` is a 0–99 rating, not mph.
- `CONTACT_RIGHT` / `POWER_RIGHT` = against right-handed pitchers. VERIFIED: left-handed hitters average 67 vs 59.5 on contact.
- **Control:** the `CCONTROL_n` fields are all 0, so control probably lives in `D_PITCHER_ATTS`. **UNKNOWN**
- To verify: compare 3–4 players against their in-game ratings screen.

**Caution: `D_ROSTER_HLPR` is not the live roster.** It disagrees with the stats (Ohtani isn't in it, for example). Its `PLAYER_NUMS` field holds 95 × (u16 player id, u16 flags), and `D_LINEUP` slot numbers refer to it. Its purpose is **UNKNOWN**: it may be a stored roster snapshot. Use the team from `SIGNED_PACK` instead.

### Stats: `D_PLAYER_STATS` and `D_PITCHER_STATS`

Each has four 3,335-row copies, in file order:

| Copy | Contents |
|---|---|
| [0] | Last MLB season (2025) |
| [1] | This MLB season |
| [2] | This season at a minor-league level, probably AAA (Konnor Griffin) |
| [3] | This season at another minor-league level, probably AA |

- Hitting fields include splits vs RHP/LHP, with RISP (`_RSP`), home and away, this month (`_TMON`), last month (`_LMON`) and this series (`_SERIES`).
- `P_IP` is stored as **outs**.
- Platoon splits: hitters `AT_BATS_RHP/LHP`, `HITS_*`, `HR_*`, `STRIKEOUTS_*`; pitchers `P_AB_RHB/LHB`, `P_H_*`, `P_SO_*`. This month: `*_TMON`. (`TOTAL_BASES_TMON` gives nonsense values: **UNKNOWN**.)
- **More splits** (exported Nov 21, 2026):
  - **Home/away:** hitters `HITS_HOME/AWAY`, `HR_HOME/AWAY`, `RBI_HOME/AWAY`; pitchers `P_ER_HOME/AWAY`, `P_IP_HOME/AWAY` (outs). VERIFIED: home plus away equals the season total (Harper 49 + 64 = 113 hits; Wheeler 18 + 26 = 44 ER, 296 + 183 = 479 outs).
  - **Runners in scoring position:** `AT_BATS_RSP`/`HITS_RSP` and `P_AB_RSP`/`P_H_RSP`/`P_SO_RSP`. LIKELY (plausible values).
  - **Other:** `GROUNDED_DP` and `P_WILDPITCHES`. LIKELY.
  - **Not used, values look wrong:** `RBI_RSP` (Harper 17 of 61 RBI), `CAUGHT_STEALING` and `P_B_SAVES` (closers read 0): UNKNOWN.
- `PITCHES_TODAY`, `PITCHES_1D_AGO` … `PITCHES_6D_AGO` in the current-season pitcher copy: pitches on each of the last 7 game days, most recent first. VERIFIED: starters show one outing about every 5–6 days.

### Upcoming games and probable starters (VERIFIED on two saves)

These describe the **two teams of the game the save is set up to play next**, `D_GAME_OPTIONS.AWAYTEAM` and `HOMETEAM`. That is not always the user's team: in the Mets May 29 save those were the Portland and Binghamton minor-league clubs. Only use them when the user's team is one of the two.

| Table | Contents |
|---|---|
| `D_SCHED_INFO` (14 rows, database 0) | Rows 0–6 = AWAYTEAM's next 7 schedule slots, rows 7–13 = HOMETEAM's. `ACTIVE` (0 = off day), `HOME`, `OPPONENT` (team index), `GAME` (game number; the next one = games played + 1), `TIME` (1840 = 6:40 PM) |
| `D_UPCOMING_PI` (28 rows) | Row *i* = the starter for the team owning schedule row *i*; row 14 + *i* = the opposing starter. `PLAYER_ID` (→ `D_PLR_PROFILE.PLAYER_ID`), `NAME`, `WINS`, `LOSSES`, `ERA` (float32 bits). Blank = not named yet |
| `D_GAMEINFO.UPCMG_GM_DATES` (14 × u16) | Season day of each schedule row |

### Full schedule: `D_SCHEDULE_DATA` (VERIFIED on two saves)

- **Layout:** a grid of **255 days per team**, in team-index order (MLB clubs 0–29 first, then minor-league clubs; 120 teams have games). Row = team × 255 + day, where `day` counts from March 25 like `SEASONDATE`. Empty rows are off days.
- **`PACKED_DATA`:**
  - bits 0–7 = opponent team index
  - bits 8–15 = this team's game number (1–162)
  - bit 23 = home (values look like `0xC0nnoo` for home, `0x40nnoo` for away)
- **`DATE_TIME`** = start time as hhmm (1840 = 6:40 PM).
- **Checks:** every MLB club has games 1–162 and every game's mirror (same day and time, home flipped) exists on the opponent's row (4,860 of 4,860). The White Sox's games 24–30 land on days 28–34, as the game's own upcoming list says. Game *k* lines up with row *k* of `D_SEASON_SCORES`, so past games get their opponent.

### Per-game pitchers, series lines, All-Star Game, last season's awards

- **`D_SEASON_INFO` → `D_SEAS_PIT_INFO`** (162 rows per team): `WIN`, `LOSS`, `SAVE` = **`D_PLR_PROFILE` row numbers** (65535 = none). VERIFIED: Burke W / Pfaadt L in the White Sox's 3-2 win at Arizona.
- **`*_SERIES` stats** (`AT_BATS_SERIES`, `HITS_SERIES`, `HR_SERIES`, `RBI_SERIES`, `P_IP_SERIES`, `P_SO_SRS` …) = the current or just-finished series. VERIFIED (Soto 6-for-13, 2 HR vs CIN).
- **`D_SCHED_CONST`:** `ALLSTAR_MONTH` (**0-based**) / `ALLSTAR_DATE` = July 14, 2026; also the season, spring training and half-season dates. VERIFIED on the Royals Feb 20, 2026 save: `ST_START` Feb 20 (the save's own date), `ST_END` Mar 24, `SEAS_START` Mar 25 (= `SEASONDATE` 0), `SEAS_END` Sep 27. Exported as `season.calendar`.

### Postseason (Dodgers Oct 3, 2026 save)

- **`MODESTATE` 7 = postseason.** `SEASONDATE` keeps counting from Opening Day (192 = Oct 3). Exported as `season.phase = "postseason"`.
- **`D_PLAYOFF_ROUND`** (VERIFIED):
  - **Rows:** 0–3 are the Wild Card Series, 4–7 the Division Series, 8–9 the LCS and 10 the World Series. LCS and WS row order is LIKELY, since those rows were still empty. Rows 11 and up are the minor-league playoffs (club ids).
  - **Fields:** `TEAM1` is the higher seed and home team. `WINNER` is a team index, or 255 while undecided; both teams read 255 until the round is set. `DATA1`/`DATA2` are UNKNOWN.
  - **Children of each row:** `D_PLAYOFF_GAME` (7 rows: `SCORE1/2`, `HITS1/2`, `ERRORS1/2`; unplayed games are all zero) and `D_SEAS_PIT_INFO` (W/L/S pitchers per game).
  - **Checks:** the Wild Card results matched the winners (Mets over Diamondbacks 1–0 and 8–3; Phillies over Braves 3–5, 9–1, 6–3).
- **Stats in the postseason** (VERIFIED):
  - The "this season" stats copy [1] holds playoff games only, and copy [0] still holds last season.
  - The regular season survives only in `D_CAREER_STATS` (Judge 2026: 144 G, 548 AB).
  - The exporter rebuilds `stats.season` from the career row (no splits) and puts the playoff line in `stats.post`.
- `D_SCHED_INFO` is empty in the postseason.

### Spring training (Royals Feb 20 and Mar 13, 2026 saves; Mets Feb 20)

- **`D_GAME_OPTIONS.MODESTATE`: 2 = spring training, 4 = regular season.** VERIFIED on 8 saves (3 spring, 5 in season). Exported as `season.phase`. `TIME_OF_YEAR` reads 3 in both.
- **`SEASONDATE` counts days from the start of camp during spring** (Royals Mar 13 = 21 = Feb 20 + 21), and from Opening Day in the season. `D_GAMEINFO.UPCMG_GM_DATES` uses the same base.
- **Spring games live in the current-season tables:** the "this season" stats copy [1] (996 hitters and 453 pitchers with lines on Mar 13) and `D_SEASON_RECORD` / `D_SEASON_SCORES` (Royals 12-8 after 20 games). `D_SCHED_INFO` / `D_UPCOMING_PI` list the next spring games, numbered after the spring games played (21, 22, ...).
- **`D_SCHEDULE_DATA` holds the regular-season schedule** during spring (all 162 games, from Opening Day).
- Clubhouse doesn't record spring saves in the franchise history or the stat snapshots.
- **Every MLB club holds exactly 40 players** (all 30 clubs), against 26–28 in season. This is the 40-man roster in big-league camp (LIKELY). The other organization players sit on their minor-league clubs.
- **`D_ROSTER_HLPR` is still not the 40-man roster:** 8–14 players on each club aren't on its list.
- **`D_ALL_STAR_INFO`:**
  - Row 0 = the All-Star Game: `HOST` 18 = Philadelphia, matching the real 2026 host; `HOME`/`AWAY` 31/30 = the NL/AL All-Star clubs; scores, hits and W/L/S pitchers once played (65535 before).
  - Row 1 = the Futures Game.
- **No All-Star fan votes are stored anywhere** (no field in any table). The game must compute them on its ballot screen.
- **`D_AWARD_STRUCT`** (in `D_AWARD_INFO` / `D_AWARD_WINNERS`, `HISTORICAL_REC` = 1) = **last season's award winners**: Judge MVP, Skubal Cy Young, Chapman, Kurtz Rookie of the Year, then Gold Gloves by `POS_INDEX` (3 = C Dingler, 4 = 1B France, 5 = 2B Semien, 6 = 3B Garcia, 7 = SS Witt). LIKELY; not used yet, useful for the Almanac.
- **`D_INBOX_MESSAGE`:** the inbox, empty in these saves.
- Career totals are in `D_CAREER_STATS` (93,380 rows): **UNKNOWN layout**, but this is the key to the Almanac.

### Standings and game log: `D_SEASON_INFO` (95 rows; rows 0–29 = MLB teams)

Each row's children:

| Child | Contents | Status |
|---|---|---|
| `D_SEASON_RECORD` (2 rows) | Row 0 = this season: `WINS`, `GAMES`, home, division, one-run, extra-inning and day splits, `LAST_10` (1 = W, 0 = L, 255 = none) and `STREAK` | VERIFIED |
| `D_SEASON_SCORES` (162 rows) | Each game's runs and hits for both teams. **The opponent isn't stored here**; it's probably in `D_SCHEDULE_DATA` (upcoming opponents are in `D_SCHED_INFO`, see above) | |
| `D_SEAS_PIT_INFO` (162 rows) | Winning, losing and saving pitcher ids per game | |

## Not yet mapped

All of these use the same format, so mapping them is mostly naming work:

- **Schedule:** `D_SCHEDULE`, `D_SCHEDULE_DATA`, `D_SCHED_CONST`
- **Playoffs:** `D_PLAYOFFS`, `D_PLAYOFF_ROUND`, `D_PLAYOFF_GAME`
- **Inbox and news:** `D_INBOX`, `D_INBOX_MESSAGE` (headline, text), `D_SEASON_NEWS`
- **Draft (partly mapped):**
  - `D_AMATUER_PLAYER` (sic, 540 rows): each row has its own child `D_PLR_PROFILE` / `D_PLAYER_ATTS` / `D_PLYR_CONTRACT` / `D_PLAYER_APP` (1 row each) with the prospect's name and real ratings. VERIFIED.
  - `DRAFT_RANK`: 0-based, 65535 = unranked; 200 are ranked. VERIFIED.
  - `BONUS_DEMAND`: dollars, about $10.6M for No. 1. LIKELY.
  - `PLAYER_NUM` does NOT index the league player table.
  - **UNKNOWN:** `CLASS` (0–6), `REGION` (0–3), `PRESTIGE`, and the 30-entry per-team `SCOUTED_VALUE` / `SCOUTED_CERT` / `INTEREST_LEVEL` / `PERCEIVED_OFFSET` (signed) / `PERCEIVED_RANGE`.
  - `D_DRAFT_DATA.DRAFT_ORDER`: 150 team indexes pick by pick (144 valid, 255 = none); White Sox = No. 1 in this save. LIKELY.
  - `D_DRAFT_PICKS` (200 rows): empty before the draft, probably filled with selections after it.
  - `D_SCOUT`, `D_SCOUT_INFO`: still unmapped.
- **Transactions:** `D_FREE_AGENTS`, `D_TRADING_BLOCK`, `D_TRADEHISTORY`, `D_TRANSACTION`, `D_WAIVERDATA`
- **History:** `D_TEAM_HISTORY`, `D_HOF_PLAYER`, `D_AWARD_WINNERS`, `D_MLB_RECORDS`, `D_ALL_STAR_INFO`
- **Staff and GM:** `D_COACH_STAFF`, `D_COACH_PROF`, `D_GM_GOALS`, `D_GM_HISTORY`
- **Organization:** `D_AFFILIATIONS` (which minor-league club belongs to which MLB team)
- **Sim settings:** `D_AISLIDERS`

## Writing: NOT YET TESTED IN-GAME

`SaveSlot.write()` and `Database.patch()` do the following:
1. Patch fixed-size fields in the unpacked bytes.
2. Recompress with zlib.
3. Write the new SHA-256 into `SAVEINFO`.
4. Back up the previous pair first, keeping the last 5.

The in-memory round trip passes: the recompressed save decodes with the change applied, and `tests/test_edit.py` checks that a player edit changes only that player's profile row. **No edited save has been loaded in the game yet.**

**Player editor (Nov 20, 2026):** The user asked for player edits that reach the save, so `mlb26save/edit.py` patches first and last name, jersey number, position (hitter to hitter only), bats and throws. In the app it is opt-in (Settings → "Allow save edits", config `allowEdits`, off by default). The app also:
- refuses while `mlb.exe` or a Switch emulator is running;
- refuses if a newer save of the franchise exists than the one on screen;
- backs up to `%APPDATA%\Clubhouse\backups\<slot>` (last 5 kept) and logs every edit to `%APPDATA%\Clubhouse\edits.log`;
- reads the written file back before reloading.

His first real edit is the in-game write test:
1. Edit one jersey number in Clubhouse with the game closed.
2. Load that franchise in the game.
3. Confirm the change shows and the game doesn't report corruption.

If it fails, restore the backup and turn editing off again.
