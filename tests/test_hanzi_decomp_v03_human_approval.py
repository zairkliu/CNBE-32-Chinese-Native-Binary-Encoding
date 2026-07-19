from scripts.approve_hanzi_decomp_v03_8105_structure_packet import build


def test_human_approved_v03_packet_covers_all_8105_rows() -> None:
    approved, changed, report = build()

    assert report["overall_status"] == "PASS_HUMAN_APPROVED_V03_8105_AGENT_STRUCTURE_PACKET_READY"
    assert len(approved) == 8105
    assert report["checks"]["all_structures_nonblank"] is True
    assert report["checks"]["all_structures_allowed"] is True
    assert report["checks"]["all_structures_have_agent_code"] is True
    assert len(changed) >= 358


def test_jue_is_human_confirmed_independent_character() -> None:
    approved, _changed, report = build()
    by_char = {row["character"]: row for row in approved}

    assert report["checks"]["jue_is_independent"] is True
    assert by_char["孓"]["unicode_codepoint"] == "U+5B53"
    assert by_char["孓"]["candidate_structure_label"] == "独体字"
    assert by_char["孓"]["candidate_decomposition"] == "孓"
    assert by_char["孓"]["agent_struct_type"] == "0"
    assert by_char["孓"]["human_review_basis"] == "HUMAN_CONFIRMED_JUE_U5B53_DUTIZI"


def test_known_legacy_regressions_follow_v03_left_right() -> None:
    approved, _changed, report = build()
    by_char = {row["character"]: row for row in approved}

    assert report["checks"]["known_legacy_regressions_are_left_right"] is True
    for char in ("侵", "偶", "冁"):
        assert by_char[char]["candidate_structure_label"] == "左右"
        assert by_char[char]["agent_struct_type"] == "3"
        assert by_char[char]["human_review_basis"] == "HUMAN_CONFIRMED_HANZI_DECOMP_V03"


def test_human_approved_packet_keeps_no_write_boundary() -> None:
    approved, _changed, report = build()

    assert report["decision"]["may_write_cnbe32"] is False
    assert report["decision"]["may_rebuild_database"] is False
    assert all(row["final_source_table_write_status"] == "NO_SOURCE_TABLE_WRITE" for row in approved)
    assert all(row["final_cnbe32_write_status"] == "NO_CNBE32_WRITE" for row in approved)
    assert all(row["final_database_rebuild_status"] == "NO_DATABASE_REBUILD" for row in approved)
