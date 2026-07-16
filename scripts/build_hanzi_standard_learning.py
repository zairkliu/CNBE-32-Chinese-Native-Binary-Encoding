#!/usr/bin/env python3
"""Build a read-only Hanzi standard learning packet from cnbe-research assets."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

RESEARCH_ROOT = Path("/Users/liuzhaoqi/Documents/cnbe-research")
SKILL_ROOT = RESEARCH_ROOT / "cnbe-hanzi-knowledge-builder"
TERM_REFERENCE = SKILL_ROOT / "references" / "hanzi_knowledge_terms.json"
STANDARD_REFERENCE = SKILL_ROOT / "references" / "national_standard_files.json"

DEFAULT_AUDIT_OUTPUT = Path("reports/hanzi_standard_learning_audit.json")
DEFAULT_MACHINE_OUTPUT = Path("data/sources/hanzi-standard-learning.json")
DEFAULT_PLAN_OUTPUT = Path("reports/HANZI_STANDARD_LEARNING_PLAN.md")
DEFAULT_TERMS_OUTPUT = Path("reports/HANZI_STANDARD_TERMS.md")
DEFAULT_STRUCTURES_OUTPUT = Path("reports/HANZI_STRUCTURE_TYPES.md")

CHUNK_SIZE = 1024 * 1024

ALLOWED_STRUCTURES = [
    {"id": 1, "name": "上下", "description": "上部和下部组合。"},
    {"id": 2, "name": "上中下", "description": "上、中、下三段组合。"},
    {"id": 3, "name": "左右", "description": "左部和右部组合。"},
    {"id": 4, "name": "左中右", "description": "左、中、右三段组合。"},
    {"id": 5, "name": "左上包", "description": "左上方向包围或覆盖内部部件。"},
    {"id": 6, "name": "右上包", "description": "右上方向包围或覆盖内部部件。"},
    {"id": 7, "name": "左三包", "description": "左侧三面包围。"},
    {"id": 8, "name": "左下包", "description": "左下方向包围或承托内部部件。"},
    {"id": 9, "name": "上三包", "description": "上方三面包围。"},
    {"id": 10, "name": "下三包", "description": "下方三面包围。"},
    {"id": 11, "name": "全包围", "description": "外部部件完整包围内部部件。"},
    {"id": 12, "name": "镶嵌", "description": "部件交错嵌合，不能简单归入普通上下或左右结构。"},
]

SPECIAL_STRUCTURE = {"id": 0, "name": "独体字", "description": "结构上不拆分为两个及以上部件。"}

READING_STAGES = [
    {
        "stage": 1,
        "title": "术语统一",
        "standards": [
            "chinese_hanzi_terms_gbt12200_2_94",
            "chinese_information_terms_gb12200_1_90",
        ],
        "goal": "先统一汉字、字形、部件、结构、信息处理等基础术语。",
    },
    {
        "stage": 2,
        "title": "部件和拆字",
        "standards": [
            "common_component_name_standard_gf0014_2009",
            "gb13000_component_standard_1998",
        ],
        "goal": "学习汉字部件、成字部件、非成字部件、基础部件、偏旁和拆分边界。",
    },
    {
        "stage": 3,
        "title": "独体字和结构",
        "standards": [
            "single_component_standard_gf0013_2009",
            "keyboard_shape_input_evaluation_gf0017_2013",
        ],
        "goal": "学习独体字判定和规范结构类型，不使用自造结构名。",
    },
    {
        "stage": 4,
        "title": "部首系统",
        "standards": [
            "hanzi_radical_table_gg0011_2009",
        ],
        "goal": "区分部首、偏旁、部件、康熙部首、Unicode radical-stroke 索引。",
    },
    {
        "stage": 5,
        "title": "笔画、笔形、笔顺",
        "standards": [
            "standard_hanzi_stroke_order_gf0031_2026",
            "gb13000_stroke_order_gf3002_1999",
            "gb13000_fold_stroke_standard",
        ],
        "goal": "分离笔画数、笔形类别、折笔规则和笔顺序列。",
    },
    {
        "stage": 6,
        "title": "字序和字表范围",
        "standards": [
            "gb13000_stroke_ordering_gf3003_1999",
            "common_standard_hanzi_8105",
        ],
        "goal": "学习字序、笔画序、字表等级和字形参照，避免混入结构判断。",
    },
    {
        "stage": 7,
        "title": "语音、语义和语料上下文",
        "standards": [
            "hanyu_pinyin_scheme_1958",
            "pinyin_orthography_gbt16159_2012",
            "punctuation_usage_gbt15834_2011",
            "pos_tagging_standard_gft20532_2006",
            "ai_corpus_terms_gf0031_2026",
        ],
        "goal": "建立上下文和审核方法，不把语义或语料规范直接当作 CNBE 结构字段。",
    },
]

TERM_RULES = {
    "stroke": {
        "learning_note": "笔画是字形书写的连续单位；CNBE 审核时必须与笔形、笔顺分开记录。",
        "forbidden_use": "不得把 CNBE 压缩 stroke 字段等同于完整实际笔画数。",
    },
    "stroke_shape": {
        "learning_note": "笔形是笔画形态类别；折笔规范负责处理折类笔形及其变体。",
        "forbidden_use": "不得用笔形类别替代笔画数或笔顺序列。",
    },
    "stroke_order": {
        "learning_note": "笔顺是笔画出现的先后顺序；可用数字序列记录。",
        "forbidden_use": "不得把字序、Unicode 顺序或 Excel 行号当作笔顺。",
    },
    "hanzi_component": {
        "learning_note": "汉字部件是构字单位，必须通过部件规范或审核过的拆分来源确认。",
        "forbidden_use": "不得用 AI 视觉直觉直接生成部件。",
    },
    "character_component": {
        "learning_note": "成字部件可以独立成字，仍需在具体拆分层级中确认其部件角色。",
        "forbidden_use": "不得因为部件能成字就自动等同为部首。",
    },
    "non_character_component": {
        "learning_note": "非成字部件不能独立成字，但可参与构字。",
        "forbidden_use": "不得把非成字部件误登记为独立汉字。",
    },
    "basic_component": {
        "learning_note": "基础部件是在选定规范体系中不再继续拆分的构字单位。",
        "forbidden_use": "不得无限细拆到笔画后仍称为部件规范结果。",
    },
    "radical": {
        "learning_note": "部首是检字和归类系统，必须说明采用现代部首表、康熙或 Unicode 系统。",
        "forbidden_use": "不得混用现代部首、康熙部首和 Unicode radical-stroke。",
    },
    "side_component": {
        "learning_note": "偏旁是传统构字分析概念，可用于解释部件位置和功能。",
        "forbidden_use": "不得用偏旁泛称覆盖正式部件和部首字段。",
    },
    "glyph_form": {
        "learning_note": "字形是方块汉字的规范视觉形体，来源应与字表或字形规范关联。",
        "forbidden_use": "不得把字源语义说明当作字形规范。",
    },
    "single_component_character": {
        "learning_note": "独体字是不再拆分为两个及以上部件的汉字，需要独体字规范支持。",
        "forbidden_use": "不得因为笔画少就自动判定为独体字。",
    },
    "hanzi_structure": {
        "learning_note": "结构只能落入十二类规范结构，或单独标为独体字。",
        "forbidden_use": "不得写入品字形、三叠结构、会意结构等非规范结构字段。",
    },
    "decomposition_method": {
        "learning_note": "拆分方法必须记录层级、部件序列、结构关系和来源。",
        "forbidden_use": "不得只给出语义解释而没有结构和部件证据。",
    },
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def source_identity(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": path.as_posix(),
        "exists": path.exists(),
    }
    if not path.exists():
        return result
    if path.is_dir():
        files = [item for item in path.rglob("*") if item.is_file()]
        result["kind"] = "directory"
        result["file_count"] = len(files)
        result["sample_files"] = [item.relative_to(path).as_posix() for item in sorted(files)[:20]]
        return result
    result["kind"] = "file"
    result["size_bytes"] = path.stat().st_size
    result["sha256"] = sha256_file(path)
    if path.suffix == ".md":
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        result["line_count"] = len(text.splitlines())
        result["char_count"] = len(text)
        result["image_reference_count"] = text.count("![image")
        result["text_preview"] = "\n".join(text.splitlines()[:8])
    elif path.suffix == ".json":
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as exc:
            result["json_status"] = "FAIL"
            result["json_error"] = str(exc)
        else:
            result["json_status"] = "PASS"
            result["json_type"] = type(data).__name__
            if isinstance(data, dict):
                result["json_top_keys"] = list(data)[:20]
            elif isinstance(data, list):
                result["json_count"] = len(data)
    return result


def validate_references(terms: dict[str, Any], standards: dict[str, Any]) -> list[str]:
    issues = []
    term_ids = {term["id"] for term in terms["required_terms"]}
    required_terms = set(TERM_RULES)
    if term_ids != required_terms:
        issues.append(f"term id mismatch: missing={sorted(required_terms - term_ids)} extra={sorted(term_ids - required_terms)}")
    structure_names = {item["name"] for item in ALLOWED_STRUCTURES}
    expected_structures = {
        "上下",
        "上中下",
        "左右",
        "左中右",
        "左上包",
        "右上包",
        "左三包",
        "左下包",
        "上三包",
        "下三包",
        "全包围",
        "镶嵌",
    }
    if structure_names != expected_structures:
        issues.append("allowed structure set mismatch")
    if SPECIAL_STRUCTURE["name"] != "独体字":
        issues.append("special structure must be 独体字")
    standard_ids = {standard["id"] for standard in standards["standards"]}
    for stage in READING_STAGES:
        missing = set(stage["standards"]) - standard_ids
        if missing:
            issues.append(f"reading stage {stage['stage']} missing standards: {sorted(missing)}")
    return issues


def build_learning_model(terms: dict[str, Any], standards: dict[str, Any]) -> dict[str, Any]:
    standard_lookup = {standard["id"]: standard for standard in standards["standards"]}
    standard_assets = []
    for standard in standards["standards"]:
        json_path = RESEARCH_ROOT / standard["converted_json"]
        markdown_path = RESEARCH_ROOT / standard["converted_markdown"]
        standard_assets.append(
            {
                **standard,
                "converted_json_identity": source_identity(json_path),
                "converted_markdown_identity": source_identity(markdown_path),
            }
        )
    learned_terms = []
    for term in terms["required_terms"]:
        rule = TERM_RULES[term["id"]]
        primary_identities = [source_identity(RESEARCH_ROOT / source) for source in term["primary_sources"]]
        supporting_identities = [source_identity(RESEARCH_ROOT / source) for source in term["supporting_sources"]]
        learned_terms.append(
            {
                **term,
                "learning_note": rule["learning_note"],
                "forbidden_use": rule["forbidden_use"],
                "primary_source_identities": primary_identities,
                "supporting_source_identities": supporting_identities,
                "learning_status": "SOURCE_IDENTIFIED",
            }
        )
    stage_models = []
    for stage in READING_STAGES:
        stage_models.append(
            {
                **stage,
                "standard_records": [standard_lookup[item] for item in stage["standards"]],
            }
        )
    authority_counts = Counter(standard["encoding_authority"] for standard in standards["standards"])
    return {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "audit_mode": "read_only_hanzi_standard_learning",
        "research_root": str(RESEARCH_ROOT),
        "skill_root": str(SKILL_ROOT),
        "summary": {
            "learning_status": "READY_FOR_HUMAN_REVIEW",
            "required_terms": len(learned_terms),
            "national_standards": len(standard_assets),
            "allowed_structures": len(ALLOWED_STRUCTURES),
            "special_structure": SPECIAL_STRUCTURE["name"],
            "encoding_generation_gate": "NO_GO",
            "sqlite_build_gate": "NO_GO",
            "authority_counts": dict(sorted(authority_counts.items())),
        },
        "reading_stages": stage_models,
        "terms": learned_terms,
        "allowed_structures": ALLOWED_STRUCTURES,
        "special_structure": SPECIAL_STRUCTURE,
        "national_standards": standard_assets,
        "validation_issues": validate_references(terms, standards),
        "next_stage": "human_reading_review_then_schema_pilot",
    }


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(item).replace("\n", "<br>") for item in row) + " |")
    return "\n".join(lines)


def render_plan(model: dict[str, Any]) -> str:
    rows = []
    for stage in model["reading_stages"]:
        rows.append(
            [
                stage["stage"],
                stage["title"],
                "<br>".join(item["pdf_filename"] for item in stage["standard_records"]),
                stage["goal"],
            ]
        )
    return (
        "# Hanzi Standard Learning Plan\n\n"
        "This plan is generated by `scripts/build_hanzi_standard_learning.py`.\n\n"
        "The goal is to learn national language and writing standards before any CNBE-32 encoding audit or mapping work.\n"
        "PDF originals are recorded by filename only; converted source/OCR assets under `cnbe-research/source` and "
        "`cnbe-research/knowledge` are the working inputs.\n\n"
        "## Gates\n\n"
        "- `encoding_generation_gate`: `NO_GO`\n"
        "- `sqlite_build_gate`: `NO_GO`\n"
        "- Next allowed action: human reading review, schema design, and small pilot evidence rows only.\n\n"
        "## Reading Stages\n\n"
        + markdown_table(["Stage", "Title", "Standards", "Goal"], rows)
        + "\n\n## Stop Rules\n\n"
        "- Stop if a formal field is supported only by OCR.\n"
        "- Stop if a term has no primary standard source.\n"
        "- Stop if a structure name is outside the twelve allowed structures or `独体字`.\n"
        "- Stop if a script attempts to write CNBE mapping values.\n"
        "- Stop if a large PDF, OCR batch, dictionary, image slice, or Wikipedia payload would be committed.\n"
        "\n## Learning Acceptance Checklist\n\n"
        "- Every one of the 13 Hanzi knowledge items is present in the term model.\n"
        "- Every term has at least one primary standard source or a documented methodological source.\n"
        "- Every national standard is represented by filename only and mapped to converted JSON/Markdown assets.\n"
        "- Every converted source has identity metadata in the machine-readable audit report.\n"
        "- The structure vocabulary is closed over the twelve allowed structures plus `独体字`.\n"
        "- OCR-only evidence is marked as review-needed rather than accepted as authority.\n"
        "- Dictionary, etymology, and Wikipedia sources remain context or adjudication evidence only.\n"
        "- Current CNBE values remain diagnostic and cannot be used as self-evidence.\n"
        "- Encoding generation remains blocked until a human review packet is designed and approved.\n"
        "\n## Next Human Reading Pass\n\n"
        "A human or reviewer agent should now read the generated term report and structure report, compare them against the\n"
        "converted standard assets, and mark any disputed definitions before schema extraction starts. The first permitted\n"
        "implementation step after that review is a small evidence-row pilot, not a full database and not a code table.\n"
    )


def render_terms(model: dict[str, Any]) -> str:
    sections = [
        "# Hanzi Standard Terms\n\n",
        "This report records the current learned term model. It is a preparation artifact, not a mapping proposal.\n\n",
    ]
    for term in model["terms"]:
        sections.append(f"## {term['zh']} (`{term['id']}`)\n\n")
        sections.append(f"Definition: {term['definition']}\n\n")
        sections.append(f"Learning note: {term['learning_note']}\n\n")
        sections.append(f"Forbidden use: {term['forbidden_use']}\n\n")
        sections.append(f"Evidence domain: `{term['evidence_domain']}`\n\n")
        sections.append("Primary sources:\n\n")
        for source in term["primary_sources"]:
            sections.append(f"- `{source}`\n")
        sections.append("\nSupporting sources:\n\n")
        for source in term["supporting_sources"]:
            sections.append(f"- `{source}`\n")
        sections.append("\n")
    return "".join(sections)


def render_structures(model: dict[str, Any]) -> str:
    rows = [[item["id"], item["name"], item["description"]] for item in model["allowed_structures"]]
    return (
        "# Hanzi Structure Types\n\n"
        "Only these structure values are allowed for normalized Hanzi structure review.\n\n"
        "## Special Case\n\n"
        f"- `{model['special_structure']['name']}`: {model['special_structure']['description']}\n\n"
        "## Twelve Allowed Structures\n\n"
        + markdown_table(["ID", "Structure", "Description"], rows)
        + "\n\n## Forbidden Structure Labels\n\n"
        "- `品字形`\n"
        "- `三叠结构`\n"
        "- `三金结构`\n"
        "- `会意结构`\n"
        "- Any other label not listed above.\n\n"
        "Such descriptions may appear only in semantic or etymology notes, never in the normalized structure field.\n"
        "Any new label must first be traced to a cited national standard before it can enter the controlled vocabulary.\n"
    )


def write_outputs(args: argparse.Namespace, model: dict[str, Any]) -> None:
    outputs = {
        args.audit_output: json.dumps(model, ensure_ascii=False, indent=2) + "\n",
        args.machine_output: json.dumps(
            {
                "schema_version": 1,
                "generated_at_utc": model["generated_at_utc"],
                "terms": [
                    {
                        "id": term["id"],
                        "zh": term["zh"],
                        "evidence_domain": term["evidence_domain"],
                        "primary_sources": term["primary_sources"],
                        "forbidden_use": term["forbidden_use"],
                    }
                    for term in model["terms"]
                ],
                "allowed_structures": model["allowed_structures"],
                "special_structure": model["special_structure"],
                "national_standards": [
                    {
                        "id": standard["id"],
                        "pdf_filename": standard["pdf_filename"],
                        "converted_json": standard["converted_json"],
                        "converted_markdown": standard["converted_markdown"],
                        "audit_domains": standard["audit_domains"],
                        "encoding_authority": standard["encoding_authority"],
                    }
                    for standard in model["national_standards"]
                ],
                "gates": {
                    "encoding_generation_gate": "NO_GO",
                    "sqlite_build_gate": "NO_GO",
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        args.plan_output: render_plan(model),
        args.terms_output: render_terms(model),
        args.structures_output: render_structures(model),
    }
    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-output", type=Path, default=DEFAULT_AUDIT_OUTPUT)
    parser.add_argument("--machine-output", type=Path, default=DEFAULT_MACHINE_OUTPUT)
    parser.add_argument("--plan-output", type=Path, default=DEFAULT_PLAN_OUTPUT)
    parser.add_argument("--terms-output", type=Path, default=DEFAULT_TERMS_OUTPUT)
    parser.add_argument("--structures-output", type=Path, default=DEFAULT_STRUCTURES_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parent.parent
    for key in ("audit_output", "machine_output", "plan_output", "terms_output", "structures_output"):
        value = getattr(args, key)
        if not value.is_absolute():
            setattr(args, key, repo_root / value)
    try:
        terms = load_json(TERM_REFERENCE)
        standards = load_json(STANDARD_REFERENCE)
        model = build_learning_model(terms, standards)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"HANZI STANDARD LEARNING ERROR: {exc}", file=sys.stderr)
        return 2
    write_outputs(args, model)
    if model["validation_issues"]:
        print("HANZI STANDARD LEARNING ACTION_REQUIRED")
        for issue in model["validation_issues"]:
            print(f"- {issue}", file=sys.stderr)
        return 1
    print("HANZI STANDARD LEARNING PASS")
    print(f"Terms: {model['summary']['required_terms']}")
    print(f"National standards: {model['summary']['national_standards']}")
    print(f"Allowed structures: {model['summary']['allowed_structures']} + {model['summary']['special_structure']}")
    print(f"Encoding generation gate: {model['summary']['encoding_generation_gate']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
