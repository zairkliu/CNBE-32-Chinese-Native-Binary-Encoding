from pathlib import Path

from scripts.run_hanzi_decomp_v03_8105_adapter import (
    APPROVED_STRUCTURES,
    DEFAULT_ZIP,
    build,
)


def test_hanzi_decomp_v03_zip_is_available() -> None:
    assert DEFAULT_ZIP.exists()
    assert DEFAULT_ZIP.stat().st_size > 0


def test_hanzi_decomp_v03_adapter_covers_8105_and_separates_conflicts() -> None:
    rows, fill_rows, conflict_rows, report = build(Path(DEFAULT_ZIP))

    assert report["overall_status"] == "PASS_HANZI_DECOMP_V03_ADAPTER_READY_FOR_REVIEW"
    assert len(rows) == 8105
    assert report["summary"]["tool_8105_ids_or_dutizi_coverage"] >= 7800
    assert len(fill_rows) == 1243
    assert len(conflict_rows) == 357
    assert report["checks"]["conflicts_are_separated"] is True


def test_hanzi_decomp_v03_adapter_uses_only_approved_structure_labels() -> None:
    rows, _fill_rows, _conflict_rows, report = build(Path(DEFAULT_ZIP))
    structures = {row["tool_structure"] for row in rows if row["tool_structure"]}

    assert structures <= set(APPROVED_STRUCTURES)
    assert report["checks"]["tool_structures_approved_or_blank"] is True
    assert report["checks"]["forbidden_structure_labels_absent"] is True


def test_hanzi_decomp_v03_adapter_locks_known_regressions() -> None:
    rows, _fill_rows, _conflict_rows, _report = build(Path(DEFAULT_ZIP))
    by_char = {row["character"]: row for row in rows}

    assert by_char["侵"]["tool_structure"] == "左右"
    assert by_char["偶"]["tool_structure"] == "左右"
    assert by_char["冁"]["tool_structure"] == "左右"


def test_hanzi_decomp_v03_adapter_keeps_no_write_boundary() -> None:
    rows, _fill_rows, _conflict_rows, report = build(Path(DEFAULT_ZIP))

    assert report["decision"]["may_promote_to_national_standard"] is False
    assert report["decision"]["may_write_cnbe32"] is False
    assert report["decision"]["may_rebuild_database"] is False
    assert all(row["cnbe32_write_status"] == "NO_CNBE32_WRITE" for row in rows)
    assert all(row["database_rebuild_status"] == "NO_DATABASE_REBUILD" for row in rows)


def test_hanzi_decomp_v03_adapter_records_packaging_risk() -> None:
    _rows, _fill_rows, _conflict_rows, report = build(Path(DEFAULT_ZIP))

    assert report["tool_risks"]["hardcoded_windows_base_path"] is True
    assert report["tool_risks"]["starts_local_http_server"] is True
