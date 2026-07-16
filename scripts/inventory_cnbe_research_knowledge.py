#!/usr/bin/env python3
"""Create a read-only inventory for the local cnbe-research knowledge assets."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_KNOWLEDGE_ROOT = Path("/Users/liuzhaoqi/Documents/cnbe-research/knowledge")
DEFAULT_OUTPUT = Path("reports/cnbe_research_knowledge_inventory.json")
CHUNK_SIZE = 1024 * 1024
JSONL_SAMPLE_LIMIT = 25
LARGE_JSON_THRESHOLD = 100 * 1024 * 1024
TEXT_SUFFIXES = {".json", ".md", ".txt", ".yaml", ".yml", ".toml", ".csv"}
CORE_DATASETS = {
    "structured/base_character_data.json": {
        "class": "primary_candidate",
        "expected_top_type": "dict",
        "expected_count": 8105,
        "purpose": "candidate normalized basic CJK character table",
    },
    "structured/cnbe_character_knowledge.json": {
        "class": "primary_candidate",
        "expected_top_type": "list",
        "expected_count": 8105,
        "purpose": "candidate merged character knowledge table",
    },
    "cnbe32_updated.json": {
        "class": "diagnostic",
        "expected_top_type": "dict",
        "purpose": "previous CNBE32 diagnostic output, not an encoding authority",
    },
    "yuanliu_chars.json": {
        "class": "reference_index",
        "expected_top_type": "dict",
        "purpose": "Chinese character origin reference index",
    },
    "structured/cihai_search_index.json": {
        "class": "reference_index",
        "expected_top_type": "dict",
        "purpose": "Ci Hai OCR/search index for human verification",
    },
    "stroke_order_8105_clean.json": {
        "class": "reference_index",
        "expected_top_type": "list",
        "purpose": "stroke order reference table",
    },
    "component_db.json": {
        "class": "reference_index",
        "expected_top_type": "dict",
        "purpose": "component and decomposition support data",
    },
    "wikipedia-zh-cn-20260501.json": {
        "class": "encyclopedia_semantic_index",
        "expected_top_type": "jsonl",
        "purpose": "offline Chinese Wikipedia semantic cross-check corpus",
    },
    "Unihan2.zip": {
        "class": "canonical_external_archive",
        "expected_top_type": "zip",
        "purpose": "pinned Unihan 17.0.0 archive candidate",
    },
    "Unihan.zip": {
        "class": "excluded_archive",
        "expected_top_type": "zip",
        "purpose": "legacy Unihan archive candidate, excluded unless integrity passes",
    },
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def status(ok: bool) -> str:
    return "PASS" if ok else "FAIL"


def relative_asset_path(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def classify_asset(relative_path: str, suffix: str) -> str:
    if relative_path in CORE_DATASETS:
        return CORE_DATASETS[relative_path]["class"]
    if "wikipedia" in relative_path.lower():
        return "encyclopedia_semantic_index"
    if relative_path.startswith("ocr/ci_hai/"):
        return "ocr_cihai_review_aid"
    if relative_path.startswith("ocr/standards/"):
        return "ocr_standard_review_aid"
    if relative_path.startswith("ocr/"):
        return "ocr_review_aid"
    if relative_path.startswith("structured/"):
        return "structured_reference"
    if relative_path.startswith("references/"):
        return "reference_note_or_scan"
    if suffix == ".zip":
        return "archive"
    if suffix == ".json":
        return "json_reference"
    if suffix in {".md", ".txt"}:
        return "documentation"
    return "other"


def read_text_traits(path: Path) -> dict[str, Any]:
    size = path.stat().st_size
    with path.open("rb") as handle:
        first = handle.read(3) if size else b""
    traits: dict[str, Any] = {
        "utf8_bom": first.startswith(b"\xef\xbb\xbf"),
        "contains_crlf": False,
        "contains_bare_cr": False,
        "line_count": 0,
        "ends_with_lf": False,
        "max_line_length": 0,
    }
    previous_tail = b""
    try:
        with path.open("rb") as handle:
            for raw_line in handle:
                traits["line_count"] += 1
                traits["max_line_length"] = max(traits["max_line_length"], len(raw_line.rstrip(b"\r\n")))
                if raw_line.endswith(b"\r\n"):
                    traits["contains_crlf"] = True
                elif raw_line.endswith(b"\r"):
                    traits["contains_bare_cr"] = True
                previous_tail = raw_line[-1:]
                raw_line.decode("utf-8-sig" if traits["line_count"] == 1 else "utf-8")
    except UnicodeDecodeError as exc:
        traits["utf8_status"] = "FAIL"
        traits["utf8_error"] = str(exc)
        return traits
    traits["utf8_status"] = "PASS"
    traits["ends_with_lf"] = previous_tail == b"\n"
    return traits


def safe_load_json(path: Path) -> tuple[Any | None, dict[str, Any]]:
    traits: dict[str, Any] = {}
    if path.stat().st_size >= LARGE_JSON_THRESHOLD:
        return None, inspect_jsonl(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        jsonl = inspect_jsonl(path)
        if jsonl["parse_status"] == "PASS":
            return None, jsonl
        traits["parse_status"] = "FAIL"
        traits["error"] = str(exc)
        traits["jsonl_error"] = jsonl.get("error")
        return None, traits
    except UnicodeDecodeError as exc:
        traits["parse_status"] = "FAIL"
        traits["error"] = str(exc)
        return None, traits
    traits["parse_status"] = "PASS"
    traits.update(json_shape(data))
    traits.update(extract_json_domain_metrics(data))
    return data, traits


def inspect_jsonl(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "parse_status": "FAIL",
        "top_type": "jsonl",
        "line_count": 0,
        "sampled_record_count": 0,
        "sample_keys": [],
    }
    key_counter: Counter[str] = Counter()
    try:
        with path.open("r", encoding="utf-8-sig") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                result["line_count"] += 1
                try:
                    record = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    result["error"] = f"line {line_number}: {exc}"
                    return result
                if isinstance(record, dict) and result["sampled_record_count"] < JSONL_SAMPLE_LIMIT:
                    result["sampled_record_count"] += 1
                    key_counter.update(record.keys())
    except UnicodeDecodeError as exc:
        result["error"] = str(exc)
        return result
    result["parse_status"] = "PASS"
    result["top_count"] = result["line_count"]
    result["sample_keys"] = [key for key, _count in key_counter.most_common(30)]
    return result


def json_shape(data: Any) -> dict[str, Any]:
    result: dict[str, Any] = {"top_type": type(data).__name__}
    if isinstance(data, dict):
        result["top_count"] = len(data)
        result["top_keys_sample"] = list(data)[:20]
        first_value = next(iter(data.values()), None)
        if isinstance(first_value, dict):
            result["first_value_keys"] = list(first_value)[:20]
    elif isinstance(data, list):
        result["top_count"] = len(data)
        if data and isinstance(data[0], dict):
            result["first_item_keys"] = list(data[0])[:20]
    return result


def extract_json_domain_metrics(data: Any) -> dict[str, Any]:
    result: dict[str, Any] = {}
    if isinstance(data, dict) and isinstance(data.get("characters"), list):
        result["character_count"] = len(data["characters"])
    if isinstance(data, dict) and {"verified", "match", "mismatch"} <= set(data):
        result["validation_match_rate"] = data.get("match_rate")
    if isinstance(data, dict) and {"st", "ts"} <= set(data):
        result["simplified_to_traditional_count"] = len(data.get("st", {}))
        result["traditional_to_simplified_count"] = len(data.get("ts", {}))
    if isinstance(data, list):
        confidence_values = []
        for item in data:
            if isinstance(item, dict) and isinstance(item.get("confidence"), (int, float)):
                confidence_values.append(float(item["confidence"]))
        if confidence_values:
            result["confidence"] = confidence_stats(confidence_values)
    return result


def confidence_stats(values: list[float]) -> dict[str, Any]:
    return {
        "count": len(values),
        "min": min(values),
        "max": max(values),
        "average": round(sum(values) / len(values), 2),
    }


def inspect_zip(path: Path) -> dict[str, Any]:
    try:
        with zipfile.ZipFile(path) as archive:
            members = archive.namelist()
            bad_member = archive.testzip()
    except zipfile.BadZipFile as exc:
        return {"status": "FAIL", "error": str(exc)}
    return {
        "status": "PASS" if bad_member is None else "FAIL",
        "member_count": len(members),
        "bad_member": bad_member,
        "members_sample": members[:20],
    }


def expected_asset_checks(relative_path: str, details: dict[str, Any]) -> dict[str, Any]:
    expected = CORE_DATASETS.get(relative_path)
    if not expected:
        return {}
    checks: dict[str, Any] = {
        "purpose": expected["purpose"],
        "expected_top_type": expected.get("expected_top_type"),
    }
    json_info = details.get("json", {})
    zip_info = details.get("zip", {})
    if expected.get("expected_top_type") == "zip":
        checks["top_type_status"] = status(zip_info.get("status") == "PASS")
    elif expected.get("expected_top_type") == "jsonl":
        checks["top_type_status"] = status(json_info.get("top_type") == "jsonl")
    elif "expected_top_type" in expected:
        checks["top_type_status"] = status(json_info.get("top_type") == expected["expected_top_type"])
    if "expected_count" in expected:
        checks["expected_count"] = expected["expected_count"]
        checks["actual_count"] = json_info.get("top_count")
        checks["count_status"] = status(json_info.get("top_count") == expected["expected_count"])
        checks["count_delta"] = expected["expected_count"] - int(json_info.get("top_count") or 0)
    return checks


def inspect_asset(root: Path, path: Path) -> dict[str, Any]:
    relative_path = relative_asset_path(root, path)
    suffix = path.suffix.lower()
    stat = path.stat()
    details: dict[str, Any] = {
        "relative_path": relative_path,
        "suffix": suffix or "[none]",
        "size_bytes": stat.st_size,
        "sha256": sha256_file(path),
        "category": classify_asset(relative_path, suffix),
    }
    if stat.st_size == 0:
        details["flags"] = ["empty_file"]
        return details
    if suffix in TEXT_SUFFIXES:
        details["text"] = read_text_traits(path)
    if suffix == ".json":
        _data, json_details = safe_load_json(path)
        details["json"] = json_details
    elif suffix == ".zip":
        details["zip"] = inspect_zip(path)
    expected_checks = expected_asset_checks(relative_path, details)
    if expected_checks:
        details["expected_checks"] = expected_checks
    flags = asset_flags(details)
    if flags:
        details["flags"] = flags
    return details


def asset_flags(details: dict[str, Any]) -> list[str]:
    flags = []
    if details["size_bytes"] == 0:
        flags.append("empty_file")
    text = details.get("text", {})
    if text.get("utf8_status") == "FAIL":
        flags.append("not_utf8_text")
    if text.get("utf8_bom"):
        flags.append("utf8_bom")
    if text.get("contains_crlf") or text.get("contains_bare_cr"):
        flags.append("non_lf_line_endings")
    json_info = details.get("json", {})
    if json_info.get("parse_status") == "FAIL":
        flags.append("json_parse_failed")
    zip_info = details.get("zip", {})
    if zip_info and zip_info.get("status") != "PASS":
        flags.append("zip_integrity_failed")
    expected = details.get("expected_checks", {})
    if expected.get("top_type_status") == "FAIL":
        flags.append("unexpected_top_type")
    if expected.get("count_status") == "FAIL":
        flags.append("count_mismatch")
    if details.get("category", "").startswith("ocr_"):
        confidence = json_info.get("confidence", {})
        if confidence and confidence.get("average", 100) < 70:
            flags.append("ocr_low_confidence_review_only")
    return flags


def aggregate_ocr_stats(assets: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[str, list[float]] = {
        "ocr": [],
        "ocr_standards": [],
        "ocr_ci_hai": [],
    }
    file_counts = Counter()
    for asset in assets:
        category = asset["category"]
        if not category.startswith("ocr_"):
            continue
        group = "ocr"
        if category == "ocr_standard_review_aid":
            group = "ocr_standards"
        elif category == "ocr_cihai_review_aid":
            group = "ocr_ci_hai"
        file_counts[group] += 1
        confidence = asset.get("json", {}).get("confidence", {})
        if confidence:
            groups[group].append(float(confidence.get("average", 0)))
    result: dict[str, Any] = {}
    for group, averages in groups.items():
        if not file_counts[group]:
            continue
        result[group] = {
            "file_count": file_counts[group],
            "files_with_confidence": len(averages),
            "average_of_file_average_confidence": round(sum(averages) / len(averages), 2) if averages else None,
        }
    return result


def summarize_assets(root: Path, assets: list[dict[str, Any]]) -> dict[str, Any]:
    suffix_counts = Counter(asset["suffix"] for asset in assets)
    category_counts = Counter(asset["category"] for asset in assets)
    flag_counts = Counter(flag for asset in assets for flag in asset.get("flags", []))
    json_assets = [asset for asset in assets if asset["suffix"] == ".json"]
    zip_assets = [asset for asset in assets if asset["suffix"] == ".zip"]
    json_pass = sum(1 for asset in json_assets if asset.get("json", {}).get("parse_status") == "PASS")
    zip_pass = sum(1 for asset in zip_assets if asset.get("zip", {}).get("status") == "PASS")
    return {
        "knowledge_root": str(root),
        "total_files": len(assets),
        "total_size_bytes": sum(asset["size_bytes"] for asset in assets),
        "suffix_counts": dict(sorted(suffix_counts.items())),
        "category_counts": dict(sorted(category_counts.items())),
        "flag_counts": dict(sorted(flag_counts.items())),
        "json_files": len(json_assets),
        "json_parse_pass": json_pass,
        "json_parse_fail": len(json_assets) - json_pass,
        "zip_files": len(zip_assets),
        "zip_integrity_pass": zip_pass,
        "zip_integrity_fail": len(zip_assets) - zip_pass,
        "ocr_summary": aggregate_ocr_stats(assets),
    }


def action_items(assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for asset in assets:
        flags = asset.get("flags", [])
        if not flags:
            continue
        relative_path = asset["relative_path"]
        if "count_mismatch" in flags:
            items.append(
                {
                    "severity": "BLOCKER",
                    "asset": relative_path,
                    "issue": "primary candidate count does not match 8105 target",
                    "next_step": "reconcile missing or duplicate basic CJK entry before encoding generation",
                }
            )
        if "zip_integrity_failed" in flags:
            items.append(
                {
                    "severity": "BLOCKER" if relative_path == "Unihan.zip" else "WARN",
                    "asset": relative_path,
                    "issue": "zip archive failed Python zipfile integrity check",
                    "next_step": "exclude or replace before treating as authoritative input",
                }
            )
        if "json_parse_failed" in flags:
            items.append(
                {
                    "severity": "BLOCKER",
                    "asset": relative_path,
                    "issue": "JSON file is not parseable",
                    "next_step": "repair source export or exclude file from structured inputs",
                }
            )
        if "ocr_low_confidence_review_only" in flags:
            items.append(
                {
                    "severity": "INFO",
                    "asset": relative_path,
                    "issue": "OCR confidence is low",
                    "next_step": "use as reviewer navigation aid only, not as direct authority",
                }
            )
    return items


def gate_summary(items: list[dict[str, Any]]) -> dict[str, Any]:
    blocker_count = sum(1 for item in items if item["severity"] == "BLOCKER")
    warn_count = sum(1 for item in items if item["severity"] == "WARN")
    return {
        "asset_confirmation_status": "ACTION_REQUIRED" if blocker_count else "PASS_WITH_NOTES",
        "blocker_count": blocker_count,
        "warning_count": warn_count,
        "encoding_generation_gate": "NO_GO" if blocker_count else "REVIEW_REQUIRED",
        "sqlite_build_gate": "NO_GO" if blocker_count else "REVIEW_REQUIRED",
        "sdk_replacement_allowed": False,
        "external_assets_imported": False,
    }


def build_inventory(knowledge_root: Path) -> dict[str, Any]:
    root = knowledge_root.resolve()
    if not root.exists():
        raise FileNotFoundError(f"knowledge root not found: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"knowledge root is not a directory: {root}")
    assets = [inspect_asset(root, path) for path in sorted(root.rglob("*")) if path.is_file()]
    items = action_items(assets)
    return {
        "report_schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "audit_mode": "read_only_asset_confirmation",
        "summary": summarize_assets(root, assets),
        "gates": gate_summary(items),
        "action_items": items,
        "assets": assets,
        "recommended_next_stage": "curate_authoritative_source_map_before_encoding_or_sqlite_build",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--knowledge-root", type=Path, default=DEFAULT_KNOWLEDGE_ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parent.parent
    output = (repo_root / args.output).resolve() if not args.output.is_absolute() else args.output
    try:
        inventory = build_inventory(args.knowledge_root)
    except (OSError, ValueError) as exc:
        print(f"CNBE RESEARCH KNOWLEDGE INVENTORY ERROR: {exc}", file=sys.stderr)
        return 2
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    summary = inventory["summary"]
    gates = inventory["gates"]
    print(f"CNBE RESEARCH KNOWLEDGE INVENTORY {gates['asset_confirmation_status']}: {output}")
    print(f"Assets: {summary['total_files']} files, JSON {summary['json_parse_pass']}/{summary['json_files']} parse")
    print(f"Zip integrity: {summary['zip_integrity_pass']}/{summary['zip_files']} pass")
    print(f"Encoding generation gate: {gates['encoding_generation_gate']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
