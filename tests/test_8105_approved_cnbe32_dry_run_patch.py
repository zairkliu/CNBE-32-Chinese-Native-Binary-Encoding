from scripts.build_8105_approved_cnbe32_dry_run_patch import build


def test_approved_cnbe32_dry_run_counts_and_status() -> None:
    model = build()
    summary = model["summary"]

    assert model["overall_status"] == "PASS_8105_APPROVED_CNBE32_DRY_RUN_READY"
    assert summary["total_rows"] == 8105
    assert summary["dry_run_ready_rows"] == 6712
    assert summary["dry_run_blocked_rows"] == 1393
    assert summary["status_counts"] == {
        "DRY_RUN_BLOCKED": 1393,
        "DRY_RUN_READY": 6712,
    }
    assert summary["block_reason_counts"] == {
        "missing_approved_radical": 964,
        "missing_current_model_row": 276,
        "radical_resolution_blocked": 153,
    }


def test_approved_cnbe32_dry_run_roundtrips_and_preserves_index() -> None:
    model = build()

    assert model["checks"]["all_ready_roundtrips_pass"] is True
    assert model["checks"]["all_ready_use_current_index"] is True
    assert model["checks"]["ready_plus_blocked_equals_total"] is True
    assert model["checks"]["all_blocked_have_reason"] is True


def test_approved_cnbe32_dry_run_known_samples_are_routed() -> None:
    model = build()
    known = model["known_samples"]

    assert known["家"]["status"] == "DRY_RUN_READY"
    assert known["家"]["proposed_struct_name"] == "上下"
    assert known["侵"]["status"] == "DRY_RUN_READY"
    assert known["侵"]["proposed_struct_name"] == "左右"
    assert known["偶"]["status"] == "DRY_RUN_READY"
    assert known["偶"]["proposed_struct_name"] == "左右"
    assert known["孓"]["status"] == "DRY_RUN_READY"
    assert known["孓"]["proposed_struct_name"] == "独体字"
    assert known["冁"]["status"] == "DRY_RUN_BLOCKED"
    assert known["冁"]["block_reason"] == "radical_resolution_blocked"
    assert known["㑇"]["status"] == "DRY_RUN_BLOCKED"
    assert known["㑇"]["block_reason"] == "missing_current_model_row"


def test_approved_cnbe32_dry_run_keeps_no_write_boundary() -> None:
    model = build()

    assert model["decision"]["may_write_data_cnbe32_json"] is False
    assert model["decision"]["may_rebuild_sqlite_database"] is False
    assert model["summary"]["source_table_rows_written"] == 0
    assert model["summary"]["cnbe32_source_rows_written"] == 0
    assert model["summary"]["database_rebuild_allowed"] is False
