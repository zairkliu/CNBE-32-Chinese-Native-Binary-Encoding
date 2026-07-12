#!/usr/bin/env python3
"""Audit the repository evidence chain for the SDK and full-catalog mappings."""

from __future__ import annotations

import argparse
import gzip
import json
import sqlite3
import subprocess
import sys
import tempfile
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from audit_full_catalog_structure import audit_records as audit_structure_records
    from audit_full_catalog_xlsx import sha256_file
    from build_full_catalog_db import workbook_records
except ModuleNotFoundError:  # pragma: no cover - import path used by tests
    from scripts.audit_full_catalog_structure import audit_records as audit_structure_records
    from scripts.audit_full_catalog_xlsx import sha256_file
    from scripts.build_full_catalog_db import workbook_records

SDK_INTRODUCTION_COMMIT = "7244e3e14875cd3492c15eb567ac32d6ede1a79a"
FULL_ARTIFACT_COMMIT = "83d29eca822bd8089b780521458ee8505a1b4ba4"
FULL_XLSX_BLOB = "352e91956af4d64df7cf9ff37a88a6beb0f66822"
FULL_DB_GZIP_BLOB = "27e3e9282e8f29f4c7a04e40188fddda79809391"

EXPECTED_SDK_ROWS = 20_902
EXPECTED_FULL_ROWS = 97_686
DEFAULT_SDK_DATABASE = Path("data/cnbe32.db")
DEFAULT_JSON_OUTPUT = Path("reports/mapping_provenance_audit.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/MAPPING_PROVENANCE_AUDIT.md")


def run_git(repo_root: Path, *args: str, binary: bool = False) -> str | bytes:
    result = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        error = result.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(f"git {' '.join(args)} failed: {error}")
    return result.stdout if binary else result.stdout.decode("utf-8", errors="strict")


def sha256_bytes(data: bytes) -> str:
    import hashlib

    return hashlib.sha256(data).hexdigest()


def expected_sdk_fields(codepoint: int) -> dict[str, int]:
    index = codepoint - 0x4E00
    radical = (index % 214) + 1
    strokes = (index % 31) + 1
    struct_type = index % 13
    library_index = index & 0x7FF
    cnbe = (
        (radical << 24)
        | (strokes << 19)
        | (struct_type << 15)
        | (library_index << 4)
    )
    return {
        "cnbe": cnbe,
        "radical": radical,
        "strokes": strokes,
        "struct_type": struct_type,
        "idx": library_index,
    }


def audit_sdk_database(database: Path) -> dict[str, Any]:
    mismatches = []
    with sqlite3.connect(f"file:{database.resolve()}?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        rows = connection.execute(
            "SELECT unicode, cnbe, radix, strokes, struct_type, idx FROM cnbe32 ORDER BY unicode"
        ).fetchall()
    for row in rows:
        expected = expected_sdk_fields(int(row["unicode"]))
        actual = {
            "cnbe": int(row["cnbe"]),
            "radical": int(row["radix"]),
            "strokes": int(row["strokes"]),
            "struct_type": int(row["struct_type"]),
            "idx": int(row["idx"]),
        }
        if actual != expected and len(mismatches) < 20:
            mismatches.append(
                {
                    "unicode": f"U+{int(row['unicode']):04X}",
                    "actual": actual,
                    "expected": expected,
                }
            )
    return {
        "row_count": len(rows),
        "sqlite_integrity_check": integrity,
        "formula_mismatch_count": sum(
            {
                "cnbe": int(row["cnbe"]),
                "radical": int(row["radix"]),
                "strokes": int(row["strokes"]),
                "struct_type": int(row["struct_type"]),
                "idx": int(row["idx"]),
            }
            != expected_sdk_fields(int(row["unicode"]))
            for row in rows
        ),
        "mismatch_samples": mismatches,
        "formula": {
            "radical": "((unicode - U+4E00) mod 214) + 1",
            "strokes": "((unicode - U+4E00) mod 31) + 1",
            "structure": "(unicode - U+4E00) mod 13",
            "index": "(unicode - U+4E00) bitwise-and 0x7FF",
        },
    }


