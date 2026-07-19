#!/usr/bin/env python3
"""Read-only audit for the local CNBE Chinese-standard research workspace."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_MANIFEST = Path("data/sources/cnbe-research-local.json")
DEFAULT_OUTPUT = Path("reports/cnbe_research_source_audit.json")
CHUNK_SIZE = 1024 * 1024
CANONICAL_UNICODE_RE = re.compile(r"^U\+[0-9A-F]{4,5}$")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_manifest(path: Path) -> dict[str, Any]:
    manifest = load_json(path)
    if manifest.get("schema_version") != 1:
        raise ValueError("manifest schema_version must be 1")
    if "source_root" not in manifest:
        raise ValueError("manifest missing source_root")
    return manifest


def status(ok: bool) -> str:
    return "PASS" if ok else "FAIL"


def inspect_json_shape(data: Any, expected: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {"json_type": type(data).__name__}
    if isinstance(data, dict):
        result["top_level_count"] = len(data)
        result["top_level_keys_sample"] = list(data)[:20]
    elif isinstance(data, list):
        result["top_level_count"] = len(data)
        result["first_item_keys"] = list(data[0])[:20] if data and isinstance(data[0], dict) else []

    expected_type = expected.get("type")
    if expected_type:
        result["type_status"] = status(result["json_type"] == expected_type)
    for key in ("count", "target_count"):
        if key in expected:
            result[f"{key}_status"] = status(result.get("top_level_count") == expected[key])
            result[key] = expected[key]
    if "min_count" in expected:
        result["min_count_status"] = status(result.get("top_level_count", 0) >= expected["min_count"])
        result["min_count"] = expected["min_count"]
    return result


def inspect_specific_source(source_id: str, data: Any) -> dict[str, Any]:
    if source_id == "base_character_data" and isinstance(data, dict):
        return {
            "actual_count": len(data),
            "target_8105_delta": 8105 - len(data),
            "has_duplicate_keys": len(data) != len(set(data)),
            "unicode_label_issues": count_unicode_label_issues(data.values()),
        }
    if source_id == "cnbe_character_knowledge" and isinstance(data, list):
        return {
            "actual_count": len(data),
            "target_8105_delta": 8105 - len(data),
            "unicode_label_issues": count_unicode_label_issues(data),
            "with_dictionary_entry": sum(1 for row in data if row.get("has_dictionary_entry")),
            "with_wiki_entry": sum(1 for row in data if row.get("has_wiki_entry")),
        }
    if source_id == "component_db" and isinstance(data, dict):
        char_mappings = data.get("char_mappings", {})
        comp_mappings = data.get("comp_mappings", {})
        return {
            "char_mappings": len(char_mappings) if isinstance(char_mappings, dict) else 0,
            "component_mappings": len(comp_mappings) if isinstance(comp_mappings, dict) else 0,
            "coverage": data.get("char_coverage", {}),
        }
    if source_id == "decomp_rules" and isinstance(data, dict):
        return {
            "chars_with_ids": data.get("chars_with_ids"),
            "chars_single_component": data.get("chars_single_component"),
            "chars_needing_rules": data.get("chars_needing_rules"),
            "rule_count": len(data.get("rules", [])),
        }
    if source_id == "kangxi_radicals" and isinstance(data, dict):
        radical_data = data.get("data", {})
        return {"data_count": len(radical_data) if isinstance(radical_data, dict) else 0}
    if source_id == "cnbe32_updated" and isinstance(data, dict):
        characters = data.get("characters", [])
        struct_counts = Counter(str(row.get("struct_type")) for row in characters if isinstance(row, dict))
        return {
            "character_count": len(characters) if isinstance(characters, list) else 0,
            "struct_distribution": dict(sorted(struct_counts.items())),
            "diagnostic_only": True,
        }
    if source_id == "cnbe32_addendum" and isinstance(data, list):
        return {"addendum_count": len(data), "chars": [row.get("char") for row in data[:20] if isinstance(row, dict)]}
    if source_id == "alignment_report" and isinstance(data, dict):
        return {
            "common_chars": data.get("common_chars"),
            "missing_in_cnbe32": len(data.get("missing_in_cnbe32", [])),
            "missing_in_standard": len(data.get("missing_in_standard", [])),
        }
    if source_id == "alignment_report_v2" and isinstance(data, dict):
        return {"alignment_summary": data.get("alignment_summary")}
    if source_id == "decomposition_dictionary" and isinstance(data, list):
        invalid = [row.get("character") for row in data if isinstance(row, dict) and str(row.get("decomposition", "")).startswith("?")]
        return {"dictionary_count": len(data), "unknown_decomposition_count": len(invalid), "unknown_samples": invalid[:20]}
    return {}


def count_unicode_label_issues(rows: Any) -> dict[str, Any]:
    issues = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        label = row.get("unicode")
        char = row.get("char")
        if not isinstance(label, str):
            continue
        expected = f"U+{ord(char):04X}" if isinstance(char, str) and len(char) == 1 else None
        if not CANONICAL_UNICODE_RE.match(label) or (expected is not None and label != expected):
            issues.append({"char": char, "unicode": label, "expected": expected})
    return {"count": len(issues), "samples": issues[:20]}


def inspect_source(source_root: Path, entry: dict[str, Any]) -> dict[str, Any]:
    path = source_root / entry["relative_path"]
    result: dict[str, Any] = {
        "id": entry["id"],
        "relative_path": entry["relative_path"],
        "kind": entry["kind"],
        "acceptance": entry["acceptance"],
        "exists": path.exists(),
    }
    if not path.exists():
        result["status"] = "FAIL"
        result["error"] = "missing file"
        return result
    size = path.stat().st_size
    digest = sha256_file(path)
    result.update(
        {
            "size_bytes": size,
            "expected_size_bytes": entry["size_bytes"],
            "sha256": digest,
            "expected_sha256": entry["sha256"],
            "identity_status": status(size == entry["size_bytes"] and digest == entry["sha256"]),
        }
    )
    expected = entry.get("expected", {})
    if expected.get("zip"):
        result["zip"] = inspect_zip(path)
    elif path.suffix == ".json":
        data = load_json(path)
        result["json"] = inspect_json_shape(data, expected)
        result["domain"] = inspect_specific_source(entry["id"], data)
    elif path.suffix in {".md", ".txt"}:
        line_count = sum(1 for _ in path.open("r", encoding="utf-8-sig", errors="replace"))
        result["text"] = {"line_count": line_count}
        if "min_lines" in expected:
            result["text"]["min_lines_status"] = status(line_count >= expected["min_lines"])
    result["status"] = source_status(result)
    return result


def inspect_zip(path: Path) -> dict[str, Any]:
    try:
        with zipfile.ZipFile(path) as archive:
            members = archive.namelist()
    except zipfile.BadZipFile:
        return {"status": "FAIL", "error": "bad zip"}
    return {"status": "PASS", "member_count": len(members), "members_sample": members[:20]}


def source_status(result: dict[str, Any]) -> str:
    if result.get("identity_status") != "PASS":
        return "FAIL"
    json_result = result.get("json", {})
    if any(value == "FAIL" for key, value in json_result.items() if key.endswith("_status")):
        return "ATTENTION"
    domain = result.get("domain", {})
    if isinstance(domain.get("unicode_label_issues"), dict) and domain["unicode_label_issues"].get("count", 0):
        return "ATTENTION"
    if domain.get("target_8105_delta") not in (None, 0):
        return "ATTENTION"
    zip_result = result.get("zip", {})
    if zip_result and zip_result.get("status") != "PASS":
        return "FAIL"
    text_result = result.get("text", {})
    if any(value == "FAIL" for key, value in text_result.items() if key.endswith("_status")):
        return "ATTENTION"
    return "PASS"


def inspect_directory(source_root: Path, entry: dict[str, Any]) -> dict[str, Any]:
    path = source_root / entry["relative_path"]
    json_files = sorted(path.rglob("*.json")) if path.exists() else []
    markdown_files = sorted(path.rglob("*.md")) if path.exists() else []
    expected = entry.get("expected", {})
    checks = {
        "json_files": len(json_files),
        "markdown_files": len(markdown_files),
    }
    if "json_files_min" in expected:
        checks["json_files_min_status"] = status(len(json_files) >= expected["json_files_min"])
    if "markdown_files_min" in expected:
        checks["markdown_files_min_status"] = status(len(markdown_files) >= expected["markdown_files_min"])
    return {
        "id": entry["id"],
        "relative_path": entry["relative_path"],
        "kind": entry["kind"],
        "acceptance": entry["acceptance"],
        "exists": path.exists(),
        "checks": checks,
        "status": "PASS" if path.exists() and all(value != "FAIL" for value in checks.values()) else "FAIL",
    }


def inspect_excluded(source_root: Path, entry: dict[str, Any]) -> dict[str, Any]:
    path = source_root / entry["relative_path"]
    result = {"relative_path": entry["relative_path"], "reason": entry["reason"], "exists": path.exists()}
    if path.exists():
        result["size_bytes"] = path.stat().st_size
        result["sha256"] = sha256_file(path)
        if path.suffix == ".zip":
            result["zip"] = inspect_zip(path)
    return result


def build_report(manifest_path: Path) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    source_root = Path(manifest["source_root"])
    sources = [inspect_source(source_root, entry) for entry in manifest.get("sources", [])]
    directories = [inspect_directory(source_root, entry) for entry in manifest.get("directories", [])]
    excluded = [inspect_excluded(source_root, entry) for entry in manifest.get("excluded_sources", [])]
    source_counts = Counter(item["status"] for item in sources)
    directory_counts = Counter(item["status"] for item in directories)
    action_items = action_item_summary(sources, directories, excluded)
    generation_gate = "NO_GO" if action_items else "REVIEW_REQUIRED"
    return {
        "report_schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "audit_mode": "read_only_external_research_exploration",
        "manifest": str(manifest_path),
        "source_root": str(source_root),
        "summary": {
            "status": "ACTION_REQUIRED" if action_items else "PASS",
            "sources_total": len(sources),
            "sources_pass": source_counts["PASS"],
            "sources_attention": source_counts["ATTENTION"],
            "sources_fail": source_counts["FAIL"],
            "directories_total": len(directories),
            "directories_pass": directory_counts["PASS"],
            "directories_fail": directory_counts["FAIL"],
            "encoding_generation_gate": generation_gate,
            "sdk_replacement_allowed": False,
            "sqlite_build_allowed": False,
        },
        "sources": sources,
        "directories": directories,
        "excluded_sources": excluded,
        "action_items": action_items,
        "recommended_next_stage": "normalize_standard_character_table_and_unicode_labels",
    }


def action_item_summary(
    sources: list[dict[str, Any]],
    directories: list[dict[str, Any]],
    excluded: list[dict[str, Any]],
) -> list[str]:
    items = []
    for source in sources:
        if source["status"] == "FAIL":
            items.append(f"{source['id']}: identity or readability failed")
        if source["status"] == "ATTENTION":
            items.append(f"{source['id']}: schema/count/normalization attention required")
    for directory in directories:
        if directory["status"] == "FAIL":
            items.append(f"{directory['id']}: directory minimum checks failed")
    return items


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parent.parent
    manifest_path = (repo_root / args.manifest).resolve() if not args.manifest.is_absolute() else args.manifest
    output = (repo_root / args.output).resolve() if not args.output.is_absolute() else args.output
    try:
        report = build_report(manifest_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"CNBE RESEARCH SOURCE AUDIT ERROR: {exc}", file=sys.stderr)
        return 2
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"CNBE RESEARCH SOURCE AUDIT {report['summary']['status']}: {output}")
    print(f"Sources: {report['summary']['sources_pass']} PASS, {report['summary']['sources_attention']} ATTENTION")
    print(f"Encoding generation gate: {report['summary']['encoding_generation_gate']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
