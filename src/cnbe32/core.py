"""CNBE-32 core encoding/decoding — uses constants.py + typed exceptions"""
import numpy as np
import warnings

from .constants import (
    RADIX_SHIFT, STROKE_SHIFT, STRUCT_SHIFT, INDEX_SHIFT, EXT_SHIFT,
    RADIX_MASK, STROKE_MASK, STRUCT_MASK, INDEX_MASK, EXT_MASK,
    STRUCT_NAMES, CNBE_STRUCT_MIN, CNBE_STRUCT_MAX,
    CNBE_STROKE_MIN, CNBE_STROKE_MAX, CNBE_RADIX_MIN, CNBE_RADIX_MAX,
    CJK_UNICODE_START, CJK_UNICODE_COUNT,
)
from .exceptions import CNBEValueError, CNBEFormatError


def encode_cnbe(radix=0, stroke=0, struct=0, index=0, ext=0):
    """Encode CJK fields into 32-bit CNBE code with boundary validation"""
    for (name, val, lo, hi) in [
        ("radix", radix, CNBE_RADIX_MIN, CNBE_RADIX_MAX),
        ("stroke", stroke, CNBE_STROKE_MIN, CNBE_STROKE_MAX),
        ("struct", struct, CNBE_STRUCT_MIN, CNBE_STRUCT_MAX),
    ]:
        if not lo <= val <= hi:
            raise CNBEValueError(f"{name}={val} is out of range [{lo}, {hi}]")
    return ((radix & 0xFF) << RADIX_SHIFT) | \
           ((stroke & 0x1F) << STROKE_SHIFT) | \
           ((struct & 0xF) << STRUCT_SHIFT) | \
           ((index & 0x7FF) << INDEX_SHIFT) | \
           (ext & 0xF)


def decode_cnbe(code):
    """Decode 32-bit CNBE code into fields; raises CNBEFormatError on invalid code"""
    if not 0 <= code <= 0xFFFFFFFF:
        raise CNBEFormatError(f"code 0x{code:08X} is out of 32-bit range")
    return {
        "radix": (code >> RADIX_SHIFT) & 0xFF,
        "stroke": (code >> STROKE_SHIFT) & 0x1F,
        "structure": (code >> STRUCT_SHIFT) & 0xF,
        "index": (code >> INDEX_SHIFT) & 0x7FF,
        "extension": code & 0xF,
        "struct_name": STRUCT_NAMES.get((code >> STRUCT_SHIFT) & 0xF, "unknown"),
    }


def hamming_distance(a, b):
    """Weighted Hamming distance between two CNBE codes (radix*8 + stroke*5 + struct*4)"""
    ra = (a >> RADIX_SHIFT) & 0xFF
    rb = (b >> RADIX_SHIFT) & 0xFF
    sa = (a >> STROKE_SHIFT) & 0x1F
    sb = (b >> STROKE_SHIFT) & 0x1F
    ta = (a >> STRUCT_SHIFT) & 0xF
    tb = (b >> STRUCT_SHIFT) & 0xF
    return abs(ra - rb) * 8 + abs(sa - sb) * 5 + abs(ta - tb) * 4


class CNBE32:
    """CNBE-32 encoding/decoding for Chinese characters (wraps constants + SkillTable)"""

    def encode(self, char):
        idx = ord(char) - CJK_UNICODE_START
        if 0 <= idx < CJK_UNICODE_COUNT:
            return getattr(self, "_table", np.zeros(CJK_UNICODE_COUNT, dtype=np.uint32))[idx]
        return 0

    def decode(self, code):
        return decode_cnbe(code)

    def distance(self, a, b):
        return hamming_distance(a, b)
