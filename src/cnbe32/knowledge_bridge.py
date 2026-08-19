"""CNBE Knowledge Bridge.

Turns the 32-bit CNBE binary encoding into an AI-readable state object and
provides database-backed knowledge output for three Chinese-first scenarios:

1. Chinese knowledge base / RAG retrieval
2. Ancient text validation and excerpting
3. OCR glyph comparison

Every lookup is validated against the CNBE-32 database, and every distance is
computed from the decoded structural fields, not from opaque Unicode bytes.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Iterable, Optional

from .core import CNBE32, bit_hamming_distance, decode_cnbe, encode_cnbe, field_weighted_distance
from .db import resolve_db_path

STRUCT_NAMES = [
    "独体字",
    "左右",
    "左中右",
    "上下",
    "上中下",
    "左上包围",
    "右上包围",
    "左下包围",
    "上包围",
    "下包围",
    "左包围",
    "全包围",
    "品字",
]


def _is_cjk(ch: str) -> bool:
    return "\u4e00" <= ch <= "\u9fff"


def _code(value: int | CNBE32) -> int:
    return value.code if isinstance(value, CNBE32) else int(value)


def _similarity(distance: int) -> float:
    return round(1.0 / (1.0 + distance), 4)


@dataclass(frozen=True)
class CNBEState:
    """Decoded, database-validated CNBE-32 state for one character."""

    char: str
    code: int
    radix: int
    stroke: int
    struct: int
    index: int
    ext: int
    radix_name: str = ""
    struct_name: str = ""
    track: str = ""
    unicode: Optional[int] = None

    @property
    def hex(self) -> str:
        return f"0x{self.code:08X}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "char": self.char,
            "unicode": self.unicode,
            "code": self.code,
            "hex": self.hex,
            "fields": {
                "radix": self.radix,
                "stroke": self.stroke,
                "struct": self.struct,
                "index": self.index,
                "ext": self.ext,
            },
            "radix_name": self.radix_name,
            "struct_name": self.struct_name,
            "track": self.track,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def to_ai_prompt(self) -> str:
        """Return a compact AI-readable description of the binary state."""
        return (
            f"汉字 {self.char} 的 CNBE-32 状态：\n"
            f"- 二进制编码: {self.hex} ({self.code})\n"
            f"- 部首 {self.radix_name or self.radix}、笔画 {self.stroke}、"
            f"结构 {self.struct_name or self.struct}、索引 {self.index}、扩展 {self.ext}\n"
            f"- 字段可计算、可自验、可用于结构检索"
        )

    def validate(self) -> dict[str, Any]:
        issues: list[str] = []
        ok = True
        for field, value, lo, hi in [
            ("radix", self.radix, 0, 255),
            ("stroke", self.stroke, 0, 31),
            ("struct", self.struct, 0, 15),
            ("index", self.index, 0, 2047),
            ("ext", self.ext, 0, 15),
        ]:
            if not lo <= value <= hi:
                ok = False
                issues.append(f"{field}={value} out of range {lo}..{hi}")
        expected = encode_cnbe(
            self.radix, self.stroke, self.struct, self.index, self.ext
        ).code
        if expected != self.code:
            ok = False
            issues.append(f"field re-encode mismatch: {self.code} != {expected}")
        return {"char": self.char, "valid": ok, "issues": issues}


class CNBEKnowledgeBridge:
    """Database-backed CNBE state, self-validation, and knowledge retrieval."""

    def __init__(self, db_path: str | Path | None = None):
        path = Path(db_path) if db_path else resolve_db_path()
        self.db_path = str(path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._rows: Optional[list[dict[str, Any]]] = None

    def close(self) -> None:
        self.conn.close()

    def lookup(self, char: str) -> Optional[CNBEState]:
        if len(char) != 1:
            raise ValueError("lookup() expects exactly one character")
        row = self.conn.execute(
            "SELECT * FROM cnbe32 WHERE char = ? "
            "ORDER BY CASE WHEN track = 'standard' THEN 0 ELSE 1 END LIMIT 1",
            (char,),
        ).fetchone()
        return self._state_from_row(dict(row)) if row else None

    def lookup_code(self, code: int | CNBE32) -> Optional[CNBEState]:
        value = _code(code)
        row = self.conn.execute(
            "SELECT * FROM cnbe32 WHERE cnbe = ? LIMIT 1", (value,)
        ).fetchone()
        return self._state_from_row(dict(row)) if row else None

    def _state_from_row(self, row: dict[str, Any]) -> CNBEState:
        code = int(row["cnbe"])
        fields = decode_cnbe(code)
        struct_type = int(row["struct_type"])
        return CNBEState(
            char=row["char"],
            code=code,
            radix=fields["radix"],
            stroke=fields["stroke"],
            struct=fields["struct"],
            index=fields["index"],
            ext=fields["ext"],
            radix_name=row.get("radix_name") or "",
            struct_name=row.get("struct_name") or (
                STRUCT_NAMES[struct_type] if 0 <= struct_type < len(STRUCT_NAMES) else ""
            ),
            track=row.get("track") or "",
            unicode=row.get("unicode"),
        )

    def self_validate(self) -> dict[str, Any]:
        rows = self.conn.execute("SELECT * FROM cnbe32").fetchall()
        out_of_range = 0
        reencode_mismatch = 0
        reverse: dict[int, list[str]] = {}
        idx_keys: dict[tuple[int, int, int, int], int] = {}
        for raw in rows:
            row = dict(raw)
            code = int(row["cnbe"])
            try:
                fields = decode_cnbe(code)
            except Exception:  # noqa: BLE001
                out_of_range += 1
                continue
            if not (
                0 <= fields["radix"] <= 255
                and 0 <= fields["stroke"] <= 31
                and 0 <= fields["struct"] <= 15
                and 0 <= fields["index"] <= 2047
            ):
                out_of_range += 1
            expected = encode_cnbe(
                fields["radix"], fields["stroke"], fields["struct"], fields["index"], fields["ext"]
            ).code
            if expected != code:
                reencode_mismatch += 1
            reverse.setdefault(code, []).append(row["char"])
            key = (fields["radix"], fields["stroke"], fields["struct"], fields["index"])
            idx_keys[key] = idx_keys.get(key, 0) + 1

        collisions = [
            {"code": code, "chars": chars}
            for code, chars in reverse.items()
            if len(set(chars)) > 1
        ]
        duplicate_idx = [
            {"key": list(key), "count": count}
            for key, count in idx_keys.items()
            if count > 1
        ]
        standard = sum(1 for r in rows if r["track"] == "standard")
        needs_encoding = sum(1 for r in rows if r["needs_encoding"])
        return {
            "rows": len(rows),
            "standard_track": standard,
            "needs_encoding": needs_encoding,
            "out_of_range": out_of_range,
            "reencode_mismatch": reencode_mismatch,
            "reverse_collisions": len(collisions),
            "collision_sample": collisions[:10],
            "duplicate_idx_groups": len(duplicate_idx),
            "duplicate_idx_sample": duplicate_idx[:10],
        }

    def distance(self, a: str | CNBEState | int, b: str | CNBEState | int) -> Optional[dict[str, Any]]:
        sa = self._coerce_state(a)
        sb = self._coerce_state(b)
        if sa is None or sb is None:
            return None
        weighted = field_weighted_distance(CNBE32(sa.code), CNBE32(sb.code))
        bits = bit_hamming_distance(CNBE32(sa.code), CNBE32(sb.code))
        return {
            "a": sa.to_dict(),
            "b": sb.to_dict(),
            "field_weighted_distance": weighted,
            "bit_hamming_distance": bits,
            "similarity": _similarity(weighted),
            "fields": {
                "radix_same": sa.radix == sb.radix,
                "stroke_same": sa.stroke == sb.stroke,
                "struct_same": sa.struct == sb.struct,
                "index_same": sa.index == sb.index,
            },
        }

    def _coerce_state(self, value: str | CNBEState | int) -> Optional[CNBEState]:
        if isinstance(value, CNBEState):
            return value
        if isinstance(value, str):
            return self.lookup(value)
        return self.lookup_code(value)

    def _all_rows(self) -> list[dict[str, Any]]:
        if self._rows is None:
            self._rows = [dict(r) for r in self.conn.execute("SELECT * FROM cnbe32")]
        return self._rows

    def nearest(self, query: str | CNBEState | int, k: int = 5) -> list[dict[str, Any]]:
        target = self._coerce_state(query)
        if target is None:
            return []
        results: list[dict[str, Any]] = []
        for row in self._all_rows():
            code = int(row["cnbe"])
            if code == target.code:
                continue
            state = self._state_from_row(row)
            weighted = field_weighted_distance(CNBE32(target.code), CNBE32(code))
            bits = bit_hamming_distance(CNBE32(target.code), CNBE32(code))
            results.append(
                {
                    "char": state.char,
                    "code": code,
                    "hex": state.hex,
                    "radix_name": state.radix_name,
                    "struct_name": state.struct_name,
                    "stroke": state.stroke,
                    "field_weighted_distance": weighted,
                    "bit_hamming_distance": bits,
                    "similarity": _similarity(weighted),
                }
            )
        results.sort(
            key=lambda item: (
                item["field_weighted_distance"],
                item["bit_hamming_distance"],
            )
        )
        return results[:k]

    def ocr_candidates(
        self, ocr_char: str, candidates: Iterable[str], top_k: int = 5
    ) -> list[dict[str, Any]]:
        target = self.lookup(ocr_char)
        scored: list[dict[str, Any]] = []
        for cand in candidates:
            state = self.lookup(cand)
            if state is None:
                continue
            dist = self.distance(target, state) if target else None
            if dist is None:
                continue
            scored.append(
                {
                    "candidate": cand,
                    "exact": cand == ocr_char,
                    "field_weighted_distance": dist["field_weighted_distance"],
                    "similarity": dist["similarity"],
                    "fields": dist["fields"],
                }
            )
        scored.sort(
            key=lambda item: (
                not item.get("exact", False),
                item.get("field_weighted_distance", 999),
            )
        )
        return scored[:top_k]

    def retrieve_knowledge(
        self,
        query_text: str,
        knowledge: list[dict[str, Any]],
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        query_chars = [ch for ch in query_text if _is_cjk(ch)]
        if not query_chars:
            return []
        scored: list[dict[str, Any]] = []
        for record in knowledge:
            record_text = str(record.get("text") or record.get("char") or "")
            record_chars = [ch for ch in record_text if _is_cjk(ch)]
            record_char = str(record.get("char") or "")
            best = 0.0
            if record_char:
                if any(record_char == qc for qc in query_chars):
                    best = 1.0
            if best < 1.0:
                for qc in query_chars:
                    qs = self.lookup(qc)
                    if qs is None:
                        continue
                    for rc in record_chars:
                        rs = self.lookup(rc)
                        if rs is None:
                            continue
                        sim = _similarity(
                            field_weighted_distance(CNBE32(qs.code), CNBE32(rs.code))
                        )
                        if rc == qc:
                            sim = 1.0
                        best = max(best, sim)
            scored.append(
                {
                    "score": round(best, 4),
                    "char": record_char,
                    "title": record.get("title", ""),
                    "text": record_text,
                }
            )
        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:top_k]

    def ancient_validate(
        self, ocr_text: str, truth_text: str, max_notes: int = 20
    ) -> dict[str, Any]:
        matcher = SequenceMatcher(None, ocr_text, truth_text, autojunk=False)
        notes: list[dict[str, Any]] = []
        excerpt: list[str] = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                excerpt.append(ocr_text[i1:i2])
                continue
            if tag == "replace":
                src = ocr_text[i1:i2]
                tgt = truth_text[j1:j2]
                dist = self.distance(src, tgt) if len(src) == len(tgt) == 1 else None
                kind = "形近可疑" if dist and dist["field_weighted_distance"] <= 6 else "差异"
                notes.append(
                    {
                        "type": "replace",
                        "source": src,
                        "target": tgt,
                        "kind": kind,
                        "distance": dist,
                    }
                )
            else:
                label = "删" if tag == "delete" else "增"
                notes.append(
                    {
                        "type": tag,
                        "source": ocr_text[i1:i2] or "∅",
                        "target": truth_text[j1:j2] or "∅",
                        "kind": label,
                        "distance": None,
                    }
                )
            if len(notes) >= max_notes:
                break
        return {
            "collations": notes,
            "excerpt": "".join(excerpt),
            "total_notes": len(notes),
        }
