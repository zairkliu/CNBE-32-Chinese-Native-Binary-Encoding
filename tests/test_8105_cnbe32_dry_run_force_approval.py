from scripts.force_approve_8105_cnbe32_dry_run_review import build


def test_force_approval_accepts_all_8105_review_rows() -> None:
    model = build()
    summary = model["summary"]

    assert model["overall_status"] == "PASS_8105_CNBE32_DRY_RUN_HUMAN_FORCE_APPROVED"
    assert summary["total_rows"] == 8105
    assert summary["force_approved_rows"] == 8105
    assert summary["original_ready_rows"] == 6712
    assert summary["original_blocked_rows"] == 1393
    assert model["checks"]["all_rows_human_force_approved"] is True


def test_force_approval_preserves_original_blocker_reasons() -> None:
    model = build()

    assert model["summary"]["preserved_block_reason_counts"] == {
        "missing_approved_radical": 964,
        "missing_current_model_row": 276,
        "radical_resolution_blocked": 153,
    }
    assert model["checks"]["original_block_reasons_preserved"] is True


def test_force_approval_routes_known_samples_without_losing_context() -> None:
    model = build()
    known = model["known_samples"]

    assert known["家"]["implementation_queue"] == "CNBE32_READY_WRITE_PLAN_CANDIDATE"
    assert known["侵"]["implementation_queue"] == "CNBE32_READY_WRITE_PLAN_CANDIDATE"
    assert known["偶"]["implementation_queue"] == "CNBE32_READY_WRITE_PLAN_CANDIDATE"
    assert known["孓"]["implementation_queue"] == "CNBE32_READY_WRITE_PLAN_CANDIDATE"
    assert known["冁"]["block_reason"] == "radical_resolution_blocked"
    assert known["㑇"]["block_reason"] == "missing_current_model_row"


def test_force_approval_keeps_no_write_boundary() -> None:
    model = build()

    assert model["decision"]["may_start_next_step_write_plan_design"] is True
    assert model["decision"]["may_write_data_cnbe32_json_now"] is False
    assert model["decision"]["may_rebuild_sqlite_database_now"] is False
    assert model["summary"]["source_table_rows_written"] == 0
    assert model["summary"]["cnbe32_source_rows_written"] == 0
    assert model["summary"]["database_rebuild_allowed"] is False
