"""CNBE64 fixed 64-bit layout codec.

bits 63..60: version (4)
bits 59..39: gb18030_pointer (21)
bit  38:     gb18030_present (1)
bits 37..36: gb18030_status (2)
bits 35..32: reserved (4)
bits 31..0:  cnbe32 (32)
"""

from __future__ import annotations

from dataclasses import dataclass

LAYOUT = {
    "version": (63, 60),
    "gb18030_pointer": (59, 39),
    "gb18030_present": (38, 38),
    "gb18030_status": (37, 36),
    "reserved": (35, 32),
    "cnbe32": (31, 0),
}


class GB18030_STATUS:
    MAPPED = 0
    CONFLICT = 1
    MISSING = 2
    UNKNOWN = 3


def pack(
    cnbe32: int,
    gb18030_pointer: int = 0,
    version: int = 1,
    status: int = GB18030_STATUS.UNKNOWN,
    present: bool = False,
    reserved: int = 0,
) -> int:
    """Pack CNBE64 fields into a 64-bit integer."""
    if not 0 <= cnbe32 < (1 << 32):
        raise ValueError("cnbe32 must fit in 32 bits")
    if not 0 <= gb18030_pointer < (1 << 21):
        raise ValueError("gb18030_pointer must fit in 21 bits")
    if not 0 <= version < 16:
        raise ValueError("version must fit in 4 bits")
    if not 0 <= status < 4:
        raise ValueError("status must fit in 2 bits")
    if not 0 <= reserved < 16:
        raise ValueError("reserved must fit in 4 bits")
    return (
        (version << 60)
        | (gb18030_pointer << 39)
        | (int(present) << 38)
        | (status << 36)
        | (reserved << 32)
        | cnbe32
    )


def unpack(code: int) -> dict:
    """Unpack a 64-bit integer into named fields."""
    if not 0 <= code < (1 << 64):
        raise ValueError("code must fit in 64 bits")
    return {
        "version": (code >> 60) & 0xF,
        "gb18030_pointer": (code >> 39) & 0x1FFFFF,
        "gb18030_present": (code >> 38) & 0x1,
        "gb18030_status": (code >> 36) & 0x3,
        "reserved": (code >> 32) & 0xF,
        "cnbe32": code & 0xFFFFFFFF,
    }


def validate(code: int) -> tuple[bool, list[str]]:
    """Validate that a 64-bit value follows the fixed layout."""
    if not 0 <= code < (1 << 64):
        return False, ["not_a_64bit_value"]
    fields = unpack(code)
    errors = []
    if fields["version"] == 0:
        errors.append("version_zero")
    if fields["gb18030_present"] and fields["gb18030_pointer"] == 0:
        errors.append("present_without_pointer")
    if fields["gb18030_status"] not in (0, 1, 2, 3):
        errors.append("invalid_status")
    return not errors, errors


def pointer_for_char(ch: str) -> tuple[int, bool]:
    """Return (gb18030_pointer, is_four_byte) for a character."""
    b = ch.encode("gb18030")
    if len(b) == 4:
        ptr = (b[0] - 0x81) * 12600 + (b[1] - 0x30) * 1260 + (b[2] - 0x81) * 10 + (b[3] - 0x30)
        return ptr, True
    ptr = (b[0] - 0x81) * 190 + (b[1] - 0x40) - (1 if b[1] > 0x7F else 0)
    return ptr, False
