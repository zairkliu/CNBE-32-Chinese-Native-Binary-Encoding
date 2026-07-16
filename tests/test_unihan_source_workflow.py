"""Tests for pinned Unihan source and full-catalog reproduction helpers."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from scripts.fetch_unihan_source import load_manifest, validate_url, verify_archive
from scripts.reproduce_full_catalog_audit import field_evidence_matrix, status_from_bool


def test_pinned_unihan_manifest_is_https_allowlisted() -> None:
    manifest = load_manifest(Path("data/sources/unihan-17.0.0.json"))
    assert validate_url(manifest) == "https://www.unicode.org/Public/17.0.0/ucd/Unihan.zip"
    assert manifest["size_bytes"] == 8518517
    assert manifest["sha256"] == "f7a48b2b545acfaa77b2d607ae28747404ce02baefee16396c5d2d7a8ef34b5e"


def test_verify_archive_reports_failures_without_writing(tmp_path: Path) -> None:
    archive = tmp_path / "Unihan.zip"
    archive.write_bytes(b"not the archive")
    manifest = {
        "official_url": "https://www.unicode.org/Public/17.0.0/ucd/Unihan.zip",
        "allowed_hosts": ["www.unicode.org"],
        "size_bytes": 8518517,
        "sha256": hashlib.sha256(b"real archive").hexdigest(),
    }
    result = verify_archive(archive, manifest)
    assert result["status"] == "FAIL"
    assert result["size_bytes"] == len(b"not the archive")


def test_verify_archive_requires_existing_file(tmp_path: Path) -> None:
    manifest = load_manifest(Path("data/sources/unihan-17.0.0.json"))
    with pytest.raises(ValueError, match="archive not found"):
        verify_archive(tmp_path / "missing.zip", manifest)


def test_reproduction_report_field_evidence_keeps_structure_heuristic() -> None:
    matrix = {item["field"]: item for item in field_evidence_matrix()}
    assert matrix["radical"]["classification"] == "upstream_derived"
    assert matrix["strokes"]["classification"] == "upstream_derived_with_31_clamp"
    assert matrix["struct_type"]["classification"] == "heuristic_derived"
    assert "not semantic authority" in matrix["struct_type"]["boundary"]


def test_status_from_bool() -> None:
    assert status_from_bool(True) == "PASS"
    assert status_from_bool(False) == "FAIL"
