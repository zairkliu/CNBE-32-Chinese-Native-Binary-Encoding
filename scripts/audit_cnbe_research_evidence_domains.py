#!/usr/bin/env python3
"""Map cnbe-research assets to CNBE-32 encoding evidence domains."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_RESEARCH_ROOT = Path("/Users/liuzhaoqi/Documents/cnbe-research")
DEFAULT_OUTPUT = Path("reports/cnbe_research_evidence_domains.json")
CHUNK_SIZE = 1024 * 1024
JSONL_SAMPLE_LIMIT = 25
LARGE_JSON_THRESHOLD = 100 * 1024 * 1024

EVIDENCE_DOMAINS: dict[str, dict[str, Any]] = {
    "standard_character_scope": {
        "cnbe_risk": "character inclusion, level, and normalized ordering must not be inferred from generated codes",
        "primary_sources": [
            "source/01-通用规范汉字表/通用规范汉字表(8105).json",
            "source/01-通用规范汉字表/通用规范汉字表(8105).md",
            "knowledge/ocr_char_table_all.json",
        ],
        "supporting_sources": [
            "knowledge/alignment_report.json",
            "knowledge/alignment_report_v2.json",
            "knowledge/cnbe32_addendum.json",
        ],
        "decision_rule": "Use for source-scope review and issue discovery, not as a standalone replacement trigger.",
    },
    "radical_classification": {
        "cnbe_risk": "CNBE radix fields can conflate Kangxi radicals, Unicode radical-stroke data, and modern indexing radicals",
        "primary_sources": [
            "source/02-汉字部首表/GG 0011-2009 汉字部首表.json",
            "source/02-汉字部首表/GG 0011-2009 汉字部首表.md",
            "knowledge/ocr/standards/std_02-汉字部首表_bc1.json",
        ],
        "supporting_sources": [
            "knowledge/kangxi_radicals.json",
            "knowledge/radical_validation.json",
            "knowledge/unicode_rsindex.json",
            "knowledge/unihan_radicals.json",
            "source/15-Unicode-RSIndex/RSIndex.md",
        ],
        "decision_rule": "Separate official modern radical table from Kangxi and Unicode indexes before any CNBE radix audit.",
    },
    "component_inventory": {
        "cnbe_risk": "component and decomposition fields are vulnerable to AI-inferred or heuristic composition errors",
        "primary_sources": [
            "source/03-部件及部件名称规范/GF 0014-2009 现代常用字部件及部件名称规范.json",
            "source/03-部件及部件名称规范/GF 0014-2009 现代常用字部件及部件名称规范.md",
            "source/06-汉字部件规范/信息处理用GB 13000.1 字符集汉字部件规范 （1998-5-1）.json",
            "source/06-汉字部件规范/信息处理用GB 13000.1 字符集汉字部件规范 （1998-5-1）.md",
            "knowledge/ocr/standards/std_03-部件及部件名称规范_bc1.json",
            "knowledge/ocr/standards/std_06-汉字部件规范_bc1.json",
        ],
        "supporting_sources": [
            "knowledge/component_db.json",
            "knowledge/decomp_rules.json",
            "decomp-data/dictionary.json",
            "cjk-decomp/cjk-decomp.txt",
        ],
        "decision_rule": "Treat standards as primary; use third-party decomposition only as disagreement discovery evidence.",
    },
    "single_component_and_structure": {
        "cnbe_risk": "structure labels can be overfit by visual heuristics instead of official single-component and layout rules",
        "primary_sources": [
            "source/04-独体字规范/GF 0013-2009 现代常用独体字规范.json",
            "source/04-独体字规范/GF 0013-2009 现代常用独体字规范.md",
            "knowledge/ocr/standards/std_04-独体字规范_bc1.json",
        ],
        "supporting_sources": [
            "knowledge/component_db.json",
            "knowledge/decomp_rules.json",
            "knowledge/structured/base_character_data.json",
            "knowledge/structured/cnbe_character_knowledge.json",
        ],
        "decision_rule": "Use as a structure review source; do not infer CNBE structure bits until conflicts are adjudicated.",
    },
    "stroke_count_order_and_shape": {
        "cnbe_risk": "stroke count, stroke order, and folded-stroke shape are separate linguistic facts but easy to collapse",
        "primary_sources": [
            "source/05-笔顺规范/GF 0031—2026 通用规范汉字笔顺规范.json",
            "source/05-笔顺规范/GF 0031—2026 通用规范汉字笔顺规范.md",
            "source/05-笔顺规范/GF3002-1999 GB13000.1字符集汉字笔顺规范.json",
            "source/05-笔顺规范/GF3002-1999 GB13000.1字符集汉字笔顺规范.md",
            "source/07-折笔规范/GB 13000.1 字符集汉字折笔规范.json",
            "source/07-折笔规范/GB 13000.1 字符集汉字折笔规范.md",
            "knowledge/stroke_order_8105.json",
            "knowledge/stroke_order_8105_clean.json",
        ],
        "supporting_sources": [
            "knowledge/ocr/ocr_stroke_order.json",
            "knowledge/ocr/ocr_fold_stroke.json",
            "knowledge/ocr/standards/std_07-折笔规范_bc1.json",
        ],
        "decision_rule": "Keep actual stroke count, stroke order sequence, and CNBE compact stroke field as separate columns.",
    },
    "stroke_based_ordering": {
        "cnbe_risk": "ordering fields must be traceable to a standard and must not be confused with Unicode or workbook order",
        "primary_sources": [
            "source/08-字序规范/GF3003-1999 GB13000.1字符集汉字字序（笔画序）规范.json",
            "source/08-字序规范/GF3003-1999 GB13000.1字符集汉字字序（笔画序）规范.md",
            "knowledge/ocr/standards/std_08-字序规范_bc1.json",
        ],
        "supporting_sources": [
            "knowledge/ocr/ocr_char_order.json",
            "knowledge/ocr_char_table_all.json",
        ],
        "decision_rule": "Use for review ordering and audit sort keys, not as a direct semantic encoding dimension.",
    },
    "etymology_dictionary_semantics": {
        "cnbe_risk": "semantic explanations improve academic defensibility but must not silently alter formal encoding bits",
        "primary_sources": [
            "source/13-汉字源流大典/汉字源流大典 钱中立主编 9典可搜索检字 中国语言文学学科建设文库.json",
            "source/13-汉字源流大典/汉字源流大典 钱中立主编 9典可搜索检字 中国语言文学学科建设文库.md",
            "knowledge/yuanliu_chars.json",
            "knowledge/etymology_data.json",
        ],
        "supporting_sources": [
            "knowledge/structured/definitions_index.json",
            "knowledge/structured/cihai_search_index.json",
            "knowledge/ocr/ci_hai/checkpoint.json",
            "knowledge/references/05-维基百科中文语料.md",
            "knowledge/wikipedia-zh-cn-20260501.json",
            "source/nlp-han-dicts/README.md",
        ],
        "decision_rule": "Use for scholarly notes, reviewer context, and conflict adjudication, not for automatic bit-field generation.",
    },
    "encoding_and_interchange_standards": {
        "cnbe_risk": "CNBE compatibility must be distinguished from Unicode, GB18030, and SDK database compatibility",
        "primary_sources": [
            "source/14-GB18030/GB+18030-2022.json",
            "source/14-GB18030/GB+18030-2022.md",
            "source/15-Unicode-RSIndex/RSIndex.md",
            "knowledge/Unihan2.zip",
            "knowledge/unicode_rsindex.json",
        ],
        "supporting_sources": [
            "knowledge/Unihan.zip",
            "knowledge/Unihan_RadicalStrokeCounts.txt",
            "knowledge/st_mapping.json",
        ],
        "decision_rule": "Pin external standards for interoperability; reject invalid or empty artifacts from authority status.",
    },
}

SOURCE_HYGIENE_NOTES = {
    "ocr": "OCR output is a review aid until source page, confidence, and extracted field are confirmed.",
    "dictionary": "Dictionary and encyclopedia material supports interpretation and scholarship, not formal CNBE bit assignment.",
    "third_party_decomposition": "Third-party decomposition is useful for disagreement discovery, not as a primary standard.",
    "legacy_generated_cnbe": "Previously generated CNBE outputs are diagnostics and must not become circular evidence.",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json_shape(path: Path) -> dict[str, Any]:
    if path.stat().st_size >= LARGE_JSON_THRESHOLD:
        return read_jsonl_shape(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        jsonl = read_jsonl_shape(path)
        if jsonl["parse_status"] == "PASS":
            return jsonl
        return {"parse_status": "FAIL", "error": str(exc), "jsonl_error": jsonl.get("error")}
    result: dict[str, Any] = {"parse_status": "PASS", "top_type": type(data).__name__}
    if isinstance(data, dict):
        result["top_count"] = len(data)
        result["top_keys_sample"] = list(data)[:12]
        if isinstance(data.get("kids"), list):
            result["kids_count"] = len(data["kids"])
        if isinstance(data.get("data"), dict):
            result["data_count"] = len(data["data"])
        if isinstance(data.get("characters"), list):
            result["character_count"] = len(data["characters"])
    elif isinstance(data, list):
        result["top_count"] = len(data)
        if data and isinstance(data[0], dict):
            result["first_item_keys"] = list(data[0])[:12]
    return result


def read_jsonl_shape(path: Path) -> dict[str, Any]:
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


def read_markdown_shape(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        return {"utf8_status": "FAIL", "error": str(exc)}
    return {
        "utf8_status": "PASS",
        "line_count": len(text.splitlines()),
        "char_count": len(text),
        "image_reference_count": text.count("![image"),
        "contains_crlf": b"\r\n" in raw,
        "contains_bom": raw.startswith(b"\xef\xbb\xbf"),
    }


def inspect_path(root: Path, relative_path: str) -> dict[str, Any]:
    path = root / relative_path
    result: dict[str, Any] = {
        "relative_path": relative_path,
        "exists": path.exists(),
        "role": infer_role(relative_path),
    }
    if not path.exists():
        result["status"] = "MISSING"
        return result
    result["size_bytes"] = path.stat().st_size
    result["sha256"] = sha256_file(path)
    suffix = path.suffix.lower()
    if suffix == ".json":
        result["json"] = read_json_shape(path)
    elif suffix == ".md":
        result["markdown"] = read_markdown_shape(path)
    elif suffix == ".zip":
        result["archive"] = inspect_archive(path)
    elif suffix == ".txt":
        result["text"] = read_markdown_shape(path)
    result["status"] = source_status(result)
    return result


def inspect_archive(path: Path) -> dict[str, Any]:
    import zipfile

    try:
        with zipfile.ZipFile(path) as archive:
            members = archive.namelist()
            bad_member = archive.testzip()
    except zipfile.BadZipFile as exc:
        return {"status": "FAIL", "error": str(exc)}
    return {
        "status": "PASS" if bad_member is None else "FAIL",
        "member_count": len(members),
        "members_sample": members[:12],
        "bad_member": bad_member,
    }


def infer_role(relative_path: str) -> str:
    if "/ocr/" in f"/{relative_path}" or relative_path.startswith("knowledge/ocr"):
        return "ocr_review_aid"
    if relative_path.startswith("source/"):
        return "converted_source_document"
    if "wikipedia" in relative_path.lower() or "百科" in relative_path:
        return "encyclopedia_semantic_index"
    if relative_path.startswith("knowledge/structured"):
        return "structured_knowledge_index"
    if relative_path.startswith("decomp-data") or relative_path.startswith("cjk-decomp"):
        return "third_party_decomposition"
    if "cihai" in relative_path.lower() or "definitions" in relative_path.lower() or "yuanliu" in relative_path:
        return "dictionary_semantic_index"
    if "cnbe32" in relative_path:
        return "legacy_generated_cnbe_diagnostic"
    return "supporting_reference"


def source_status(result: dict[str, Any]) -> str:
    if not result.get("exists"):
        return "MISSING"
    if result.get("json", {}).get("parse_status") == "FAIL":
        return "NEEDS_REPAIR"
    if result.get("archive", {}).get("status") == "FAIL":
        return "EXCLUDE_OR_REPLACE"
    if result.get("size_bytes") == 0:
        return "EMPTY"
    markdown = result.get("markdown", {})
    if markdown.get("utf8_status") == "FAIL":
        return "NEEDS_REPAIR"
    text = result.get("text", {})
    if text.get("utf8_status") == "FAIL":
        return "NEEDS_REPAIR"
    return "AVAILABLE"


def inspect_domain(root: Path, domain_id: str, config: dict[str, Any]) -> dict[str, Any]:
    primary = [inspect_path(root, path) for path in config["primary_sources"]]
    supporting = [inspect_path(root, path) for path in config["supporting_sources"]]
    missing = [item["relative_path"] for item in primary + supporting if item["status"] == "MISSING"]
    needs_repair = [
        item["relative_path"]
        for item in primary + supporting
        if item["status"] in {"NEEDS_REPAIR", "EXCLUDE_OR_REPLACE", "EMPTY"}
    ]
    primary_available = sum(1 for item in primary if item["status"] == "AVAILABLE")
    status = domain_status(primary_available, len(primary), needs_repair, domain_id)
    return {
        "domain": domain_id,
        "status": status,
        "cnbe_risk": config["cnbe_risk"],
        "decision_rule": config["decision_rule"],
        "primary_available": primary_available,
        "primary_total": len(primary),
        "missing_sources": missing,
        "sources_needing_repair_or_exclusion": needs_repair,
        "primary_sources": primary,
        "supporting_sources": supporting,
    }


def domain_status(primary_available: int, primary_total: int, needs_repair: list[str], domain_id: str) -> str:
    if primary_available == 0:
        return "BLOCKED_NO_PRIMARY_SOURCE"
    if needs_repair and domain_id in {"encoding_and_interchange_standards"}:
        return "ACTION_REQUIRED"
    if primary_available < primary_total:
        return "PARTIAL_PRIMARY_SOURCE"
    return "READY_FOR_SCHEMA_DESIGN"


def build_report(research_root: Path) -> dict[str, Any]:
    root = research_root.resolve()
    if not root.exists():
        raise FileNotFoundError(f"research root not found: {root}")
    domains = [inspect_domain(root, domain_id, config) for domain_id, config in EVIDENCE_DOMAINS.items()]
    counts = Counter(domain["status"] for domain in domains)
    return {
        "report_schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "audit_mode": "read_only_cnbe_weakness_evidence_domain_mapping",
        "research_root": str(root),
        "summary": {
            "domains_total": len(domains),
            "domain_status_counts": dict(sorted(counts.items())),
            "encoding_generation_gate": "NO_GO",
            "sqlite_build_gate": "NO_GO",
            "focus": "evidence_domain_design_before_encoding_or_database_generation",
        },
        "cnbe_weakness_model": {
            "radix_field": "requires radical table separation from Kangxi and Unicode radical-stroke indexes",
            "stroke_field": "requires actual stroke count and order evidence before compact CNBE field interpretation",
            "structure_field": "requires component, single-component, and layout evidence before structure assignment",
            "semantic_claims": "require dictionary, etymology, and encyclopedia context but remain non-bitfield evidence",
            "provenance": "each accepted field must carry source path, hash, extraction method, and review status",
        },
        "source_hygiene_notes": SOURCE_HYGIENE_NOTES,
        "domains": domains,
        "recommended_next_stage": "design_character_evidence_schema_and_review_status_columns",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--research-root", type=Path, default=DEFAULT_RESEARCH_ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parent.parent
    output = (repo_root / args.output).resolve() if not args.output.is_absolute() else args.output
    try:
        report = build_report(args.research_root)
    except (OSError, ValueError) as exc:
        print(f"CNBE RESEARCH EVIDENCE DOMAIN AUDIT ERROR: {exc}", file=sys.stderr)
        return 2
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"CNBE RESEARCH EVIDENCE DOMAIN AUDIT: {output}")
    print(f"Domains: {report['summary']['domains_total']}")
    print(f"Statuses: {report['summary']['domain_status_counts']}")
    print(f"Encoding generation gate: {report['summary']['encoding_generation_gate']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
