# Clubhouse

A Windows companion app for **MLB The Show 26 franchise mode** (Switch version, played through an emulator).
It reads your franchise save and puts the whole league in one fast app: standings, stats, award races, team
grades, series plans, the draft and your draft class, free agency, a trade evaluator, the minor leagues, a
scouting department, spring training camp, player cards with career history, and more.

Clubhouse only **reads** your save. It never changes it.

## Download

Get the latest `Clubhouse-<version>.zip` from [Releases](../../releases/latest), unzip it anywhere, and run
`Clubhouse.exe`. The first time, pick the folder where your emulator keeps MLB The Show 26 saves (the folder
with your `FRAN…` save folders, or the profile folder above them).

From 1.8.0 on, Clubhouse checks for new versions when it starts and offers to update itself (Settings → Updates).
Downloads are verified against the SHA-256 published with each release, and your settings stay put.

Needs Windows 10 or 11 with Microsoft Edge WebView2 (already on almost every PC).

## Building from source

```
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python app\clubhouse.py --save "<a copy of a save folder>"
```

Team logos and player headshots aren't in this repository; they ship inside the release zips.
`app/import_logos.py` and `app/fetch_headshots.py` build them locally. `packaging\release.ps1 -Version x.y.z`
builds, zips and publishes a release.

The save format, with every field tagged VERIFIED, LIKELY or UNKNOWN, is documented in
[docs/SAVE_FORMAT.md](docs/SAVE_FORMAT.md).

## Notes

- Projections, award races, trade values, scouting reports, press conferences and media stories are
  Clubhouse's own estimates and inventions, not the game's.
- Not affiliated with MLB, the MLBPA or Sony Interactive Entertainment. Team names, logos and player headshots
  belong to their owners and are included for personal, non-commercial use.
