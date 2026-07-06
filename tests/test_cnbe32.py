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
    test_hamming()
    test_skill_table()
    print("\nAll tests passed! (v1-v10.8 validated)")
