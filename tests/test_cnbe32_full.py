# CNBE-32 comprehensive test suite
#
# Run unit tests only:    pytest tests/test_cnbe32_full.py -m "not integration"
# Run everything:         pytest tests/test_cnbe32_full.py

import os
import sys
import warnings
from pathlib import Path

import pytest

_src = Path(__file__).resolve().parent.parent / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from cnbe32 import (
    CNBE32,
    SkillTable,
    bit_hamming_distance,
    decode_cnbe,
    encode_cnbe,
    field_weighted_distance,
    hamming_distance,
)
from cnbe32.constants import (
    CJK_UNICODE_COUNT,
    CNBE_EXT_FLAGS_MAX,
    CNBE_STRUCT_MAX,
    INDEX_MASK,
)
from cnbe32.db import batch, close, resolve_db_path
from cnbe32.exceptions import (
    CNBECharNotInTableError,
    CNBEFormatError,
    CNBEValueError,
)


def _db_available():
    try:
        resolve_db_path()
        return True
    except FileNotFoundError:
        return False


_db_marker = pytest.mark.skipif(not _db_available(), reason="cnbe32.db not found")


# ---------------------------------------------------------------------------
# 1. encode_cnbe / decode_cnbe roundtrip
# ---------------------------------------------------------------------------

class TestEncodeDecode:
    def test_roundtrip_defaults(self):
        c = encode_cnbe()
        d = decode_cnbe(c)
        assert d["radix"] == 0
        assert d["stroke"] == 0
        assert d["structure"] == 0
        assert d["index"] == 0
        assert d["extension"] == 0

    def test_roundtrip_full(self):
        c = encode_cnbe(radix=255, stroke=31, struct=15, index=2047, ext=15)
        d = decode_cnbe(c)
        assert d["radix"] == 255
        assert d["stroke"] == 31
        assert d["structure"] == 15
        assert d["index"] == 2047
        assert d["extension"] == 15

    def test_roundtrip_mid(self):
        c = encode_cnbe(72, 8, 1, index=42, ext=3)
        d = decode_cnbe(c)
        assert d["radix"] == 72
        assert d["stroke"] == 8
        assert d["structure"] == 1
        assert d["index"] == 42
        assert d["extension"] == 3
        assert "struct_name" in d


# ---------------------------------------------------------------------------
# 2. encode_cnbe boundary validation
# ---------------------------------------------------------------------------

# Tuple: (encode_param_name, value_to_test, lo, hi)
_OUT_OF_RANGE_CASES = [
    ("radix", -1, 0, 255),
    ("radix", 256, 0, 255),
    ("stroke", -1, 0, 31),
    ("stroke", 32, 0, 31),
    ("struct", -1, 0, 15),
    ("struct", 16, 0, 15),
    ("index", -1, 0, INDEX_MASK),
    ("index", INDEX_MASK + 1, 0, INDEX_MASK),
    ("ext", -1, 0, CNBE_EXT_FLAGS_MAX),
    ("ext", 16, 0, CNBE_EXT_FLAGS_MAX),
]

# Tuple: (encode_param_name, decode_key, value_to_test)
_VALID_CASES = [
    ("radix", "radix", 0),
    ("radix", "radix", 255),
    ("stroke", "stroke", 0),
    ("stroke", "stroke", 31),
    ("struct", "structure", 0),
    ("struct", "structure", CNBE_STRUCT_MAX),
    ("index", "index", 0),
    ("index", "index", INDEX_MASK),
    ("ext", "extension", 0),
    ("ext", "extension", CNBE_EXT_FLAGS_MAX),
]


class TestEncodeBoundaries:

    @pytest.mark.parametrize("param,value,lo,hi", _OUT_OF_RANGE_CASES)
    def test_out_of_range_raises(self, param, value, lo, hi):
        kwargs = {"radix": 1, "stroke": 1, "struct": 0, "index": 0, "ext": 0}
        kwargs[param] = value
        with pytest.raises(CNBEValueError, match=rf"{param}=.*\[{lo}, {hi}\]"):
            encode_cnbe(**kwargs)

    @pytest.mark.parametrize("param,decode_key,value", _VALID_CASES)
    def test_valid_boundaries(self, param, decode_key, value):
        kwargs = {"radix": 1, "stroke": 1, "struct": 0, "index": 0, "ext": 0}
        kwargs[param] = value
        c = encode_cnbe(**kwargs)
        d = decode_cnbe(c)
        assert d[decode_key] == value


# ---------------------------------------------------------------------------
# 3. decode_cnbe format error
# ---------------------------------------------------------------------------

class TestDecodeFormat:
    def test_negative_code(self):
        with pytest.raises(CNBEFormatError):
            decode_cnbe(-1)

    def test_too_large_code(self):
        with pytest.raises(CNBEFormatError):
            decode_cnbe(0x1_0000_0000)


# ---------------------------------------------------------------------------
# 4. Distance functions
# ---------------------------------------------------------------------------

