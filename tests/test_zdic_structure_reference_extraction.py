from pathlib import Path

from scripts.extract_zdic_structure_references import (
    build_report,
    parse_zdic_text,
    snapshot_path,
)


def test_parse_zdic_yan_snapshot_extracts_structure_fields() -> None:
    char = "焱"
    path = snapshot_path(char)
    assert path.exists()

    record = parse_zdic_text(char, path.read_text(encoding="utf-8"), "local_snapshot", str(path))

    assert record["parse_status"] == "PARSED_WITH_STRUCTURE"
    assert record["fields"]["radical"] == "火"
    assert record["fields"]["total_strokes"] == "12"
    assert record["fields"]["unicode_value"] == "CJK 7131"
    assert record["fields"]["stroke_order"] == "433443344334"
    assert record["fields"]["raw_structure"] == "上下结构"
    assert record["fields"]["normalized_structure"] == "上下"
    assert record["fields"]["glyph_analysis"] == "会意"
    assert record["source_level"] == "network_cross_reference"


def test_zdic_extraction_report_keeps_boundary() -> None:
    report = build_report(["焱"], allow_online=False, timeout=1)

    assert report["overall_status"] == "PASS_ZDIC_STRUCTURE_REFERENCE_EXTRACTION_READY"
    assert report["summary"]["requested_chars"] == 1
    assert report["summary"]["parsed_with_structure"] == 1
    assert report["summary"]["gf0017_points_assigned"] == 0
    assert report["summary"]["cnbe_rows_written"] == 0
    assert report["decision"]["may_promote_to_national_standard"] is False
    assert report["decision"]["may_assign_gf0017_points_directly"] is False


def test_zdic_extraction_records_snapshot_gaps_without_guessing() -> None:
    report = build_report(["亡"], allow_online=False, timeout=1)
    record = report["records"][0]

    assert record["parse_status"] == "SNAPSHOT_GAP"
    assert record["fields"] == {}
    assert Path(record["source_path"]).as_posix() == "."
