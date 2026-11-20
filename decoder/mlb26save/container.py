"""The outer file layer: SAVE_xxx (zlib) + SAVEINFO (label, timestamp, SHA-256).

SAVEINFO layout (168 bytes, little-endian):
    0x00  char[128]  slot label, e.g. "White Sox April 21, 2026", NUL padded
    0x80  u32        unix timestamp of the save
    0x84  u32        zero
    0x88  u8[32]     SHA-256 of the *compressed* SAVE_000 file
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import os
import shutil
import zlib
from dataclasses import dataclass
from pathlib import Path

from .database import Database

SAVEINFO_SIZE = 168


@dataclass
class SaveInfo:
    label: str
    timestamp: int
    sha256: bytes

    @classmethod
    def parse(cls, raw: bytes) -> "SaveInfo":
        if len(raw) != SAVEINFO_SIZE:
            raise ValueError(f"SAVEINFO should be {SAVEINFO_SIZE} bytes, got {len(raw)}")
        label = raw[:128].split(b"\0")[0].decode("utf-8", "replace")
        ts = int.from_bytes(raw[128:132], "little")
        return cls(label, ts, raw[136:168])

    def build(self) -> bytes:
        out = bytearray(SAVEINFO_SIZE)
        lab = self.label.encode("utf-8")[:127]
        out[: len(lab)] = lab
        out[128:132] = self.timestamp.to_bytes(4, "little")
        out[136:168] = self.sha256
        return bytes(out)

    @property
    def saved_at(self) -> _dt.datetime:
        return _dt.datetime.fromtimestamp(self.timestamp, _dt.timezone.utc)


class SaveSlot:
    """One save slot: a SAVE_xxx file and the SAVEINFO next to it."""

    def __init__(self, save_path: Path, info_path: Path):
        self.save_path = Path(save_path)
        self.info_path = Path(info_path)
        self.compressed = self.save_path.read_bytes()
        self.info = SaveInfo.parse(self.info_path.read_bytes())
        self.checksum_ok = hashlib.sha256(self.compressed).digest() == self.info.sha256
        self.raw = zlib.decompress(self.compressed)
        self.db = Database(self.raw)

    # ---- reading -------------------------------------------------------
    def export(self) -> dict:
        from .extract import export_league
        data = export_league(self.db)
        data["slot"] = {
            "label": self.info.label,
            "labelDate": label_date(self.info.label),
            "savedAt": self.info.saved_at.isoformat(),
            "checksumOk": self.checksum_ok,
            "file": self.save_path.name,
        }
        return data

    # ---- writing (UNTESTED IN-GAME: see docs/SAVE_FORMAT.md) -------------
    def write(self, new_raw: bytes, backup_dir: Path | None = None, keep: int = 5) -> Path:
        """Recompress `new_raw`, update SAVEINFO's checksum, and replace the slot.

        Always backs up the current pair first and keeps the newest `keep` backups.
        The decompressed size must not change: every table is fixed-size.
        """
        if len(new_raw) != len(self.raw):
            raise ValueError("decompressed save size changed; refusing to write")
        backup_dir = Path(backup_dir or self.save_path.parent / "_mlb26_backups")
        dest = make_backup(self.save_path, self.info_path, backup_dir, keep)
        comp = zlib.compress(new_raw, 9)
        info = SaveInfo(self.info.label, self.info.timestamp, hashlib.sha256(comp).digest())
        tmp_s, tmp_i = self.save_path.with_suffix(".tmp"), self.info_path.with_suffix(".tmp")
        tmp_s.write_bytes(comp)
        tmp_i.write_bytes(info.build())
        os.replace(tmp_s, self.save_path)
        os.replace(tmp_i, self.info_path)
        return dest


def label_date(label: str) -> str | None:
    """The in-game date from a slot label like 'Mets May 29, 2026' (ISO), or None.
    Used for display: in spring training SEASONDATE is still 0, so the computed date says Opening Day."""
    import re
    m = re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December) (\d{1,2}), (\d{4})", label or "")
    if not m:
        return None
    try:
        return _dt.datetime.strptime(" ".join(m.groups()), "%B %d %Y").date().isoformat()
    except ValueError:
        return None


def make_backup(save_path: Path, info_path: Path, backup_dir: Path, keep: int = 5) -> Path:
    stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")   # microseconds: two quick edits never share a folder
    dest = Path(backup_dir) / f"{save_path.name}-{stamp}"
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copy2(save_path, dest / save_path.name)
    shutil.copy2(info_path, dest / info_path.name)
    olds = sorted(p for p in Path(backup_dir).iterdir() if p.is_dir() and p.name.startswith(save_path.name))
    for old in olds[:-keep]:
        shutil.rmtree(old, ignore_errors=True)
    return dest


def find_slots(folder: str | Path) -> list[tuple[Path, Path]]:
    """Return (SAVE_xxx, SAVEINFO) pairs found directly in `folder`."""
    folder = Path(folder)
    info = folder / "SAVEINFO"
    saves = sorted(p for p in folder.iterdir() if p.is_file() and p.name.startswith("SAVE_"))
    return [(s, info) for s in saves if info.exists()]


# On the Switch build each save type gets its own slot folder inside the profile
# folder: FRAN<hash> (franchise), CARR<hash> (Road to the Show), ROST<hash>
# (roster), SETT<hash> (settings), PLYA<hash> (audio). VERIFIED on one machine.
FRANCHISE_PREFIX = "FRAN"


def find_franchise_slots(folder: str | Path, depth: int = 3) -> list[tuple[Path, Path]]:
    """Franchise (SAVE_xxx, SAVEINFO) pairs at or below `folder`, newest first.

    Accepts a FRAN slot folder, a profile folder (holding FRAN*/CARR*/... slot
    folders), or the `profile\\save` folder above the profile ids.
    """
    folder = Path(folder)
    found: list[tuple[Path, Path]] = []

    def walk(d: Path, left: int):
        try:
            entries = list(d.iterdir())
        except OSError:
            return
        if d.name.upper().startswith(FRANCHISE_PREFIX):
            found.extend(find_slots(d))
            return
        if left:
            for e in entries:
                if e.is_dir() and not e.name.startswith("_"):
                    walk(e, left - 1)

    walk(folder, depth)
    return sorted(found, key=lambda s: s[0].stat().st_mtime, reverse=True)


def open_save(path: str | Path, info: str | Path | None = None) -> SaveSlot:
    """Open an explicit SAVE_xxx file, a folder holding one, or the newest
    franchise slot found under a profile folder."""
    path = Path(path)
    if path.is_dir():
        slots = find_slots(path) or find_franchise_slots(path)
        if not slots:
            raise FileNotFoundError(f"no franchise save (SAVE_xxx + SAVEINFO) in {path}")
        return SaveSlot(*slots[0])
    return SaveSlot(path, Path(info) if info else path.with_name("SAVEINFO"))