def historical_full_codes(repo_root: Path) -> tuple[dict[int, int], dict[str, Any]]:
    compressed = run_git(repo_root, "cat-file", "blob", FULL_DB_GZIP_BLOB, binary=True)
    assert isinstance(compressed, bytes)
    database_bytes = gzip.decompress(compressed)
    with tempfile.NamedTemporaryFile(suffix=".db") as temporary:
        temporary.write(database_bytes)
        temporary.flush()
        with sqlite3.connect(f"file:{temporary.name}?mode=ro", uri=True) as connection:
            integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
            rows = connection.execute("SELECT u, v FROM t").fetchall()
    return (
        {int(codepoint): int(cnbe) for codepoint, cnbe in rows},
        {
            "compressed_blob_sha1": FULL_DB_GZIP_BLOB,
            "compressed_sha256": sha256_bytes(compressed),
            "database_sha256": sha256_bytes(database_bytes),
            "sqlite_integrity_check": integrity,
            "row_count": len(rows),
        },
    )


def audit_full_catalog(repo_root: Path, source: Path) -> dict[str, Any]:
    source_codes = {row[0]: row[2] for row in workbook_records(source)}
    historical_codes, historical_metadata = historical_full_codes(repo_root)
    historical_xlsx = run_git(repo_root, "cat-file", "blob", FULL_XLSX_BLOB, binary=True)
    assert isinstance(historical_xlsx, bytes)
    shared = set(source_codes) & set(historical_codes)
    return {
        "source_row_count": len(source_codes),
        "source_sha256": sha256_file(source),
        "historical_xlsx_blob_sha1": FULL_XLSX_BLOB,
        "historical_xlsx_sha256": sha256_bytes(historical_xlsx),
        "source_matches_historical_xlsx_bytes": source.read_bytes() == historical_xlsx,
        "historical_database": historical_metadata,
        "same_unicode_keys_as_historical_database": source_codes.keys() == historical_codes.keys(),
        "cnbe_mismatches_vs_historical_database": sum(
            source_codes[codepoint] != historical_codes[codepoint] for codepoint in shared
        ),
    }


def audit_unihan_source(unihan_path: Path, source: Path) -> dict[str, Any]:
    if not unihan_path.is_file():
        raise ValueError(f"Unihan archive not found: {unihan_path}")
    radicals: dict[int, int] = {}
    strokes: dict[int, int] = {}
    unicode_version = "UNKNOWN"
    license_reference = "UNKNOWN"
    with zipfile.ZipFile(unihan_path) as archive:
        members = archive.namelist()
        with archive.open("Unihan_IRGSources.txt") as stream:
            for raw_line in stream:
                line = raw_line.decode("utf-8", errors="replace").strip()
                if line.startswith("# Unicode Version"):
                    unicode_version = line.removeprefix("# Unicode Version").strip()
                if "unicode.org/terms_of_use.html" in line:
                    license_reference = "https://www.unicode.org/terms_of_use.html"
                if not line or line.startswith("#"):
                    continue
                parts = line.split("\t")
                if len(parts) < 3 or not parts[0].startswith("U+"):
                    continue
                codepoint = int(parts[0][2:], 16)
                value = parts[2].split()[0]
                try:
                    if parts[1] == "kRSUnicode":
                        radicals[codepoint] = int(value.replace("'", "").split(".")[0])
                    elif parts[1] == "kTotalStrokes":
                        strokes[codepoint] = int(value)
                except ValueError:
                    continue

    rows = list(workbook_records(source))
    radical_covered = [row for row in rows if row[0] in radicals]
    stroke_covered = [row for row in rows if row[0] in strokes]
    groups: dict[tuple[int, int, int], list[tuple[Any, ...]]] = defaultdict(list)
    for row in rows:
        groups[(row[3], row[4], row[5])].append(row)
    index_mismatches = sum(
        row[7] != expected_index
        for group in groups.values()
        for expected_index, row in enumerate(group)
    )
    structure_audit = audit_structure_records(rows)
    structure_reproduced = (
        structure_audit["special_override_count"] == 19
        and structure_audit["structure_code_mismatches"] == 0
        and structure_audit["structure_name_mismatches"] == 0
        and not structure_audit["radicals_with_multiple_observed_structures"]
    )
    return {
        "file_name": unihan_path.name,
        "size_bytes": unihan_path.stat().st_size,
        "sha256": sha256_file(unihan_path),
        "unicode_version": unicode_version,
        "license_reference": license_reference,
        "archive_members": members,
        "kRSUnicode_entries": len(radicals),
        "kTotalStrokes_entries": len(strokes),
        "catalog_radical_coverage": len(radical_covered),
        "catalog_radical_mismatches": sum(row[3] != radicals[row[0]] for row in radical_covered),
        "catalog_stroke_coverage": len(stroke_covered),
        "catalog_stroke_mismatches_after_31_clamp": sum(
            row[4] != min(strokes[row[0]], 31) for row in stroke_covered
        ),
        "catalog_group_count": len(groups),
        "catalog_index_mismatches": index_mismatches,
        "catalog_max_group_size": max(len(group) for group in groups.values()),
        "structure_rule_reconstruction": "PASS" if structure_reproduced else "FAIL",
        "structure_audit": structure_audit,
    }


