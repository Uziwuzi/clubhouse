"""Clubhouse desktop shell: a pywebview window over the read-only save decoder.

Run:  .venv\\Scripts\\python.exe app\\clubhouse.py [--debug]

The app only reads the save; it never writes to the save folder. Its own files (settings, stat snapshots,
franchise history) live in %APPDATA%\\Clubhouse.
"""
from __future__ import annotations

import json
import os
import sys
import threading
import time
import traceback
from pathlib import Path

import webview

HERE = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "decoder"))
import hashlib  # noqa: E402
from mlb26save.container import SaveInfo, SaveSlot, find_franchise_slots  # noqa: E402
from mlb26save.franchises import profile_root, scan  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
from updater import Updater  # noqa: E402
from version import REPO, VERSION  # noqa: E402

UPDATER = Updater()
APP_NAME = "Clubhouse"
DEFAULT_SAVE_ROOT = Path(r"E:\MLB 26 FINAL\profile\save")
CONFIG_PATH = Path(os.environ.get("APPDATA", Path.home())) / APP_NAME / "config.json"

POLL_SECONDS = 2.0
WEB_PORT = 47826   # fixed local port, so the page keeps one origin (and its local storage) between runs
# The game writes SAVE_000 first and SAVEINFO a few seconds later (17 s apart on
# one real save). Until both are written the checksum doesn't match, so wait for
# it, but give up waiting after this long and show the mismatch.
CHECKSUM_GRACE_SECONDS = 60.0


