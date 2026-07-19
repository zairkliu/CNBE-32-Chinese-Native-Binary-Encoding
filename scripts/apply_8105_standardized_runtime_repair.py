#!/usr/bin/env python3
"""Apply conservative 8105 standardized repairs to runtime CNBE32 data.

This script is the release-track follow-up to the 8105 runtime blocker plan.
It updates only force-approved 8105 rows that are already present in the
runtime model and that can be repaired with reproducible evidence:

- Unicode identity must match the 8105 approved packet.
- Structure and stroke count come from the human-approved 8105 Agent packet.
- Radical comes from the approved packet when present, otherwise from the
  cached ZDIC cross-reference record.
- Numeric radical code must resolve through the conservative radical map or a
  position-sensitive left/right 阝 rule.
- The existing CNBE32 index and extension bits must be preserved.
- The recomputed CNBE32 value must round-trip through the bitfield decoder.

Rows missing from the current runtime model or still lacking conservative
radical evidence remain in the unresolved queue. They are not invented here.
"""

from __future__ import annotations

import csv
import json
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.build_8105_approved_cnbe32_dry_run_patch import parse_int
from scripts.build_cnbe8105_dry_run_patch import (
    EXT_MASK,
    decode_cnbe_fields,
    encode_cnbe_fields,
)
from scripts.build_cnbe8105_radical_code_map import (
    KNOWLEDGE_BASE,
    load_radical_code_source,
    resolve_radical,
)

APPROVED_PACKET = Path("review_packets/8105_full/8105_hanzi_decomp_v03_human_approved_structure_packet.csv")
BLOCKER_QUEUE = Path("review_packets/8105_full/8105_runtime_blocker_resolution_queue.csv")
RUNTIME_JSON = Path("data/cnbe32.json")
ROOT_DB = Path("data/cnbe32.db")
PACKAGE_DB = Path("src/cnbe32/data/cnbe32.db")
ZDIC_CACHE = Path("reports/zdic_8105_gap_cache")
JSON_REPORT = Path("reports/8105_standardized_runtime_repair.json")
MD_REPORT = Path("reports/8105_STANDARDIZED_RUNTIME_REPAIR.md")
APPLIED_CSV = Path("review_packets/8105_full/8105_standardized_runtime_repair_applied.csv")
REMAINING_CSV = Path("review_packets/8105_full/8105_standardized_runtime_repair_remaining_blockers.csv")

EXPECTED_RUNTIME_ROWS = 20902
MAX_STROKES = 31
MAX_STRUCT_TYPE = 15
MAX_INDEX = 2047
HUMAN_DECISION_ID = "HUMAN_REVIEW_2026_07_19_CNBE32_DRY_RUN_FORCE_PASS"
REPAIR_ID = "CNBE8105_STANDARDIZED_RUNTIME_REPAIR_2026_07_19"

CREATE_SQL = """
CREATE TABLE cnbe32 (
    unicode INTEGER PRIMARY KEY,
    char TEXT,
    cnbe INTEGER,
    radix INTEGER,
    radix_name TEXT,
    strokes INTEGER,
    struct_type INTEGER,
    struct_name TEXT,
    idx INTEGER
);

CREATE INDEX idx_cnbe ON cnbe32(cnbe);
CREATE INDEX idx_radix ON cnbe32(radix);
CREATE INDEX idx_strokes ON cnbe32(strokes);
"""

