"""Tests for reviewer packet export."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from scripts.export_semantic_review_packets import export_packets, reviewer_fieldnames
from scripts.generate_semantic_review_sample import REVIEW_COLUMNS


def write_sample(path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerow(
            {
                "sample_id": "S0001",
                "unicode": "U+4E00",
                "char": "一",
                "cnbe_hex": "0x01080000",
                "radical": "1",
                "strokes": "1",
                "struct_type": "0",
                "struct_name": "独体结构",
                "idx": "0",
                "ext": "0",
                "unicode_block": "CJK Unified Ideographs",
                "source_sequence": "1",
                "selection_reasons": "structure:0",
                "reviewer_a_radical": "",
                "reviewer_a_strokes": "",
                "reviewer_a_structure": "",
                "reviewer_a_notes": "",
                "reviewer_b_radical": "",
                "reviewer_b_strokes": "",
                "reviewer_b_structure": "",
                "reviewer_b_notes": "",
                "adjudication": "",
            }
        )


def test_reviewer_fieldnames_are_split_by_role() -> None:
    assert "reviewer_a_radical" in reviewer_fieldnames("a")
    assert "reviewer_b_radical" not in reviewer_fieldnames("a")
    assert "reviewer_b_structure" in reviewer_fieldnames("b")
    assert "reviewer_a_structure" not in reviewer_fieldnames("b")


def test_export_packets_writes_two_role_specific_csvs(tmp_path: Path) -> None:
    sample = tmp_path / "sample.csv"
    output_dir = tmp_path / "packets"
    write_sample(sample)
    result = export_packets(sample, output_dir)
    manifest_path = result["manifest_path"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["row_count_per_packet"] == 1
    assert manifest["decision_boundaries"]["sqlite_build_authorized"] is False
    packet_a = output_dir / "full_catalog_semantic_review_reviewer_A.csv"
    packet_b = output_dir / "full_catalog_semantic_review_reviewer_B.csv"
    with packet_a.open("r", encoding="utf-8", newline="") as handle:
        header_a = next(csv.reader(handle))
    with packet_b.open("r", encoding="utf-8", newline="") as handle:
        header_b = next(csv.reader(handle))
    assert "reviewer_a_notes" in header_a
    assert "reviewer_b_notes" not in header_a
    assert "reviewer_b_notes" in header_b
    assert "reviewer_a_notes" not in header_b
