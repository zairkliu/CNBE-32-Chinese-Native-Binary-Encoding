"""Tests for the CNBE Agent encoding standard and structure localization."""

from __future__ import annotations

from scripts.build_cnbe_agent_encoding_standard import (
    AGENT_ALLOWED_STRUCTURES,
    DEFAULT_CNBE_INPUT,
    LEGACY_STRUCTURE_LOCALIZATION,
    build_agent_standard,
    build_structure_localization,
    render_standard_markdown,
    render_structure_markdown,
)


def test_legacy_structure_localization_covers_all_20902_rows() -> None:
    model = build_structure_localization(DEFAULT_CNBE_INPUT)

    assert model["summary"]["row_count"] == 20902
    assert model["summary"]["legacy_label_count"] == 13
    assert model["summary"]["all_legacy_labels_mapped"] is True
    assert model["summary"]["missing_label_rows"] == 0
    assert sum(model["summary"]["raw_structure_counts"].values()) == 20902


def test_agent_structure_standard_uses_chinese_labels_and_agent_types() -> None:
    model = build_structure_localization(DEFAULT_CNBE_INPUT)
    standard = build_agent_standard(model)

    assert standard["metadata"]["standard_level"] == "agent_standard_aligned_to_8105_not_national_standard"
    assert standard["authority_layers"]["national_standard_baseline"].startswith("8105")
    assert standard["structure_standard"]["allowed_structures"] == AGENT_ALLOWED_STRUCTURES
    assert standard["structure_standard"]["legacy_localization"]["single"]["agent_structure"] == "独体字"
    assert standard["structure_standard"]["legacy_localization"]["left-right"]["agent_struct_type"] == 3


def test_legacy_type_mismatch_is_preserved_as_a_review_signal() -> None:
    model = build_structure_localization(DEFAULT_CNBE_INPUT)

    assert model["summary"]["struct_type_mismatch_after_agent_mapping"] == 12864
    left_right = next(item for item in model["mapping"] if item["legacy_structure"] == "left-right")
    assert left_right["legacy_struct_type"] == 1
    assert left_right["agent_struct_type"] == 3
    assert left_right["standard_level"] == "agent_standard_mapping_not_national_standard"


def test_standard_markdown_states_agent_not_national_standard() -> None:
    structure = build_structure_localization(DEFAULT_CNBE_INPUT)
    standard = build_agent_standard(structure)

    standard_md = render_standard_markdown(standard)
    structure_md = render_structure_markdown(structure)

    assert "not a national-standard document" in standard_md
    assert "AGENT_STANDARD_MAPPING" in standard_md
    assert "agent_standard_mapping_not_national_standard" in structure_md


def test_legacy_mapping_has_expected_confidence_tiers() -> None:
    assert LEGACY_STRUCTURE_LOCALIZATION["single"]["confidence"] == 1.0
    assert LEGACY_STRUCTURE_LOCALIZATION["top-left-wrap"]["confidence"] == 0.85
    assert LEGACY_STRUCTURE_LOCALIZATION["left-wrap"]["confidence"] == 0.75
    assert LEGACY_STRUCTURE_LOCALIZATION["triangle"]["confidence"] == 0.65
