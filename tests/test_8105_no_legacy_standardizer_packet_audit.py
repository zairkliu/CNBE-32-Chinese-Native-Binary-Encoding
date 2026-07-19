from scripts.audit_8105_no_legacy_standardizer_packet import (
    REGRESSION_CHARS,
    build_audit,
)


def test_no_legacy_packet_audit_passes() -> None:
    report, recheck_rows = build_audit()

    assert report["overall_status"] == "PASS_8105_NO_LEGACY_STANDARDIZER_PACKET_AUDIT"
    assert report["summary"]["packet_rows"] == 100
    assert report["summary"]["forbidden_field_count"] == 0
    assert report["summary"]["pollution_hit_count"] == 0
    assert report["summary"]["candidate_standard_mismatch_count"] == 0
    assert report["summary"]["regression_failure_count"] == 0
    assert len(recheck_rows) > 0


def test_no_legacy_packet_keeps_scoring_and_writes_blocked() -> None:
    report, _recheck_rows = build_audit()

    assert report["decision"]["may_assign_gf0017_structure_points"] is False
    assert report["decision"]["may_write_cnbe_rows"] is False
    assert report["decision"]["may_rebuild_database"] is False


def test_no_legacy_packet_recheck_includes_regression_chars() -> None:
    _report, recheck_rows = build_audit()
    chars = {row["character"] for row in recheck_rows}

    assert set(REGRESSION_CHARS) <= chars
