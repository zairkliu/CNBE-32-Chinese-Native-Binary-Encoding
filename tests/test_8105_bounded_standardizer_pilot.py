from pathlib import Path

from scripts.run_8105_bounded_standardizer_pilot import (
    COPIED_WORK_TABLE,
    REVIEW_PACKET_CSV,
    build_report,
    build_review_rows,
    render_markdown,
)


def test_8105_bounded_standardizer_builds_100_review_rows() -> None:
    rows = build_review_rows()

    assert len(rows) == 100
    assert all(row["scope"] == "8105_national_standard_core" for row in rows)
    assert all(row["unicode_codepoint"].startswith("U+") for row in rows)


def test_8105_bounded_standardizer_does_not_promote_encoding() -> None:
    rows = build_review_rows()
    report = build_report(rows)

    assert report["overall_status"] == "PASS_8105_BOUNDED_STANDARDIZER_PILOT_REVIEW_PACKET_READY"
    assert report["summary"]["gf0017_new_points_assigned"] == 0
    assert report["summary"]["cnbe_rows_written"] == 0
    assert report["summary"]["database_rebuild_allowed"] is False
    assert report["decision"]["may_assign_more_gf0017_points"] is False
    assert report["decision"]["may_write_cnbe_rows"] is False
    assert all(row["proposed_cnbe32"] == "" for row in rows)
    assert all("legacy_structure_label" not in row for row in rows)
    assert all("legacy_cnbe32" not in row for row in rows)


def test_8105_bounded_standardizer_has_reviewable_candidates() -> None:
    rows = build_review_rows()
    report = build_report(rows)

    assert report["summary"]["rows_with_component_candidates"] > 0
    assert report["summary"]["rows_with_dictionary_context"] > 0
    assert report["summary"]["rows_with_standard_structure_candidates"] > 0
    assert report["summary"]["rows_with_standard_decomposition_candidates"] > 0
    assert "CANDIDATE_COMPONENTS" in " ".join(report["summary"]["candidate_status_counts"])


def test_8105_bounded_standardizer_rejects_legacy_structure_pollution() -> None:
    rows = {row["character"]: row for row in build_review_rows()}

    assert rows["侵"]["candidate_structure_label"] == "左右"
    assert rows["侵"]["candidate_decomposition"] == "⿰亻⿳彐冖又"
    assert rows["偶"]["candidate_structure_label"] == "左右"
    assert rows["偶"]["candidate_decomposition"] == "⿰亻禺"
    assert rows["冁"]["candidate_structure_label"] == "左右"
    assert rows["冁"]["candidate_decomposition"] == "⿰单展"
    for char in ("侵", "偶", "冁"):
        assert "右下包" not in rows[char].values()
        assert "右上包" not in rows[char].values()
        assert "独体字" not in rows[char].values()


def test_8105_bounded_standardizer_markdown_and_outputs_are_bounded() -> None:
    rows = build_review_rows()
    markdown = render_markdown(build_report(rows))

    assert "# 8105 Core Bounded Standardizer Pilot" in markdown
    assert "bounded 100-row candidate review packet" in markdown
    assert str(REVIEW_PACKET_CSV) in markdown
    assert str(COPIED_WORK_TABLE) in markdown
    assert Path(REVIEW_PACKET_CSV).suffix == ".csv"
