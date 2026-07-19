from scripts.apply_8105_gap_auto_fill_candidates import (
    ALLOWED_STRUCTURES,
    FORBIDDEN_LEGACY_STRUCTURES,
    build_candidates,
)


def test_gap_auto_fill_candidates_account_for_all_gap_rows() -> None:
    auto_rows, remaining_rows, report = build_candidates()

    assert report["overall_status"] == "PASS_8105_GAP_AUTO_FILL_CANDIDATES_READY"
    assert report["summary"]["gap_rows"] == 1537
    assert len(auto_rows) + len(remaining_rows) == 1537
    assert report["summary"]["auto_fill_candidate_rows"] > 0
    assert report["summary"]["remaining_review_rows"] > 0


def test_gap_auto_fill_structures_stay_inside_allowed_set() -> None:
    auto_rows, _remaining_rows, report = build_candidates()
    proposed = {row["proposed_structure"] for row in auto_rows if row["proposed_structure"]}

    assert proposed <= ALLOWED_STRUCTURES
    assert not (proposed & FORBIDDEN_LEGACY_STRUCTURES)
    assert report["checks"]["proposed_structures_allowed"] is True
    assert report["checks"]["forbidden_legacy_structures_absent"] is True


def test_gap_auto_fill_keeps_review_only_no_write_boundary() -> None:
    auto_rows, remaining_rows, report = build_candidates()
    rows = auto_rows + remaining_rows

    assert report["decision"]["may_write_cnbe_rows"] is False
    assert report["decision"]["may_rebuild_database"] is False
    assert all(row["authority_boundary"] == "AGENT_REVIEW_CANDIDATE_NOT_NATIONAL_STANDARD" for row in rows)
    assert all(row["cnbe_write_status"] == "NO_CNBE_WRITE" for row in rows)
    assert all(row["database_rebuild_status"] == "NO_DATABASE_REBUILD" for row in rows)


def test_gap_auto_fill_handles_single_component_identity_safely() -> None:
    auto_rows, _remaining_rows, _report = build_candidates()
    by_char = {row["character"]: row for row in auto_rows}

    assert by_char["一"]["fill_rule"] == "single_component_identity_decomposition"
    assert by_char["一"]["proposed_structure"] == "独体字"
    assert by_char["一"]["proposed_decomposition"] == "一"
    assert by_char["一"]["blocker"] == "REVIEW_REQUIRED_BEFORE_MERGE"
