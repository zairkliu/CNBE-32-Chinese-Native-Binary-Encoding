"""Tests for the local CNBE research source audit helpers."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

from scripts.audit_cnbe_research_sources import (
    build_report,
    count_unicode_label_issues,
    inspect_zip,
    source_status,
)


def test_count_unicode_label_issues_detects_extra_padding() -> None:
    rows = [
        {"char": "一", "unicode": "U+04E00"},
        {"char": "丁", "unicode": "U+4E01"},
    ]
    result = count_unicode_label_issues(rows)
    assert result["count"] == 1
    assert result["samples"][0]["expected"] == "U+4E00"


def test_source_status_marks_attention_for_count_delta() -> None:
    result = {
        "identity_status": "PASS",
        "json": {"target_count_status": "FAIL"},
        "domain": {"target_8105_delta": 1},
    }
    assert source_status(result) == "ATTENTION"


def test_inspect_zip_accepts_valid_archive(tmp_path: Path) -> None:
    archive = tmp_path / "sample.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("sample.txt", "CNBE")
    result = inspect_zip(archive)
    assert result["status"] == "PASS"
    assert result["member_count"] == 1


def test_build_report_keeps_encoding_gate_closed(tmp_path: Path) -> None:
    source_root = tmp_path / "research"
    source_root.mkdir()
    payload = source_root / "sample.json"
    payload.write_text(json.dumps({"一": {"char": "一", "unicode": "U+04E00"}}), encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "source_root": str(source_root),
                "sources": [
                    {
                        "id": "generic_reference",
                        "relative_path": "sample.json",
                        "kind": "standard_character_table",
                        "size_bytes": payload.stat().st_size,
                        "sha256": "bad-hash",
                        "expected": {"type": "dict", "target_count": 8105},
                        "acceptance": "needs_count_reconciliation",
                    }
                ],
                "directories": [],
                "excluded_sources": [],
            }
        ),
        encoding="utf-8",
    )
    report = build_report(manifest)
    assert report["summary"]["encoding_generation_gate"] == "NO_GO"
    assert report["summary"]["sdk_replacement_allowed"] is False


def test_build_report_marks_review_required_without_action_items(tmp_path: Path) -> None:
    source_root = tmp_path / "research"
    source_root.mkdir()
    payload = source_root / "sample.json"
    payload.write_text(json.dumps({"一": {"char": "一", "unicode": "U+4E00"}}), encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "source_root": str(source_root),
                "sources": [
                    {
                        "id": "generic_reference",
                        "relative_path": "sample.json",
                        "kind": "standard_character_table",
                        "size_bytes": payload.stat().st_size,
                        "sha256": __import__("hashlib").sha256(payload.read_bytes()).hexdigest(),
                        "expected": {"type": "dict"},
                        "acceptance": "identity_source",
                    }
                ],
                "directories": [],
                "excluded_sources": [
                    {
                        "relative_path": "legacy.zip",
                        "reason": "excluded legacy artifact",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    report = build_report(manifest)
    assert report["summary"]["status"] == "PASS"
    assert report["summary"]["encoding_generation_gate"] == "REVIEW_REQUIRED"
    assert report["summary"]["sqlite_build_allowed"] is False
