"""Tests for the 20,902-row CNBE agent pre-encoding pressure test."""

from __future__ import annotations

from scripts.run_cnbe20902_agent_preencoding_test import (
    DEFAULT_CNBE_INPUT,
    DEFAULT_GF0017_SCORES,
    build_outputs,
)


def test_agent_preencoding_scans_full_repository_table() -> None:
    report, checkpoint, markdown = build_outputs(DEFAULT_CNBE_INPUT, DEFAULT_GF0017_SCORES)

    assert report["metadata"]["agent_skill"] == "cnbe-hanzi-structure-encoding-agent"
    assert report["summary"]["row_count"] == 20902
    assert report["summary"]["unique_chars"] == 20902
    assert report["summary"]["unique_codepoints"] == 20902
    assert report["summary"]["duplicate_chars"] == 0
    assert report["summary"]["duplicate_codepoints"] == 0
    assert checkpoint["last_verified_offset"] == 20901
    assert checkpoint["resume_from"] == 20902
    assert "# CNBE 20,902 Agent Pre-Encoding Test" in markdown


def test_unicode_first_gate_passes_for_repository_table() -> None:
    report, _, _ = build_outputs(DEFAULT_CNBE_INPUT, DEFAULT_GF0017_SCORES)

    assert report["summary"]["unicode_status_counts"] == {"PASS": 20902}
    assert report["summary"]["first_blocker_offset"] is None
    assert report["summary"]["first_blocker_char"] is None


def test_legacy_structure_labels_are_localized_but_not_silently_accepted() -> None:
    report, _, _ = build_outputs(DEFAULT_CNBE_INPUT, DEFAULT_GF0017_SCORES)

    assert report["summary"]["structure_source_counts"] == {"english_alias": 20902}
    assert report["summary"]["issue_counts"]["structure_label_requires_localization"] == 20902
    assert report["records"][0]["knowledge_schema_gate"]["current_structure_raw"] == "single"
    assert report["records"][0]["knowledge_schema_gate"]["current_structure_normalized"] == "独体字"


def test_agent_exposes_gf0017_scope_gap_for_non_8105_rows() -> None:
    report, _, _ = build_outputs(DEFAULT_CNBE_INPUT, DEFAULT_GF0017_SCORES)

    assert report["summary"]["issue_counts"]["outside_8105_gf0017_score_scope"] == 13073
    assert report["summary"]["agent_status_counts"]["EVIDENCE_GAP"] == 14042
    assert report["summary"]["agent_status_counts"]["HUMAN_REVIEW_REQUIRED"] == 292
    assert report["summary"]["agent_status_counts"]["SOURCE_GAP"] == 2510


def test_cnbe32_bitfield_review_is_separate_from_unicode_identity() -> None:
    report, _, _ = build_outputs(DEFAULT_CNBE_INPUT, DEFAULT_GF0017_SCORES)

    assert report["summary"]["bitfield_status_counts"]["PASS"] == 8038
    assert report["summary"]["bitfield_status_counts"]["REVIEW_REQUIRED"] == 12864
    assert report["summary"]["issue_counts"]["struct_type_name_mismatch_after_normalization"] == 12864
