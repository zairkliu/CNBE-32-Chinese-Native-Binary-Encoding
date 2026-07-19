#!/usr/bin/env python3
"""Map full-catalog GF0017 items to source-evidence assets.

This is the source-evidence mapping step after the full-catalog GF0017
preflight plan. It is intentionally read-only: it does not score workbook rows,
rewrite CNBE fields, rebuild databases, create releases, or publish artifacts.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

RESEARCH_ROOT = Path("/Users/liuzhaoqi/Documents/cnbe-research")
PREFLIGHT_PLAN = Path("reports/full_catalog_gf0017_preflight_plan.json")
KNOWLEDGE_INVENTORY = Path("reports/cnbe_research_knowledge_inventory.json")
SOURCE_AUDIT = Path("reports/cnbe_research_source_audit.json")
EVIDENCE_DOMAINS = Path("reports/cnbe_research_evidence_domains.json")

DEFAULT_JSON_OUTPUT = Path("reports/full_catalog_gf0017_source_mapping.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/FULL_CATALOG_GF0017_SOURCE_MAPPING.md")

SOURCE_GRADES = {
    "direct_standard",
    "standard_derived",
    "cross_reference",
    "referenced_not_direct",
    "unresolved",
}

GF0017_SOURCE_MAPPING = {
    "character_set_coverage": {
        "points": 3,
        "source_status": "SOURCE_GAP",
        "domain": "standard_character_scope",
        "controlling_sources": [
            {
                "name": "GF 0017-2013 识字教学用通用键盘汉字字形输入系统评测规则",
                "relative_path": "source/11-评测与分类/GF 0017-2013 识字教学用通用键盘汉字字形输入系统评测规则.md",
                "grade": "direct_standard",
                "role": "scoring_methodology",
            },
            {
                "name": "通用规范汉字表 8105",
                "relative_path": "source/01-通用规范汉字表/通用规范汉字表(8105).md",
                "grade": "cross_reference",
                "role": "project national-standard baseline",
            },
        ],
        "supporting_sources": [
            "knowledge/ocr_char_table_all.json",
            "knowledge/alignment_report.json",
            "knowledge/alignment_report_v2.json",
        ],
        "reason": (
            "GF0017 references GB2312 and 现代汉语通用字表 for this item. "
            "The current project uses 8105 as the baseline, so full-catalog scoring "
            "must report this as SOURCE_GAP until required-set handling is explicitly resolved."
        ),
    },
    "stroke_shape": {
        "points": 3,
        "source_status": "SOURCE_GAP",
        "domain": "stroke_shape_order",
        "controlling_sources": [
            {
                "name": "GF 0017-2013 识字教学用通用键盘汉字字形输入系统评测规则",
                "relative_path": "source/11-评测与分类/GF 0017-2013 识字教学用通用键盘汉字字形输入系统评测规则.md",
                "grade": "direct_standard",
                "role": "scoring_methodology",
            },
            {
                "name": "GB 13000.1 字符集汉字折笔规范",
                "relative_path": "source/07-折笔规范/GB 13000.1 字符集汉字折笔规范.md",
                "grade": "cross_reference",
                "role": "folded-stroke and stroke-shape review source",
            },
        ],
        "supporting_sources": [
            "knowledge/ocr/ocr_fold_stroke.json",
            "knowledge/ocr/standards/std_07-折笔规范_bc1.json",
        ],
        "reason": (
            "The workbook only has stroke count. Stroke-shape classification requires "
            "standard-derived extraction before final scoring."
        ),
    },
    "stroke_order": {
        "points": 3,
        "source_status": "SOURCE_EVIDENCE_REQUIRED",
        "domain": "stroke_shape_order",
        "controlling_sources": [
            {
                "name": "GF 0031-2026 通用规范汉字笔顺规范",
                "relative_path": "source/05-笔顺规范/GF 0031—2026 通用规范汉字笔顺规范.md",
                "grade": "direct_standard",
                "role": "current stroke-order standard source",
            },
            {
                "name": "GF3002-1999 GB13000.1字符集汉字笔顺规范",
                "relative_path": "source/05-笔顺规范/GF3002-1999 GB13000.1字符集汉字笔顺规范.md",
                "grade": "direct_standard",
                "role": "GB13000.1 stroke-order source",
            },
        ],
        "supporting_sources": [
            "knowledge/stroke_order_8105.json",
            "knowledge/stroke_order_8105_clean.json",
        ],
        "reason": (
            "The workbook stroke-count field can be compared only after stroke-order "
            "records are mapped to Unicode identities."
        ),
    },
    "component_validity": {
        "points": 3,
        "source_status": "SOURCE_EVIDENCE_REQUIRED",
        "domain": "component_inventory",
        "controlling_sources": [
            {
                "name": "GF 0014-2009 现代常用字部件及部件名称规范",
                "relative_path": "source/03-部件及部件名称规范/GF 0014-2009 现代常用字部件及部件名称规范.md",
                "grade": "direct_standard",
                "role": "modern common-character component source",
            },
            {
                "name": "信息处理用GB 13000.1 字符集汉字部件规范",
                "relative_path": "source/06-汉字部件规范/信息处理用GB 13000.1 字符集汉字部件规范 （1998-5-1）.md",
                "grade": "direct_standard",
                "role": "information-processing component source",
            },
        ],
        "supporting_sources": [
            "knowledge/component_db.json",
            "knowledge/decomp_rules.json",
            "decomp-data/dictionary.json",
            "cjk-decomp/cjk-decomp.txt",
        ],
        "reason": (
            "The workbook has no component list. Component validity must be built "
            "from standard evidence before any row score is calculated."
        ),
    },
    "component_name_validity": {
        "points": 8,
        "source_status": "SOURCE_EVIDENCE_REQUIRED",
        "domain": "component_inventory",
        "controlling_sources": [
            {
                "name": "GF 0014-2009 现代常用字部件及部件名称规范",
                "relative_path": "source/03-部件及部件名称规范/GF 0014-2009 现代常用字部件及部件名称规范.md",
                "grade": "direct_standard",
                "role": "component-name source",
            }
        ],
        "supporting_sources": [
            "knowledge/component_db.json",
            "knowledge/ocr/standards/std_03-部件及部件名称规范_bc1.json",
        ],
        "reason": (
            "Component names carry the largest non-decomposition sub-score outside "
            "structure. OCR-only component names must remain review aids."
        ),
    },
    "radical_validity": {
        "points": 3,
        "source_status": "SOURCE_EVIDENCE_REQUIRED",
        "domain": "radical_classification",
        "controlling_sources": [
            {
                "name": "GG 0011-2009 汉字部首表",
                "relative_path": "source/02-汉字部首表/GG 0011-2009 汉字部首表.md",
                "grade": "direct_standard",
                "role": "modern radical classification source",
            }
        ],
        "supporting_sources": [
            "knowledge/kangxi_radicals.json",
            "knowledge/radical_validation.json",
            "knowledge/unicode_rsindex.json",
            "source/15-Unicode-RSIndex/RSIndex.md",
        ],
        "reason": (
            "The workbook has a numeric radical field. It cannot be trusted until "
            "the GG0011 radical source and numeric radical-code map agree."
        ),
    },
    "independent_character_rule": {
        "points": 7,
        "source_status": "SOURCE_EVIDENCE_REQUIRED",
        "domain": "single_component_and_structure",
        "controlling_sources": [
            {
                "name": "GF 0013-2009 现代常用独体字规范",
                "relative_path": "source/04-独体字规范/GF 0013-2009 现代常用独体字规范.md",
                "grade": "direct_standard",
                "role": "single-component character source",
            },
            {
                "name": "GF 0014-2009 现代常用字部件及部件名称规范",
                "relative_path": "source/03-部件及部件名称规范/GF 0014-2009 现代常用字部件及部件名称规范.md",
                "grade": "direct_standard",
                "role": "decomposition compatibility source",
            },
        ],
        "supporting_sources": [
            "knowledge/decomp_rules.json",
            "knowledge/component_db.json",
        ],
        "reason": (
            "The workbook structure fields must be checked against independent-character "
            "evidence so an independent character is not split into invalid components."
        ),
    },
    "structure_first_decomposition": {
        "points": 20,
        "source_status": "SOURCE_EVIDENCE_REQUIRED",
        "domain": "single_component_and_structure",
        "controlling_sources": [
            {
                "name": "GF 0014-2009 现代常用字部件及部件名称规范",
                "relative_path": "source/03-部件及部件名称规范/GF 0014-2009 现代常用字部件及部件名称规范.md",
                "grade": "direct_standard",
                "role": "structure and decomposition source",
            },
            {
                "name": "信息处理用GB 13000.1 字符集汉字部件规范",
                "relative_path": "source/06-汉字部件规范/信息处理用GB 13000.1 字符集汉字部件规范 （1998-5-1）.md",
                "grade": "direct_standard",
                "role": "GB13000.1 component/decomposition source",
            },
        ],
        "supporting_sources": [
            "evidence/agent-standard/cnbe_legacy_structure_localization.json",
            "knowledge/component_db.json",
            "knowledge/decomp_rules.json",
            "decomp-data/dictionary.json",
            "cjk-decomp/cjk-decomp.txt",
        ],
        "reason": (
            "This 20-point item cannot be scored from a workbook structure label alone. "
            "The Agent 13-label localization must be joined with standard decomposition evidence."
        ),
    },
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def file_record(relative_path: str) -> dict[str, Any]:
    local_path = RESEARCH_ROOT / relative_path
    if not local_path.exists():
        return {
            "relative_path": relative_path,
            "exists": False,
            "grade_status": "unresolved",
        }
    data = local_path.read_bytes()
    return {
        "relative_path": relative_path,
        "exists": True,
        "size_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "line_count": data.count(b"\n") if local_path.suffix in {".md", ".txt"} else None,
    }


def expand_source(item: dict[str, Any]) -> dict[str, Any]:
    if item["grade"] not in SOURCE_GRADES:
        raise ValueError(f"invalid source grade: {item['grade']}")
    record = file_record(item["relative_path"])
    return {
        **item,
        **record,
        "grade_status": item["grade"] if record["exists"] else "unresolved",
    }


def build_source_mapping() -> dict[str, Any]:
    preflight = load_json(PREFLIGHT_PLAN)
    inventory = load_json(KNOWLEDGE_INVENTORY)
    source_audit = load_json(SOURCE_AUDIT)
    evidence_domains = load_json(EVIDENCE_DOMAINS)

    items: list[dict[str, Any]] = []
    source_status_counts: dict[str, int] = {}
    missing_sources: list[dict[str, Any]] = []
    for item_id, config in GF0017_SOURCE_MAPPING.items():
        controlling = [expand_source(source) for source in config["controlling_sources"]]
        supporting = [file_record(path) for path in config["supporting_sources"]]
        unresolved = [
            source
            for source in controlling
            if not source["exists"] or source["grade_status"] == "unresolved"
        ]
        if unresolved:
            status = "BLOCKER"
            missing_sources.extend(unresolved)
        else:
            status = config["source_status"]
        source_status_counts[status] = source_status_counts.get(status, 0) + 1
        items.append(
            {
                "id": item_id,
                "points": config["points"],
                "domain": config["domain"],
                "source_status": status,
                "controlling_sources": controlling,
                "supporting_sources": supporting,
                "workbook_fields": next(
                    item["workbook_fields"]
                    for item in preflight["gf0017_item_mapping"]
                    if item["id"] == item_id
                ),
                "batch_scoring_rule": "do_not_score_rows_until_source_status_is_not_unresolved",
                "reason": config["reason"],
            }
        )

    knowledge_blockers = [
        item for item in inventory.get("action_items", []) if item.get("severity") == "BLOCKER"
    ]
    total_points = sum(item["points"] for item in items)
    direct_standard_items = sum(
        1
        for item in items
        if any(source["grade_status"] == "direct_standard" for source in item["controlling_sources"])
    )

    return {
        "report_schema_version": "1.0",
        "mode": "read_only_full_catalog_gf0017_source_mapping",
        "source_workbook": preflight["source_workbook"],
        "source_sheet": preflight["source_sheet"],
        "overall_status": "PASS" if not missing_sources else "FAIL",
        "next_workflow_status": "SOURCE_MAPPING_READY_KNOWLEDGE_BLOCKERS_REMAIN",
        "authority_boundary": {
            "does_not_score_rows": True,
            "does_not_modify_workbook": True,
            "does_not_rebuild_database": True,
            "does_not_publish_release": True,
            "national_standard_vs_agent_standard_preserved": True,
            "ocr_dictionary_wiki_are_not_bitfield_authority": True,
        },
        "source_grades": sorted(SOURCE_GRADES),
        "summary": {
            "gf0017_items": len(items),
            "gf0017_total_points": total_points,
            "direct_standard_items": direct_standard_items,
            "source_status_counts": source_status_counts,
            "missing_controlling_sources": len(missing_sources),
            "knowledge_blockers": len(knowledge_blockers),
            "source_audit_status": source_audit["summary"]["status"],
            "evidence_domain_status_counts": evidence_domains["summary"]["domain_status_counts"],
            "preflight_status": preflight["overall_status"],
        },
        "items": items,
        "known_blockers": knowledge_blockers,
        "missing_sources": missing_sources,
        "decision": {
            "may_start_schema_join_design": not missing_sources,
            "may_start_batch_gf0017_scoring": False,
            "may_rebuild_database": False,
            "may_modify_workbook": False,
            "reason": (
                "The GF0017 source map is now explicit. The next allowed step is "
                "schema join design and blocker reconciliation; row scoring remains blocked."
            ),
        },
        "next_artifacts": [
            "reports/full_catalog_gf0017_join_schema.json",
            "reports/FULL_CATALOG_GF0017_JOIN_SCHEMA.md",
            "scripts/design_full_catalog_gf0017_join_schema.py",
        ],
    }


def render_markdown(mapping: dict[str, Any]) -> str:
    lines = [
        "# Full Catalog GF0017 Source Mapping",
        "",
        "## Purpose",
        "",
        "This report binds each GF0017 50-point normativity item to source-evidence",
        "assets before any full-catalog row scoring begins.",
        "",
        "It is read-only. It does not score rows, modify the workbook, rebuild",
        "databases, alter CNBE32 values, create tags, publish releases, or upload",
        "to PyPI.",
        "",
        "## Result",
        "",
        f"- Overall status: `{mapping['overall_status']}`",
        f"- Next workflow status: `{mapping['next_workflow_status']}`",
        f"- GF0017 items: `{mapping['summary']['gf0017_items']}`",
        f"- GF0017 total points: `{mapping['summary']['gf0017_total_points']}`",
        f"- Direct-standard-backed items: `{mapping['summary']['direct_standard_items']}`",
        f"- Knowledge blockers: `{mapping['summary']['knowledge_blockers']}`",
        f"- May start schema join design: `{mapping['decision']['may_start_schema_join_design']}`",
        f"- May start batch GF0017 scoring: `{mapping['decision']['may_start_batch_gf0017_scoring']}`",
        "",
        "## Authority Boundary",
        "",
        "- National standards and directly derived standard extracts can control formal evidence.",
        "- Agent-standard mappings are project outputs, not national-standard claims.",
        "- OCR, dictionary, Wikipedia, and third-party decomposition assets remain review aids.",
        "- Legacy CNBE fields are candidate carrier data, not proof of correctness.",
        "",
        "## Source Status Counts",
        "",
    ]
    for status, count in sorted(mapping["summary"]["source_status_counts"].items()):
        lines.append(f"- `{status}`: {count}")

    lines.extend(
        [
            "",
            "## GF0017 Source Map",
            "",
            "| Item | Points | Source status | Workbook fields | Controlling sources |",
            "|---|---:|---|---|---|",
        ]
    )
    for item in mapping["items"]:
        fields = ", ".join(f"`{field}`" for field in item["workbook_fields"]) or "none"
        sources = "; ".join(
            f"{source['name']} ({source['grade_status']})" for source in item["controlling_sources"]
        )
        lines.append(
            f"| `{item['id']}` | {item['points']} | {item['source_status']} | {fields} | {sources} |"
        )

    lines.extend(
        [
            "",
            "## Known Blockers",
            "",
        ]
    )
    if mapping["known_blockers"]:
        for item in mapping["known_blockers"]:
            lines.append(f"- `{item['asset']}`: {item['issue']} -> {item['next_step']}")
    else:
        lines.append("- None.")

    lines.extend(
        [
            "",
            "## Decision",
            "",
            mapping["decision"]["reason"],
            "",
            "Batch GF0017 scoring remains blocked until the join schema and source",
            "blockers are resolved.",
            "",
            "## Next Artifacts",
            "",
        ]
    )
    for artifact in mapping["next_artifacts"]:
        lines.append(f"- `{artifact}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    mapping = build_source_mapping()
    write_json(DEFAULT_JSON_OUTPUT, mapping)
    write_text(DEFAULT_MARKDOWN_OUTPUT, render_markdown(mapping))
    print(f"wrote {DEFAULT_JSON_OUTPUT}")
    print(f"wrote {DEFAULT_MARKDOWN_OUTPUT}")
    print(f"overall_status={mapping['overall_status']}")
    print(f"next_workflow_status={mapping['next_workflow_status']}")
    if mapping["overall_status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
