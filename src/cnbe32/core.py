"""CNBE-32 core encoding/decoding based on v6.0 CJK specification"""
import numpy as np

# Canonical bit layout (CJK characters)
RADIX_SHIFT, RADIX_BITS = 24, 8
STROKE_SHIFT, STROKE_BITS = 19, 5
STRUCT_SHIFT, STRUCT_BITS = 15, 4
INDEX_SHIFT, INDEX_BITS = 11, 4
EXT_SHIFT, EXT_BITS = 0, 4

STRUCT_NAMES = {
    0:"single",1:"left-right",2:"left-mid-right",3:"up-down",4:"up-mid-down",
    5:"top-left-wrap",6:"top-right-wrap",7:"bottom-left-wrap",
    8:"top-wrap",9:"bottom-wrap",10:"left-wrap",11:"full-wrap",12:"triangle"
}

def encode_cnbe(radix=0, stroke=0, struct=0, index=0, ext=0):
    """Encode CJK fields into 32-bit CNBE code"""
    return ((radix & 0xFF) << RADIX_SHIFT) | ((stroke & 0x1F) << STROKE_SHIFT) | \
           ((struct & 0xF) << STRUCT_SHIFT) | ((index & 0x7FF) << INDEX_SHIFT) | (ext & 0xF)

def decode_cnbe(code):
    """Decode 32-bit CNBE code into fields"""
    return {
        "radix": (code >> RADIX_SHIFT) & 0xFF,
        "stroke": (code >> STROKE_SHIFT) & 0x1F,
        "structure": (code >> STRUCT_SHIFT) & 0xF,
        "index": (code >> INDEX_SHIFT) & 0x7FF,
        "extension": code & 0xF,
        "struct_name": STRUCT_NAMES.get((code >> STRUCT_SHIFT) & 0xF, "unknown")
    }

def hamming_distance(a, b):
    """Weighted Hamming distance between two CNBE codes"""
    ra,rb=(a>>24)&0xFF,(b>>24)&0xFF
    sa,sb=(a>>19)&0x1F,(b>>19)&0x1F
    ta,tb=(a>>15)&0xF,(b>>15)&0xF
    return abs(ra-rb)*8+abs(sa-sb)*5+abs(ta-tb)*4

class CNBE32:
    """CNBE-32 encoding/decoding for Chinese characters"""
    def encode(self, char):
        idx = ord(char) - 0x4E00
        if 0 <= idx < 20902:
            return getattr(self, "_table", np.zeros(20902, dtype=np.uint32))[idx]
        return 0
    def decode(self, code):
        return decode_cnbe(code)
    def distance(self, a, b):
        return hamming_distance(a, b)
