import sys, os, random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from cnbe32.db import lookup

class Encoder:
    name = ""
    def encode(self, text):
        return text

class UnicodeEncoder(Encoder):
    name = "unicode"
    def encode(self, text):
        return text

class FullCNBEEncoder(Encoder):
    name = "cnbe_full"
    def encode(self, text):
        result = []
        for ch in text:
            r = lookup(ch)
            if r:
                result.append(f"0x{r['cnbe']:08X}")
            else:
                result.append(f"U+{ord(ch):04X}")
        return " ".join(result)

class RadicalOnlyEncoder(Encoder):
    name = "radical_only"
    def encode(self, text):
        result = []
        for ch in text:
            r = lookup(ch)
            if r:
                result.append(str(r.get("radix", 0)))
            else:
                result.append(f"U+{ord(ch):04X}")
        return " ".join(result)

class StrokeOnlyEncoder(Encoder):
    name = "stroke_only"
    def encode(self, text):
        result = []
        for ch in text:
            r = lookup(ch)
            if r:
                result.append(str(r.get("strokes", 0)))
            else:
                result.append(f"U+{ord(ch):04X}")
        return " ".join(result)

class StructureOnlyEncoder(Encoder):
    name = "structure_only"
    def encode(self, text):
        result = []
        for ch in text:
            r = lookup(ch)
            if r:
                result.append(str(r.get("struct_type", 0)))
            else:
                result.append(f"U+{ord(ch):04X}")
        return " ".join(result)

class RandomBitfieldEncoder(Encoder):
    name = "random_bitfield"
    def __init__(self, seed=42):
        self.rng = random.Random(seed)
    def encode(self, text):
        result = []
        for ch in text:
            r = lookup(ch)
            if r:
                code = r["cnbe"]
                random_val = self.rng.randint(0, 0xFFFFFFFF)  # 0 to 32-bit max
                # XOR to preserve structure but randomize
                flipped = code ^ random_val
                result.append(f"0x{flipped & 0xFFFFFFFF:08X}")
            else:
                result.append(f"U+{ord(ch):04X}")
        return " ".join(result)

class RadicalStrokeEncoder(Encoder):
    name = "radical_stroke"
    def encode(self, text):
        result = []
        for ch in text:
            r = lookup(ch)
            if r:
                rad = r.get("radix", 0)
                st = r.get("strokes", 0)
                result.append(f"R{rad}S{st}")
            else:
                result.append(f"U+{ord(ch):04X}")
        return " ".join(result)

def get_all_encoders():
    return [
        UnicodeEncoder(),
        FullCNBEEncoder(),
        RadicalOnlyEncoder(),
        StrokeOnlyEncoder(),
        StructureOnlyEncoder(),
        RandomBitfieldEncoder(),
        RadicalStrokeEncoder(),
    ]