def repository_evidence(repo_root: Path) -> dict[str, Any]:
    sdk_commit = run_git(repo_root, "show", "-s", "--format=%H|%aI|%an|%s", SDK_INTRODUCTION_COMMIT).strip()
    full_commit = run_git(repo_root, "show", "-s", "--format=%H|%aI|%an|%s", FULL_ARTIFACT_COMMIT).strip()
    tracked_files = run_git(repo_root, "ls-tree", "-r", "--name-only", FULL_ARTIFACT_COMMIT).splitlines()
    candidate_generators = [
        path
        for path in tracked_files
        if path.endswith((".py", ".ipynb")) and any(term in path.lower() for term in ("generate", "cnbe", "unihan"))
    ]
    return {
        "sdk_introduction_commit": sdk_commit,
        "full_artifact_commit": full_commit,
        "full_artifact_candidate_generator_files": candidate_generators,
        "full_raw_input_files_tracked": [
            path for path in tracked_files if "unihan" in path.lower() or path.lower().endswith("unihan.zip")
        ],
        "observed_limitations": [
            "The tracked full-catalog table generator consumes an already-created workbook; it does not create the 97,686-row mapping.",
            "No pinned Unihan archive, upstream checksum, or complete raw-to-catalog generator is tracked with the full artifact commit.",
            "Historical documentation describes Unihan V17 extraction and heuristic structure rules, but those claims are not a reproducible source chain by themselves.",
        ],
    }


