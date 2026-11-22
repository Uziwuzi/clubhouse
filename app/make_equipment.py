r"""Build app/ui/data/equipment.json (the Road to the Show gear catalog Clubhouse ships) from the game's
FRONTEND/EQUIPMENT/MLBEQUIPMENT.JSON. Only the five mapped slots (see decoder/mlb26save/rtts.py), only enabled items
with real names. Kept out of the public repo like the logos; it ships inside the release zip.
Run: .venv\Scripts\python.exe app\make_equipment.py "E:\MLB 26 FINAL\game\romfs\FRONTEND\EQUIPMENT\MLBEQUIPMENT.JSON"
"""
import collections
import html
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

TYPES = {0: "bat", 1: "batgloves", 2: "cleats", 3: "glove", 9: "elbow", 8: "grip", 7: "glasses", 13: "sleeves",
         14: "wrist", 12: "shin", 10: "cmask", 15: "cshin", 11: "chest"}
src = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
mk = {m["id"]: m["name"] for m in src["makers"]}
items = []
for x in src["eqlist"]:
    slot = TYPES.get(x["type"])
    name = (x["name"] or "").strip()
    if not slot or not x["enb"] or not name or name.lower() == "tbd":
        continue
    brand = mk.get(x["brand"], "")
    if brand == "zGeneric":
        brand = "Generic"
    elif brand == "TheShow":                 # ": KGriffeyJ C271" = a legend's signature bat
        brand, name = "Legends", name.lstrip(": ").strip()
    elif brand == "Vintage/NLB":
        brand, name = "Vintage", (name.capitalize() if name.islower() else name)   # "fifties" -> "Vintage Fifties"
        if name.startswith("Vintage"):
            name = name[7:].strip() or name   # "Vintage1" -> "Vintage 1"
    if brand and name.lower().startswith(brand.lower() + " "):
        name = name[len(brand) + 1:]         # "Jordan Jordan Fly Elite" -> "Jordan Fly Elite"
    items.append({"slot": slot, "s": x["style"], "b": brand, "n": name, "tier": x["tier"]})
items.sort(key=lambda i: (i["slot"], i["b"], i["n"]))
out = Path(__file__).parent / "ui" / "data" / "equipment.json"
out.write_text(json.dumps({"items": items}, separators=(",", ":")), encoding="utf-8")
print(f"{len(items)} items -> {out}")

# --- pictures, full names and rarity from The Show's public item database (mlb26.theshow.com/apis/items.json),
# matched by brand and model (legend bats by last name and model code). Like the MLB headshots, the pictures go to
# app/ui/gear/ and ship only inside the release zip. Unmatched items (novelty and vintage gear) show a slot icon.
SLOT={'Bat':'bat','Batting Gloves':'batgloves','Cleats':'cleats','Fielding Glove':'glove','Elbow Guard':'elbow','Bat Grips':'grip','Eyewear':'glasses',
      'Compression Sleeve':'sleeves','Wrist Guard':'wrist','Leg Guards':'shin','Catcher Masks':'cmask','Catcher Leg Guards':'cshin','Chest Protector':'chest'}
def clean(s): s=html.unescape(s or ''); return re.sub(r'[®™]','',s)
def toks(s): return [t for t in re.findall(r'[a-z0-9]+',clean(s).lower().replace("'",''))]
def joined(s): return ''.join(toks(s))
def match(cat, api):
    cands=collections.defaultdict(list)
    for a in api:
        sl=SLOT.get(a['slot'])
        if sl: cands[sl].append(a)
    res={}; amb=[]; miss=[]; score={}
    for c in cat:
        if c['b']=='Generic': continue
        scored=[]
        for a in cands[c['slot']]:
            ab=joined(a['brand']); an=joined(a['name']); at=set(toks(a['name']))
            if c['b']=='Legends':
                name,code=c['n'].rsplit(' ',1)
                last=re.sub(r'J$','',name[1:])            # "KGriffeyJ" -> "Griffey", "BONeil" -> "ONeil"
                if code.lower() in at and last.lower().replace("'",'') in an: scored.append((100,a))
                continue
            if joined(c['b'])[:4] not in ab: continue
            ct=toks(c['n']); cj=joined(c['n'])
            if cj==an: scored.append((1000,a)); continue
            shared=sum(1 for t in set(ct) if t in at or t in an)
            if not shared: continue
            sc=shared*10-len(at-set(ct)) + (50 if cj in an or an in cj else 0)
            scored.append((sc,a))
        scored.sort(key=lambda x:-x[0])
        if scored and (len(scored)==1 or scored[0][0]>scored[1][0]): res[(c['slot'],c['s'])]=scored[0][1]; score[(c['slot'],c['s'])]=scored[0][0]
        elif scored: amb.append((c,[(s,clean(a['name'])) for s,a in scored[:3]]))
        else: miss.append(c)
    best={}
    for k,a in res.items():
        u=a['uuid']
        if u not in best or score[k]>score[best[u]]: best[u]=k
    res={k:a for k,a in res.items() if best[a['uuid']]==k}   # one website item = one catalog item
    return res,amb,miss

def fetch_api():
    out = []
    for p in range(1, 60):
        req = urllib.request.Request(f"https://mlb26.theshow.com/apis/items.json?type=equipment&page={p}", headers={"User-Agent": "Clubhouse"})
        d = json.load(urllib.request.urlopen(req, timeout=30))
        out += d["items"]
        if p >= d["total_pages"]:
            return out
        time.sleep(0.3)
    return out


if "--images" in sys.argv:
    api = fetch_api()
    res, amb, miss = match(items, api)
    gear = Path(__file__).parent / "ui" / "gear"
    gear.mkdir(exist_ok=True)
    got = 0
    for it in items:
        a = res.get((it["slot"], it["s"]))
        if not a:
            continue
        br, nm = clean(a["brand"]).strip(), clean(a["name"]).strip()
        it["full"] = nm if nm.lower().startswith(br.split()[0].lower()) else f"{br} {nm}"   # no "Jordan Jordan ..."
        it["r"] = a.get("rarity")
        fn = f"{it['slot']}-{it['s']}.webp"
        dest = gear / fn
        if not dest.exists():
            try:
                req = urllib.request.Request(a["img"], headers={"User-Agent": "Clubhouse"})
                dest.write_bytes(urllib.request.urlopen(req, timeout=30).read())
                from PIL import Image          # 512 px originals -> 420 px (cards and the full-size popup)
                im = Image.open(dest)
                im.thumbnail((420, 420))
                im.save(dest, "WEBP", quality=82)
                time.sleep(0.15)
            except OSError:
                continue
        it["img"] = fn
        got += 1
    # The website uses one placeholder picture (crossed bats) for several items: a picture shared by 3+ items isn't
    # the item's own, so those show Clubhouse's slot icon instead.
    import hashlib
    digest = {it["img"]: hashlib.md5((gear / it["img"]).read_bytes()).hexdigest() for it in items if it.get("img")}
    shared = {h for h, n in collections.Counter(digest.values()).items() if n >= 3}
    for it in items:
        if it.get("img") and digest[it["img"]] in shared:
            (gear / it.pop("img")).unlink(missing_ok=True)
            got -= 1
    out.write_text(json.dumps({"items": items}, separators=(",", ":")), encoding="utf-8")
    print(f"pictures for {got} items in {gear} ({len(amb)} ambiguous, {len(miss)} unmatched)")
