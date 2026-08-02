# -*- coding: utf-8 -*-
"""CNBE Volume 核心实现：分页 zlib 压缩 + O(1) 索引 + 结构化检索。"""

from __future__ import annotations

import json
import struct
import zlib
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple

HEADER_SIZE = 256
MAGIC = b"CNBE"
INDEX_ITEM = struct.Struct("<II")
SUMMARY_SIZE = 32 + 32 + 2  # radix bitmap + stroke bitmap + struct bitmap


class CNBEVolume:
    def __init__(self, path: str, reverse_map: Optional[Dict[int, str]] = None, forward_map: Optional[Dict[str, int]] = None):
        self.path = Path(path)
        self.file = open(self.path, "rb")
        self.meta = self._read_header()
        self.reverse_map = reverse_map or {}
        self.forward_map = forward_map or {}
        self._index: List[Tuple[int, int]] = []
        self._summaries: Optional[dict] = None
        self._char_cache: Dict[str, List[int]] = {}
        self._page_cache: Dict[int, bytes] = {}
        self._load_index()

    def _read_header(self) -> dict:
        raw = self.file.read(HEADER_SIZE)
        if raw[:4] != MAGIC:
            raise ValueError("not a CNBE volume")
        vals = struct.unpack("<8I", raw[4:36])
        meta = {
            "magic": raw[:4].decode("ascii"),
            "version": vals[0],
            "total_chars": vals[1],
            "unique_chars": vals[2],
            "page_size": vals[3],
            "total_pages": vals[4],
            "index_offset": vals[5],
            "data_offset": vals[6],
            "compress_level": vals[7],
        }
        meta["index_size"] = meta["total_pages"] * INDEX_ITEM.size
        file_size = self.path.stat().st_size
        data_region_size = file_size - meta["data_offset"] - meta["total_pages"] * SUMMARY_SIZE
        meta["summary_offset"] = meta["data_offset"] + data_region_size
        return meta

    def _load_index(self) -> None:
        self.file.seek(self.meta["index_offset"])
        raw = self.file.read(self.meta["index_size"])
        self._index = [INDEX_ITEM.unpack_from(raw, i * INDEX_ITEM.size) for i in range(self.meta["total_pages"])]

    def _load_summaries(self) -> None:
        if self._summaries is not None:
            return
        self.file.seek(self.meta["summary_offset"])
        raw = self.file.read(self.meta["total_pages"] * SUMMARY_SIZE)
        radix_bits, stroke_bits, struct_bits = [], [], []
        for i in range(self.meta["total_pages"]):
            off = i * SUMMARY_SIZE
            radix_bits.append(raw[off : off + 32])
            stroke_bits.append(raw[off + 32 : off + 64])
            struct_bits.append(raw[off + 64 : off + 66])
        self._summaries = {"radix": radix_bits, "stroke": stroke_bits, "struct": struct_bits}

    def info(self) -> dict:
        return {**self.meta, "file_size": self.path.stat().st_size, "storage_ratio": self.path.stat().st_size / max(1, self.meta["total_chars"] * 4)}

    def page_codes(self, page: int) -> List[int]:
        if page in self._page_cache:
            return self._page_cache[page]
        offset, length = self._index[page]
        self.file.seek(offset)
        raw = zlib.decompress(self.file.read(length))
        codes = [struct.unpack_from(">I", raw, i * 4)[0] for i in range(len(raw) // 4)]
        if len(self._page_cache) > 8:
            self._page_cache.clear()
        self._page_cache[page] = codes
        return codes

    def seek(self, pos: int) -> dict:
        if not 0 <= pos < self.meta["total_chars"]:
            raise IndexError("position out of range")
        page, inner = divmod(pos, self.meta["page_size"])
        code = self.page_codes(page)[inner]
        return {"pos": pos, "page": page, "offset": inner, "code": hex(code), "char": self.reverse_map.get(code, "□")}

    def extract(self, start: int, end: int) -> str:
        if start < 0 or end > self.meta["total_chars"] or start >= end:
            raise IndexError("invalid range")
        out = []
        for pos in range(start, end):
            page, inner = divmod(pos, self.meta["page_size"])
            code = self.page_codes(page)[inner]
            out.append(self.reverse_map.get(code, "□"))
        return "".join(out)

    def extract_codes(self, start: int, length: int) -> List[int]:
        end = min(self.meta["total_chars"], start + length)
        out = []
        for pos in range(start, end):
            page, inner = divmod(pos, self.meta["page_size"])
            out.append(self.page_codes(page)[inner])
        return out

    def search(self, radix: Optional[int] = None, struct: Optional[int] = None, strokes: Optional[int] = None, limit: int = 10000) -> List[int]:
        self._load_summaries()
        pages = range(self.meta["total_pages"])
        if radix is not None:
            pages = (p for p in pages if self._summaries["radix"][p][radix // 8] & (1 << (radix % 8)))
        if strokes is not None:
            pages = (p for p in pages if self._summaries["stroke"][p][strokes // 8] & (1 << (strokes % 8)))
        if struct is not None:
            pages = (p for p in pages if self._summaries["struct"][p][struct // 8] & (1 << (struct % 8)))
        hits = []
        for page in pages:
            codes = self.page_codes(page)
            for inner, code in enumerate(codes):
                if radix is not None and ((code >> 24) & 0xFF) != radix:
                    continue
                if strokes is not None and ((code >> 19) & 0x1F) != strokes:
                    continue
                if struct is not None and ((code >> 15) & 0x0F) != struct:
                    continue
                hits.append(page * self.meta["page_size"] + inner)
                if len(hits) >= limit:
                    return hits
        return hits

    def search_char(self, char: str, limit: int = 10000) -> List[int]:
        if char in self._char_cache:
            return self._char_cache[char][:limit]
        code = self.forward_map.get(char) or next((c for c, ch in self.reverse_map.items() if ch == char), None)
        if code is None:
            return []
        hits = []
        for page in range(self.meta["total_pages"]):
            codes = self.page_codes(page)
            hits.extend(page * self.meta["page_size"] + i for i, c in enumerate(codes) if c == code)
            if len(hits) >= limit:
                break
        self._char_cache[char] = hits
        return hits[:limit]

    def random_passage(self, length: int) -> str:
        import random

        if length <= 0 or length > self.meta["total_chars"]:
            raise ValueError("invalid length")
        start = random.randint(0, self.meta["total_chars"] - length)
        return self.extract(start, start + length)

    def stream(self, start: int, length: int) -> Iterator[str]:
        end = min(self.meta["total_chars"], start + length)
        pos = start
        while pos < end:
            page, inner = divmod(pos, self.meta["page_size"])
            codes = self.page_codes(page)
            chunk = codes[inner : inner + min(self.meta["page_size"] - inner, end - pos)]
            yield "".join(self.reverse_map.get(c, "□") for c in chunk)
            pos += len(chunk)

    def close(self) -> None:
        self.file.close()


def load(path: str, reverse_map: Optional[Dict[int, str]] = None) -> CNBEVolume:
    return CNBEVolume(path, reverse_map=reverse_map)


def load_maps(db_path: str):
    import sqlite3

    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT char, cnbe FROM cnbe32 WHERE cnbe IS NOT NULL").fetchall()
    conn.close()
    reverse: Dict[int, str] = {}
    forward: Dict[str, int] = {}
    for ch, code in rows:
        if ch and code is not None:
            forward.setdefault(ch, int(code))
            if int(code) not in reverse:
                reverse[int(code)] = ch
    return reverse, forward


def load_reverse_map(db_path: str) -> Dict[int, str]:
    reverse, _ = load_maps(db_path)
    return reverse
