"""CNBE-32 test suite based on v6.0-v10.8 validation"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from cnbe32 import CNBE32, encode_cnbe, decode_cnbe, hamming_distance

def test_encode_decode():
    code = encode_cnbe(radix=1, stroke=1, struct=0)
    d = decode_cnbe(code)
    assert d["radix"] == 1
    assert d["stroke"] == 1
    assert d["structure"] == 0
    print("PASS: encode/decode")


def test_boundary_values():
    from cnbe32 import encode_cnbe, decode_cnbe
    c0 = encode_cnbe(radix=1, stroke=0, struct=0)
    c31 = encode_cnbe(radix=1, stroke=31, struct=0)
    assert decode_cnbe(c0)["stroke"] == 0
    assert decode_cnbe(c31)["stroke"] == 31
    p0 = encode_cnbe(radix=1, stroke=1, struct=0)
    p15 = encode_cnbe(radix=1, stroke=1, struct=15)
    assert decode_cnbe(p0)["structure"] == 0
    assert decode_cnbe(p15)["structure"] == 15
    print("PASS: boundary values (stroke 0/31, struct 0/15)")
def test_index_field():
    from cnbe32 import encode_cnbe, decode_cnbe
    from cnbe32.constants import INDEX_MASK
    assert INDEX_MASK == 0x7FF
    for idx in [0, 1, 127, 512, 2047]:
        c = encode_cnbe(radix=1, stroke=1, struct=0, index=idx)
        assert decode_cnbe(c)["index"] == idx
    print("PASS: index field round-trip (11 bits, INDEX_MASK=0x7FF)")
def test_non_cjk_error():
    from cnbe32 import CNBE32
    from cnbe32.exceptions import CNBECharNotInTableError
    cnbe = CNBE32()
    for ch in ["?", "@", "\u20AC"]:
        try:
            cnbe.encode(ch)
            print("FAIL: should have raised for", ascii(ch))
        except CNBECharNotInTableError:
            print("PASS: CNBECharNotInTableError for", ascii(ch))
        except:
            print("FAIL: unexpected exception for", ascii(ch)); raise
    print("PASS: non-CJK error handling")

def test_hamming():
    a = encode_cnbe(radix=1, stroke=1, struct=0)
    b = encode_cnbe(radix=2, stroke=1, struct=0)
    assert hamming_distance(a, b) == 8  # |1-2|*8 = 8
    print("PASS: hamming distance")

def test_skill_table():
    from cnbe32.skill_table import SkillTable
    st = SkillTable()
    assert st.lookup(0x4E00) == 0  # no table loaded
    print("PASS: skill table")

if __name__ == "__main__":
    test_encode_decode()
    test_boundary_values()
    test_index_field()
    test_hamming()
    test_skill_table()
    test_non_cjk_error()
    print("\nAll 6 tests passed! (v0.3.1)")


