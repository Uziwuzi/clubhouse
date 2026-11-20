"""The decompressed save: three self-describing "LE90" databases back to back.

Each database is:
    "LE90"  u32 desc_len
    "[DESC]"  struct definitions ...
    "[DATA]"  table blocks ...

Struct definition:
    char[16] name, u32 desc_len, u32 n_fields, then n_fields x 32-byte field records
Field record:
    char[22] name, u16 index, u16 elem_size, u16 count, u16 total_size, u16 reserved

Table block in [DATA]:
    char[16] struct name, u32 row_count, then for each row:
        the fields packed back to back IN DESCRIPTOR ORDER (no padding),
        followed by that row's child table blocks (same format, recursive).

See docs/SAVE_FORMAT.md for what is verified and what is still a guess.
"""
from __future__ import annotations

import re
import struct
from dataclasses import dataclass, field

STRING_HINTS = ("NAME", "MESSAGE", "TEXT", "HEADLINE", "TITLE", "CITY")


@dataclass
class Field:
    name: str
    index: int
    elem_size: int
    count: int
    size: int

    @property
    def is_string(self) -> bool:
        return self.elem_size == 1 and self.count > 1 and any(h in self.name for h in STRING_HINTS)


@dataclass
class Struct:
    name: str
    fields: list[Field]
    row_size: int = 0
    offsets: dict[str, int] = field(default_factory=dict)

    def __post_init__(self):
        off = 0
        for f in self.fields:
            self.offsets[f.name] = off
            off += f.size
        self.row_size = off


@dataclass
class Table:
    """A parsed table block. rows[i] is a dict of field values; children[i] maps
    child struct name -> Table for that row."""
    name: str
    offset: int          # offset of the block header in the raw save
    rows: list[dict]
    row_offsets: list[int]
    children: list[dict]
    end: int


class Database:
    def __init__(self, raw: bytes):
        self.raw = raw
        self.parts: list[tuple[int, int, int]] = []   # (db_start, data_start, db_end)
        self.structs: dict[str, Struct] = {}
        self._child_names: dict[str, list[str]] = {}
        starts = [m.start() - 8 for m in re.finditer(rb"\[DESC\]", raw)]
        for i, base in enumerate(starts):
            data_start = self._parse_desc(base)
            end = starts[i + 1] if i + 1 < len(starts) else len(raw)
            self.parts.append((base, data_start, end))
        self._names = {n.encode().ljust(16, b"\0") for n in self.structs}

    # ---- schema --------------------------------------------------------
    def _parse_desc(self, base: int) -> int:
        d = self.raw
        p = base + 8
        assert d[p:p + 6] == b"[DESC]", hex(base)
        p += 6
        while d[p:p + 6] != b"[DATA]":
            name = d[p:p + 16].split(b"\0")[0].decode()
            _dl, n = struct.unpack_from("<II", d, p + 16)
            q = p + 24
            fields = []
            for _ in range(n):
                fname = d[q:q + 22].split(b"\0")[0].decode()
                idx, es, cnt, tot, _r = struct.unpack_from("<5H", d, q + 22)
                fields.append(Field(fname, idx, es, cnt, tot))
                q += 32
            self.structs.setdefault(name, Struct(name, fields))
            p = q
        return p + 6

    def schema_text(self) -> str:
        lines = []
        for s in self.structs.values():
            lines.append(f"{s.name}  ({len(s.fields)} fields, {s.row_size} bytes/row)")
            for f in s.fields:
                shape = f"{f.elem_size}B" if f.count == 1 else f"{f.elem_size}B x {f.count}"
                lines.append(f"    +{s.offsets[f.name]:<4} {f.name:<24} {shape}")
        return "\n".join(lines)

    # ---- locating tables ------------------------------------------------
    def _in_data(self, off: int) -> bool:
        return any(ds <= off < end for _b, ds, end in self.parts)

    def find(self, name: str) -> list[tuple[int, int]]:
        """All (offset, row_count) block headers for a struct name in the data areas."""
        key = name.encode().ljust(16, b"\0")
        return [(m.start(), struct.unpack_from("<I", self.raw, m.start() + 16)[0])
                for m in re.finditer(re.escape(key), self.raw) if self._in_data(m.start())]

    def largest(self, name: str) -> Table:
        """The block with the most rows: the league-wide copy of a table."""
        off, _ = max(self.find(name), key=lambda x: x[1])
        return self.read(off)

    # ---- reading ---------------------------------------------------------
    def _is_header(self, p: int) -> bool:
        return self.raw[p:p + 16] in self._names

    def _name_at(self, p: int) -> str:
        return self.raw[p:p + 16].split(b"\0")[0].decode()

    def decode(self, f: Field, raw: bytes):
        if f.is_string:
            return raw.split(b"\0")[0].decode("latin-1")  # names are Latin-1 (e.g. Domínguez)
        if f.count == 1:
            return int.from_bytes(raw, "little")
        if f.elem_size == 1:
            return list(raw)
        return [int.from_bytes(raw[i * f.elem_size:(i + 1) * f.elem_size], "little")
                for i in range(f.count)]

    def read(self, off: int) -> Table:
        name = self._name_at(off)
        st = self.structs[name]
        cnt = struct.unpack_from("<I", self.raw, off + 16)[0]
        p = off + 20
        rows, row_offs, kids = [], [], []
        for r in range(cnt):
            row_offs.append(p)
            row = {}
            for f in st.fields:
                row[f.name] = self.decode(f, self.raw[p:p + f.size])
                p += f.size
            rows.append(row)
            ch: dict[str, Table] = {}
            known = self._child_names.get(name)
            if known is None and r < cnt - 1:
                # Learn the child list from a row that is not the last one:
                # everything between this row and the next row must be children.
                # A repeated name means the next row has started (zero-field
                # structs such as D_SEASON_INFO have rows made only of children).
                learned = []
                while self._is_header(p) and self._name_at(p) not in learned:
                    t = self.read(p)
                    ch[t.name] = t
                    learned.append(t.name)
                    p = t.end
                self._child_names[name] = learned
            else:
                for cn in known or []:
                    if self._name_at(p) != cn:
                        break
                    t = self.read(p)
                    ch[cn] = t
                    p = t.end
            kids.append(ch)
        return Table(name, off, rows, row_offs, kids, p)

    # ---- patching (for editors; the save is fixed-size) -------------------
    def field_offset(self, table: Table, row: int, field_name: str) -> int:
        return table.row_offsets[row] + self.structs[table.name].offsets[field_name]

    def patch(self, raw: bytearray, table: Table, row: int, field_name: str, value: int) -> None:
        f = next(x for x in self.structs[table.name].fields if x.name == field_name)
        if f.count != 1:
            raise ValueError("patch() only handles scalar fields")
        o = self.field_offset(table, row, field_name)
        raw[o:o + f.size] = int(value).to_bytes(f.size, "little")
