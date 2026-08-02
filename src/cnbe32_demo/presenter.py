"""Presentation-layer helpers for the CNBE-32 desktop demo."""

from __future__ import annotations

from dataclasses import dataclass

from cnbe32 import decode_cnbe, lookup


@dataclass(frozen=True)
class CharacterEncoding:
    """One character's demo-ready CNBE-32 lookup result."""

    char: str
    unicode_hex: str
    codepoint: int
    cnbe_decimal: int | None
    cnbe_hex: str | None
    cnbe_binary: str | None
    radix: int | None
    radix_name: str | None
    strokes: int | None
    struct_type: int | None
    struct_name: str | None
    index: int | None
    ext: int | None
    track: str | None
    needs_encoding: bool | None
    status: str

    @property
    def display_status(self) -> str:
        if self.status == "encoded":
            if self.track == "standard":
                return "已编码：标准运行时轨道"
            if self.track == "legacy":
                return "已编码：旧版运行时轨道"
            return "已编码"
        if self.status == "pending":
            return "已收录：等待授权编码"
        return "未收录：当前运行时暂无记录"


def encode_text_for_demo(text: str) -> list[CharacterEncoding]:
    """Look up CJK characters and return rows suitable for the demo UI."""
    rows: list[CharacterEncoding] = []
    for char in text:
        if char.isspace():
            continue
        codepoint = ord(char)
        row = lookup(char)
        if row is None:
            rows.append(
                CharacterEncoding(
                    char=char,
                    unicode_hex=f"U+{codepoint:04X}",
                    codepoint=codepoint,
                    cnbe_decimal=None,
                    cnbe_hex=None,
                    cnbe_binary=None,
                    radix=None,
                    radix_name=None,
                    strokes=None,
                    struct_type=None,
                    struct_name=None,
                    index=None,
                    ext=None,
                    track=None,
                    needs_encoding=None,
                    status="missing",
                )
            )
            continue

        cnbe_value = row.get("cnbe")
        needs_encoding = bool(row.get("needs_encoding", 0))
        decoded = decode_cnbe(int(cnbe_value)) if cnbe_value is not None else {}
        status = "pending" if cnbe_value is None or needs_encoding else "encoded"
        rows.append(
            CharacterEncoding(
                char=char,
                unicode_hex=f"U+{codepoint:04X}",
                codepoint=codepoint,
                cnbe_decimal=int(cnbe_value) if cnbe_value is not None else None,
                cnbe_hex=f"0x{int(cnbe_value):08X}" if cnbe_value is not None else None,
                cnbe_binary=f"{int(cnbe_value):032b}" if cnbe_value is not None else None,
                radix=row.get("radix"),
                radix_name=row.get("radix_name"),
                strokes=row.get("strokes"),
                struct_type=row.get("struct_type"),
                struct_name=row.get("struct_name"),
                index=decoded.get("index", row.get("idx")),
                ext=decoded.get("ext"),
                track=row.get("track"),
                needs_encoding=needs_encoding,
                status=status,
            )
        )
    return rows
