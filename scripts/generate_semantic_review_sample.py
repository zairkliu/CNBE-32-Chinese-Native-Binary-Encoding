#!/usr/bin/env python3
"""Generate a deterministic semantic-review sample for the full catalog."""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from collections import Counter, defaultdict
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from audit_full_catalog_structure import SPECIAL_RADICAL_STRUCTURES
    from audit_full_catalog_xlsx import sha256_file
    from build_full_catalog_db import workbook_records
except ModuleNotFoundError:  # pragma: no cover - import path used by tests
    from scripts.audit_full_catalog_structure import SPECIAL_RADICAL_STRUCTURES
    from scripts.audit_full_catalog_xlsx import sha256_file
    from scripts.build_full_catalog_db import workbook_records

DEFAULT_SEED = 20260712
DEFAULT_TARGET_SIZE = 500
DEFAULT_MIN_PER_STRUCTURE = 30
DEFAULT_MIN_PER_BLOCK = 20
DEFAULT_JSON_OUTPUT = Path("reports/full_catalog_semantic_review_sample.json")
DEFAULT_CSV_OUTPUT = Path("reports/full_catalog_semantic_review_sample.csv")

REVIEW_COLUMNS = [
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
    "reviewer_a_radical",
    "reviewer_a_strokes",
    "reviewer_a_structure",
    "reviewer_a_notes",
    "reviewer_b_radical",
    "reviewer_b_strokes",
    "reviewer_b_structure",
    "reviewer_b_notes",
    "adjudication",
]


@dataclass(frozen=True)
class CatalogRecord:
    codepoint: int
    char: str
    cnbe: int
    radical: int
    strokes: int
    struct_type: int
    struct_name: str
    idx: int
    ext: int
    unicode_block: str
    source_sequence: int

    @property
    def unicode_label(self) -> str:
        return f"U+{self.codepoint:04X}"

    @property
    def cnbe_hex(self) -> str:
        return f"0x{self.cnbe:08X}"


def load_records(source: Path) -> list[CatalogRecord]:
    return [CatalogRecord(*row) for row in workbook_records(source)]


def shuffled(records: Iterable[CatalogRecord], rng: random.Random) -> list[CatalogRecord]:
    items = list(records)
    rng.shuffle(items)
    return items


def add_record(
    selected: dict[int, CatalogRecord],
    reasons: dict[int, set[str]],
    record: CatalogRecord,
    reason: str,
) -> None:
    selected.setdefault(record.codepoint, record)
    reasons[record.codepoint].add(reason)


def select_until(
    candidates: Iterable[CatalogRecord],
    selected: dict[int, CatalogRecord],
    reasons: dict[int, set[str]],
    reason: str,
    limit: int,
) -> None:
    count = sum(reason in item for item in reasons.values())
    for record in candidates:
        if count >= limit:
            break
        before = record.codepoint in selected
        add_record(selected, reasons, record, reason)
        if not before:
            count += 1


def select_group_minimums(
    records: list[CatalogRecord],
    selected: dict[int, CatalogRecord],
    reasons: dict[int, set[str]],
    rng: random.Random,
    key: Callable[[CatalogRecord], Any],
    minimum: int,
    reason_prefix: str,
) -> None:
    grouped: dict[Any, list[CatalogRecord]] = defaultdict(list)
    for record in records:
        grouped[key(record)].append(record)
    for group_key in sorted(grouped, key=str):
        candidates = shuffled(grouped[group_key], rng)
        needed = min(minimum, len(candidates))
        already = sum(1 for record in candidates if record.codepoint in selected)
        for record in candidates:
            if already >= needed:
                break
            before = record.codepoint in selected
            add_record(selected, reasons, record, f"{reason_prefix}:{group_key}")
            if not before:
                already += 1


def build_sample(
    records: list[CatalogRecord],
    seed: int,
    target_size: int,
    min_per_structure: int,
    min_per_block: int,
) -> tuple[list[CatalogRecord], dict[int, set[str]]]:
    if target_size < 400 or target_size > 600:
        raise ValueError("target size must be between 400 and 600")
    rng = random.Random(seed)
    selected: dict[int, CatalogRecord] = {}
    reasons: dict[int, set[str]] = defaultdict(set)

    select_group_minimums(records, selected, reasons, rng, lambda item: item.struct_type, min_per_structure, "structure")
    select_group_minimums(records, selected, reasons, rng, lambda item: item.unicode_block, min_per_block, "unicode_block")

    for radical in sorted(SPECIAL_RADICAL_STRUCTURES):
        candidates = [record for record in records if record.radical == radical]
        if not candidates:
            continue
        add_record(selected, reasons, shuffled(candidates, rng)[0], f"special_radical:{radical}")

    stroke_31 = [record for record in records if record.strokes == 31]
    select_until(shuffled(stroke_31, rng), selected, reasons, "stroke_clamp_31", 50)

    high_index = sorted(records, key=lambda item: (-item.idx, item.codepoint))
    select_until(high_index, selected, reasons, "high_group_index", 50)

    remainder = shuffled(records, rng)
    for record in remainder:
        if len(selected) >= target_size:
            break
        add_record(selected, reasons, record, "seeded_fill")

    sample = sorted(selected.values(), key=lambda item: item.codepoint)
    if len(sample) != target_size:
        raise ValueError(f"sample size mismatch: expected {target_size}, got {len(sample)}")
    return sample, reasons


