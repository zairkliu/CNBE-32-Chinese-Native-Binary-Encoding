from scripts.materialize_8105_initial_auto_filled_packet import (
    ALLOWED_STRUCTURES,
    build,
)


def test_initial_auto_filled_packet_preserves_8105_row_count() -> None:
    packet, filled_rows, remaining_rows, report = build()

    assert report["overall_status"] == "PASS_8105_INITIAL_AUTO_FILLED_PROJECT_READY"
    assert len(packet) == 8105
    assert len(filled_rows) == 30
    assert len(remaining_rows) == 1507
    assert report["summary"]["initial_review_ready_rows"] == 6598


def test_initial_auto_filled_packet_keeps_allowed_structure_set() -> None:
    packet, _filled_rows, _remaining_rows, report = build()
    structures = {row["candidate_structure_label"] for row in packet if row["candidate_structure_label"]}

    assert structures <= ALLOWED_STRUCTURES
    assert report["checks"]["all_structures_allowed_or_blank"] is True


def test_initial_auto_filled_packet_keeps_no_write_boundary() -> None:
    packet, _filled_rows, _remaining_rows, report = build()

    assert report["decision"]["may_write_cnbe_rows"] is False
    assert report["decision"]["may_rebuild_database"] is False
    assert all(row["initial_cnbe_write_status"] == "NO_CNBE_WRITE" for row in packet)
    assert all(row["initial_database_rebuild_status"] == "NO_DATABASE_REBUILD" for row in packet)


def test_initial_auto_filled_packet_materializes_yuanliu_xiao_components() -> None:
    packet, _filled_rows, _remaining_rows, _report = build()
    by_char = {row["character"]: row for row in packet}

    assert by_char["肖"]["initial_fill_status"] == "APPLIED_TO_REVIEW_PACKET"
    assert by_char["肖"]["candidate_structure_label"] == "上下"
    assert by_char["肖"]["candidate_decomposition"] == "⿱⺌⺼"
    assert by_char["肖"]["direct_component_candidates"] == "⺌ ⺼"
    assert by_char["肖"]["initial_source_priority"] == "yuanliu_core_reference"
