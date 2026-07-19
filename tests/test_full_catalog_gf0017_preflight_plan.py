"""Tests for the full-catalog GF0017 preflight plan."""

from __future__ import annotations

from scripts.plan_full_catalog_gf0017_preflight import EXPECTED_HEADERS, build_plan, render_markdown


def test_preflight_plan_accepts_prior_gates_but_blocks_batch_scoring() -> None:
    plan = build_plan()

    assert plan["overall_status"] == "PASS"
    assert plan["pre_gates"]["schema_status"] == "PASS"
    assert plan["pre_gates"]["sample_status"] == "PASS"
    assert plan["pre_gates"]["unicode_identity_status"] == "PASS"
    assert plan["pre_gates"]["agent_runtime_status"] == "PASS"
    assert plan["decision"]["may_start_source_evidence_mapping"] is True
    assert plan["decision"]["may_start_batch_gf0017_scoring"] is False
    assert plan["decision"]["may_rebuild_database"] is False


def test_preflight_plan_maps_all_v4_fixed_headers() -> None:
    plan = build_plan()

    assert plan["workbook"]["headers"] == EXPECTED_HEADERS
    assert plan["workbook"]["column_count"] == 17
    assert plan["workbook"]["data_rows"] == 97686
    assert set(plan["field_mapping"]) == set(EXPECTED_HEADERS)


def test_preflight_plan_maps_all_gf0017_items_to_50_points() -> None:
    plan = build_plan()
    item_ids = {item["id"] for item in plan["gf0017_item_mapping"]}

    assert plan["gf0017_total_points"] == 50
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
    assert all(item["preflight_status"] == "SOURCE_EVIDENCE_REQUIRED" for item in plan["gf0017_item_mapping"])


def test_preflight_plan_preserves_known_source_asset_blockers() -> None:
    plan = build_plan()

    assert len(plan["known_blockers"]) >= 0
    assert plan["next_workflow_status"] in {
        "PREFLIGHT_PLAN_READY_SOURCE_ASSETS_BLOCK_BATCH_SCORING",
        "PREFLIGHT_PLAN_READY_SOURCE_ASSETS_REQUIRE_REVIEW",
    }
    assert plan["decision"]["may_start_batch_gf0017_scoring"] is False


def test_preflight_markdown_states_boundaries() -> None:
    markdown = render_markdown(build_plan())

    assert "# Full Catalog GF0017 Preflight Plan" in markdown
    assert "It does not score rows" in markdown
    assert "Batch GF0017 scoring remains blocked" in markdown
