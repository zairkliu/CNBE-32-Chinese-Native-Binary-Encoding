"""Tests for the Hanzi standard learning packet builder."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.build_hanzi_standard_learning import (
    ALLOWED_STRUCTURES,
    SPECIAL_STRUCTURE,
    TERM_RULES,
    markdown_table,
    render_structures,
)


def test_allowed_structure_set_matches_policy() -> None:
    names = {item["name"] for item in ALLOWED_STRUCTURES}
    assert names == {
        "上下",
        "上中下",
        "左右",
        "左中右",
        "左上包",
        "右上包",
        "左三包",
        "左下包",
        "上三包",
        "下三包",
        "全包围",
        "镶嵌",
    }
    assert SPECIAL_STRUCTURE["name"] == "独体字"
    assert "右下包" not in names


def test_term_rules_cover_all_required_knowledge_items() -> None:
    assert set(TERM_RULES) == {
        "stroke",
        "stroke_shape",
        "stroke_order",
        "hanzi_component",
        "character_component",
        "non_character_component",
        "basic_component",
        "radical",
        "side_component",
        "glyph_form",
        "single_component_character",
        "hanzi_structure",
        "decomposition_method",
    }


def test_markdown_table_renders_headers() -> None:
    table = markdown_table(["A", "B"], [[1, "x"]])
    assert "| A | B |" in table
    assert "| 1 | x |" in table


def test_render_structures_marks_forbidden_labels() -> None:
    text = render_structures({"allowed_structures": ALLOWED_STRUCTURES, "special_structure": SPECIAL_STRUCTURE})
    assert "品字形" in text
    assert "三叠结构" in text
    assert "独体字" in text


def test_build_learning_model_keeps_generation_gate_closed() -> None:
    model = json.loads(Path("reports/hanzi_standard_learning_audit.json").read_text(encoding="utf-8"))
    assert model["summary"]["encoding_generation_gate"] == "NO_GO"
    assert model["summary"]["sqlite_build_gate"] == "NO_GO"


def test_committed_learning_audit_preserves_standard_scope() -> None:
    model = json.loads(Path("reports/hanzi_standard_learning_audit.json").read_text(encoding="utf-8"))

    assert model["summary"]["required_terms"] == len(TERM_RULES)
    assert model["summary"]["national_standards"] == 17
    assert model["summary"]["allowed_structures"] == len(ALLOWED_STRUCTURES)
    assert model["summary"]["special_structure"] == "独体字"
    assert model["validation_issues"] == []


def test_committed_learning_audit_keeps_no_write_mode() -> None:
    model = json.loads(Path("reports/hanzi_standard_learning_audit.json").read_text(encoding="utf-8"))

    assert model["audit_mode"] == "read_only_hanzi_standard_learning"
    assert model["next_stage"] == "human_reading_review_then_schema_pilot"
    assert {term["id"] for term in model["terms"]} == set(TERM_RULES)
