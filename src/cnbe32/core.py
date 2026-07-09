"""Core CNBE-32 bitfield encoding and distance utilities."""

from __future__ import annotations

import warnings
from dataclasses import dataclass

from .constants import (
    EXT_MAX,
    EXT_MIN,
    EXT_SHIFT,
    INDEX_MAX,
    INDEX_MIN,
    INDEX_SHIFT,
    RADIX_MAX,
    RADIX_MIN,
    RADIX_SHIFT,
    STROKE_MAX,
    STROKE_MIN,
    STROKE_SHIFT,
    STRUCT_MAX,
    STRUCT_MIN,
    STRUCT_SHIFT,
)
from .exceptions import CNBEValueError


def _validate_range(name: str, value: int, minimum: int, maximum: int) -> None:
    if not isinstance(value, int):
        raise CNBEValueError(
            f"{name} must be an int in range {minimum}..{maximum}; got {type(value).__name__}"
        )
    if not minimum <= value <= maximum:
        raise CNBEValueError(f"{name} must be in range {minimum}..{maximum}; got {value}")


@dataclass(frozen=True)
class CNBE32:
    """A CNBE-32 encoded value."""

    code: int

    @property
    def radix(self) -> int:
        return (self.code >> RADIX_SHIFT) & 0xFF

    @property
    def stroke(self) -> int:
        return (self.code >> STROKE_SHIFT) & 0x1F

    @property
    def struct(self) -> int:
        return (self.code >> STRUCT_SHIFT) & 0x0F

    @property
    def index(self) -> int:
        return (self.code >> INDEX_SHIFT) & 0x7FF

    @property
    def ext(self) -> int:
        return (self.code >> EXT_SHIFT) & 0x0F

    def to_dict(self) -> dict[str, int]:
        return {
            "code": self.code,
            "radix": self.radix,
            "stroke": self.stroke,
            "struct": self.struct,
            "index": self.index,
            "ext": self.ext,
        }


def encode_cnbe(radix: int, stroke: int, struct: int, index: int = 0, ext: int = 0) -> CNBE32:
    """Encode CNBE-32 fields into a 32-bit value.

    This function validates every field and never silently truncates values.
    """
    _validate_range("radix", radix, RADIX_MIN, RADIX_MAX)
    _validate_range("stroke", stroke, STROKE_MIN, STROKE_MAX)
    _validate_range("struct", struct, STRUCT_MIN, STRUCT_MAX)
    _validate_range("index", index, INDEX_MIN, INDEX_MAX)
    _validate_range("ext", ext, EXT_MIN, EXT_MAX)

    code = (
        (radix << RADIX_SHIFT)
        | (stroke << STROKE_SHIFT)
        | (struct << STRUCT_SHIFT)
        | (index << INDEX_SHIFT)
        | (ext << EXT_SHIFT)
    )
    return CNBE32(code)


def decode_cnbe(code: int | CNBE32) -> dict[str, int]:
    """Decode a CNBE-32 integer or CNBE32 object into field values."""
    value = code.code if isinstance(code, CNBE32) else code
    cnbe = CNBE32(int(value))
    return cnbe.to_dict()


def bit_hamming_distance(a: CNBE32, b: CNBE32) -> int:
    """Return the true bit-level Hamming distance between two CNBE-32 values."""
    return int(a.code ^ b.code).bit_count()


def field_weighted_distance(a: CNBE32, b: CNBE32) -> int:
    """Return the legacy weighted field distance.

    This is not a bit-level Hamming distance. It compares decoded fields and
    weights radix, stroke, and struct differences.
    """
    return abs(a.radix - b.radix) * 8 + abs(a.stroke - b.stroke) * 5 + abs(a.struct - b.struct) * 4


def hamming_distance(a: CNBE32, b: CNBE32) -> int:
    """Deprecated alias for field_weighted_distance.

    Use bit_hamming_distance for true bit-level Hamming distance, or
    field_weighted_distance for the legacy CNBE field-weighted metric.
    """
    warnings.warn(
        "hamming_distance() is deprecated because it is not a bit-level Hamming distance. "
        "Use bit_hamming_distance() or field_weighted_distance() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return field_weighted_distance(a, b)
# integrity check: 1783623667
