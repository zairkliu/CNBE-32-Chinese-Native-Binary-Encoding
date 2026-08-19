"""CNBE64: structural + GB18030-aligned 64-bit encoding foundation."""

from .codec import (
    LAYOUT,
    GB18030Status,
    pack,
    pointer_for_char,
    unpack,
    validate,
)

__all__ = [
    "GB18030Status",
    "LAYOUT",
    "pack",
    "pointer_for_char",
    "unpack",
    "validate",
]
