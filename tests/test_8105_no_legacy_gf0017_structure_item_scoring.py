from scripts.score_8105_no_legacy_gf0017_structure_items import (
    build_report,
    build_scored_rows,
)


def test_no_legacy_structure_item_scoring_passes() -> None:
    rows = build_scored_rows()
    report = build_report(rows)

    assert report["overall_status"] == "PASS_8105_NO_LEGACY_GF0017_STRUCTURE_ITEM_SCORING"
    assert report["summary"]["scored_rows"] == 100
    assert report["summary"]["rows_with_structure_item_score"] == 86
    assert report["summary"]["rows_without_structure_item_score"] == 14
    assert report["summary"]["score_counts"] == {"6": 14, "32": 86}


def test_no_legacy_structure_item_scoring_keeps_remaining_items_blocked() -> None:
    rows = build_scored_rows()
    report = build_report(rows)

    assert report["decision"]["may_score_component_names"] is False
    assert report["decision"]["may_score_independent_character_rule"] is False
    assert report["decision"]["may_write_cnbe_rows"] is False
    assert report["decision"]["may_rebuild_database"] is False
    for row in rows:
        assert "component_name_validity" in row["remaining_blocked_items"]
        assert "independent_character_rule" in row["remaining_blocked_items"]
        assert "stroke_shape" in row["remaining_blocked_items"]


def test_regression_chars_receive_structure_item_scores() -> None:
    rows = {row["character"]: row for row in build_scored_rows()}

    for char in ("侵", "偶", "冁"):
        assert rows[char]["candidate_structure_label"] == "左右"
        assert rows[char]["assigned_score"] == 32
        assert rows[char]["structure_first_decomposition_score"] == 20
        assert rows[char]["component_validity_score"] == 3
        assert rows[char]["radical_validity_score"] == 3
