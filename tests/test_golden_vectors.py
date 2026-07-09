"""Golden vector consistency tests for CNBE-32."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cnbe32 import CNBE32, decode_cnbe, encode_cnbe
from cnbe32.exceptions import CNBEValueError

ROOT = Path(__file__).resolve().parents[1]
GOLDEN_VECTORS_PATH = ROOT / "spec" / "golden_vectors.json"


def load_vectors() -> dict:
    with GOLDEN_VECTORS_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def test_golden_vectors_file_exists() -> None:
    assert GOLDEN_VECTORS_PATH.exists()


def test_golden_vectors_metadata() -> None:
    data = load_vectors()
    assert data["version"] == "1.0.0"
    assert data["encoding"] == "CNBE-32"
    assert "vectors" in data
    assert "invalid_vectors" in data


@pytest.mark.parametrize(
    "vector", load_vectors()["vectors"], ids=lambda v: v["name"]
)
def test_encode_matches_golden_vectors(vector: dict) -> None:
    f = vector["fields"]
    encoded = encode_cnbe(
        radix=f["radix"], stroke=f["stroke"], struct=f["struct"],
        index=f["index"], ext=f["ext"],
    )
    assert encoded.code == vector["code_dec"]
    assert f"0x{encoded.code:08X}" == vector["code_hex"]


@pytest.mark.parametrize(
    "vector", load_vectors()["vectors"], ids=lambda v: v["name"]
)
def test_decode_matches_golden_vectors(vector: dict) -> None:
    decoded = decode_cnbe(vector["code_dec"])
    assert decoded["radix"] == vector["fields"]["radix"]
    assert decoded["stroke"] == vector["fields"]["stroke"]
    assert decoded["struct"] == vector["fields"]["struct"]
    assert decoded["index"] == vector["fields"]["index"]
    assert decoded["ext"] == vector["fields"]["ext"]


@pytest.mark.parametrize(
    "vector", load_vectors()["vectors"], ids=lambda v: v["name"]
)
def test_cnbe32_properties_match_golden_vectors(vector: dict) -> None:
    cnbe = CNBE32(vector["code_dec"])
    assert cnbe.radix == vector["fields"]["radix"]
    assert cnbe.stroke == vector["fields"]["stroke"]
    assert cnbe.struct == vector["fields"]["struct"]
    assert cnbe.index == vector["fields"]["index"]
    assert cnbe.ext == vector["fields"]["ext"]


@pytest.mark.parametrize(
    "vector", load_vectors()["invalid_vectors"], ids=lambda v: v["name"]
)
def test_invalid_golden_vectors_raise(vector: dict) -> None:
    f = vector["fields"]
    with pytest.raises(CNBEValueError):
        encode_cnbe(
            radix=f["radix"], stroke=f["stroke"], struct=f["struct"],
            index=f["index"], ext=f["ext"],
        )
