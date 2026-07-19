"""Tests for the full-catalog GF0017 source mapping."""

from __future__ import annotations

from scripts.map_full_catalog_gf0017_sources import build_source_mapping, render_markdown


def test_source_mapping_covers_all_gf0017_items_and_points() -> None:
    mapping = build_source_mapping()
    item_ids = {item["id"] for item in mapping["items"]}

    assert mapping["overall_status"] == "PASS"
    assert mapping["summary"]["gf0017_items"] == 8
    assert mapping["summary"]["gf0017_total_points"] == 50
    assert item_ids == {
        "character_set_coverage",
        "stroke_shape",
        "stroke_order",
        "component_validity",
        "component_name_validity",
        "radical_validity",
        "independent_character_rule",
        "structure_first_decomposition",
    }


def test_source_mapping_preserves_source_gap_and_required_evidence_statuses() -> None:
    mapping = build_source_mapping()
    counts = mapping["summary"]["source_status_counts"]

    assert counts["SOURCE_GAP"] == 2
    assert counts["SOURCE_EVIDENCE_REQUIRED"] == 6
    assert mapping["summary"]["missing_controlling_sources"] == 0


def test_source_mapping_keeps_batch_scoring_blocked() -> None:
    mapping = build_source_mapping()

    assert mapping["decision"]["may_start_schema_join_design"] is True
    assert mapping["decision"]["may_start_batch_gf0017_scoring"] is False
    assert mapping["decision"]["may_rebuild_database"] is False
    assert mapping["authority_boundary"]["does_not_score_rows"] is True


def test_source_mapping_confirms_no_open_knowledge_blockers() -> None:
    mapping = build_source_mapping()

    assert mapping["summary"]["knowledge_blockers"] == 0
    assert mapping["known_blockers"] == []


def test_source_mapping_markdown_states_boundaries() -> None:
    markdown = render_markdown(build_source_mapping())

    assert "# Full Catalog GF0017 Source Mapping" in markdown
    assert "It is read-only" in markdown
    assert "Batch GF0017 scoring remains blocked" in markdown
