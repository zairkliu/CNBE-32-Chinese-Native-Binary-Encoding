"""CNBE-32 Python SDK tests."""

from __future__ import annotations

import warnings

import numpy as np
import pytest

from cnbe32 import (
    CNBE32,
    SkillTable,
    bit_hamming_distance,
    decode_cnbe,
    encode_cnbe,
    field_weighted_distance,
    hamming_distance,
)
from cnbe32.db import batch
from cnbe32.exceptions import CNBEValueError


def test_encode_decode_roundtrip() -> None:
    value = encode_cnbe(radix=72, stroke=8, struct=1, index=123, ext=2)
    assert isinstance(value, CNBE32)
    decoded = decode_cnbe(value)
    assert decoded["radix"] == 72
    assert decoded["stroke"] == 8
    assert decoded["struct"] == 1
    assert decoded["index"] == 123
    assert decoded["ext"] == 2


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({"radix": 0, "stroke": 0, "struct": 0, "index": 0, "ext": 0}, (0, 0, 0, 0, 0)),
        ({"radix": 255, "stroke": 31, "struct": 15, "index": 2047, "ext": 15}, (255, 31, 15, 2047, 15)),
    ],
)
def test_encode_boundary_values(
    kwargs: dict[str, int], expected: tuple[int, int, int, int, int]
) -> None:
    value = encode_cnbe(**kwargs)
    decoded = decode_cnbe(value)
    assert (
        decoded["radix"],
        decoded["stroke"],
        decoded["struct"],
        decoded["index"],
        decoded["ext"],
    ) == expected


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("radix", -1),
        ("radix", 256),
        ("stroke", -1),
        ("stroke", 32),
        ("struct", -1),
        ("struct", 16),
        ("index", -1),
        ("index", 2048),
        ("ext", -1),
        ("ext", 16),
    ],
)
def test_encode_rejects_invalid_field_values(field: str, bad_value: int) -> None:
    kwargs: dict[str, int] = {"radix": 1, "stroke": 1, "struct": 1, "index": 1, "ext": 1}
    kwargs[field] = bad_value
    with pytest.raises(CNBEValueError, match=field):
        encode_cnbe(**kwargs)


@pytest.mark.parametrize("bad_code", [-1, 2**32, 1.5, "123", True])
def test_decode_rejects_invalid_code_values(bad_code: object) -> None:
    with pytest.raises(CNBEValueError, match="code"):
        decode_cnbe(bad_code)  # type: ignore[arg-type]


@pytest.mark.parametrize("bad_code", [-1, 2**32, 1.5, "123", True])
def test_cnbe32_rejects_invalid_code_values(bad_code: object) -> None:
    with pytest.raises(CNBEValueError, match="code"):
        CNBE32(bad_code)  # type: ignore[arg-type]


def test_bit_hamming_distance() -> None:
    a = CNBE32(0b0000)
    b = CNBE32(0b1011)
    assert bit_hamming_distance(a, b) == 3


def test_field_weighted_distance() -> None:
    a = encode_cnbe(radix=1, stroke=1, struct=1)
    b = encode_cnbe(radix=2, stroke=3, struct=4)
    assert field_weighted_distance(a, b) == 1 * 8 + 2 * 5 + 3 * 4


def test_legacy_hamming_distance_warns_and_matches_field_weighted_distance() -> None:
    a = encode_cnbe(radix=1, stroke=1, struct=1)
    b = encode_cnbe(radix=2, stroke=3, struct=4)
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        result = hamming_distance(a, b)
    assert result == field_weighted_distance(a, b)
    assert any(item.category is DeprecationWarning for item in captured)


def test_batch_empty_inputs() -> None:
    assert batch("") == []
    assert batch([]) == []


def test_batch_preserves_input_order_and_duplicates() -> None:
    rows = batch("丁一丁")
    assert [row["char"] for row in rows] == ["丁", "一", "丁"]


def test_batch_rejects_multi_character_iterable_items() -> None:
    with pytest.raises(ValueError, match="one-character"):
        batch(["一", "丁乙"])


def test_skill_table_empty_is_explicit() -> None:
    table = SkillTable.empty()
    assert table.lookup(0x4E00) == 0


def test_skill_table_direct_constructor_requires_table() -> None:
    with pytest.raises(TypeError):
        SkillTable()  # type: ignore[call-arg]


def test_skill_table_rejects_wrong_shape() -> None:
    with pytest.raises(ValueError):
        SkillTable(np.zeros(3, dtype=np.uint32))


def test_skill_table_from_file_missing_path() -> None:
    with pytest.raises(FileNotFoundError):
        SkillTable.from_file("/path/that/does/not/exist.npy")
