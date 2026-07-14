"""Tests for the Hanzi standard learning packet builder."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.build_hanzi_standard_learning import (
    ALLOWED_STRUCTURES,
    SPECIAL_STRUCTURE,
    TERM_RULES,
    build_learning_model,
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
    terms = {
        "required_terms": [
            {
                "id": term_id,
                "zh": term_id,
                "definition": term_id,
                "evidence_domain": "domain",
                "primary_sources": [],
                "supporting_sources": [],
            }
            for term_id in TERM_RULES
        ]
    }
    real_standards = json.loads(
        Path("/Users/liuzhaoqi/Documents/cnbe-research/cnbe-hanzi-knowledge-builder/references/national_standard_files.json")
        .read_text(encoding="utf-8")
    )
    model = build_learning_model(terms, real_standards)
    assert model["summary"]["encoding_generation_gate"] == "NO_GO"
    assert model["summary"]["sqlite_build_gate"] == "NO_GO"
