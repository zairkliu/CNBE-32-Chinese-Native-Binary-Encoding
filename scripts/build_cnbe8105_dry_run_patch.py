#!/usr/bin/env python3
"""Build a read-only dry-run patch for radix-ready 8105 CNBE candidates."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_CANDIDATE_INPUT = Path("evidence/8105/cnbe8105_auto_fix_candidates.json")
DEFAULT_RADICAL_MAP_INPUT = Path("evidence/8105/cnbe8105_radical_code_map.json")
DEFAULT_DRY_RUN_OUTPUT = Path("evidence/8105/cnbe8105_dry_run_patch.json")
DEFAULT_MARKDOWN_OUTPUT = Path("evidence/8105/CNBE8105_DRY_RUN_PATCH.md")

RADIX_SHIFT = 24
STROKE_SHIFT = 19
STRUCT_SHIFT = 15
INDEX_SHIFT = 4
EXT_MASK = 0x0F
SAMPLE_LIMIT = 30


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def encode_cnbe_fields(radix: int, strokes: int, struct_type: int, index: int, ext: int) -> int:
    return (radix << RADIX_SHIFT) | (strokes << STROKE_SHIFT) | (struct_type << STRUCT_SHIFT) | (index << INDEX_SHIFT) | ext


def decode_cnbe_fields(code: int) -> dict[str, int]:
    return {
        "radix": (code >> RADIX_SHIFT) & 0xFF,
        "strokes": (code >> STROKE_SHIFT) & 0x1F,
        "struct_type": (code >> STRUCT_SHIFT) & 0x0F,
        "index": (code >> INDEX_SHIFT) & 0x7FF,
        "ext": code & EXT_MASK,
    }


def radical_resolution_map(radical_model: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {record["radical"]: record for record in radical_model.get("records", [])}


def dry_run_record(candidate: dict[str, Any], radical_record: dict[str, Any]) -> dict[str, Any]:
    current = candidate["current"]
    proposed = candidate["proposed"]
    current_cnbe = int(current["cnbe"])
    ext = current_cnbe & EXT_MASK
    proposed_radix = int(radical_record["code"])
    proposed_code = encode_cnbe_fields(
        radix=proposed_radix,
        strokes=int(proposed["strokes"]),
        struct_type=int(proposed["struct_type"]),
        index=int(current["index"]),
        ext=ext,
    )
    decoded = decode_cnbe_fields(proposed_code)
    return {
        "char": candidate["char"],
        "unicode": candidate["unicode"],
        "standard_rank": candidate["standard_rank"],
        "status": "DRY_RUN_READY",
        "current": {
            "cnbe": current_cnbe,
            "cnbe_hex": f"0x{current_cnbe:08X}",
            "radix": current["radix"],
            "radix_name": current["radix_name"],
            "strokes": current["strokes"],
            "struct_type": current["struct_type"],
            "struct_name": current["struct_name"],
            "index": current["index"],
            "ext": ext,
        },
        "proposed": {
            "cnbe": proposed_code,
            "cnbe_hex": f"0x{proposed_code:08X}",
            "radix": proposed_radix,
            "radix_name": proposed["radix_name"],
            "canonical_radical": radical_record["canonical_radical"],
            "radical_resolution": radical_record["status"],
            "strokes": proposed["strokes"],
            "struct_type": proposed["struct_type"],
            "struct_name": proposed["struct_name"],
            "index": current["index"],
            "ext": ext,
            "decomposition": proposed["decomposition"],
            "components": proposed.get("components") or [],
        },
        "roundtrip": {
            "decoded": decoded,
            "pass": decoded
            == {
                "radix": proposed_radix,
                "strokes": proposed["strokes"],
                "struct_type": proposed["struct_type"],
                "index": current["index"],
                "ext": ext,
            },
        },
        "write_gate": "NO_WRITE_DRY_RUN_ONLY",
    }


def blocked_record(candidate: dict[str, Any], radical_record: dict[str, Any] | None) -> dict[str, Any]:
    proposed = candidate["proposed"]
    return {
        "char": candidate["char"],
        "unicode": candidate["unicode"],
        "standard_rank": candidate["standard_rank"],
        "status": "RADIX_BLOCKED",
        "proposed_radix_name": proposed["radix_name"],
        "reason": (radical_record or {}).get("reason", "missing radical resolution record"),
        "write_gate": "BLOCKED",
    }


def build_dry_run_patch(candidate_model: dict[str, Any], radical_model: dict[str, Any]) -> dict[str, Any]:
    resolutions = radical_resolution_map(radical_model)
    ready_records = []
    blocked_records = []
    structure_counts: Counter[str] = Counter()
    radical_resolution_counts: Counter[str] = Counter()
    changed_field_counts: Counter[str] = Counter()

    for candidate in candidate_model.get("candidates", []):
        radical = candidate["proposed"]["radix_name"]
        resolution = resolutions.get(radical)
        if not resolution or resolution.get("status") == "BLOCKED" or resolution.get("code") is None:
            blocked_records.append(blocked_record(candidate, resolution))
            continue
        record = dry_run_record(candidate, resolution)
        ready_records.append(record)
        structure_counts[record["proposed"]["struct_name"]] += 1
        radical_resolution_counts[record["proposed"]["radical_resolution"]] += 1
        for field in ("radix", "radix_name", "strokes", "struct_type", "struct_name", "cnbe"):
            current_value = record["current"].get(field)
            proposed_value = record["proposed"].get(field)
            if current_value != proposed_value:
                changed_field_counts[field] += 1

    ready_records.sort(key=lambda item: item["standard_rank"])
    blocked_records.sort(key=lambda item: item["standard_rank"])
    return {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "scope": "dry-run patch for radix-ready 8105 auto-fix candidates",
            "write_gate": "NO_WRITE_DRY_RUN_ONLY",
            "source_candidate_rows": candidate_model["summary"]["candidate_rows"],
            "source_ready_radical_rows": radical_model["summary"]["ready_candidate_rows"],
        },
        "summary": {
            "dry_run_ready_rows": len(ready_records),
            "radix_blocked_rows": len(blocked_records),
            "all_roundtrips_pass": all(record["roundtrip"]["pass"] for record in ready_records),
            "changed_field_counts": dict(sorted(changed_field_counts.items())),
            "structure_counts": dict(sorted(structure_counts.items())),
            "radical_resolution_counts": dict(sorted(radical_resolution_counts.items())),
            "write_gate": "NO_WRITE_DRY_RUN_ONLY",
        },
        "samples": {
            "first_ready": ready_records[:SAMPLE_LIMIT],
            "first_blocked": blocked_records[:SAMPLE_LIMIT],
            "known_ready": {
                record["char"]: record
                for record in ready_records
                if record["char"] in {"家", "遛", "涡", "焱", "衍"}
            },
        },
        "blocked": blocked_records,
        "patch": ready_records,
    }


def render_markdown_report(model: dict[str, Any]) -> str:
    summary = model["summary"]
    known = model["samples"]["known_ready"]
    known_rows = []
    for char in ["家", "遛", "涡", "焱", "衍"]:
        record = known.get(char)
        if not record:
            continue
        known_rows.append(
            [
                char,
                record["current"]["cnbe_hex"],
                record["proposed"]["cnbe_hex"],
                record["current"]["radix_name"],
                record["proposed"]["radix_name"],
                record["current"]["strokes"],
                record["proposed"]["strokes"],
                record["current"]["struct_name"],
                record["proposed"]["struct_name"],
            ]
        )
    blocked_rows = [
        [record["char"], record["unicode"], record["proposed_radix_name"], record["reason"]]
        for record in model["samples"]["first_blocked"]
    ]
    return "\n".join(
        [
            "# CNBE-32 8105 Dry-Run Patch",
            "",
            "## Scope",
            "",
            "This report previews the field-level patch for radix-ready 8105 candidates.",
            "It does not write to `cnbe32_updated.json`, does not update SDK databases, and does not change golden vectors.",
            "",
            "## Gate",
            "",
            f"- Dry-run ready rows: {summary['dry_run_ready_rows']}",
            f"- Radix blocked rows: {summary['radix_blocked_rows']}",
            f"- All roundtrips pass: {summary['all_roundtrips_pass']}",
            f"- Write gate: {summary['write_gate']}",
            "",
            "## Changed Field Counts",
            "",
            markdown_table(["Field", "Rows"], [[key, value] for key, value in summary["changed_field_counts"].items()]),
            "",
            "## Known Ready Samples",
            "",
            markdown_table(
                [
                    "Char",
                    "Current CNBE",
                    "Proposed CNBE",
                    "Current Radical",
                    "Proposed Radical",
                    "Current Strokes",
                    "Proposed Strokes",
                    "Current Structure",
                    "Proposed Structure",
                ],
                known_rows,
            ),
            "",
            "## First Blocked Samples",
            "",
            markdown_table(["Char", "Unicode", "Radical", "Reason"], blocked_rows),
            "",
            "## Decision",
            "",
            "This dry-run is suitable for review only. A write patch requires explicit authorization and must operate on a copied dataset first.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-input", type=Path, default=DEFAULT_CANDIDATE_INPUT)
    parser.add_argument("--radical-map-input", type=Path, default=DEFAULT_RADICAL_MAP_INPUT)
    parser.add_argument("--dry-run-output", type=Path, default=DEFAULT_DRY_RUN_OUTPUT)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        candidate_model = load_json(args.candidate_input)
        radical_model = load_json(args.radical_map_input)
        dry_run = build_dry_run_patch(candidate_model, radical_model)
    except Exception as exc:  # pragma: no cover - command-line guard
        print(f"CNBE8105 DRY-RUN PATCH FAIL: {exc}", file=sys.stderr)
        return 1

    write_json(args.dry_run_output, dry_run)
    write_text(args.markdown_output, render_markdown_report(dry_run))
    summary = dry_run["summary"]
    print("CNBE8105 DRY-RUN PATCH PASS")
    print(f"Dry-run ready rows: {summary['dry_run_ready_rows']}")
    print(f"Radix blocked rows: {summary['radix_blocked_rows']}")
    print(f"All roundtrips pass: {summary['all_roundtrips_pass']}")
    print(f"Write gate: {summary['write_gate']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
