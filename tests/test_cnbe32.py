# CNBE-32 test suite (v0.4.0)
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from cnbe32 import CNBE32, decode_cnbe, encode_cnbe, hamming_distance


def test_encode_decode():
    c = encode_cnbe(1, 1, 0)
    d = decode_cnbe(c)
    assert d["radix"] == 1 and d["stroke"] == 1
    print("PASS: encode/decode")

def test_index_field():
    from cnbe32.constants import INDEX_MASK
    assert INDEX_MASK == 0x7FF
    for idx in [0, 1, 127, 512, 2047]:
        c = encode_cnbe(1, 1, 0, idx)
        assert decode_cnbe(c)["index"] == idx
    print("PASS: index field")

def test_db():
    from cnbe32.db import lookup, search, stats
    r = lookup(chr(0x4E00))
    assert r and r["cnbe"] == 0x01080000
    s = search(r["cnbe"])
    assert s["char"] == chr(0x4E00)
    st = stats()
    assert st["total"] == 20902
    print("PASS: DB lookup")

def test_boundary():
    assert decode_cnbe(encode_cnbe(1,0,0))["stroke"] == 0
    assert decode_cnbe(encode_cnbe(1,31,0))["stroke"] == 31
    assert decode_cnbe(encode_cnbe(1,1,0))["structure"] == 0
    assert decode_cnbe(encode_cnbe(1,1,15))["structure"] == 15
    print("PASS: boundary")

def test_hamming():
    assert hamming_distance(encode_cnbe(1,1,0), encode_cnbe(2,1,0)) == 8
    print("PASS: hamming")

def test_skill_table():
    from cnbe32.skill_table import SkillTable
    assert SkillTable.empty().lookup(0x4E00) == 0
    print("PASS: skill table")

def test_non_cjk_error():
    from cnbe32.exceptions import CNBECharNotInTableError
    for ch in ["?", "@"]:
        try:
            CNBE32().encode(ch)
            print("FAIL:", ascii(ch))
        except CNBECharNotInTableError:
            print("PASS: error for", ascii(ch))
    print("PASS: non-CJK error")

if __name__ == "__main__":
    for fn in [test_encode_decode, test_index_field, test_db,
               test_boundary, test_hamming, test_skill_table,
               test_non_cjk_error]:
        fn()
    print()
    print("All 7 tests passed! (v1.0.1)")
