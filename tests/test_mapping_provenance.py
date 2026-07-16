"""Tests for mapping provenance helpers."""

from __future__ import annotations

from scripts.audit_mapping_provenance import expected_sdk_fields, sha256_bytes


def test_expected_sdk_fields_first_row() -> None:
    fields = expected_sdk_fields(0x4E00)
    assert fields == {
        "cnbe": 0x01080000,
        "radical": 1,
        "strokes": 1,
        "struct_type": 0,
        "idx": 0,
    }


def test_expected_sdk_fields_second_row() -> None:
    fields = expected_sdk_fields(0x4E01)
    assert fields == {
        "cnbe": 0x02108010,
        "radical": 2,
        "strokes": 2,
        "struct_type": 1,
        "idx": 1,
    }


def test_sdk_index_wraps_at_2048() -> None:
    assert expected_sdk_fields(0x4E00 + 2047)["idx"] == 2047
    assert expected_sdk_fields(0x4E00 + 2048)["idx"] == 0


def test_sha256_bytes_is_stable() -> None:
    assert sha256_bytes(b"CNBE-32") == "517f14fcdae97288e2d9e22978415d856e6d5027e609d6f37d7ab4cba9609066"
