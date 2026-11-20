"""Builds app/ui/agm/ (portraits + agms.json) from app/agm_roster.json.

Run:  .venv\\Scripts\\python.exe app\\fetch_agm_portraits.py

Portrait sources, in order, and only these:
  1. MLB's official headshot, when the executive played in the majors (matched by exact name with an MLB debut).
  2. The lead image of his English Wikipedia article, only when that image is freely licensed (pilicense=free) and
     the article's intro is about baseball. The author and license are recorded for credit.
Otherwise there's no portrait and the app draws a monogram in team colors; the user can pick a photo in the app.
"""
import io, json, re, sys, urllib.parse, urllib.request
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
SRC = HERE / "agm_roster.json"
DST = HERE / "ui" / "agm"
UA = {"User-Agent": "Clubhouse/1.8 (personal companion app; portraits for team staff pages)"}


def get(url, raw=False):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
        data = r.read()
    return data if raw else json.loads(data)


def mlb_headshot(name):
    q = urllib.parse.quote(name)
    try:
        people = get(f"https://statsapi.mlb.com/api/v1/people/search?names={q}").get("people", [])
    except Exception:
        return None
    hits = [p for p in people if p.get("fullName", "").lower() == name.lower() and p.get("mlbDebutDate")]
    if len(hits) != 1:
        return None
    pid = hits[0]["id"]
    try:
        raw = get(f"https://img.mlbstatic.com/mlb-photos/image/upload/w_360,q_auto:good/v1/people/{pid}/headshot/silo/current", raw=True)
    except Exception:
        return None
    return raw, {"source": "MLB headshot (from his playing career)", "mlbam": pid}


def wiki_portrait(name):
    q = urllib.parse.quote(name)
    try:
        pages = get("https://en.wikipedia.org/w/api.php?action=query&format=json&redirects=1&prop=pageimages|extracts"
                    f"&exintro=1&explaintext=1&piprop=original|name&pilicense=free&titles={q}")["query"]["pages"]
    except Exception:
        return None
    page = next(iter(pages.values()))
    intro = (page.get("extract") or "").lower()
    if "baseball" not in intro or "original" not in page:
        return None
    fname = page.get("pageimage")
    meta = {}
    try:
        info = get("https://commons.wikimedia.org/w/api.php?action=query&format=json&prop=imageinfo&iiprop=extmetadata"
                   f"&titles=File:{urllib.parse.quote(fname)}")["query"]["pages"]
        em = next(iter(info.values()))["imageinfo"][0]["extmetadata"]
        meta = {"author": re.sub("<[^>]+>", "", em.get("Artist", {}).get("value", "")).strip(),
                "license": em.get("LicenseShortName", {}).get("value", "")}
    except Exception:
        return None   # no license info, no portrait
    if not meta.get("license"):
        return None
    try:
        raw = get(page["original"]["source"], raw=True)
    except Exception:
        return None
    return raw, {"source": "Wikimedia Commons", "file": fname, "page": page.get("title"), **meta}


def save(raw, path):
    im = Image.open(io.BytesIO(raw)).convert("RGBA")
    w, h = im.size
    if h > w * 1.25:   # tall photo: keep the top (head and shoulders)
        im = im.crop((0, 0, w, int(w * 1.25)))
    im.thumbnail((320, 400), Image.LANCZOS)
    im.save(path, "WEBP", quality=85)


def main():
    roster = {k: v for k, v in json.loads(SRC.read_text(encoding="utf-8")).items() if not k.startswith("_")}
    DST.mkdir(parents=True, exist_ok=True)
    out = {}
    for abbr, a in roster.items():
        entry = dict(a)
        got = mlb_headshot(a["name"]) or wiki_portrait(a["name"])
        if got:
            raw, meta = got
            save(raw, DST / f"{abbr}.webp")
            entry.update(portrait=f"agm/{abbr}.webp", credit=meta)
        print(f"{abbr:4} {a['name']:20} {'-> ' + got[1]['source'] if got else 'no free portrait (monogram)'}")
        out[abbr] = entry
    (DST / "agms.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print("wrote", DST / "agms.json")


if __name__ == "__main__":
    sys.exit(main())
