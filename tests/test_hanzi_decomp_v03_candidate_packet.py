from scripts.materialize_hanzi_decomp_v03_8105_candidate_packet import build


def test_v03_candidate_packet_materializes_all_8105_rows() -> None:
    packet, applied, remaining_blank, report = build()

    assert report["overall_status"] == "PASS_HANZI_DECOMP_V03_STRUCTURE_CODE_PACKET_READY"
    assert len(packet) == 8105
    assert len(applied) == 1243
    assert len(remaining_blank) == 1
    assert report["summary"]["structure_code_candidate_rows"] == 8104


def test_v03_candidate_packet_applies_gap_fill_without_overwriting_conflicts() -> None:
    packet, applied, _remaining_blank, report = build()
    by_char = {row["character"]: row for row in packet}
    applied_chars = {row["character"] for row in applied}

    assert "㑇" in applied_chars
    assert by_char["㑇"]["candidate_structure_label"] == "左右"
    assert by_char["㑇"]["candidate_decomposition"] == "⿰亻刍"
    assert by_char["㑇"]["agent_struct_type"] == "3"
    assert by_char["修"]["v03_tool_status"] == "TOOL_CONFLICT_REVIEW_REQUIRED"
    assert by_char["修"]["v03_materialize_status"] == "UNCHANGED"
    assert report["checks"]["conflict_rows_not_applied"] is True


def test_v03_candidate_packet_has_structure_codes_for_nonblank_rows() -> None:
    packet, _applied, _remaining_blank, report = build()

    assert report["checks"]["all_nonblank_structures_have_code"] is True
    assert all(row["agent_struct_type"] != "" for row in packet if row["candidate_structure_label"])


def test_v03_candidate_packet_keeps_no_write_boundary() -> None:
    packet, _applied, _remaining_blank, report = build()

    assert report["decision"]["may_write_cnbe32"] is False
    assert report["decision"]["may_rebuild_database"] is False
    assert all(row["cnbe32_write_status"] == "NO_CNBE32_WRITE" for row in packet)
    assert all(row["database_rebuild_status"] == "NO_DATABASE_REBUILD" for row in packet)
