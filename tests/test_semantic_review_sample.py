"""Tests for the deterministic semantic-review sampler."""

from __future__ import annotations

from scripts.generate_semantic_review_sample import CatalogRecord, build_sample, coverage_summary, report_record


def make_record(index: int, struct_type: int, block: str, radical: int, strokes: int = 10, idx: int = 0) -> CatalogRecord:
    return CatalogRecord(
        codepoint=0x3400 + index,
        char=chr(0x3400 + index),
        cnbe=(radical << 24) | (strokes << 19) | (struct_type << 15) | (idx << 4),
        radical=radical,
        strokes=strokes,
        struct_type=struct_type,
        struct_name=f"structure-{struct_type}",
        idx=idx,
        ext=0,
        unicode_block=block,
        source_sequence=index,
    )


def test_build_sample_is_deterministic_and_covers_constraints() -> None:
    records = []
    for index in range(700):
        records.append(
            make_record(
                index=index,
                struct_type=index % 5,
                block=f"block-{index % 4}",
                radical=(index % 214) + 1,
                strokes=31 if index % 11 == 0 else (index % 30) + 1,
                idx=index % 389,
            )
        )
    sample_a, reasons_a = build_sample(records, seed=1234, target_size=400, min_per_structure=30, min_per_block=20)
    sample_b, reasons_b = build_sample(records, seed=1234, target_size=400, min_per_structure=30, min_per_block=20)
    assert [item.codepoint for item in sample_a] == [item.codepoint for item in sample_b]
    assert reasons_a == reasons_b
    coverage = coverage_summary(sample_a, reasons_a)
    assert coverage["sample_size"] == 400
    assert min(coverage["structure_distribution"].values()) >= 30
    assert min(coverage["unicode_block_distribution"].values()) >= 20
    assert coverage["special_radical_coverage"] == 19
    assert coverage["stroke_31_rows"] >= 50
    assert coverage["max_idx"] == 388


def test_report_record_formats_review_row() -> None:
    record = make_record(1, struct_type=0, block="Basic", radical=1)
    row = report_record(1, record, {record.codepoint: {"structure:0", "seeded_fill"}})
    assert row["sample_id"] == "S0001"
    assert row["unicode"] == "U+3401"
    assert row["cnbe_hex"].startswith("0x")
    assert row["selection_reasons"] == ["seeded_fill", "structure:0"]
