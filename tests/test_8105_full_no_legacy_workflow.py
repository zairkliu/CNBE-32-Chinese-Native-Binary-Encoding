from scripts.run_8105_full_no_legacy_workflow import (
    EXPECTED_ROWS,
    build_scoring_report,
    build_scoring_rows,
    build_standardizer_report,
    build_standardizer_rows,
    build_zdic_gap_queue,
)


def test_full_8105_standardizer_covers_all_rows_without_legacy_fields() -> None:
    rows = build_standardizer_rows()
    queue = build_zdic_gap_queue(rows)
    report = build_standardizer_report(rows, queue)

    assert len(rows) == EXPECTED_ROWS
    assert report["overall_status"] == "PASS_8105_FULL_NO_LEGACY_STANDARDIZER_READY"
    assert report["summary"]["review_rows"] == 8105
    assert report["summary"]["complete_candidate_rows"] > 6000
    assert report["summary"]["zdic_gap_queue_rows"] > 0
    assert report["checks"]["no_legacy_fields_present"] is True


def test_full_8105_regression_characters_are_correct() -> None:
    rows = {row["character"]: row for row in build_standardizer_rows()}

    assert rows["侵"]["candidate_structure_label"] == "左右"
    assert rows["侵"]["candidate_decomposition"] == "⿰亻⿳彐冖又"
    assert rows["偶"]["candidate_structure_label"] == "左右"
    assert rows["偶"]["candidate_decomposition"] == "⿰亻禺"
    assert rows["冁"]["candidate_structure_label"] == "左右"
    assert rows["冁"]["candidate_decomposition"] == "⿰单展"


def test_full_8105_structure_scoring_keeps_writes_blocked() -> None:
    rows = build_standardizer_rows()
    standardizer_report = build_standardizer_report(rows, build_zdic_gap_queue(rows))
    scored_rows = build_scoring_rows(rows)
    scoring_report = build_scoring_report(scored_rows, standardizer_report)

    assert scoring_report["overall_status"] == "PASS_8105_FULL_NO_LEGACY_GF0017_STRUCTURE_SCORING"
    assert scoring_report["summary"]["scored_rows"] == 8105
    assert scoring_report["summary"]["rows_with_structure_item_score"] == standardizer_report["summary"]["complete_candidate_rows"]
    assert scoring_report["decision"]["may_write_cnbe_rows"] is False
    assert scoring_report["decision"]["may_rebuild_database"] is False
    assert all(row["cnbe_write_status"] == "NO_CNBE_WRITE" for row in scored_rows)
