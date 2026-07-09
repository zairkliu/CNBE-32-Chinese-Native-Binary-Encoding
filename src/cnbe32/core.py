"""CNBE-32 core encoding/decoding — uses constants.py + typed exceptions"""

import warnings
from typing import Union

from .constants import (
    RADIX_SHIFT, STROKE_SHIFT, STRUCT_SHIFT, INDEX_SHIFT, EXT_SHIFT,
    RADIX_MASK, STROKE_MASK, STRUCT_MASK, INDEX_MASK, EXT_MASK,
    STRUCT_NAMES, CNBE_STRUCT_MIN, CNBE_STRUCT_MAX,
    CNBE_STROKE_MIN, CNBE_STROKE_MAX, CNBE_RADIX_MIN, CNBE_RADIX_MAX,
    CNBE_EXT_FLAGS_MIN, CNBE_EXT_FLAGS_MAX,
    CNBE_SUB_TYPE_MIN, CNBE_SUB_TYPE_MAX,
    CJK_UNICODE_START, CJK_UNICODE_COUNT,
)
from .exceptions import CNBEValueError, CNBEFormatError, CNBECharNotInTableError

# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def encode_cnbe(radix: int = 0, stroke: int = 0, struct: int = 0, index: int = 0, ext: int = 0) -> int:
    """Encode CJK fields into a 32-bit CNBE code with strict boundary validation.

    All fields are validated against their defined bit-width ranges.
    Out-of-range values raise :exc:`CNBEValueError` with the field name and
    legal range — no silent masking.
    """
    bounds: list[tuple[str, int, int, int]] = [
        ("radix",  radix,  CNBE_RADIX_MIN,  CNBE_RADIX_MAX),
        ("stroke", stroke, CNBE_STROKE_MIN, CNBE_STROKE_MAX),
        ("struct", struct, CNBE_STRUCT_MIN, CNBE_STRUCT_MAX),
        ("index",  index,  0,                INDEX_MASK),
        ("ext",    ext,    CNBE_EXT_FLAGS_MIN, CNBE_EXT_FLAGS_MAX),
    ]
    for name, val, lo, hi in bounds:
        if not lo <= val <= hi:
            raise CNBEValueError(f"{name}={val} is out of range [{lo}, {hi}]")

    return (
        ((radix & RADIX_MASK) << RADIX_SHIFT)
        | ((stroke & STROKE_MASK) << STROKE_SHIFT)
        | ((struct & STRUCT_MASK) << STRUCT_SHIFT)
        | ((index & INDEX_MASK) << INDEX_SHIFT)
        | (ext & EXT_MASK)
    )


def decode_cnbe(code: int) -> dict:
    """Decode a 32-bit CNBE code into its named fields.

    Raises :exc:`CNBEFormatError` if *code* does not fit in 32 bits.
    """
    if not 0 <= code <= 0xFFFF_FFFF:
        raise CNBEFormatError(f"code 0x{code:08X} is out of 32-bit range")
    struct_val = (code >> STRUCT_SHIFT) & STRUCT_MASK
    return {
        "radix":     (code >> RADIX_SHIFT) & RADIX_MASK,
        "stroke":    (code >> STROKE_SHIFT) & STROKE_MASK,
        "structure": struct_val,
        "index":     (code >> INDEX_SHIFT) & INDEX_MASK,
        "extension": code & EXT_MASK,
        "struct_name": STRUCT_NAMES.get(struct_val, "unknown"),
    }


# ---------------------------------------------------------------------------
# Distance functions
# ---------------------------------------------------------------------------

def bit_hamming_distance(a: int, b: int) -> int:
    """True bit-level Hamming distance between two CNBE-32 codes.

    Counts the number of differing bits after XOR:
    ``popcount(a XOR b)``.

    This is the standard information-theoretic Hamming distance.
    """
    return (a ^ b).bit_count()


def field_weighted_distance(a: int, b: int) -> int:
    """Field-weighted distance between two CNBE-32 codes.

    Computed as:
        ``|Δradix| * 8 + |Δstroke| * 5 + |Δstruct| * 4``

    The index and extension fields are intentionally excluded because they
    are positional identifiers, not semantic features.
    """
    ra = (a >> RADIX_SHIFT) & RADIX_MASK
    rb = (b >> RADIX_SHIFT) & RADIX_MASK
    sa = (a >> STROKE_SHIFT) & STROKE_MASK
    sb = (b >> STROKE_SHIFT) & STROKE_MASK
    ta = (a >> STRUCT_SHIFT) & STRUCT_MASK
    tb = (b >> STRUCT_SHIFT) & STRUCT_MASK
    return abs(ra - rb) * 8 + abs(sa - sb) * 5 + abs(ta - tb) * 4


def hamming_distance(a: int, b: int) -> int:
    """Weighted Hamming distance — **deprecated**.

    .. deprecated:: 1.1.0
        This name is misleading: the function computes a *field-weighted*
        distance, not bit-level Hamming distance.

        Use :func:`field_weighted_distance` for the same behaviour,
        or :func:`bit_hamming_distance` for true bit-level distance.

    This wrapper is kept for backward compatibility and will be removed
    in a future major version.
    """
    warnings.warn(
        "hamming_distance() is deprecated; use field_weighted_distance() or "
        "bit_hamming_distance() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return field_weighted_distance(a, b)


# ---------------------------------------------------------------------------
# CNBE32 class
# ---------------------------------------------------------------------------

class CNBE32:
    """CNBE-32 encoding/decoding for Chinese characters.

    Wraps the field-level helpers and optionally a SkillTable for
    direct character-to-code lookup.
    """

    def __init__(self, skill_table=None):
        """Initialize with an optional SkillTable.

        Args:
            skill_table: Optional :class:`~cnbe32.skill_table.SkillTable`
                instance for char-to-code lookup.  When omitted,
                :meth:`encode` will raise :exc:`CNBECharNotInTableError`
                unless ``_table`` is set externally.
        """
        self._table = skill_table.table if skill_table is not None else None

    def encode(self, char: str) -> int:
        """Return the CNBE-32 code for *char*.

        Raises :exc:`CNBECharNotInTableError` when no table is available
        or the character is outside the supported CJK range.
        """
        code_point = ord(char)
        idx = code_point - CJK_UNICODE_START
        if 0 <= idx < CJK_UNICODE_COUNT:
            if self._table is not None and len(self._table) > idx:
                return self._table[idx]
            raise CNBECharNotInTableError(char, code_point)
        raise CNBECharNotInTableError(char, code_point)

    def decode(self, code: int) -> dict:
        """Decode a CNBE-32 code, returning a field dict."""
        return decode_cnbe(code)

    def distance(self, a: int, b: int) -> int:
        """Compute field-weighted distance (same as :func:`field_weighted_distance`)."""
        return field_weighted_distance(a, b)