class TestDistances:
    def test_bit_hamming_distance(self):
        a = encode_cnbe(1, 1, 0)
        b = encode_cnbe(2, 1, 0)
        assert bit_hamming_distance(a, b) > 0
        assert bit_hamming_distance(a, a) == 0

    def test_bit_hamming_symmetric(self):
        a = encode_cnbe(10, 5, 3, 100, 7)
        b = encode_cnbe(20, 10, 6, 200, 14)
        assert bit_hamming_distance(a, b) == bit_hamming_distance(b, a)

    def test_field_weighted_distance(self):
        a = encode_cnbe(1, 1, 0)
        b = encode_cnbe(2, 1, 0)
        assert field_weighted_distance(a, b) == 8
        assert field_weighted_distance(a, a) == 0

    def test_field_weighted_larger(self):
        a = encode_cnbe(1, 1, 0)
        c = encode_cnbe(3, 4, 2)
        expected = abs(1 - 3) * 8 + abs(1 - 4) * 5 + abs(0 - 2) * 4
        assert field_weighted_distance(a, c) == expected

    def test_hamming_distance_deprecated(self):
        a = encode_cnbe(1, 1, 0)
        b = encode_cnbe(2, 1, 0)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = hamming_distance(a, b)
            assert len(w) >= 1
            assert issubclass(w[0].category, DeprecationWarning)
        assert result == field_weighted_distance(a, b)


# ---------------------------------------------------------------------------
# 5. CNBE32 class
# ---------------------------------------------------------------------------

class TestCNBE32:
    def test_encode_without_table_raises(self):
        encoder = CNBE32()
        with pytest.raises(CNBECharNotInTableError):
            encoder.encode("?")

    def test_encode_non_cjk_raises(self):
        encoder = CNBE32()
        with pytest.raises(CNBECharNotInTableError):
            encoder.encode("A")

    @_db_marker
    def test_encode_with_real_table(self):
        st = SkillTable.empty()
        from cnbe32.db import lookup
        row = lookup(chr(0x4E00))
        if row:
            st.table[0] = row["cnbe"]
            encoder = CNBE32(st)
            assert encoder.encode(chr(0x4E00)) == row["cnbe"]

    def test_decode(self):
        encoder = CNBE32()
        d = encoder.decode(encode_cnbe(5, 3, 2))
        assert d["radix"] == 5


# ---------------------------------------------------------------------------
# 6. SkillTable
# ---------------------------------------------------------------------------

class TestSkillTable:
    def test_empty_returns_zero(self):
        st = SkillTable.empty()
        assert st.lookup(0x4E00) == 0
        assert st[chr(0x4E00)] == 0

    def test_from_file_nonexistent(self):
        with pytest.raises(FileNotFoundError):
            SkillTable.from_file("/nonexistent/path/skill.bin")

    def test_direct_call_raises(self):
        with pytest.raises(TypeError, match=r'SkillTable\(\) is not supported'):
            SkillTable()

    def test_lookup_out_of_range(self):
        st = SkillTable.empty()
        assert st.lookup(0x0041) == 0  # 'A'
        assert st.lookup(0xFFFF) == 0


# ---------------------------------------------------------------------------
# 7. Database path resolution
# ---------------------------------------------------------------------------

class TestDBPathResolution:
    def test_env_var_valid(self, tmp_path, monkeypatch):
        db_file = tmp_path / "test.db"
        db_file.write_text("")
        monkeypatch.setenv("CNBE32_DB_PATH", str(db_file))
        assert resolve_db_path() == db_file

    def test_env_var_invalid(self, monkeypatch):
        monkeypatch.setenv("CNBE32_DB_PATH", "/nonexistent/db")
        with pytest.raises(FileNotFoundError, match="CNBE32_DB_PATH"):
            resolve_db_path()

    @_db_marker
    def test_default_resolves(self):
        p = resolve_db_path()
        assert p.is_file()


# ---------------------------------------------------------------------------
# 8. Database query edge cases (integration)
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestDBQueries:
    def test_batch_empty_string(self):
        assert batch("") == []

    def test_batch_empty_list(self):
        assert batch([]) == []

    def test_batch_nonempty(self):
        results = batch([chr(0x4E00), chr(0x6C49)])
        assert isinstance(results, list)

    def test_close_connection(self):
        close()


# ---------------------------------------------------------------------------
# 9. Index field covers full range
# ---------------------------------------------------------------------------

class TestIndexField:
    def test_index_zero(self):
        assert decode_cnbe(encode_cnbe(1, 1, 0, index=0))["index"] == 0

    def test_index_max(self):
        assert decode_cnbe(encode_cnbe(1, 1, 0, index=INDEX_MASK))["index"] == INDEX_MASK

    def test_index_powers_of_two(self):
        for idx in [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024]:
            assert decode_cnbe(encode_cnbe(1, 1, 0, index=idx))["index"] == idx
