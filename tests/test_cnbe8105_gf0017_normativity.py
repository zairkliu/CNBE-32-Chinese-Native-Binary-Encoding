"""Tests for the GF0017 50-point CNBE normativity scoring report."""

from __future__ import annotations

from pathlib import Path

from scripts.score_cnbe8105_gf0017_normativity import (
    DEFAULT_COMPARISON_INPUT,
    DEFAULT_MODEL_INPUT,
    RESEARCH_ROOT,
    build_outputs,
)


def test_gf0017_scoring_outputs_8105_rows_and_50_point_model() -> None:
    scores, markdown = build_outputs(DEFAULT_MODEL_INPUT, DEFAULT_COMPARISON_INPUT, RESEARCH_ROOT)

    assert scores["metadata"]["model_id"] == "gf0017_cnbe50_normativity_v1"
    assert scores["metadata"]["model_total_points"] == 50
    assert scores["summary"]["row_count"] == 8105
    assert scores["summary"]["min_score"] is not None
    assert scores["summary"]["max_score"] <= 50
    assert "# CNBE8105 GF0017 Normativity Score Report" in markdown


def test_gf0017_score_items_match_model_fields() -> None:
    scores, _ = build_outputs(DEFAULT_MODEL_INPUT, DEFAULT_COMPARISON_INPUT, RESEARCH_ROOT)
    row = scores["characters"]["家"]

    assert set(row["items"]) == {
        "character_set_coverage",
        "stroke_shape",
        "stroke_order",
        "component_validity",
        "component_name_validity",
        "radical_validity",
        "independent_character_rule",
        "structure_first_decomposition",
    }
    assert sum(item["max_points"] for item in row["items"].values()) == 50
    assert sum(item["score"] for item in row["items"].values()) == row["score"]


def test_known_cnbe32_field_repair_candidates_are_scored() -> None:
    scores, _ = build_outputs(DEFAULT_MODEL_INPUT, DEFAULT_COMPARISON_INPUT, RESEARCH_ROOT)
    characters = scores["characters"]

    assert characters["家"]["repair_class"] == "CNBE32_FIELD_REPAIR_CANDIDATE"
    assert characters["家"]["standard_snapshot"]["radical"] == "宀"
    assert characters["家"]["standard_snapshot"]["stroke_count"] == 10
    assert characters["家"]["standard_snapshot"]["structure"] == "上下"

    assert characters["涡"]["repair_class"] == "CNBE32_FIELD_REPAIR_CANDIDATE"
    assert characters["涡"]["standard_snapshot"]["radical"] == "氵"
    assert characters["涡"]["standard_snapshot"]["structure"] == "左右"


def test_review_required_and_source_gap_statuses_are_preserved() -> None:
    scores, _ = build_outputs(DEFAULT_MODEL_INPUT, DEFAULT_COMPARISON_INPUT, RESEARCH_ROOT)
    characters = scores["characters"]

    assert characters["与"]["overall_status"] == "REVIEW_REQUIRED"
    assert characters["与"]["repair_class"] == "HUMAN_REVIEW_REQUIRED"
    assert "ambiguous_decomposition" in characters["与"]["issues"]

    family = characters["家"]["items"]
    assert family["character_set_coverage"]["status"] == "SOURCE_GAP"
    assert family["stroke_shape"]["status"] == "SOURCE_GAP"


def test_generated_report_files_are_read_only_outputs() -> None:
    assert Path("evidence/gf0017/cnbe8105_gf0017_normativity_scores.json").suffix == ".json"
    assert Path("evidence/gf0017/CNBE8105_GF0017_NORMATIVITY_SCORE_REPORT.md").suffix == ".md"