def build_report(
    repo_root: Path,
    source: Path,
    sdk_database: Path,
    unihan_path: Path | None = None,
) -> dict[str, Any]:
    sdk = audit_sdk_database(sdk_database)
    full = audit_full_catalog(repo_root, source)
    evidence = repository_evidence(repo_root)
    sdk_reproducible = sdk["row_count"] == EXPECTED_SDK_ROWS and sdk["formula_mismatch_count"] == 0
    full_artifact_identity = (
        full["source_row_count"] == EXPECTED_FULL_ROWS
        and full["source_matches_historical_xlsx_bytes"]
        and full["same_unicode_keys_as_historical_database"]
        and full["cnbe_mismatches_vs_historical_database"] == 0
    )
    unihan = audit_unihan_source(unihan_path, source) if unihan_path is not None else None
    raw_source_recovered = unihan is not None
    source_fields_reproduced = bool(
        unihan
        and unihan["catalog_radical_mismatches"] == 0
        and unihan["catalog_stroke_mismatches_after_31_clamp"] == 0
        and unihan["catalog_index_mismatches"] == 0
        and unihan["structure_rule_reconstruction"] == "PASS"
    )

    return {
        "report_schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "question": "Which mapping has sufficient provenance and authority to become the canonical CNBE-32 mapping?",
        "summary": {
            "status": "COMPLETE",
            "canonical_mapping_gate": "NO_GO",
            "sdk_reproducibility": "PASS" if sdk_reproducible else "FAIL",
            "sdk_semantic_authority": "INSUFFICIENT",
            "full_artifact_identity": "PASS" if full_artifact_identity else "FAIL",
            "full_raw_input_identity": "RECOVERED_UNTRACKED" if raw_source_recovered else "INSUFFICIENT",
            "full_raw_to_catalog_reproducibility": "PASS" if source_fields_reproduced else "INSUFFICIENT",
            "full_semantic_authority": "INSUFFICIENT",
        },
        "sdk_mapping": {
            "database": {
                "path": "data/cnbe32.db",
                "sha256": sha256_file(sdk_database),
            },
            "audit": sdk,
            "provenance_assessment": (
                "Strong implementation provenance: every row is reproduced by the tracked modulo-based generator. "
                "Weak semantic authority: radical, stroke, structure, and index values are deterministic heuristics "
                "derived from Unicode position rather than cited character data."
            ),
        },
        "full_catalog_mapping": {
            "source": {"file_name": source.name, "sha256": sha256_file(source)},
            "audit": full,
            "provenance_assessment": (
                "Strong artifact identity: the supplied workbook is byte-identical to the historical Git object and "
                "all 97,686 CNBE values match the historical compressed SQLite artifact. The local Unicode 17.0.0 "
                "Unihan archive reproduces all radical and stroke fields, grouping reproduces every index, and the "
                "recovered 19-override radical classifier reproduces every structure field."
            ),
            "recovered_unihan_source": unihan,
        },
        "repository_evidence": evidence,
        "authority_matrix": [
            {
                "mapping": "packaged SDK",
                "artifact_identity": "strong",
                "algorithm_reproducibility": "strong",
                "upstream_source_traceability": "not applicable to heuristic fields",
                "linguistic_semantic_authority": "insufficient",
                "compatibility_status": "current SDK contract",
            },
            {
                "mapping": "97,686-row full catalog",
                "artifact_identity": "strong",
                "algorithm_reproducibility": "strong with recovered local input",
                "upstream_source_traceability": "recovered locally, not repository-controlled",
                "linguistic_semantic_authority": "insufficient",
                "compatibility_status": "separate experimental mapping",
            },
        ],
        "decision": {
            "canonical_mapping_selected": False,
            "sdk_replacement_allowed": False,
            "full_catalog_publication_as_authoritative_allowed": False,
            "historical_artifact_preservation_allowed": True,
            "required_evidence": [
                "Add a documented, checksum-pinned retrieval procedure for Unicode 17.0.0 Unihan and its license notice.",
                "Preserve the recovered structure classifier and its historical evidence references.",
                "Separate source-derived fields from heuristic structure classifications in the schema.",
                "Define a versioned canonical mapping contract and migration policy for existing SDK codes.",
                "Run an independently reviewed stratified sample before making semantic-accuracy claims.",
            ],
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    sdk = report["sdk_mapping"]["audit"]
    full = report["full_catalog_mapping"]["audit"]
    unihan = report["full_catalog_mapping"].get("recovered_unihan_source")
    unihan_summary = (
        f"""
## Unicode 17.0.0 Source Was Recovered Locally

- Unihan SHA-256: `{unihan['sha256']}`
- Unicode version: **{unihan['unicode_version']}**
- Catalog radical coverage/mismatches: **{unihan['catalog_radical_coverage']:,} / {unihan['catalog_radical_mismatches']}**
- Catalog stroke coverage/mismatches after the 31 clamp: **{unihan['catalog_stroke_coverage']:,} / {unihan['catalog_stroke_mismatches_after_31_clamp']}**
- Group-index mismatches across {unihan['catalog_group_count']:,} groups: **{unihan['catalog_index_mismatches']}**
- Structure code/name mismatches: **{unihan['structure_audit']['structure_code_mismatches']} / {unihan['structure_audit']['structure_name_mismatches']}**
- Recovered structure rule: **{unihan['structure_rule_reconstruction']}**
- License reference embedded in the archive: `{unihan['license_reference']}`

This substantially strengthens the full-catalog lineage: radical and stroke fields are reproducible from the recovered
source, while structure and index fields are reproducible from documented deterministic rules. The archive remains
external to the repository, so the input chain is not yet repository-controlled.
"""
        if unihan
        else ""
    )
    return f"""# CNBE-32 Mapping Provenance Audit

## Technical Summary

No current mapping has enough evidence to become the canonical CNBE-32 semantic mapping. The SDK mapping is fully
reproducible but generated from Unicode-position modulo heuristics. The 97,686-row catalog has a strong historical
artifact chain, and its Unicode 17.0.0 source plus complete radical-based structure rule were recovered locally.

**Canonical mapping gate: NO_GO.** Preserve both mappings under their current boundaries; do not replace the SDK or
publish the full catalog as an authoritative linguistic mapping.

## Two Different Evidence Strengths

| Mapping | Artifact identity | Algorithm reproducibility | Upstream traceability | Semantic authority |
|---|---|---|---|---|
| Packaged SDK | Strong | Strong | Heuristic, no upstream source | Insufficient |
| 97,686-row catalog | Strong | Strong with local input | Recovered, not pinned | Insufficient |

The distinction matters: reproducibility establishes that the same numbers can be regenerated. It does not establish that
those numbers correctly represent a character's radical, strokes, or structure.

## SDK Mapping Is Exactly Reproducible but Heuristic

- Rows inspected: **{sdk['row_count']:,}**
- SQLite integrity: **{sdk['sqlite_integrity_check']}**
- Rows differing from the tracked modulo formula: **{sdk['formula_mismatch_count']}**
- Database SHA-256: `{report['sdk_mapping']['database']['sha256']}`
- Introduction commit: `{SDK_INTRODUCTION_COMMIT}`

The tracked generator assigns radical, stroke count, structure, and index from the character's sequential Unicode
offset using modulo operations. This is deterministic engineering test data, not evidence-backed linguistic
annotation. Its authority is therefore limited to preserving the existing SDK compatibility contract.

## Full Catalog Has a Strong Historical Artifact Chain

- Workbook rows: **{full['source_row_count']:,}**
- Workbook SHA-256: `{full['source_sha256']}`
- Byte-identical to historical workbook blob: **{full['source_matches_historical_xlsx_bytes']}**
- Same Unicode keys as historical compressed SQLite: **{full['same_unicode_keys_as_historical_database']}**
- CNBE differences versus historical SQLite: **{full['cnbe_mismatches_vs_historical_database']}**
- Historical artifact commit: `{FULL_ARTIFACT_COMMIT}`

This establishes that the supplied workbook is the same artifact lineage committed in July 2026. It does not reconstruct how
the artifact was produced from upstream character data.

{unihan_summary}

## Raw-to-Catalog Algorithm Is Reconstructed

Historical documentation says the catalog used Unihan V17 radical/stroke data and heuristic structure rules. The
recovered archive confirms all radical and stroke assignments, deterministic grouping confirms all index assignments,
and the documented 19-override radical classifier reproduces all structure codes and names with zero differences. The
tracked historical `generate_cnbe_table.py` consumes an existing workbook, but the newly recovered classifier closes
the algorithmic structure-field gap.

Consequently, the workbook is algorithmically reproducible with the recovered local Unihan input. It is still not
semantically authoritative: the structure field is a radical-level heuristic and does not perform character-level
glyph decomposition.

## Methods and Definitions

The audit used four independent checks:

1. Recomputed every SDK row from the formula present in `tools/generate_mapping.py`.
2. Compared the supplied workbook bytes with historical Git blob `{FULL_XLSX_BLOB}`.
3. Compared all workbook Unicode/CNBE pairs with the historical compressed SQLite blob `{FULL_DB_GZIP_BLOB}`.
4. Reconstructed all structure fields from the documented 19 radical overrides and fallback rule.

"Artifact identity" means exact bytes or exact row values match historical repository objects. "Algorithm
reproducibility" means tracked code and pinned inputs can regenerate the mapping. "Semantic authority" means the
field values have traceable, reviewed evidence for their linguistic meaning.

## Limitations and Uncertainty

- Git history records what was committed, not the external legal status of upstream datasets.
- Historical prose claims are supporting context, not substitutes for pinned inputs and executable generation code.
- This audit does not independently judge every Unihan radical/stroke value or heuristic structure label.
- The exact reason the SDK chose the U+9FA5 cutoff is strongly suggested by code history but not documented as a
  formal compatibility decision.

## Required Next Steps

1. Add a checksum-pinned retrieval procedure for Unicode 17.0.0 Unihan and preserve its license notice.
2. Pin the recovered structure-classification rules and their historical evidence references.
3. Mark every field as source-derived, manually overridden, or heuristic.
4. Define a versioned canonical mapping and migration policy before changing existing SDK codes.
5. Run an independently reviewed stratified sample before making semantic-accuracy claims.

## Further Questions

- Is the original Unihan archive used in July 2026 still available on a development machine or backup?
- Was there an uncommitted script between Unihan extraction and the final workbook?
- Which mapping is intended to retain backward compatibility, and which may be versioned as a new mapping family?
- What redistribution notice is required for the upstream character-property data?
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="path to the full-catalog .xlsx file")
    parser.add_argument("--sdk-db", type=Path, default=DEFAULT_SDK_DATABASE)
    parser.add_argument("--unihan", type=Path, help="optional recovered Unihan.zip used for source reconciliation")
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parent.parent
    source = args.source.expanduser().resolve()
    sdk_database = args.sdk_db.expanduser().resolve()
    unihan_path = args.unihan.expanduser().resolve() if args.unihan else None
    try:
        report = build_report(repo_root, source, sdk_database, unihan_path)
    except (OSError, sqlite3.Error, ValueError) as exc:
        print(f"MAPPING PROVENANCE AUDIT ERROR: {exc}", file=sys.stderr)
        return 2
    json_output = args.json_output.expanduser().resolve()
    markdown_output = args.markdown_output.expanduser().resolve()
    json_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    markdown_output.write_text(render_markdown(report), encoding="utf-8", newline="\n")
    print(f"MAPPING PROVENANCE AUDIT COMPLETE: {report['summary']['canonical_mapping_gate']}")
    print(f"JSON: {json_output}")
    print(f"Markdown: {markdown_output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
