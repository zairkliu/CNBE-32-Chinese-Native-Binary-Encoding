"""CNBE64: structural + GB18030-aligned 64-bit encoding foundation."""

from .codec import (
    GB18030_STATUS,
    LAYOUT,
    pack,
    pointer_for_char,
    unpack,
    validate,
)

__all__ = [
    "GB18030_STATUS",
    "LAYOUT",
    "pack",
    "pointer_for_char",
    "unpack",
    "validate",
]
