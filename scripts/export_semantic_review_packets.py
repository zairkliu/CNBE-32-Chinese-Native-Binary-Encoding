#!/usr/bin/env python3
"""Export separate reviewer packets from the semantic-review sample CSV."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_SAMPLE_CSV = Path("reports/full_catalog_semantic_review_sample.csv")
DEFAULT_OUTPUT_DIR = Path("build/review_packets")

BASE_COLUMNS = [
    "sample_id",
    "unicode",
    "char",
    "cnbe_hex",
    "radical",
    "strokes",
    "struct_type",
    "struct_name",
    "idx",
    "ext",
    "unicode_block",
    "source_sequence",
    "selection_reasons",
]

REVIEWER_COLUMNS = {
    "a": [
        "reviewer_a_radical",
        "reviewer_a_strokes",
        "reviewer_a_structure",
        "reviewer_a_notes",
    ],
    "b": [
        "reviewer_b_radical",
        "reviewer_b_strokes",
        "reviewer_b_structure",
        "reviewer_b_notes",
    ],
}

ALLOWED_REVIEWERS = tuple(sorted(REVIEWER_COLUMNS))


def read_rows(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("sample CSV is missing a header row")
        required = BASE_COLUMNS + [column for columns in REVIEWER_COLUMNS.values() for column in columns]
        missing = [column for column in required if column not in reader.fieldnames]
        if missing:
            raise ValueError(f"sample CSV missing required columns: {', '.join(missing)}")
        return [dict(row) for row in reader], list(reader.fieldnames)


def reviewer_fieldnames(reviewer: str) -> list[str]:
    if reviewer not in REVIEWER_COLUMNS:
        raise ValueError(f"unsupported reviewer: {reviewer}")
    return BASE_COLUMNS + REVIEWER_COLUMNS[reviewer]


def packet_path(output_dir: Path, reviewer: str) -> Path:
    return output_dir / f"full_catalog_semantic_review_reviewer_{reviewer.upper()}.csv"


def write_packet(rows: list[dict[str, str]], output_dir: Path, reviewer: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = packet_path(output_dir, reviewer)
    fieldnames = reviewer_fieldnames(reviewer)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in fieldnames})
    return path


def build_manifest(sample_csv: Path, output_dir: Path, packet_paths: list[Path], row_count: int) -> dict[str, Any]:
    return {
        "manifest_schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_csv": str(sample_csv),
        "output_dir": str(output_dir),
        "row_count_per_packet": row_count,
        "packets": [str(path) for path in packet_paths],
        "allowed_judgments": ["agree", "disagree", "unclear"],
        "merge_back_target": "reports/full_catalog_semantic_review_sample.csv",
        "decision_boundaries": {
            "semantic_authority": "INSUFFICIENT_UNTIL_REVIEW_VALIDATION_PASSES",
            "sdk_replacement_allowed": False,
            "sqlite_build_authorized": False,
            "release_or_pypi_authorized": False,
        },
    }


def export_packets(sample_csv: Path, output_dir: Path) -> dict[str, Any]:
    rows, _ = read_rows(sample_csv)
    paths = [write_packet(rows, output_dir, reviewer) for reviewer in ALLOWED_REVIEWERS]
    manifest = build_manifest(sample_csv, output_dir, paths, len(rows))
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return {"manifest_path": manifest_path, "manifest": manifest}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-csv", type=Path, default=DEFAULT_SAMPLE_CSV)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parent.parent
    sample_csv = (repo_root / args.sample_csv).resolve() if not args.sample_csv.is_absolute() else args.sample_csv
    output_dir = (repo_root / args.output_dir).resolve() if not args.output_dir.is_absolute() else args.output_dir
    try:
        result = export_packets(sample_csv, output_dir)
    except (OSError, ValueError) as exc:
        print(f"SEMANTIC REVIEW PACKET EXPORT ERROR: {exc}", file=sys.stderr)
        return 2
    manifest = result["manifest"]
    print(f"SEMANTIC REVIEW PACKETS READY: {result['manifest_path']}")
    print(f"Rows per packet: {manifest['row_count_per_packet']}")
    for packet in manifest["packets"]:
        print(f"Packet: {packet}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