def coverage_summary(sample: list[CatalogRecord], reasons: dict[int, set[str]]) -> dict[str, Any]:
    structures = Counter(str(record.struct_type) for record in sample)
    blocks = Counter(record.unicode_block for record in sample)
    special_radicals = sorted({record.radical for record in sample if record.radical in SPECIAL_RADICAL_STRUCTURES})
    reason_counts: Counter[str] = Counter()
    for values in reasons.values():
        for value in values:
            reason_counts[value.split(":", maxsplit=1)[0]] += 1
    return {
        "sample_size": len(sample),
        "structure_distribution": dict(sorted(structures.items())),
        "unicode_block_distribution": dict(sorted(blocks.items())),
        "special_radicals_covered": special_radicals,
        "special_radicals_expected": sorted(SPECIAL_RADICAL_STRUCTURES),
        "special_radical_coverage": len(special_radicals),
        "stroke_31_rows": sum(1 for record in sample if record.strokes == 31),
        "max_idx": max(record.idx for record in sample),
        "selection_reason_counts": dict(sorted(reason_counts.items())),
    }


def report_record(index: int, record: CatalogRecord, reasons: dict[int, set[str]]) -> dict[str, Any]:
    return {
        "sample_id": f"S{index:04d}",
        "unicode": record.unicode_label,
        "char": record.char,
        "cnbe_hex": record.cnbe_hex,
        "radical": record.radical,
        "strokes": record.strokes,
        "struct_type": record.struct_type,
        "struct_name": record.struct_name,
        "idx": record.idx,
        "ext": record.ext,
        "unicode_block": record.unicode_block,
        "source_sequence": record.source_sequence,
        "selection_reasons": sorted(reasons[record.codepoint]),
    }


def write_outputs(
    source: Path,
    json_output: Path,
    csv_output: Path,
    seed: int,
    sample: list[CatalogRecord],
    reasons: dict[int, set[str]],
) -> dict[str, Any]:
    rows = [report_record(index, record, reasons) for index, record in enumerate(sample, start=1)]
    report = {
        "report_schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "audit_mode": "semantic_review_sampling_only",
        "source": {
            "path": str(source),
            "sha256": sha256_file(source),
        },
        "sampling": {
            "seed": seed,
            "target_size": len(sample),
            "method": (
                "Deterministic coverage-constrained sample: structure classes, Unicode blocks, "
                "special radical overrides, 31-stroke clamp rows, high group-index rows, then seeded fill."
            ),
        },
        "coverage": coverage_summary(sample, reasons),
        "review_boundaries": {
            "semantic_authority": "INSUFFICIENT_UNTIL_REVIEWED",
            "sdk_replacement_allowed": False,
            "sqlite_build_authorized": False,
            "release_or_pypi_authorized": False,
        },
        "records": rows,
    }
    json_output.parent.mkdir(parents=True, exist_ok=True)
    csv_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    with csv_output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_COLUMNS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    **row,
                    "selection_reasons": ";".join(row["selection_reasons"]),
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
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="path to the 97,686-row catalog workbook")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--target-size", type=int, default=DEFAULT_TARGET_SIZE)
    parser.add_argument("--min-per-structure", type=int, default=DEFAULT_MIN_PER_STRUCTURE)
    parser.add_argument("--min-per-block", type=int, default=DEFAULT_MIN_PER_BLOCK)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--csv-output", type=Path, default=DEFAULT_CSV_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = args.source.expanduser().resolve()
    repo_root = Path(__file__).resolve().parent.parent
    json_output = (repo_root / args.json_output).resolve() if not args.json_output.is_absolute() else args.json_output
    csv_output = (repo_root / args.csv_output).resolve() if not args.csv_output.is_absolute() else args.csv_output
    try:
        records = load_records(source)
        sample, reasons = build_sample(
            records,
            seed=args.seed,
            target_size=args.target_size,
            min_per_structure=args.min_per_structure,
            min_per_block=args.min_per_block,
        )
        report = write_outputs(source, json_output, csv_output, args.seed, sample, reasons)
    except (OSError, ValueError) as exc:
        print(f"SEMANTIC REVIEW SAMPLE ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"SEMANTIC REVIEW SAMPLE READY: {json_output}")
    print(f"CSV: {csv_output}")
    print(f"Sample size: {report['coverage']['sample_size']}")
    print(f"Special radicals covered: {report['coverage']['special_radical_coverage']}/19")
    return 0


if __name__ == "__main__":
    sys.exit(main())
