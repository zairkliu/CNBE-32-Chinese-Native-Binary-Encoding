"""Tests for CNBE research evidence-domain mapping."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.audit_cnbe_research_evidence_domains import (
    build_report,
    domain_status,
    infer_role,
    read_json_shape,
    read_jsonl_shape,
)


def test_infer_role_marks_ocr_as_review_aid() -> None:
    assert infer_role("knowledge/ocr/standards/std_02-汉字部首表_bc1.json") == "ocr_review_aid"


def test_infer_role_marks_source_document() -> None:
    assert infer_role("source/02-汉字部首表/GG 0011-2009 汉字部首表.md") == "converted_source_document"


def test_infer_role_marks_wikipedia_semantic_index() -> None:
    assert infer_role("knowledge/wikipedia-zh-cn-20260501.json") == "encyclopedia_semantic_index"


def test_domain_status_ready_when_all_primary_available() -> None:
    status = domain_status(primary_available=2, primary_total=2, needs_repair=[], domain_id="radical_classification")
    assert status == "READY_FOR_SCHEMA_DESIGN"


def test_domain_status_blocks_without_primary_sources() -> None:
    status = domain_status(primary_available=0, primary_total=2, needs_repair=[], domain_id="component_inventory")
    assert status == "BLOCKED_NO_PRIMARY_SOURCE"


def test_read_json_shape_handles_pdf_conversion_metadata(tmp_path: Path) -> None:
    sample = tmp_path / "source.json"
    sample.write_text(
        json.dumps({"file name": "sample.pdf", "number of pages": 2, "kids": [{"page": 1}, {"page": 2}]}),
        encoding="utf-8",
    )
    shape = read_json_shape(sample)
    assert shape["parse_status"] == "PASS"
    assert shape["kids_count"] == 2


def test_read_jsonl_shape_handles_offline_wikipedia_corpus(tmp_path: Path) -> None:
    sample = tmp_path / "wikipedia.json"
    sample.write_text('{"title": "汉字", "text": "文字体系"}\n{"title": "部首", "text": "检字法"}\n', encoding="utf-8")
    shape = read_jsonl_shape(sample)
    assert shape["parse_status"] == "PASS"
    assert shape["top_type"] == "jsonl"
    assert shape["top_count"] == 2


def test_build_report_keeps_generation_gate_closed(tmp_path: Path) -> None:
    root = tmp_path / "research"
    root.mkdir()
    report = build_report(root)
    assert report["summary"]["encoding_generation_gate"] == "NO_GO"
    assert report["summary"]["sqlite_build_gate"] == "NO_GO"
    assert report["summary"]["domains_total"] >= 8
