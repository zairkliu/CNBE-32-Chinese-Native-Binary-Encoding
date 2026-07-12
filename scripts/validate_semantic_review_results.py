#!/usr/bin/env python3
"""Validate completed semantic-review CSV results without changing catalog data."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_CSV = Path("reports/full_catalog_semantic_review_sample.csv")
DEFAULT_SAMPLE_JSON = Path("reports/full_catalog_semantic_review_sample.json")
DEFAULT_OUTPUT = Path("reports/full_catalog_semantic_review_validation.json")

REQUIRED_COLUMNS = [
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

JUDGMENT_COLUMNS = [
    "reviewer_a_radical",
    "reviewer_a_strokes",
    "reviewer_a_structure",
    "reviewer_b_radical",
    "reviewer_b_strokes",
    "reviewer_b_structure",
]

PAIR_FIELDS = [
    ("radical", "reviewer_a_radical", "reviewer_b_radical"),
    ("strokes", "reviewer_a_strokes", "reviewer_b_strokes"),
    ("structure", "reviewer_a_structure", "reviewer_b_structure"),
]

ALLOWED_JUDGMENTS = {"agree", "disagree", "unclear"}
ALLOWED_ADJUDICATIONS = {"accept", "revise", "exclude", "needs_source", "no_action"}


def normalize(value: str | None) -> str:
    return (value or "").strip().lower()


def load_sample_ids(path: Path) -> list[str]:
    report = json.loads(path.read_text(encoding="utf-8"))
    return [str(row["sample_id"]) for row in report["records"]]


def read_rows(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("CSV is missing a header row")
        missing = [column for column in REQUIRED_COLUMNS if column not in reader.fieldnames]
        if missing:
            raise ValueError(f"CSV missing required columns: {', '.join(missing)}")
        return [dict(row) for row in reader], list(reader.fieldnames)


def validate_rows(rows: list[dict[str, str]], expected_ids: list[str] | None, strict: bool) -> dict[str, Any]:
    invalid_judgments: list[dict[str, str]] = []
    missing_judgments: list[dict[str, str]] = []
    disagreements: list[dict[str, str]] = []
    missing_adjudications: list[dict[str, str]] = []
    duplicate_ids = [sample_id for sample_id, count in Counter(row["sample_id"] for row in rows).items() if count > 1]

    if expected_ids is None:
        sample_id_alignment = "NOT_CHECKED"
        missing_ids: list[str] = []
        unexpected_ids: list[str] = []
    else:
        actual_ids = [row["sample_id"] for row in rows]
        sample_id_alignment = "PASS" if actual_ids == expected_ids else "FAIL"
        missing_ids = [sample_id for sample_id in expected_ids if sample_id not in set(actual_ids)]
        unexpected_ids = [sample_id for sample_id in actual_ids if sample_id not in set(expected_ids)]

    for row in rows:
        sample_id = row["sample_id"]
        for column in JUDGMENT_COLUMNS:
            value = normalize(row.get(column))
            if not value:
                missing_judgments.append({"sample_id": sample_id, "column": column})
                continue
            if value not in ALLOWED_JUDGMENTS:
                invalid_judgments.append({"sample_id": sample_id, "column": column, "value": value})
        for field, reviewer_a, reviewer_b in PAIR_FIELDS:
            left = normalize(row.get(reviewer_a))
            right = normalize(row.get(reviewer_b))
            if left and right and left != right:
                disagreements.append(
                    {
                        "sample_id": sample_id,
                        "field": field,
                        "reviewer_a": left,
                        "reviewer_b": right,
                    }
                )
                if not normalize(row.get("adjudication")):
                    missing_adjudications.append({"sample_id": sample_id, "field": field})
        adjudication = normalize(row.get("adjudication"))
        if adjudication and adjudication not in ALLOWED_ADJUDICATIONS:
            invalid_judgments.append({"sample_id": sample_id, "column": "adjudication", "value": adjudication})

    complete = not missing_judgments and not invalid_judgments and not missing_adjudications
    aligned = sample_id_alignment in {"PASS", "NOT_CHECKED"} and not duplicate_ids and not unexpected_ids
    if complete and aligned:
        status = "PASS"
    elif strict:
        status = "FAIL"
    else:
        status = "TEMPLATE_INCOMPLETE"

    return {
        "status": status,
        "strict": strict,
        "row_count": len(rows),
        "sample_id_alignment": sample_id_alignment,
        "duplicate_sample_ids": duplicate_ids[:20],
        "missing_sample_ids": missing_ids[:20],
        "unexpected_sample_ids": unexpected_ids[:20],
        "missing_judgment_count": len(missing_judgments),
        "invalid_judgment_count": len(invalid_judgments),
        "disagreement_count": len(disagreements),
        "missing_adjudication_count": len(missing_adjudications),
        "missing_judgment_samples": missing_judgments[:20],
        "invalid_judgment_samples": invalid_judgments[:20],
        "disagreement_samples": disagreements[:20],
        "missing_adjudication_samples": missing_adjudications[:20],
    }


def build_report(csv_path: Path, sample_json: Path | None, strict: bool) -> dict[str, Any]:
    rows, columns = read_rows(csv_path)
    expected_ids = load_sample_ids(sample_json) if sample_json is not None else None
    validation = validate_rows(rows, expected_ids, strict)
    return {
        "report_schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "audit_mode": "semantic_review_results_validation",
        "source_csv": str(csv_path),
        "sample_json": str(sample_json) if sample_json is not None else None,
        "columns": columns,
        "allowed_judgments": sorted(ALLOWED_JUDGMENTS),
        "allowed_adjudications": sorted(ALLOWED_ADJUDICATIONS),
        "summary": validation,
        "decision_boundaries": {
            "semantic_authority": "INSUFFICIENT_UNLESS_STRICT_PASS_AND_MANUAL_REVIEWED",
            "sdk_replacement_allowed": False,
            "sqlite_build_authorized": False,
            "release_or_pypi_authorized": False,
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--sample-json", type=Path, default=DEFAULT_SAMPLE_JSON)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--strict", action="store_true", help="fail unless every reviewer/adjudication field is complete")
    parser.add_argument("--no-sample-json", action="store_true", help="skip sample-id alignment check")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parent.parent
    csv_path = (repo_root / args.csv).resolve() if not args.csv.is_absolute() else args.csv
    output = (repo_root / args.output).resolve() if not args.output.is_absolute() else args.output
    sample_json = None
    if not args.no_sample_json:
        sample_json = (repo_root / args.sample_json).resolve() if not args.sample_json.is_absolute() else args.sample_json
    try:
        report = build_report(csv_path, sample_json, args.strict)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"SEMANTIC REVIEW VALIDATION ERROR: {exc}", file=sys.stderr)
        return 2
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"SEMANTIC REVIEW VALIDATION {report['summary']['status']}: {output}")
    print(f"Rows: {report['summary']['row_count']}")
    print(f"Missing judgments: {report['summary']['missing_judgment_count']}")
    print(f"Disagreements: {report['summary']['disagreement_count']}")
    return 0 if report["summary"]["status"] in {"PASS", "TEMPLATE_INCOMPLETE"} and not args.strict else int(
        report["summary"]["status"] != "PASS"
    )


if __name__ == "__main__":
    sys.exit(main())
