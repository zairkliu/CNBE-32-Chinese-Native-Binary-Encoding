from scripts.build_8105_approved_structure_model_merge import build


def test_approved_structure_merge_covers_8105_and_current_model() -> None:
    model = build()
    summary = model["summary"]

    assert model["overall_status"] == "PASS_8105_APPROVED_STRUCTURE_MODEL_MERGE_READY"
    assert summary["total_rows"] == 8105
    assert summary["current_model_rows"] == 21184
    assert summary["current_model_intersection_rows"] == 8105
    assert summary["missing_from_current_model_rows"] == 0
    assert summary["current_model_intersection_rows"] + summary["missing_from_current_model_rows"] == 8105
    assert summary["current_model_confirmed_rows"] == 7613
    assert summary["current_model_structure_repair_candidate_rows"] == 492


def test_approved_structure_merge_has_valid_agent_structure_codes() -> None:
    model = build()

    assert model["checks"]["all_approved_structures_allowed"] is True
    assert model["checks"]["all_approved_structures_have_codes"] is True
    assert model["checks"]["unique_character_count_is_8105"] is True
    assert model["checks"]["unique_unicode_count_is_8105"] is True
    assert model["checks"]["no_unicode_mismatch"] is True


def test_known_regressions_are_marked_for_repair_or_insert() -> None:
    model = build()
    known = model["known_regression_samples"]

    assert known["家"]["approved_agent_structure"] == "上下"
    assert known["家"]["merge_status"] == "CURRENT_MODEL_STRUCTURE_CONFIRMED"
    assert known["侵"]["approved_agent_structure"] == "左右"
    assert known["侵"]["merge_status"] == "CURRENT_MODEL_STRUCTURE_CONFIRMED"
    assert known["偶"]["approved_agent_structure"] == "左右"
    assert known["偶"]["merge_status"] == "CURRENT_MODEL_STRUCTURE_CONFIRMED"
    assert known["冁"]["approved_agent_structure"] == "左右"
    assert known["冁"]["merge_status"] == "CURRENT_MODEL_STRUCTURE_REPAIR_CANDIDATE"
    assert known["孓"]["approved_agent_structure"] == "独体字"
    assert known["孓"]["merge_status"] == "CURRENT_MODEL_STRUCTURE_CONFIRMED"
    assert known["㑇"]["merge_status"] == "CURRENT_MODEL_STRUCTURE_CONFIRMED"


def test_approved_structure_merge_keeps_no_write_boundary() -> None:
    model = build()

    assert model["decision"]["may_write_data_cnbe32_json"] is False
    assert model["decision"]["may_rebuild_database"] is False
    assert model["checks"]["no_source_table_writes"] is True
    assert model["checks"]["no_cnbe32_writes"] is True
    assert model["checks"]["no_database_rebuild"] is True