# ---- config -----------------------------------------------------------------
def load_config() -> dict:
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_config(cfg: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def _signature(slot: tuple[Path, Path]) -> tuple:
    out = []
    for p in slot:
        try:
            st = p.stat()
            out.append((str(p), st.st_mtime_ns, st.st_size))
        except OSError:
            out.append((str(p), None, None))
    return tuple(out)


def _code_signature() -> tuple:
    """Modification times of Clubhouse's own code: the page, the shell and the decoder."""
    files = [HERE / "ui" / "index.html", Path(__file__)] + sorted((ROOT / "decoder" / "mlb26save").glob("*.py"))
    out = []
    for f in files:
        try:
            out.append((f.name, f.stat().st_mtime_ns))
        except OSError:
            out.append((f.name, None))
    return tuple(out)


def restart_app():
    """Start a fresh copy of Clubhouse (same interpreter and arguments), then let this one close."""
    import subprocess
    flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    if getattr(sys, "frozen", False):   # packaged Clubhouse.exe
        cmd = [sys.executable, *sys.argv[1:]]
    else:
        cmd = [sys.executable, str(Path(__file__).resolve()), *sys.argv[1:]]
    subprocess.Popen(cmd, cwd=str(Path(sys.executable).parent if getattr(sys, "frozen", False) else ROOT), creationflags=flags, close_fds=True)


# ---- the league, loaded from the save ---------------------------------------
class League:
    """Holds the decoded save of the chosen franchise and watches the save folder.

    A profile folder can hold several franchises, and the game may put a new save of the same
    franchise into a new FRAN<hash> slot. So the app picks a franchise (by its id) and always
    reads that franchise's newest slot.
    """

    def __init__(self):
        self.lock = threading.Lock()
        self.folder: Path | None = None          # profile folder (or any folder above the slots)
        self.franchise: str | None = None        # franchise id (D_GAME_OPTIONS.UUID_STR)
        self.franchises: list[dict] = []
        self.remember = True
        self.slot: tuple[Path, Path] | None = None
        self.loaded_sig: tuple | None = None
        self.json: str | None = None
        self.error: str | None = None
        self.loading = False
        self.booting = True             # until startup() has tried the saved folder
        self.on_change = None          # callback(meta dict) after a reload
        self._stop = threading.Event()

    # -- loading
    def set_folder(self, folder: str | Path, remember: bool = True) -> dict:
        if not str(folder).strip():
            return {"ok": False, "error": "No folder given."}
        folder = profile_root(Path(str(folder).strip().strip('"'))).resolve()   # a FRAN slot widens to its profile
        fs = scan(folder) if folder.is_dir() else []
        if not fs:
            return {"ok": False, "error": f"No franchise save found in {folder}. "
                                          "Pick the folder that holds your FRAN… save folders."}
        saved = load_config().get("franchise")
        with self.lock:
            self.folder, self.franchises, self.remember = folder, fs, remember
            self.franchise = saved if any(f["id"] == saved for f in fs) else fs[0]["id"]
            self.slot, self.loaded_sig, self.json = None, None, None
        self._remember()
        return self.reload()

    def choose_franchise(self, fid: str) -> dict:
        with self.lock:
            if not any(f["id"] == fid for f in self.franchises):
                return {"ok": False, "error": "That franchise isn't in the save folder anymore."}
            self.franchise, self.loaded_sig, self.json = fid, None, None
        self._remember()
        return self.reload()

    def _remember(self):
        if self.remember and self.folder:
            cfg = load_config()
            cfg["saveFolder"], cfg["franchise"] = str(self.folder), self.franchise
            save_config(cfg)

    def _current_slot(self) -> tuple[Path, Path] | None:
        """Rescan (cheap when nothing changed) and return the chosen franchise's newest slot."""
        fs = scan(self.folder)
        self.franchises = fs
        if not fs:
            return None
        f = next((f for f in fs if f["id"] == self.franchise), None)
        if f is None:                      # the chosen franchise disappeared: fall back to the newest one
            f = fs[0]
            self.franchise = f["id"]
        return Path(f["latest"]["save"]), Path(f["latest"]["info"])

    def reload(self, wait_for_checksum_until: float | None = None, only_if_changed: bool = False) -> dict:
        with self.lock:
            if not self.folder:
                return {"ok": False, "error": "No save folder chosen yet."}
            slot = self._current_slot()
            if not slot:
                self.error = f"No franchise save found in {self.folder}."
                return {"ok": False, "error": self.error}
            sig = _signature(slot)
            if only_if_changed and sig == self.loaded_sig and self.json is not None:
                return {"ok": True, "unchanged": True, **self.meta()}
            self.slot = slot
            self.loading = True
        try:
            save = SaveSlot(*slot)
            if not save.checksum_ok and wait_for_checksum_until and time.time() < wait_for_checksum_until:
                return {"ok": False, "waiting": True}
            data = save.export()
            data["slot"]["folder"] = str(slot[0].parent)
            data["slot"]["franchise"] = self.franchise
            try:   # "since your last save" stat lines (performance watch); never fatal
                from mlb26save.snapshots import attach_recent
                # --save runs (tests, copies) keep their own snapshots so they never mix with the real ones
                attach_recent(data, CONFIG_PATH.parent / ("snapshots" if self.remember else "snapshots-copies"), self.franchise)
            except Exception:
                traceback.print_exc()
                data["recent"] = None
            try:   # franchise history: seasons, standings and drafts kept after the game overwrites them
                from mlb26save.history import update_history
                update_history(data, CONFIG_PATH.parent / ("history" if self.remember else "history-copies"), self.franchise)
            except Exception:
                traceback.print_exc()
                data["history"] = {}
            blob = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
            with self.lock:
                self.json, self.loaded_sig, self.error = blob, sig, None
            return {"ok": True, **self.meta()}
        except Exception as e:  # a half-written save fails to decompress, etc.
            traceback.print_exc()
            with self.lock:
                self.error = f"Couldn't read the save: {e}"
                self.loaded_sig = sig
            return {"ok": False, "error": self.error}
        finally:
            self.loading = False

    def meta(self) -> dict:
        return {
            "folder": str(self.folder) if self.folder else None,
            "slotFolder": str(self.slot[0].parent) if self.slot else None,
            "franchise": self.franchise,
            "franchises": [{"id": f["id"], "abbr": f["abbr"], "city": f["city"], "name": f["name"],
                            "label": f["latest"]["label"], "labelDate": f["latest"]["labelDate"],
                            "yearOffset": f["latest"].get("yearOffset", 0),
                            "savedAt": f["latest"]["savedAt"], "day": f["latest"]["day"], "year": f["latest"]["year"],
                            "saves": len(f["slots"])} for f in self.franchises],
            "loadedAt": time.time(),
        }

    # -- watching
    def watch(self):
        """Poll every franchise slot. When the folder settles after a change, reload if the chosen
        franchise has a newer save; otherwise just refresh the franchise list in the page."""
        pending, since, seen = None, 0.0, None
        code_at_start, announced = _code_signature(), False
        while not self._stop.wait(POLL_SECONDS):
            # Clubhouse's own files changed (an update): the running copy still has the old code in memory.
            if not announced and _code_signature() != code_at_start:
                announced = True
                if self.on_change:
                    self.on_change({"ok": True, "appUpdated": True, **self.meta()})
            with self.lock:
                folder = self.folder
            if not folder:
                continue
            try:
                allsig = tuple(_signature(s) for s in find_franchise_slots(folder))
            except OSError:
                continue
            if allsig == seen:
                pending = None
                continue
            if allsig != pending:          # still changing: wait until it settles
                pending, since = allsig, time.time()
                continue
            if time.time() - since < POLL_SECONDS:
                continue
            before = [(f["id"], f["latest"]["save"], f["latest"]["ts"]) for f in self.franchises]
            if not load_config().get("autoLoad", False):
                # Ask first: tell the page a newer save of this franchise is ready, but don't swap it in.
                newer = self.peek_newer()
                if newer == "waiting" and time.time() < since + CHECKSUM_GRACE_SECONDS:
                    continue
                seen, pending = allsig, None
                after = [(f["id"], f["latest"]["save"], f["latest"]["ts"]) for f in self.franchises]
                if isinstance(newer, dict) and self.on_change:
                    self.on_change({"ok": True, "newSave": newer, **self.meta()})
                elif before != after and self.on_change:
                    self.on_change({"ok": True, "franchisesOnly": True, **self.meta()})
                continue
            res = self.reload(wait_for_checksum_until=since + CHECKSUM_GRACE_SECONDS, only_if_changed=True)
            if res.get("waiting"):
                continue
            seen, pending = allsig, None
            after = [(f["id"], f["latest"]["save"], f["latest"]["ts"]) for f in self.franchises]
            if res.get("unchanged"):
                if before != after and self.on_change:
                    self.on_change({**res, "franchisesOnly": True})
                continue
            if self.on_change:
                self.on_change(res)

    def peek_newer(self):
        """A newer save of the chosen franchise that isn't loaded yet: its summary, "waiting" while it's
        still being written (checksum mismatch), or None."""
        with self.lock:
            slot = self._current_slot()
            if not slot:
                return None
            sig = _signature(slot)
            if sig == self.loaded_sig:
                return None
            try:
                info = SaveInfo.parse(slot[1].read_bytes())
                if hashlib.sha256(slot[0].read_bytes()).digest() != info.sha256:
                    return "waiting"
            except (OSError, ValueError):
                return "waiting"
            f = next((f for f in self.franchises if f["id"] == self.franchise), None)
            return {"label": info.label, "savedAt": info.saved_at.isoformat(), "slot": str(slot[0].parent),
                    "day": f["latest"]["day"] if f else None}

    def stop(self):
        self._stop.set()


# ---- what the page can call (window.pywebview.api.*) -------------------------
class Api:
    def __init__(self, league: League):
        self._league = league
        self._window = None

    def restart(self) -> dict:
        """Relaunch Clubhouse so code updates take effect (after the page's "Clubhouse was updated" prompt)."""
        try:
            restart_app()
        except Exception as e:
            return {"ok": False, "error": str(e)}
        if self._window:
            threading.Timer(0.8, self._window.destroy).start()
        return {"ok": True}

    def get_state(self) -> dict:
        lg = self._league
        cfg = load_config()
        suggestion = str(profile_root(cfg["saveFolder"])) if cfg.get("saveFolder") else (str(DEFAULT_SAVE_ROOT) if DEFAULT_SAVE_ROOT.exists() else "")
        return {"hasData": lg.json is not None, "error": lg.error,
                "loading": lg.loading or lg.booting,
                "suggestion": suggestion, **lg.meta()}

    def get_league(self) -> str | None:
        """The decoded league as a JSON string (parsed in the page)."""
        return self._league.json

    def use_folder(self, folder: str) -> dict:
        return self._league.set_folder(folder)

    def choose_folder(self) -> dict:
        start = self.get_state()["suggestion"] or str(Path.home())
        picked = self._window.create_file_dialog(webview.FileDialog.FOLDER, directory=start)
        if not picked:
            return {"ok": False, "cancelled": True}
        return self._league.set_folder(picked[0])

    def reload(self) -> dict:
        return self._league.reload()

    def choose_franchise(self, fid: str) -> dict:
        """Switch to another franchise in the save folder (remembered)."""
        return self._league.choose_franchise(fid)

    def load_latest(self) -> dict:
        """Load the newest save of the current franchise (after the page's "new save" prompt)."""
        return self._league.reload()

    def discover_in_game(self, players: list) -> dict:
        """Put prospects Clubhouse discovered on the game's draft list (SCOUTED_CERT 0 -> 5 for your club).
        The one save write Clubhouse makes: the game must be closed, the loaded save must still be the newest,
        and the save is backed up first. players = [{"row": amateur row, "name": "First Last"}]."""
        from mlb26save.discover import discover
        lg = self._league
        with lg.lock:
            slot, loaded = lg.slot, lg.loaded_sig
            fs = lg.franchises
        if not slot or lg.json is None:
            return {"ok": False, "error": "No save loaded."}
        if _signature(slot) != loaded:
            return {"ok": False, "error": "The save changed since Clubhouse loaded it. Load the new save, then try again."}
        f = next((f for f in fs if f["id"] == lg.franchise), None)
        if f and Path(f["latest"]["save"]) != slot[0]:
            return {"ok": False, "error": "There's a newer save of this franchise. Load it, then try again."}
        try:
            team = json.loads(lg.json)["season"]["userTeam"]
        except (KeyError, ValueError, TypeError):
            return {"ok": False, "error": "Couldn't tell which club you control."}
        res = discover(slot[0], slot[1], int(team), list(players or []), CONFIG_PATH.parent / "save-backups")
        if res.get("ok") and res.get("written"):
            res["reload"] = lg.reload()
        return res

    # -- scouting department: the page owns the logic; Python keeps it safe on disk, per franchise.
    #    Stored outside the save, so imports never touch it. Each write is atomic and keeps the previous copy as .bak.
    def _scout_dir(self) -> Path:
        return CONFIG_PATH.parent / ("scouting" if self._league.remember else "scouting-copies")

    def _scout_file(self) -> Path | None:
        fid = self._league.franchise
        return self._scout_dir() / f"{fid}.json" if fid else None

    def get_scouting(self) -> str | None:
        f = self._scout_file()
        for p in (f, f.with_suffix(".bak")) if f else ():
            try:
                text = p.read_text(encoding="utf-8")
                json.loads(text)
                return text
            except (OSError, ValueError):
                continue
        return None

    def save_scouting(self, blob: str) -> dict:
        f = self._scout_file()
        if not f:
            return {"ok": False, "error": "No franchise loaded."}
        try:
            json.loads(blob)
        except ValueError:
            return {"ok": False, "error": "Scouting data was malformed; nothing written."}
        f.parent.mkdir(parents=True, exist_ok=True)
        tmp = f.with_suffix(".tmp")
        tmp.write_text(blob, encoding="utf-8")
        if f.exists():
            os.replace(f, f.with_suffix(".bak"))
        os.replace(tmp, f)
        return {"ok": True}

    def _portrait_dir(self) -> Path:
        return self._scout_dir() / "portraits" / str(self._league.franchise or "none")

    @staticmethod
    def _data_url(p: Path) -> str:
        import base64
        mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}.get(p.suffix.lower(), "image/png")
        return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()

    def get_portraits(self) -> dict:
        d = self._portrait_dir()
        out = {}
        if d.is_dir():
            for p in d.iterdir():
                if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
                    try:
                        out[p.stem.replace("_", ":")] = self._data_url(p)
                    except OSError:
                        pass
        return out

    def choose_portrait(self, key: str) -> dict:
        """Pick an image for a prospect; it is copied into Clubhouse's own folder (the original is untouched)."""
        import re, shutil
        picked = self._window.create_file_dialog(webview.FileDialog.OPEN, file_types=("Images (*.png;*.jpg;*.jpeg;*.webp)",))
        if not picked:
            return {"ok": False, "cancelled": True}
        src = Path(picked[0])
        if src.stat().st_size > 4 * 1024 * 1024:
            return {"ok": False, "error": "That image is over 4 MB. Pick a smaller one."}
        safe = re.sub(r"[^0-9A-Za-z:_-]", "", key).replace(":", "_")
        d = self._portrait_dir()
        d.mkdir(parents=True, exist_ok=True)
        for old in d.glob(safe + ".*"):
            old.unlink()
        dest = d / (safe + src.suffix.lower())
        shutil.copyfile(src, dest)
        return {"ok": True, "url": self._data_url(dest)}

    def clear_portrait(self, key: str) -> dict:
        import re
        safe = re.sub(r"[^0-9A-Za-z:_-]", "", key).replace(":", "_")
        for old in self._portrait_dir().glob(safe + ".*"):
            old.unlink()
        return {"ok": True}

    # ---- assistant GM: shipped roster (app/ui/agm/agms.json) plus the user's own edits and photos ----
    @staticmethod
    def _agm_dir() -> Path:
        return CONFIG_PATH.parent / "agm"

    def get_agms(self) -> dict:
        """{abbr: {name, title, confirmed, portrait (url or data URL), credit}} with the user's overrides applied."""
        try:
            base = json.loads((HERE / "ui" / "agm" / "agms.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            base = {}
        d = self._agm_dir()
        try:
            custom = json.loads((d / "custom.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            custom = {}
        for abbr, c in custom.items():
            e = base.setdefault(abbr, {})
            for k in ("name", "title"):
                if c.get(k):
                    e[k] = c[k]; e["edited"] = True
        if d.is_dir():
            for p in d.iterdir():
                if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
                    try:
                        base.setdefault(p.stem.upper(), {})["portrait"] = self._data_url(p)
                        base[p.stem.upper()]["credit"] = {"source": "Your photo"}
                    except OSError:
                        pass
        return base

    def set_agm(self, abbr: str, name: str, title: str) -> dict:
        import re
        abbr = re.sub(r"[^A-Za-z]", "", abbr).upper()[:4]
        d = self._agm_dir(); d.mkdir(parents=True, exist_ok=True)
        f = d / "custom.json"
        try:
            custom = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            custom = {}
        custom[abbr] = {"name": str(name or "").strip()[:60], "title": str(title or "").strip()[:80]}
        if not custom[abbr]["name"] and not custom[abbr]["title"]:
            custom.pop(abbr)
        f.write_text(json.dumps(custom, indent=1), encoding="utf-8")
        return {"ok": True}

    def choose_agm_portrait(self, abbr: str) -> dict:
        """Pick a photo for the assistant GM; it's copied into Clubhouse's folder (the original stays put)."""
        import re, shutil
        abbr = re.sub(r"[^A-Za-z]", "", abbr).upper()[:4]
        picked = self._window.create_file_dialog(webview.FileDialog.OPEN, file_types=("Images (*.png;*.jpg;*.jpeg;*.webp)",))
        if not picked:
            return {"ok": False, "cancelled": True}
        src = Path(picked[0])
        if src.stat().st_size > 4 * 1024 * 1024:
            return {"ok": False, "error": "That image is over 4 MB. Pick a smaller one."}
        d = self._agm_dir(); d.mkdir(parents=True, exist_ok=True)
        for old in d.glob(abbr + ".*"):
            old.unlink()
        dest = d / (abbr + src.suffix.lower())
        shutil.copyfile(src, dest)
        return {"ok": True, "url": self._data_url(dest)}

    def clear_agm_portrait(self, abbr: str) -> dict:
        import re
        abbr = re.sub(r"[^A-Za-z]", "", abbr).upper()[:4]
        for old in self._agm_dir().glob(abbr + ".*"):
            old.unlink()
        return {"ok": True}

    def get_prefs(self) -> dict:
        cfg = load_config()
        return {"autoLoad": bool(cfg.get("autoLoad", False)), "updateCheck": bool(cfg.get("updateCheck", True))}

    # ---- in-app updates (app/updater.py, GitHub Releases) ----
    def get_version(self) -> dict:
        return {"version": VERSION, "repo": REPO, "frozen": bool(getattr(sys, "frozen", False))}

    def check_update(self) -> dict:
        return UPDATER.check()

    def download_update(self) -> dict:
        return UPDATER.download()

    def update_progress(self) -> dict:
        return UPDATER.progress()

    def install_update(self) -> dict:
        """Start the swap helper, then close so it can replace this folder and start the new version."""
        res = UPDATER.install()
        if res.get("ok") and self._window:
            threading.Timer(0.6, self._window.destroy).start()
        return res

    def set_pref(self, key: str, value) -> dict:
        if key not in ("autoLoad", "updateCheck"):
            return {"ok": False}
        cfg = load_config()
        cfg[key] = bool(value)
        save_config(cfg)
        return {"ok": True}

    def get_heads(self) -> list:
        """MLB headshots in app/ui/heads/ (written by app/fetch_headshots.py): [{i: MLB id, n: names, b: birth year, p: pitcher}]."""
        manifest = HERE / "ui" / "heads" / "manifest.json"
        try:
            return json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return []

    def get_assets(self) -> dict:
        """Optional team art dropped into app/ui/teams/:
        <ABBR>.png|svg|webp = logo, <ABBR>-hero.jpg|png|webp = banner background."""
        out: dict[str, dict] = {}
        folder = HERE / "ui" / "teams"
        if not folder.is_dir():
            return out
        manifest = folder / "manifest.json"   # written by app/import_logos.py: logo, mark, dark/solid flags
        if manifest.exists():
            try:
                out = json.loads(manifest.read_text(encoding="utf-8"))
            except ValueError:
                out = {}
        for f in folder.iterdir():
            if f.suffix.lower() not in {".png", ".svg", ".webp", ".jpg", ".jpeg"}:
                continue
            stem = f.stem.upper()
            kind = "hero" if stem.endswith("-HERO") else "mark" if stem.endswith("-MARK") else "logo"
            abbr = stem[:-5] if kind in ("hero", "mark") else stem
            out.setdefault(abbr, {}).setdefault(kind, f"teams/{f.name}")
        return out


def build(argv=None):
    """Create the window and wire it up. Returns (window, league, startup)."""
    import argparse
    ap = argparse.ArgumentParser(prog="clubhouse")
    ap.add_argument("--debug", action="store_true", help="open the web inspector")
    ap.add_argument("--save", help="read this folder for this run only (not remembered)")
    args, _ = ap.parse_known_args(argv)
    league = League()
    api = Api(league)

    window = webview.create_window(
        APP_NAME, str(HERE / "ui" / "index.html"), js_api=api,
        width=1600, height=960, min_size=(1000, 640), background_color="#0A0B0E", maximized=True,
    )
    api._window = window

    def push(meta: dict):
        window.evaluate_js(f"window.clubhouse && window.clubhouse.saveChanged({json.dumps(meta)})")

    league.on_change = push

    def startup():
        # First run: no folder saved, so the page asks (pre-filled with the default).
        if args.save:
            league.set_folder(args.save, remember=False)
        else:
            folder = load_config().get("saveFolder")
            if folder and Path(folder).is_dir():
                league.set_folder(folder)
        league.booting = False
        threading.Thread(target=league.watch, daemon=True).start()
        push({"ok": league.json is not None, "boot": True, **league.meta()})

    window.events.closed += league.stop
    return window, league, startup, args


def main():
    window, league, startup, args = build()
    # Keep the page's local storage between runs (My board, press answers, ranking arrows...): pywebview
    # defaults to a private session, and a random port would also give the page a new origin each time.
    import socket
    port = None
    with socket.socket() as s:
        try:
            s.bind(("127.0.0.1", WEB_PORT))
            port = WEB_PORT
        except OSError:
            port = None   # someone has it (a second Clubhouse?): fall back to a random port for this run
    store = CONFIG_PATH.parent / ("webview" if not args.save else "webview-copies")
    store.mkdir(parents=True, exist_ok=True)
    webview.start(startup, debug=args.debug, http_server=True, http_port=port, private_mode=False, storage_path=str(store))


if __name__ == "__main__":
    main()