INSERT_SQL = """
INSERT INTO cnbe32 (
    unicode,
    char,
    cnbe,
    radix,
    radix_name,
    strokes,
    struct_type,
    struct_name,
    idx
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def approved_by_char() -> dict[str, dict[str, str]]:
    return {row["character"]: row for row in read_csv(APPROVED_PACKET)}


def blocker_rows() -> list[dict[str, str]]:
    return read_csv(BLOCKER_QUEUE)


def zdic_cache_path(unicode_label: str) -> Path:
    return ZDIC_CACHE / f"U_{unicode_label.removeprefix('U+').upper()}.json"


def zdic_fields(unicode_label: str) -> dict[str, str]:
    path = zdic_cache_path(unicode_label)
    if not path.exists():
        return {}
    record = read_json(path)
    if record.get("parse_status") != "PARSED_WITH_STRUCTURE":
        return {}
    fields = record.get("fields", {})
    if not isinstance(fields, dict):
        return {}
    return {str(key): str(value) for key, value in fields.items()}


def row_unicode_label(row: dict[str, Any]) -> str:
    return f"U+{int(row['unicode']):04X}"


def split_top_level_components(value: str) -> list[str]:
    if not value:
        return []
    for separator in ("|", ";", "、", ","):
        value = value.replace(separator, " ")
    return [part for part in value.split() if part]


def infer_er_position(approved: dict[str, str]) -> str:
    components = split_top_level_components(approved.get("direct_component_candidates", ""))
    decomposition = approved.get("candidate_decomposition", "")
    if components:
        if components[0] == "阝":
            return "left"
        if components[-1] == "阝":
            return "right"
    if decomposition.startswith("⿰阝"):
        return "left"
    if decomposition.endswith("阝"):
        return "right"
    return ""


def resolve_radical_for_row(
    radical: str,
    approved: dict[str, str],
    radical_to_code: dict[str, int],
) -> dict[str, Any]:
    if radical == "阝":
        position = infer_er_position(approved)
        if position == "left" and "阜" in radical_to_code:
            return {
                "radical": radical,
                "status": "POSITION_LEFT_ALIAS",
                "canonical_radical": "阜",
                "code": radical_to_code["阜"],
                "reason": "left 阝 resolved to 阜 from top-level decomposition position",
            }
        if position == "right" and "邑" in radical_to_code:
            return {
                "radical": radical,
                "status": "POSITION_RIGHT_ALIAS",
                "canonical_radical": "邑",
                "code": radical_to_code["邑"],
                "reason": "right 阝 resolved to 邑 from top-level decomposition position",
            }
        return {
            "radical": radical,
            "status": "BLOCKED",
            "canonical_radical": None,
            "code": None,
            "reason": "阝 requires left/right decomposition position before CNBE32 radix assignment",
        }
    return resolve_radical(radical, radical_to_code)


def choose_radical(
    blocker: dict[str, str],
    approved: dict[str, str],
) -> tuple[str, str, str]:
    if approved.get("radical"):
        return approved["radical"], "approved_8105_packet", approved.get("radical_status", "")
    fields = zdic_fields(blocker["unicode"])
    radical = fields.get("radical", "")
    if radical:
        return radical, "zdic_cached_cross_reference_radical", "NETWORK_CROSS_REFERENCE_NOT_NATIONAL_STANDARD"
    return "", "missing_radical", ""


def validate_runtime_row(row: dict[str, Any]) -> None:
    codepoint = int(row["unicode"])
    if len(row["char"]) != 1 or ord(row["char"]) != codepoint:
        raise ValueError(f"Unicode identity mismatch: {row!r}")
    for field, maximum in {"radix": 255, "strokes": 31, "struct_type": 15, "index": 2047}.items():
        value = int(row[field])
        if not 0 <= value <= maximum:
            raise ValueError(f"{row['char']} invalid {field}: {value}")
    decoded = decode_cnbe_fields(int(row["cnbe"]))
    expected = {
        "radix": int(row["radix"]),
        "strokes": int(row["strokes"]),
        "struct_type": int(row["struct_type"]),
        "index": int(row["index"]),
        "ext": int(row["cnbe"]) & EXT_MASK,
    }
    if decoded != expected:
        raise ValueError(f"{row['char']} failed CNBE32 roundtrip: {decoded} != {expected}")


def build_repair_record(
    blocker: dict[str, str],
    approved: dict[str, str],
    current: dict[str, Any],
    radical_resolution: dict[str, Any],
    radical_source: str,
    radical_status: str,
) -> dict[str, Any]:
    current_code = int(current["cnbe"])
    decoded = decode_cnbe_fields(current_code)
    current_index = decoded["index"]
    ext = current_code & EXT_MASK
    strokes = int(approved["stroke_count"])
    struct_type = int(approved["agent_struct_type"])
    radix = int(radical_resolution["code"])
    proposed_cnbe = encode_cnbe_fields(radix, strokes, struct_type, current_index, ext)
    roundtrip = decode_cnbe_fields(proposed_cnbe)
    return {
        "char": blocker["char"],
        "unicode": blocker["unicode"],
        "standard_rank": int(blocker["standard_rank"]),
        "repair_status": "APPLIED_RUNTIME_REPAIR_CANDIDATE",
        "original_block_reason": blocker["block_reason"],
        "radical_source": radical_source,
        "radical_source_status": radical_status,
        "radical_resolution_status": radical_resolution["status"],
        "radical_resolution_reason": radical_resolution["reason"],
        "approved_radical": radical_resolution["radical"],
        "canonical_radical": radical_resolution["canonical_radical"],
        "proposed_radix": radix,
        "proposed_radix_name": radical_resolution["canonical_radical"],
        "approved_strokes": strokes,
        "approved_structure": approved["candidate_structure_label"],
        "approved_struct_type": struct_type,
        "approved_decomposition": approved["candidate_decomposition"],
        "current_cnbe": current_code,
        "current_cnbe_hex": f"0x{current_code:08X}",
        "current_radix": current["radix"],
        "current_radix_name": current["radix_name"],
        "current_strokes": current["strokes"],
        "current_struct_name": current["struct_name"],
        "current_struct_type": current["struct_type"],
        "current_index": current_index,
        "current_ext": ext,
        "proposed_cnbe": proposed_cnbe,
        "proposed_cnbe_hex": f"0x{proposed_cnbe:08X}",
        "roundtrip_pass": roundtrip
        == {
            "radix": radix,
            "strokes": strokes,
            "struct_type": struct_type,
            "index": current_index,
            "ext": ext,
        },
        "authority_boundary": "AGENT_STANDARD_ALIGNED_TO_8105_WITH_CROSS_REFERENCE_WHERE_NEEDED",
    }


def block_record(blocker: dict[str, str], reason: str, detail: str) -> dict[str, Any]:
    record = dict(blocker)
    record.update(
        {
            "repair_status": "REMAINING_RUNTIME_BLOCKER",
            "remaining_reason": reason,
            "remaining_detail": detail,
            "write_status": "NO_RUNTIME_WRITE_FOR_THIS_ROW",
        }
    )
    return record


def apply_record(row: dict[str, Any], repair: dict[str, Any]) -> dict[str, Any]:
    updated = dict(row)
    updated.update(
        {
            "cnbe": repair["proposed_cnbe"],
            "radix": repair["proposed_radix"],
            "radix_name": repair["proposed_radix_name"],
            "strokes": repair["approved_strokes"],
            "struct_type": repair["approved_struct_type"],
            "struct_name": repair["approved_structure"],
        }
    )
    validate_runtime_row(updated)
    return updated


def rebuild_database(path: Path, rows: list[dict[str, Any]]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA encoding = 'UTF-8'")
        connection.executescript(CREATE_SQL)
        connection.executemany(
            INSERT_SQL,
            [
                (
                    int(row["unicode"]),
                    row["char"],
                    int(row["cnbe"]),
                    int(row["radix"]),
                    row["radix_name"],
                    int(row["strokes"]),
                    int(row["struct_type"]),
                    row["struct_name"],
                    int(row["index"]),
                )
                for row in rows
            ],
        )
        connection.commit()
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        count = int(connection.execute("SELECT COUNT(*) FROM cnbe32").fetchone()[0])
        distinct = connection.execute(
            "SELECT COUNT(DISTINCT unicode), COUNT(DISTINCT char) FROM cnbe32"
        ).fetchone()
        samples = {}
        for char in ("队", "玕", "冁", "㑇", "刁", "家", "侵", "偶", "孓"):
            found = connection.execute("SELECT * FROM cnbe32 WHERE char = ?", (char,)).fetchone()
            samples[char] = None if found is None else dict(
                zip(
                    ["unicode", "char", "cnbe", "radix", "radix_name", "strokes", "struct_type", "struct_name", "idx"],
                    found,
                )
            )
    return {
        "path": str(path),
        "row_count": count,
        "distinct_unicode": distinct[0],
        "distinct_char": distinct[1],
        "sqlite_integrity_check": integrity,
        "size_bytes": path.stat().st_size,
        "samples": samples,
    }


def build() -> dict[str, Any]:
    runtime_model = read_json(RUNTIME_JSON)
    approved = approved_by_char()
    blockers = blocker_rows()
    radical_source = load_radical_code_source(KNOWLEDGE_BASE)
    radical_to_code = radical_source["radical_to_code"]
    rows_by_char = {row["char"]: row for row in runtime_model["characters"]}

    applied: list[dict[str, Any]] = []
    remaining: list[dict[str, Any]] = []
    updated_by_char: dict[str, dict[str, Any]] = {}

    for blocker in blockers:
        char = blocker["char"]
        approved_row = approved.get(char)
        current_row = rows_by_char.get(char)
        if current_row is None:
            remaining.append(block_record(blocker, "missing_current_model_row", "No runtime index/ext exists to preserve."))
            continue
        if approved_row is None:
            remaining.append(block_record(blocker, "missing_approved_packet_row", "Approved 8105 packet row is missing."))
            continue
        if row_unicode_label(current_row) != blocker["unicode"] or approved_row["unicode_codepoint"] != blocker["unicode"]:
            remaining.append(block_record(blocker, "unicode_identity_mismatch", "Runtime, blocker queue, and approved packet disagree."))
            continue
        strokes = parse_int(approved_row.get("stroke_count"))
        struct_type = parse_int(approved_row.get("agent_struct_type"))
        if strokes is None or not 0 <= strokes <= MAX_STROKES:
            remaining.append(block_record(blocker, "invalid_or_missing_stroke_count", approved_row.get("stroke_count", "")))
            continue
        if struct_type is None or not 0 <= struct_type <= MAX_STRUCT_TYPE:
            remaining.append(block_record(blocker, "invalid_or_missing_structure_type", approved_row.get("agent_struct_type", "")))
            continue
        decoded = decode_cnbe_fields(int(current_row["cnbe"]))
        if not 0 <= decoded["index"] <= MAX_INDEX:
            remaining.append(block_record(blocker, "invalid_current_index", str(decoded["index"])))
            continue
        radical, source, radical_status = choose_radical(blocker, approved_row)
        if not radical:
            remaining.append(block_record(blocker, "missing_radical_after_cross_reference_join", "No approved or cached radical found."))
            continue
        resolution = resolve_radical_for_row(radical, approved_row, radical_to_code)
        if resolution["status"] == "BLOCKED":
            remaining.append(block_record(blocker, "radical_resolution_blocked", resolution["reason"]))
            continue
        repair = build_repair_record(blocker, approved_row, current_row, resolution, source, radical_status)
        if repair["roundtrip_pass"] is not True:
            remaining.append(block_record(blocker, "cnbe32_roundtrip_failed", repair["proposed_cnbe_hex"]))
            continue
        applied.append(repair)
        updated_by_char[char] = apply_record(current_row, repair)

    repaired_rows = [updated_by_char.get(row["char"], row) for row in runtime_model["characters"]]
    for row in repaired_rows:
        validate_runtime_row(row)

    metadata = dict(runtime_model.get("metadata", {}))
    if metadata.get("runtime_repair") == REPAIR_ID:
        previous_patched = int(metadata.get("patched_8105_rows_before_standardized_repair", 0))
        if previous_patched == 0:
            previous_patched = int(metadata.get("patched_8105_rows", 0)) - int(
                metadata.get("runtime_repair_applied_rows", 0)
            )
    else:
        previous_patched = int(metadata.get("patched_8105_rows", 0))
    previous_remaining = len(blockers)
    metadata.update(
        {
            "runtime_repair": REPAIR_ID,
            "runtime_repair_generated_at": datetime.now(timezone.utc).isoformat(),
            "runtime_repair_source_queue": str(BLOCKER_QUEUE),
            "runtime_repair_applied_rows": len(applied),
            "patched_8105_rows_before_standardized_repair": previous_patched,
            "patched_8105_rows": previous_patched + len(applied),
            "force_approved_not_patched_rows": len(remaining),
            "human_decision_id": HUMAN_DECISION_ID,
            "total": len(repaired_rows),
        }
    )
    repaired_model = {"metadata": metadata, "characters": repaired_rows}
    write_json(RUNTIME_JSON, repaired_model)
    db_reports = [rebuild_database(ROOT_DB, repaired_rows), rebuild_database(PACKAGE_DB, repaired_rows)]

    applied.sort(key=lambda row: int(row["standard_rank"]))
    remaining.sort(key=lambda row: int(row["standard_rank"]))
    write_csv(APPLIED_CSV, applied)
    write_csv(REMAINING_CSV, remaining)

    applied_status = Counter(row["radical_resolution_status"] for row in applied)
    applied_source = Counter(row["radical_source"] for row in applied)
    remaining_reason = Counter(row["remaining_reason"] for row in remaining)
    checks = {
        "runtime_row_count_preserved": len(repaired_rows) == EXPECTED_RUNTIME_ROWS,
        "runtime_unique_unicode_preserved": len({row["unicode"] for row in repaired_rows}) == EXPECTED_RUNTIME_ROWS,
        "runtime_unique_char_preserved": len({row["char"] for row in repaired_rows}) == EXPECTED_RUNTIME_ROWS,
        "applied_plus_remaining_matches_prior_queue": len(applied) + len(remaining) == previous_remaining == len(blockers),
        "all_applied_roundtrip_pass": all(row["roundtrip_pass"] is True for row in applied),
        "all_databases_integrity_ok": all(report["sqlite_integrity_check"] == "ok" for report in db_reports),
        "missing_current_rows_not_inserted": all(
            row["remaining_reason"] == "missing_current_model_row"
            for row in remaining
            if row.get("block_reason") == "missing_current_model_row"
        ),
        "known_samples": (
            rows_by_char.get("㑇") is None
            and next(row for row in repaired_rows if row["char"] == "队")["radix_name"] == "阜"
            and next(row for row in repaired_rows if row["char"] == "队")["struct_name"] == "左右"
            and next(row for row in repaired_rows if row["char"] == "玕")["radix_name"] == "王"
            and next(row for row in repaired_rows if row["char"] == "玕")["struct_name"] == "左右"
            and next(row for row in repaired_rows if row["char"] == "冁")["struct_name"] == "single"
        ),
    }
    report = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "mode": "authorized_8105_standardized_runtime_repair",
            "repair_id": REPAIR_ID,
            "runtime_json": str(RUNTIME_JSON),
            "approved_packet": str(APPROVED_PACKET),
            "blocker_queue": str(BLOCKER_QUEUE),
            "zdic_cache": str(ZDIC_CACHE),
            "authority_boundary": "8105_agent_standard_runtime_repair_not_full_national_standard_claim",
        },
        "overall_status": "PASS_8105_STANDARDIZED_RUNTIME_REPAIR" if all(checks.values()) else "BLOCKED",
        "summary": {
            "prior_runtime_rows": len(runtime_model["characters"]),
            "runtime_rows": len(repaired_rows),
            "previous_patched_8105_rows": previous_patched,
            "applied_repair_rows": len(applied),
            "patched_8105_rows_after_repair": previous_patched + len(applied),
            "previous_force_approved_not_patched_rows": previous_remaining,
            "remaining_force_approved_not_patched_rows": len(remaining),
            "applied_radical_resolution_counts": dict(applied_status),
            "applied_radical_source_counts": dict(applied_source),
            "remaining_reason_counts": dict(remaining_reason),
            "databases_rebuilt": len(db_reports),
        },
        "checks": checks,
        "databases": db_reports,
        "known_samples": {
            char: next((row for row in repaired_rows if row["char"] == char), None)
            for char in ("队", "玕", "刁", "冁", "㑇", "家", "侵", "偶", "孓")
        },
        "outputs": {
            "json_report": str(JSON_REPORT),
            "markdown_report": str(MD_REPORT),
            "applied_csv": str(APPLIED_CSV),
            "remaining_csv": str(REMAINING_CSV),
            "runtime_json": str(RUNTIME_JSON),
            "root_db": str(ROOT_DB),
            "package_db": str(PACKAGE_DB),
        },
        "decision": {
            "may_review_runtime_repair": all(checks.values()),
            "remaining_requires_index_or_radical_policy": len(remaining) > 0,
            "may_tag_release_or_publish": False,
        },
    }
    write_json(JSON_REPORT, report)
    write_text(MD_REPORT, render_markdown(report))
    return report


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    sample_rows = []
    for char, row in report["known_samples"].items():
        if row is None:
            sample_rows.append([char, "", "missing", "", "", "", ""])
        else:
            sample_rows.append(
                [
                    char,
                    f"U+{int(row['unicode']):04X}",
                    f"0x{int(row['cnbe']):08X}",
                    row["radix_name"],
                    row["strokes"],
                    row["struct_name"],
                    row["struct_type"],
                ]
            )
    return "\n".join(
        [
            "# 8105 Standardized Runtime Repair",
            "",
            f"- Overall status: `{report['overall_status']}`",
            f"- Runtime rows: {summary['runtime_rows']}",
            f"- Applied repair rows: {summary['applied_repair_rows']}",
            f"- Patched 8105 rows after repair: {summary['patched_8105_rows_after_repair']}",
            f"- Remaining force-approved not-patched rows: {summary['remaining_force_approved_not_patched_rows']}",
            f"- Databases rebuilt: {summary['databases_rebuilt']}",
            "",
            "This release-track repair keeps 8105 as the core baseline and",
            "treats ZDIC/cache data only as cross-reference context. It does not",
            "insert characters missing from the current runtime model and does",
            "not authorize tag, release, or PyPI publication.",
            "",
            "## Applied Radical Sources",
            "",
            markdown_table(
                ["Source", "Rows"],
                [[key, value] for key, value in sorted(summary["applied_radical_source_counts"].items())],
            ),
            "",
            "## Applied Radical Resolution",
            "",
            markdown_table(
                ["Resolution", "Rows"],
                [[key, value] for key, value in sorted(summary["applied_radical_resolution_counts"].items())],
            ),
            "",
            "## Remaining Blockers",
            "",
            markdown_table(
                ["Reason", "Rows"],
                [[key, value] for key, value in sorted(summary["remaining_reason_counts"].items())],
            ),
            "",
            "## Known Samples",
            "",
            markdown_table(["Char", "Unicode", "CNBE", "Radical", "Strokes", "Structure", "Type"], sample_rows),
            "",
        ]
    )


def main() -> None:
    report = build()
    print(report["overall_status"])
    print(f"applied_repair_rows={report['summary']['applied_repair_rows']}")
    print(f"remaining_force_approved_not_patched_rows={report['summary']['remaining_force_approved_not_patched_rows']}")
    for db_report in report["databases"]:
        print(f"{db_report['path']} rows={db_report['row_count']} integrity={db_report['sqlite_integrity_check']}")


if __name__ == "__main__":
    main()
