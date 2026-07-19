from scripts.build_8105_cnbe32_copied_dataset_write_plan import build


def test_copied_dataset_write_plan_preserves_source_shape() -> None:
    model = build()
    summary = model["summary"]

    assert model["overall_status"] == "PASS_8105_CNBE32_COPIED_DATASET_WRITE_PLAN_READY"
    assert summary["source_rows"] == 20902
    assert summary["copy_rows"] == 20902
    assert summary["patch_rows_in_copy"] == 6712
    assert summary["force_approved_not_patched_rows"] == 1393
    assert model["checks"]["source_row_count_preserved"] is True


def test_copied_dataset_write_plan_keeps_patch_and_blocked_queues() -> None:
    model = build()

    assert model["checks"]["patch_rows_match_ready_rows"] is True
    assert model["checks"]["blocked_rows_match_force_blocked_rows"] is True
    assert model["summary"]["blocked_reason_counts"] == {
        "missing_approved_radical": 964,
        "missing_current_model_row": 276,
        "radical_resolution_blocked": 153,
    }


def test_copied_dataset_known_samples_are_routed() -> None:
    model = build()
    known_patch = model["samples"]["known_patch_rows"]
    known_blocked = model["samples"]["known_blocked_rows"]

    assert known_patch["家"]["proposed_struct_name"] == "上下"
    assert known_patch["侵"]["proposed_struct_name"] == "左右"
    assert known_patch["偶"]["proposed_struct_name"] == "左右"
    assert known_patch["孓"]["proposed_struct_name"] == "独体字"
    assert known_blocked["冁"]["block_reason"] == "radical_resolution_blocked"
    assert known_blocked["㑇"]["block_reason"] == "missing_current_model_row"
    assert all(model["checks"]["known_samples_routed"].values())


def test_copied_dataset_write_plan_is_copy_only() -> None:
    model = build()

    assert model["checks"]["source_dataset_not_modified_by_script"] is True
    assert model["checks"]["all_patch_rows_preserve_index"] is True
    assert model["checks"]["all_patch_rows_write_to_copy_only"] is True
    assert model["decision"]["may_promote_copy_to_source_table_now"] is False
    assert model["decision"]["may_rebuild_sqlite_database_now"] is False
    assert model["summary"]["source_table_rows_written"] == 0
    assert model["summary"]["database_rebuild_allowed"] is False
