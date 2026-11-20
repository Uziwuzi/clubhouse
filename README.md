# Clubhouse

**A companion app for MLB The Show 26 franchise mode.** Clubhouse reads your franchise save and puts the whole
league in one fast desktop app: standings, stats, scouting, the draft, the minors, spring training and more,
in a dark broadcast-style interface themed in your team's colors.

It works with the **Nintendo Switch version played through an emulator on Windows**. It only ever **reads** your
save; it never changes it.

[**Download the latest version**](../../releases/latest)

---

## What it does

### Your team
- **Home dashboard:** power rankings, the next series with probable starters and win chances, batting and
  pitching leaders, a league news wire built from your save, and an "around the league" ticker.
- **Team page:** record, team grades against the other 29 clubs, best lineup and batting order, rotation and bullpen.
- **Series plan:** your next series in detail, with matchups, platoon-aware lineups, how to pitch each opposing
  hitter, and bullpen rest from recent pitch counts.
- **Spring training camp:** a projected 26-man Opening Day roster, position battles, who needs a look this
  spring and what to watch, minor leaguers pushing for a job, a suggested playing-time plan, and spring stats.
- **Press room:** optional postgame press conferences with your own answers (just for fun).

### Players
- **Player cards:** ratings, abilities, every season of career stats, splits, contract and a media tab with
  generated coverage. Real MLB headshots for most players.
- **Players and stats tables:** every player in the save, sortable and filterable, plus an injury report.
- **League leaders and award races,** with Clubhouse's own projections.

### Front office
- **Trade evaluator:** whether you should buy or sell, your needs by position, targets, sell candidates and
  suggested trades built by matching trade value.
- **Contracts and free agency:** every team's payroll, arbitration status and the upcoming free-agent class with
  projected deals.
- **September call-ups.**
- **Franchise history** that keeps every season's standings and draft, even after the game overwrites them.

### Minors, draft and scouting
- **Minor leagues:** standings, leaders and stats for Triple-A and Double-A, top 100 and organization top 30
  prospects, ETAs, a projected Futures Game, and a performance watch that shows who's hot between saves.
- **Draft:** the full amateur class with your own board, a draft class page after the draft, and fog of war:
  prospect ratings stay hidden unless you scout them.
- **Scouting department:** hire scouts within a budget, send them on assignments, and read their reports.
  Scouts have strengths, biases and a discovery rating, so they can be wrong, find hidden gems or fall for a hot
  stat line.

Projections, award races, trade values, scouting reports, press conferences and media stories are Clubhouse's
own estimates and inventions, not the game's.

---

## Install

### What you need
- Windows 10 or 11.
- **Microsoft Edge WebView2 Runtime.** It's already installed on almost every Windows PC. If Clubhouse opens to a
  blank window, install it from Microsoft: <https://developer.microsoft.com/microsoft-edge/webview2/>
- MLB The Show 26 (Switch) franchise saves from your emulator.

### Steps
1. Go to [**Releases**](../../releases/latest) and download `Clubhouse-<version>.zip`.
2. *(Optional)* Check the download. In PowerShell, in the folder where you saved it:
   ```
   Get-FileHash .\Clubhouse-<version>.zip -Algorithm SHA256
   ```
   The result should match the `.sha256` file on the release page.
3. Right-click the zip → **Extract All…**, and extract it somewhere you'll keep it, for example
   `C:\Games\Clubhouse` or your Documents folder. Keep the whole folder together: `Clubhouse.exe` needs the
   `_internal` folder next to it.
4. Double-click **Clubhouse.exe**. If Windows SmartScreen says it "protected your PC", click **More info → Run
   anyway**; the app isn't code-signed.
5. The first time, Clubhouse asks for your save folder. Pick the folder where your emulator keeps MLB The Show 26
   saves: the one that holds your `FRAN…` save folders, or the profile folder above it. It usually looks like
   `<emulator>\…\profile\save\<long id>\`.
6. That's it. Leave Clubhouse open while you play. When you save in the game, it asks whether to load the new save
   (or loads it automatically if you turn that on in Settings).

If you have several franchises in the same profile, switch between them from the season menu in the top bar.

### Updating
From version 1.8.0 on, Clubhouse updates itself. When a new version is out, a banner appears with **What's
new**, **Update now** and **Later**. Updates are checked against their published SHA-256, the previous version is
kept as a backup (`Clubhouse.old`), and your settings, scouting department and franchise history are never
touched. You can check manually or turn automatic checks off in **Settings → Updates**.

### Uninstalling
Delete the Clubhouse folder. To remove its settings and history too, delete `%APPDATA%\Clubhouse`.

---

## Your data

- Clubhouse never writes to your save files.
- Its own data (settings, scouting, franchise history, stat snapshots) lives in `%APPDATA%\Clubhouse`.
- The only internet access is the update check (GitHub Releases) and downloading an update you ask for.

---

## Building from source

```
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python app\clubhouse.py --save "<a copy of a save folder>"
```

Python 3.13 is tested. Team logos and player headshots aren't in this repository; they ship inside the release
zips. `app/import_logos.py` and `app/fetch_headshots.py` build them locally. `packaging\release.ps1 -Version x.y.z`
builds, zips and publishes a release.

The save format, with every field tagged VERIFIED, LIKELY or UNKNOWN, is documented in
[docs/SAVE_FORMAT.md](docs/SAVE_FORMAT.md).

---

Not affiliated with MLB, the MLBPA or Sony Interactive Entertainment. Team names, logos and player headshots
belong to their owners and are included for personal, non-commercial use.
