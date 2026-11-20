"""Command line:  python -m mlb26save <save folder | SAVE_000> [command]

Commands:
    info     slot label, date, checksum, user team        (default)
    export   write league JSON  (-o league.json)
    schema   print every table and field
    roster   print a team's roster  (--team CWS)
"""
import argparse
import json
import sys

from . import open_save


def main(argv=None):
    ap = argparse.ArgumentParser(prog="mlb26save")
    ap.add_argument("path", help="profile save folder or SAVE_xxx file")
    ap.add_argument("command", nargs="?", default="info", choices=["info", "export", "schema", "roster"])
    ap.add_argument("--info", help="SAVEINFO path if not next to the save")
    ap.add_argument("-o", "--out", default="league.json")
    ap.add_argument("--team", default=None, help="team abbreviation for `roster`")
    a = ap.parse_args(argv)

    save = open_save(a.path, a.info)
    if a.command == "schema":
        print(save.db.schema_text())
        return
    data = save.export()
    if a.command == "export":
        with open(a.out, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))
        print(f"wrote {a.out}: {len(data['teams'])} teams, {len(data['players'])} players")
        return
    teams = {t["abbr"]: t for t in data["teams"]}
    user = data["teams"][data["season"]["userTeam"]]
    if a.command == "roster":
        t = teams.get((a.team or user["abbr"]).upper())
        if not t:
            sys.exit(f"unknown team {a.team}")
        P = {p["id"]: p for p in data["players"]}
        for pid in t["roster"]:
            p = P[pid]
            print(f"{p['role']:<3} {p['first']} {p['last']:<20} OVR {p['ovr']:>2}  POT {p['pot']:>2}")
        return
    s, r = data["slot"], user["record"]
    print(f"{s['label']}  |  checksum {'OK' if s['checksumOk'] else 'MISMATCH'}")
    print(f"Season {data['season']['year']}, day {data['season']['day']} ({data['season']['date']})")
    print(f"Your team: {user['city']} {user['name']}  {r['w']}-{r['l']}  RS {r['rs']} RA {r['ra']}")


if __name__ == "__main__":
    main()
