from scripts.extract_8105_gap_zdic_reference_batch import build_report, flatten_record
from scripts.extract_zdic_structure_references import parse_zdic_text


def test_zdic_batch_report_keeps_cross_reference_boundary() -> None:
    record = parse_zdic_text(
        "焱",
        "部首 火 总笔画 12 统一码 CJK 7131 笔顺 433443344334 字形结构 上下结构 字形分析 会意",
        "unit_test",
        "memory",
    )
    report = build_report([record])

    assert report["overall_status"] == "PASS_8105_GAP_ZDIC_REFERENCE_BATCH_READY"
    assert report["summary"]["parsed_with_structure"] == 1
    assert report["summary"]["gf0017_points_assigned"] == 0
    assert report["decision"]["may_promote_to_national_standard"] is False
    assert report["decision"]["may_write_cnbe_rows"] is False


def test_zdic_batch_flatten_preserves_allowed_structure() -> None:
    record = parse_zdic_text(
        "焱",
        "部首 火 总笔画 12 统一码 CJK 7131 笔顺 433443344334 字形结构 上下结构 字形分析 会意",
        "unit_test",
        "memory",
    )
    flat = flatten_record(record)

    assert flat["normalized_structure"] == "上下"
    assert flat["authority_boundary"] == "ZDIC_STRUCTURE_REFERENCE_NOT_NATIONAL_STANDARD"
