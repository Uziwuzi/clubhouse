"""Download MLB headshots for the players in one or more saves into app/ui/heads/ and write a manifest.

Run:  .venv\\Scripts\\python.exe app\\fetch_headshots.py <league.json or save folder> [...]

Players are matched to MLB's public person ids by name (accents, punctuation and Jr./II stripped), with the
birth year (save season minus age) and pitcher/hitter used to break ties. The UI repeats the same match at
runtime against heads/manifest.json, so any save with these players gets their pictures. Images are the
transparent "silo" cutouts, resized to 200 px wide WebP. Players without a match keep the silhouette.
Already-downloaded images are skipped, so re-running only fetches new players.
"""
import io, json, re, sys, time, unicodedata, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
DST = Path(__file__).resolve().parent / "ui" / "heads"
API = "https://statsapi.mlb.com/api/v1/sports/{sport}/players?season={season}"
IMG = "https://img.mlbstatic.com/mlb-photos/image/upload/w_240,q_auto:good/v1/people/{id}/headshot/silo/current"
UA = {"User-Agent": "Clubhouse-headshots/1.0"}
SPORTS = (1, 11, 12, 13, 14, 16)        # MLB, AAA, AA, High-A, Single-A, Rookie
SEASONS = (2026, 2025, 2024, 2023, 2022)
SUFFIX = re.compile(r"\b(jr|sr|ii|iii|iv|v)\b")


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[.'`]", "", s).replace("-", " ")
    s = SUFFIX.sub("", s)
    return re.sub(r"\s+", "", s)   # spaces dropped: "WoodsRichardson" = "Woods-Richardson"


def get_json(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return json.load(r)


def mlb_people():
    people = {}
    for season in SEASONS:
        for sport in SPORTS:
            try:
                rows = get_json(API.format(sport=sport, season=season)).get("people", [])
            except Exception as e:  # noqa: BLE001
                print(f"  skip sport {sport} {season}: {e}")
                continue
            for p in rows:
                if p["id"] in people:
                    continue
                pos = (p.get("primaryPosition") or {}).get("abbreviation", "")
                people[p["id"]] = {
                    "i": p["id"],
                    "names": {norm(f"{p.get(f) or ''} {p.get('lastName') or ''}") for f in ("firstName", "useName")}
                             | {norm(p.get("fullName")), norm(p.get("nameFirstLast"))},
                    "b": int((p.get("birthDate") or "0")[:4] or 0),
                    "p": pos == "P",
                }
            print(f"  {season} sport {sport}: {len(rows)} (total {len(people)})")
            time.sleep(0.2)
    return people


def load_league(arg):
    path = Path(arg)
    if path.is_dir():
        sys.path.insert(0, str(ROOT / "decoder"))
        from mlb26save import open_save  # noqa: PLC0415
        return open_save(str(path), None).export()
    return json.loads(path.read_text(encoding="utf-8"))


def match(people, players, season):
    by_name = {}
    for m in people.values():
        for n in m["names"]:
            if n:
                by_name.setdefault(n, []).append(m)
    found = {}
    for pl in players:
        cands = by_name.get(norm(f"{pl['first']} {pl['last']}"), [])
        if not cands:
            continue
        born = season - pl["age"] if pl.get("age") else None
        pit = pl.get("pos") == "P"

        def score(m):
            d = abs(m["b"] - born) if born and m["b"] else 1
            return (d > 2, m["p"] != pit, d)
        best = min(cands, key=score)
        if born and best["b"] and abs(best["b"] - born) > 2:
            continue
        found[best["i"]] = best
    return found


def fetch(m):
    out = DST / f"{m['i']}.webp"
    if out.exists():
        return "have"
    try:
        with urllib.request.urlopen(urllib.request.Request(IMG.format(id=m["i"]), headers=UA), timeout=60) as r:
            raw = r.read()
    except urllib.error.HTTPError as e:
        return f"http {e.code}"
    except Exception as e:  # noqa: BLE001
        return f"err {e}"
    im = Image.open(io.BytesIO(raw)).convert("RGBA")
    if im.getextrema()[3][1] == 0:
        return "blank"
    im.thumbnail((200, 200), Image.LANCZOS)
    im.save(out, "WEBP", quality=82, method=6)
    return "ok"


def main(args):
    if not args:
        print(__doc__)
        return 1
    DST.mkdir(parents=True, exist_ok=True)
    print("Loading MLB player lists...")
    people = mlb_people()
    want = {}
    for a in args:
        lg = load_league(a)
        season = int(lg.get("season", {}).get("year") or 2026)
        players = [p for p in lg["players"]] + [p for p in lg.get("prospects", [])]
        got = match(people, players, season)
        print(f"{a}: matched {len(got)} of {len(players)}")
        want.update(got)
    print(f"Downloading {len(want)} headshots...")
    with ThreadPoolExecutor(6) as ex:
        res = list(ex.map(fetch, want.values()))
    tally = {}
    for r in res:
        tally[r.split(" ")[0]] = tally.get(r.split(" ")[0], 0) + 1
    print("  ", tally)
    # manifest: every person whose picture we have, so the UI can match any save at runtime
    old = {}
    mf = DST / "manifest.json"
    if mf.exists():
        old = {e["i"]: e for e in json.loads(mf.read_text(encoding="utf-8"))}
    for m in want.values():
        if (DST / f"{m['i']}.webp").exists():
            old[m["i"]] = {"i": m["i"], "n": sorted(n for n in m["names"] if n), "b": m["b"], "p": int(m["p"])}
    mf.write_text(json.dumps(sorted(old.values(), key=lambda e: e["i"]), separators=(",", ":")), encoding="utf-8")
    size = sum(f.stat().st_size for f in DST.glob("*.webp"))
    print(f"Manifest: {len(old)} players, {size / 1e6:.1f} MB of images")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
