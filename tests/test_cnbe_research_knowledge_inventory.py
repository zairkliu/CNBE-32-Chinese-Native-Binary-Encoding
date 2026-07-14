"""Tests for the cnbe-research knowledge asset inventory."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

from scripts.inventory_cnbe_research_knowledge import (
    asset_flags,
    build_inventory,
    classify_asset,
    inspect_zip,
    read_text_traits,
)


def test_classify_asset_marks_primary_candidate() -> None:
    category = classify_asset("structured/base_character_data.json", ".json")
    assert category == "primary_candidate"


def test_classify_asset_marks_ocr_subdirectories() -> None:
    assert classify_asset("ocr/ci_hai/page_001.json", ".json") == "ocr_cihai_review_aid"
    assert classify_asset("ocr/standards/page_001.json", ".json") == "ocr_standard_review_aid"
    assert classify_asset("ocr/page_001.json", ".json") == "ocr_review_aid"


def test_read_text_traits_detects_crlf(tmp_path: Path) -> None:
    sample = tmp_path / "sample.json"
    sample.write_bytes(b'{"a": 1}\r\n')
    traits = read_text_traits(sample)
    assert traits["utf8_status"] == "PASS"
    assert traits["contains_crlf"] is True
    assert traits["line_count"] == 1


def test_inspect_zip_accepts_valid_archive(tmp_path: Path) -> None:
    archive = tmp_path / "sample.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("sample.txt", "CNBE")
    result = inspect_zip(archive)
    assert result["status"] == "PASS"
    assert result["member_count"] == 1


def test_inspect_zip_rejects_invalid_archive(tmp_path: Path) -> None:
    archive = tmp_path / "bad.zip"
    archive.write_text("not a zip", encoding="utf-8")
    result = inspect_zip(archive)
    assert result["status"] == "FAIL"


def test_asset_flags_marks_count_mismatch() -> None:
    details = {
        "relative_path": "structured/base_character_data.json",
        "category": "primary_candidate",
        "size_bytes": 10,
        "json": {"parse_status": "PASS", "top_type": "dict", "top_count": 8104},
        "expected_checks": {
            "top_type_status": "PASS",
            "count_status": "FAIL",
        },
    }
    assert "count_mismatch" in asset_flags(details)


def test_build_inventory_keeps_gates_closed_for_count_mismatch(tmp_path: Path) -> None:
    knowledge = tmp_path / "knowledge"
    structured = knowledge / "structured"
    structured.mkdir(parents=True)
    (structured / "base_character_data.json").write_text(
        json.dumps({"一": {"char": "一", "unicode": "U+4E00"}}),
        encoding="utf-8",
    )
    archive = knowledge / "Unihan2.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("Unihan_Readings.txt", "U+4E00\tkMandarin\tyi\n")
    inventory = build_inventory(knowledge)
    assert inventory["summary"]["total_files"] == 2
    assert inventory["gates"]["encoding_generation_gate"] == "NO_GO"
    assert inventory["gates"]["sdk_replacement_allowed"] is False
    assert any(item["asset"] == "structured/base_character_data.json" for item in inventory["action_items"])
