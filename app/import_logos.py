"""Copy team logos from `mlb logos/` into app/ui/teams/ (trimmed, max 256 px) and write a manifest.

Run:  .venv\\Scripts\\python.exe app\\import_logos.py

For each team:
  <ABBR>.png       primary logo (lists, banners)
  <ABBR>-mark.png  compact alternate mark (small spots, chips); falls back to the primary
The manifest records whether a logo is dark (needs a light backing on the dark UI) and whether it
already has its own solid background (square cap logos).
Cleveland's folder is from the Indians era: only the block C is used, never the retired Chief Wahoo art.
"""
import json
from pathlib import Path
from PIL import Image, ImageStat

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "mlb logos"
DST = Path(__file__).resolve().parent / "ui" / "teams"

# abbr: (folder, primary file stem, mark file stem)
PICK = {
    "AZ":  ("arizona-diamondbacks-logo", "arizona-diamondbacks-logo-transparent", "arizona-diamondbacks-snake-logo-transparent"),
    "ATL": ("atlanta-braves-logo", "atlanta-braves-logo-transparent", "atlanta-braves-baseball-logo"),
    "BAL": ("baltimore-orioles-logo", "baltimore-orioles-logo-transparent", "baltimore-orioles-bird-logo"),
    "BOS": ("boston-red-sox-logo", "boston-red-sox-logo-transparent", "boston-red-sox-b-logo-cap-transparent"),
    "CHC": ("chicago-cubs-logo", "chicago-cubs-logo-transparent", "chicago-cubs-logo-transparent"),
    "CWS": ("chicago-white-sox-logo", "chicago-white-sox-logo-transparent", "chicago-white-sox-logo-transparent"),
    "CIN": ("cincinnati-reds-logo", "cincinnati-reds-logo-transparent", "cincinnati-reds-logo-transparent"),
    "CLE": ("cleveland-indians-logo", "cleveland-indians-c-logo-transparent", "cleveland-indians-c-logo-transparent"),
    "COL": ("colorado-rockies-logo", "colorado-rockies-logo-transparent", "colorado-rockies-logo-transparent"),
    "DET": ("detroit-tigers-logo", "detroit-tigers-logo-transparent", "detroit-tigers-tiger-logo"),
    "HOU": ("houston-astros-logo", "houston-astros-logo-transparent", "houston-astros-star-logo"),
    "KC":  ("kansas-city-royals-logo", "kansas-city-royals-logo-transparent", "kansas-city-royals-crown-logo"),
    "LAA": ("los-angeles-angels-logo", "los-angeles-angels-logo-transparent", "los-angeles-angels-logo-transparent"),
    "LAD": ("los-angeles-dodgers-logo", "los-angeles-dodgers-logo-transparent", "los-angeles-dodgers-cap-logo"),
    "MIA": ("miami-marlins-logo", "miami-marlins-logo-transparent", "miami-marlins-logo-transparent"),
    "MIL": ("milwaukee-brewers-logo", "milwaukee-brewers-logo-transparent", "milwaukee-brewers-glove-logo"),
    "MIN": ("minnesota-twins-logo", "minnesota-twins-logo-transparent", "minnesota-twins-hat-logo"),
    "NYM": ("new-york-mets-logo", "new-york-mets-logo-transparent", "new-york-mets-hat-logo"),
    "NYY": ("new-york-yankees-logo", "new-york-yankees-logo-transparent", "new-york-yankees-ny-logo"),
    "ATH": ("oakland-athletics-logo", "oakland-athletics-logo-transparent", "oakland-athletics-logo-elephant-head"),
    "PHI": ("philadelphia-phillies-logo", "philadelphia-phillies-logo-transparent", "philadelphia-phillies-p-logo"),
    "PIT": ("pittsburgh-pirates-logo", "pittsburgh-pirates-logo-transparent", "pittsburgh-pirates-logo-transparent"),
    "SD":  ("san-diego-padres-logo", "san-diego-padres-logo-circle", "san-diego-padres-logo-transparent"),
    "SF":  ("san-francisco-giants-logo", "san-francisco-giants-logo-transparent", "san-francisco-giants-logo-cap"),
    "SEA": ("seattle-mariners-logo", "seattle-mariners-logo-transparent", "seattle-mariners-s-logo"),
    "STL": ("st-louis-cardinals-logo", "st-louis-cardinals-logo-transparent", "st-louis-cardinals-logo-transparent"),
    "TB":  ("tampa-bay-rays-logo", "tampa-bay-rays-logo-transparent", "tampa-bay-rays-logo-transparent"),
    "TEX": ("texas-rangers-logo", "texas-rangers-logo-transparent", "texas-rangers-t-logo"),
    "TOR": ("toronto-blue-jays-logo", "toronto-blue-jays-logo-transparent", "toronto-blue-jays-logo-new"),
    "WSH": ("washington-nationals-logo", "washington-nationals-logo-transparent", "washington-nationals-logo-text"),
}


def prep(path: Path) -> tuple[Image.Image, dict]:
    im = Image.open(path).convert("RGBA")
    a = im.getchannel("A")
    solid = a.getextrema()[0] == 255             # no transparency: a square cap logo with its own background
    bbox = a.point(lambda v: 255 if v > 8 else 0).getbbox()
    if bbox and not solid:
        im = im.crop(bbox)
    im.thumbnail((256, 256), Image.LANCZOS)
    # luminance of visible pixels -> is it too dark for the dark UI?
    mask = im.getchannel("A").point(lambda v: 255 if v > 128 else 0)
    lum = ImageStat.Stat(im.convert("L"), mask=mask).mean[0] / 255 if mask.getbbox() else 1.0
    return im, {"dark": (not solid) and lum < 0.22, "solid": solid, "wide": im.width > im.height * 1.6}


def main():
    DST.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for abbr, (folder, logo, mark) in PICK.items():
        entry = {}
        for kind, stem in (("logo", logo), ("mark", mark)):
            src = SRC / folder / f"{stem}.png"
            if not src.exists():
                print("missing", src); continue
            im, info = prep(src)
            name = f"{abbr}.png" if kind == "logo" else f"{abbr}-mark.png"
            im.save(DST / name, optimize=True)
            entry[kind] = f"teams/{name}"
            entry[kind + "Info"] = info
        manifest[abbr] = entry
    (DST / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(f"wrote {len(manifest)} teams to {DST}")
    print("dark logos:", [a for a, e in manifest.items() if e.get("logoInfo", {}).get("dark")],
          "| dark marks:", [a for a, e in manifest.items() if e.get("markInfo", {}).get("dark")],
          "| solid marks:", [a for a, e in manifest.items() if e.get("markInfo", {}).get("solid")])


if __name__ == "__main__":
    main()
