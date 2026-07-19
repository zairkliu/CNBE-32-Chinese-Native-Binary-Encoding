from scripts.plan_8105_runtime_blocker_resolution import build, render_markdown


def test_runtime_blocker_resolution_plan_preserves_blocker_counts() -> None:
    model = build()
    summary = model["summary"]
    assert model["overall_status"] == "PASS_8105_RUNTIME_BLOCKER_RESOLUTION_PLAN_READY"
    assert summary["total_blocked_rows"] == 1393
    assert summary["block_reason_counts"] == {
        "missing_approved_radical": 964,
        "missing_current_model_row": 276,
        "radical_resolution_blocked": 153,
    }


def test_runtime_blocker_resolution_plan_keeps_writes_blocked() -> None:
    model = build()
    assert model["summary"]["source_table_rows_written"] == 0
    assert model["summary"]["database_rebuild_allowed"] is False
    assert model["decision"]["may_write_source_table_now"] is False
    assert model["decision"]["may_rebuild_sqlite_now"] is False
    assert model["metadata"]["write_gate"] == "NO_SOURCE_TABLE_WRITE_NO_DATABASE_REBUILD"


def test_runtime_blocker_resolution_plan_routes_known_rows() -> None:
    known = build()["samples"]["known_rows"]
    assert known["㑇"]["resolution_class"] == "requires_index_allocation_and_source_row_insertion_plan"
    assert known["㑇"]["source_model_presence"] == "missing"
    assert known["冁"]["resolution_class"] == "requires_component_to_radical_policy_review"
    assert known["刁"]["resolution_class"] == "requires_radical_alias_extension_review"
    assert known["队"]["resolution_class"] == "requires_position_sensitive_radical_rule"
    assert known["玕"]["resolution_class"] == "requires_standard_radical_and_stroke_join"


def test_runtime_blocker_resolution_markdown_states_boundary() -> None:
    markdown = render_markdown(build())
    assert "# 8105 Runtime Blocker Resolution Plan" in markdown
    assert "Source-table rows written: 0" in markdown
    assert "does not change `data/cnbe32.json`" in markdown
    assert "requires_position_sensitive_radical_rule" in markdown
