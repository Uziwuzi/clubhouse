"""In-app updates from GitHub Releases.

Flow: check (latest release > this version?) -> download the release zip to %APPDATA%\\Clubhouse\\updates and verify
its SHA-256 against the .sha256 asset -> unpack -> install: a small PowerShell helper waits for Clubhouse to close,
moves the current folder aside as a backup (<folder>.old), moves the new folder into place and starts it again.
If the swap fails the helper puts the old folder back and starts that. Settings, scouting, history and snapshots
live in %APPDATA%\\Clubhouse and are never touched; neither is any save.

Only the packaged Clubhouse.exe installs updates. Running from source, check() still reports new versions.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import urllib.request
import zipfile
from pathlib import Path

from version import REPO, VERSION

API = f"https://api.github.com/repos/{REPO}/releases/latest"
UA = {"User-Agent": f"Clubhouse/{VERSION} (updater)", "Accept": "application/vnd.github+json"}
WORK = Path(os.environ.get("APPDATA", Path.home())) / "Clubhouse" / "updates"


def _ver(s: str) -> tuple:
    return tuple(int(x) for x in re.findall(r"\d+", s or "")[:4]) or (0,)


def frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


class Updater:
    def __init__(self):
        self.latest: dict | None = None
        self.state = {"stage": "idle", "pct": 0, "error": None}
        self._lock = threading.Lock()

    # ---- check -------------------------------------------------------------------------------------------
    def check(self) -> dict:
        try:
            with urllib.request.urlopen(urllib.request.Request(API, headers=UA), timeout=15) as r:
                rel = json.load(r)
        except Exception as e:  # noqa: BLE001  (offline, rate limit, no releases yet)
            return {"ok": False, "current": VERSION, "error": str(e)}
        tag = rel.get("tag_name", "")
        assets = {a["name"]: a for a in rel.get("assets", [])}
        zipa = next((a for n, a in assets.items() if n.lower().endswith(".zip")), None)
        sha = next((a for n, a in assets.items() if n.lower().endswith(".sha256")), None)
        newer = _ver(tag) > _ver(VERSION)
        self.latest = {"version": tag.lstrip("v"), "notes": rel.get("body") or "", "url": rel.get("html_url"),
                       "zip": zipa and zipa["browser_download_url"], "size": zipa and zipa["size"],
                       "sha": sha and sha["browser_download_url"], "published": rel.get("published_at")}
        return {"ok": True, "current": VERSION, "available": bool(newer and zipa and sha), "canInstall": frozen(),
                **{k: self.latest[k] for k in ("version", "notes", "url", "size", "published")}}

    # ---- download + verify + unpack ------------------------------------------------------------------------
    def download(self) -> dict:
        with self._lock:
            if self.state["stage"] in ("downloading", "ready"):
                return dict(self.state)
            if not self.latest or not self.latest.get("zip"):
                self.check()
            if not self.latest or not self.latest.get("zip"):
                return {"stage": "error", "error": "No update found."}
            self.state = {"stage": "downloading", "pct": 0, "error": None}
        threading.Thread(target=self._download, daemon=True).start()
        return dict(self.state)

    def _download(self):
        try:
            ver = self.latest["version"]
            WORK.mkdir(parents=True, exist_ok=True)
            for old in WORK.iterdir():   # leftovers from earlier updates
                shutil.rmtree(old, ignore_errors=True) if old.is_dir() else old.unlink(missing_ok=True)
            with urllib.request.urlopen(urllib.request.Request(self.latest["sha"], headers=UA), timeout=30) as r:
                want = r.read().decode("ascii", "ignore").split()[0].strip().lower()
            dst = WORK / f"Clubhouse-{ver}.zip"
            h = hashlib.sha256()
            with urllib.request.urlopen(urllib.request.Request(self.latest["zip"], headers=UA), timeout=60) as r, open(dst, "wb") as f:
                total = int(r.headers.get("Content-Length") or self.latest.get("size") or 0)
                got = 0
                while True:
                    chunk = r.read(1 << 16)
                    if not chunk:
                        break
                    f.write(chunk); h.update(chunk); got += len(chunk)
                    if total:
                        self.state["pct"] = min(99, int(got * 100 / total))
            if h.hexdigest().lower() != want:
                raise ValueError("The download didn't match its checksum, so it wasn't installed. Try again later.")
            out = WORK / f"Clubhouse-{ver}"
            with zipfile.ZipFile(dst) as z:
                z.extractall(out)
            app = next((p.parent for p in out.rglob("Clubhouse.exe")), None)
            if not app:
                raise ValueError("The download is missing Clubhouse.exe.")
            dst.unlink(missing_ok=True)
            self.state = {"stage": "ready", "pct": 100, "error": None, "folder": str(app), "version": ver}
        except Exception as e:  # noqa: BLE001
            self.state = {"stage": "error", "pct": 0, "error": str(e)}

    def progress(self) -> dict:
        return dict(self.state)

    # ---- install: swap folders after Clubhouse closes ----------------------------------------------------
    def install(self) -> dict:
        if not frozen():
            return {"ok": False, "error": "Updates install only in the packaged Clubhouse.exe."}
        if self.state.get("stage") != "ready":
            return {"ok": False, "error": "The update hasn't finished downloading."}
        cur = Path(sys.executable).resolve().parent
        backup = cur.with_name(cur.name + ".old")
        # Stage the new version next to the current one: a folder can't be moved between drives, and
        # %APPDATA% is often on another drive than wherever Clubhouse was unzipped.
        new = cur.with_name(cur.name + ".new")
        try:
            shutil.rmtree(new, ignore_errors=True)
            shutil.copytree(self.state["folder"], new)
        except OSError as e:
            return {"ok": False, "error": f"Couldn't stage the update next to {cur}: {e}"}
        args = " ".join(f'"{a}"' for a in sys.argv[1:])
        script = WORK / "install.ps1"
        q = lambda p: str(p).replace("'", "''")
        script.write_text(f"""$ErrorActionPreference = 'Stop'
try {{ Wait-Process -Id {os.getpid()} -Timeout 60 -ErrorAction SilentlyContinue }} catch {{}}
Start-Sleep -Milliseconds 800
$cur = '{q(cur)}'; $new = '{q(new)}'; $bak = '{q(backup)}'
$moved = $false
for ($i = 0; $i -lt 20; $i++) {{
  try {{
    if (Test-Path -LiteralPath $bak) {{ Remove-Item -LiteralPath $bak -Recurse -Force }}
    Move-Item -LiteralPath $cur -Destination $bak
    $moved = $true
    Move-Item -LiteralPath $new -Destination $cur
    break
  }} catch {{
    if ($moved -and -not (Test-Path -LiteralPath $cur)) {{ Move-Item -LiteralPath $bak -Destination $cur; $moved = $false }}
    Start-Sleep -Milliseconds 700
  }}
}}
Start-Process -FilePath (Join-Path $cur 'Clubhouse.exe') -WorkingDirectory $cur {('-ArgumentList ' + repr(args)) if args else ''}
""", encoding="utf-8")
        flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) | getattr(subprocess, "CREATE_NO_WINDOW", 0)
        subprocess.Popen(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-File", str(script)],
                         creationflags=flags, close_fds=True)
        return {"ok": True}
