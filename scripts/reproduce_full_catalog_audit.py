#!/usr/bin/env python3
"""Run the read-only full-catalog provenance reproduction gate."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from audit_full_catalog_xlsx import audit_catalog, sha256_file
    from audit_mapping_provenance import (
        EXPECTED_FULL_ROWS,
        audit_full_catalog,
        audit_sdk_database,
        audit_unihan_source,
        repository_evidence,
    )
    from fetch_unihan_source import load_manifest, verify_archive
except ModuleNotFoundError:  # pragma: no cover - import path used by tests
    from scripts.audit_full_catalog_xlsx import audit_catalog, sha256_file
    from scripts.audit_mapping_provenance import (
        EXPECTED_FULL_ROWS,
        audit_full_catalog,
        audit_sdk_database,
        audit_unihan_source,
        repository_evidence,
    )
    from scripts.fetch_unihan_source import load_manifest, verify_archive

DEFAULT_SOURCE_MANIFEST = Path("data/sources/unihan-17.0.0.json")
DEFAULT_SDK_DATABASE = Path("data/cnbe32.db")
DEFAULT_OUTPUT = Path("reports/full_catalog_reproduction_audit.json")


def status_from_bool(value: bool) -> str:
    return "PASS" if value else "FAIL"


def field_evidence_matrix() -> list[dict[str, str]]:
    return [
        {
            "field": "unicode",
            "classification": "source_identity",
            "authority": "Unicode code point identity from the workbook and historical artifact.",
            "boundary": "Does not validate CNBE semantic field choices by itself.",
        },
        {
            "field": "char",
            "classification": "source_identity",
            "authority": "Character/code point equality is checked row by row.",
            "boundary": "Representative glyph variation is outside this audit.",
        },
        {
            "field": "radical",
            "classification": "upstream_derived",
            "authority": "Reproduced from Unicode 17.0.0 Unihan kRSUnicode.",
            "boundary": "Accepts Unihan data as upstream input; no independent radical adjudication.",
        },
        {
            "field": "strokes",
            "classification": "upstream_derived_with_31_clamp",
            "authority": "Reproduced from Unicode 17.0.0 Unihan kTotalStrokes with documented clamp.",
            "boundary": "Stroke counts above 31 are intentionally saturated by the CNBE bit field.",
        },
        {
            "field": "struct_type",
            "classification": "heuristic_derived",
            "authority": "Reproduced from the recovered radical-level structure classifier.",
            "boundary": "Not a character-level glyph decomposition and not semantic authority.",
        },
        {
            "field": "idx",
            "classification": "algorithm_derived",
            "authority": "Reproduced by grouping on radical, clamped strokes, and structure.",
            "boundary": "Only establishes deterministic historical indexing.",
        },
        {
            "field": "cnbe",
            "classification": "bitfield_derived",
            "authority": "Recomputed as R<<24 | S<<19 | G<<15 | I<<4 | E.",
            "boundary": "Depends on the upstream and heuristic fields above.",
        },
    ]


def build_report(repo_root: Path, source: Path, unihan: Path, sdk_database: Path, manifest_path: Path) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    source_verification = verify_archive(unihan, manifest)
    workbook_audit = audit_catalog(source, repo_root)
    full_audit = audit_full_catalog(repo_root, source)
    unihan_audit = audit_unihan_source(unihan, source)
    sdk_audit = audit_sdk_database(sdk_database)
    evidence = repository_evidence(repo_root)

    workbook_pass = workbook_audit.get("summary", {}).get("status") == "PASS"
    unihan_identity_pass = source_verification["status"] == "PASS"
    full_identity_pass = (
        full_audit["source_row_count"] == EXPECTED_FULL_ROWS
        and full_audit["source_matches_historical_xlsx_bytes"]
        and full_audit["same_unicode_keys_as_historical_database"]
        and full_audit["cnbe_mismatches_vs_historical_database"] == 0
    )
    raw_to_catalog_pass = (
        unihan_audit["catalog_radical_coverage"] == EXPECTED_FULL_ROWS
        and unihan_audit["catalog_radical_mismatches"] == 0
        and unihan_audit["catalog_stroke_coverage"] == EXPECTED_FULL_ROWS
        and unihan_audit["catalog_stroke_mismatches_after_31_clamp"] == 0
        and unihan_audit["catalog_index_mismatches"] == 0
        and unihan_audit["structure_rule_reconstruction"] == "PASS"
    )
    sdk_reproducible = sdk_audit["sqlite_integrity_check"] == "ok" and sdk_audit["formula_mismatch_count"] == 0
    overall_pass = workbook_pass and unihan_identity_pass and full_identity_pass and raw_to_catalog_pass

    return {
        "report_schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "status": status_from_bool(overall_pass),
            "canonical_mapping_gate": "NO_GO",
            "sqlite_build_gate": "NO_GO",
            "sdk_replacement_allowed": False,
            "semantic_authority": "INSUFFICIENT",
        },
        "inputs": {
            "catalog": {"path": str(source), "sha256": sha256_file(source)},
            "unihan_manifest": str(manifest_path),
            "unihan_archive": source_verification,
            "sdk_database": {"path": str(sdk_database), "sha256": sha256_file(sdk_database)},
        },
        "gates": {
            "catalog_quality": status_from_bool(workbook_pass),
            "unihan_identity": status_from_bool(unihan_identity_pass),
            "historical_full_artifact_identity": status_from_bool(full_identity_pass),
            "raw_to_catalog_reproducibility": status_from_bool(raw_to_catalog_pass),
            "sdk_current_contract_reproducibility": status_from_bool(sdk_reproducible),
            "semantic_authority": "INSUFFICIENT",
        },
        "field_evidence_matrix": field_evidence_matrix(),
        "catalog_quality_audit": workbook_audit,
        "historical_full_artifact_audit": full_audit,
        "unihan_reproduction_audit": unihan_audit,
        "sdk_current_contract_audit": sdk_audit,
        "repository_evidence": evidence,
        "decision": {
            "allowed_next_step": "semantic_stratified_review_protocol",
            "blocked_actions": [
                "Do not replace data/cnbe32.db.",
                "Do not publish the full catalog as authoritative.",
                "Do not tag, release, or publish to PyPI from this audit.",
                "Do not commit upstream ZIP or generated SQLite artifacts.",
            ],
            "required_before_sqlite_build": [
                "Keep the full catalog under an experimental provenance boundary.",
                "Record the pinned Unihan source manifest.",
                "Complete an independent stratified semantic review before accuracy claims.",
            ],
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="path to the 97,686-row catalog workbook")
    parser.add_argument("--unihan", type=Path, required=True, help="local Unicode 17.0.0 Unihan.zip")
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_SOURCE_MANIFEST)
    parser.add_argument("--sdk-db", type=Path, default=DEFAULT_SDK_DATABASE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parent.parent
    source = args.source.expanduser().resolve()
    unihan = args.unihan.expanduser().resolve()
    sdk_database = (repo_root / args.sdk_db).resolve() if not args.sdk_db.is_absolute() else args.sdk_db
    manifest_path = (
        (repo_root / args.source_manifest).resolve()
        if not args.source_manifest.is_absolute()
        else args.source_manifest
    )
    output = (repo_root / args.output).resolve() if not args.output.is_absolute() else args.output
    try:
        report = build_report(repo_root, source, unihan, sdk_database, manifest_path)
    except (OSError, sqlite3.Error, ValueError) as exc:
        print(f"FULL CATALOG REPRODUCTION ERROR: {exc}", file=sys.stderr)
        return 2
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"FULL CATALOG REPRODUCTION AUDIT {report['summary']['status']}: {output}")
    print(f"Canonical mapping gate: {report['summary']['canonical_mapping_gate']}")
    return 0 if report["summary"]["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
