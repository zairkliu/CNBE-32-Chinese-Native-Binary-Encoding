"""Tests for semantic-review result validation."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from scripts.validate_semantic_review_results import build_report

FIELDNAMES = [
    "sample_id",
    "unicode",
    "char",
    "cnbe_hex",
    "radical",
    "strokes",
    "struct_type",
    "struct_name",
    "idx",
    "unicode_block",
    "selection_reasons",
    "reviewer_a_radical",
    "reviewer_a_strokes",
    "reviewer_a_structure",
    "reviewer_b_radical",
    "reviewer_b_strokes",
    "reviewer_b_structure",
    "adjudication",
]


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_sample_json(path: Path, sample_ids: list[str]) -> None:
    path.write_text(
        json.dumps({"records": [{"sample_id": sample_id} for sample_id in sample_ids]}),
        encoding="utf-8",
    )


def base_row(sample_id: str = "S0001") -> dict[str, str]:
    return {
        "sample_id": sample_id,
        "unicode": "U+4E00",
        "char": "一",
        "cnbe_hex": "0x01080000",
        "radical": "1",
        "strokes": "1",
        "struct_type": "0",
        "struct_name": "独体结构",
        "idx": "0",
        "unicode_block": "CJK Unified Ideographs",
        "selection_reasons": "structure:0",
        "reviewer_a_radical": "",
        "reviewer_a_strokes": "",
        "reviewer_a_structure": "",
        "reviewer_b_radical": "",
        "reviewer_b_strokes": "",
        "reviewer_b_structure": "",
        "adjudication": "",
    }


def test_blank_template_is_incomplete_but_usable_before_review(tmp_path: Path) -> None:
    csv_path = tmp_path / "review.csv"
    sample_json = tmp_path / "sample.json"
    write_csv(csv_path, [base_row()])
    write_sample_json(sample_json, ["S0001"])
    report = build_report(csv_path, sample_json, strict=False)
    assert report["summary"]["status"] == "TEMPLATE_INCOMPLETE"
    assert report["summary"]["missing_judgment_count"] == 6


def test_strict_pass_requires_complete_matching_judgments(tmp_path: Path) -> None:
    row = base_row()
    for column in (
        "reviewer_a_radical",
        "reviewer_a_strokes",
        "reviewer_a_structure",
        "reviewer_b_radical",
        "reviewer_b_strokes",
        "reviewer_b_structure",
    ):
        row[column] = "agree"
    csv_path = tmp_path / "review.csv"
    sample_json = tmp_path / "sample.json"
    write_csv(csv_path, [row])
    write_sample_json(sample_json, ["S0001"])
    report = build_report(csv_path, sample_json, strict=True)
    assert report["summary"]["status"] == "PASS"
    assert report["decision_boundaries"]["sqlite_build_authorized"] is False


def test_disagreement_requires_adjudication_in_strict_mode(tmp_path: Path) -> None:
    row = base_row()
    row.update(
        {
            "reviewer_a_radical": "agree",
            "reviewer_a_strokes": "agree",
            "reviewer_a_structure": "agree",
            "reviewer_b_radical": "disagree",
            "reviewer_b_strokes": "agree",
            "reviewer_b_structure": "agree",
        }
    )
    csv_path = tmp_path / "review.csv"
    sample_json = tmp_path / "sample.json"
    write_csv(csv_path, [row])
    write_sample_json(sample_json, ["S0001"])
    report = build_report(csv_path, sample_json, strict=True)
    assert report["summary"]["status"] == "FAIL"
    assert report["summary"]["disagreement_count"] == 1
    assert report["summary"]["missing_adjudication_count"] == 1
