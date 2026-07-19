from scripts.build_8105_gap_priority_reference_candidates import (
    ALLOWED_STRUCTURES,
    build,
)


def test_priority_reference_candidates_cover_full_gap_queue() -> None:
    candidate_rows, remaining_rows, report = build()

    assert report["overall_status"] == "PASS_8105_GAP_PRIORITY_REFERENCE_CANDIDATES_READY"
    assert report["summary"]["gap_rows"] == 1537
    assert len(candidate_rows) + len(remaining_rows) == 1537
    assert report["summary"]["cihai_hits"] > 0
    assert report["summary"]["wiki_hits"] >= 0


def test_priority_reference_candidates_keep_structure_range_and_no_zdic_default() -> None:
    candidate_rows, remaining_rows, report = build()
    proposed = {row["proposed_structure"] for row in candidate_rows if row["proposed_structure"]}

    assert proposed <= ALLOWED_STRUCTURES
    assert report["checks"]["zdic_not_used_by_default"] is True
    assert all(row["zdic_status"] == "NOT_USED_IN_PRIORITY_DEFAULT_WORKFLOW" for row in candidate_rows + remaining_rows)


def test_priority_reference_candidates_do_not_promote_context_to_source() -> None:
    candidate_rows, remaining_rows, report = build()
    rows = candidate_rows + remaining_rows

    assert report["decision"]["may_write_cnbe_rows"] is False
    assert report["decision"]["may_rebuild_database"] is False
    assert all(row["authority_boundary"] == "REVIEW_CANDIDATE_NOT_NATIONAL_STANDARD" for row in rows)
    assert all(row["cnbe_write_status"] == "NO_CNBE_WRITE" for row in rows)
    assert all(row["database_rebuild_status"] == "NO_DATABASE_REBUILD" for row in rows)


def test_priority_reference_candidates_keep_single_component_rule() -> None:
    candidate_rows, _remaining_rows, _report = build()
    by_char = {row["character"]: row for row in candidate_rows}

    assert by_char["一"]["candidate_rule"] == "standard_side_single_component_identity"
    assert by_char["一"]["proposed_structure"] == "独体字"
    assert by_char["一"]["proposed_decomposition"] == "一"
