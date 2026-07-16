#!/usr/bin/env python3
"""Build the CNBE Agent encoding standard and legacy structure mapping reports."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_CNBE_INPUT = Path("data/cnbe32.json")
DEFAULT_STANDARD_OUTPUT = Path("evidence/agent-standard/cnbe_agent_encoding_standard.json")
DEFAULT_STANDARD_MARKDOWN = Path("evidence/agent-standard/CNBE_AGENT_ENCODING_STANDARD.md")
DEFAULT_STRUCTURE_OUTPUT = Path("evidence/agent-standard/cnbe_legacy_structure_localization.json")
DEFAULT_STRUCTURE_MARKDOWN = Path("evidence/agent-standard/CNBE_LEGACY_STRUCTURE_LOCALIZATION.md")

AGENT_ALLOWED_STRUCTURES = {
    "独体字": 0,
    "上下": 1,
    "上中下": 2,
    "左右": 3,
    "左中右": 4,
    "左上包": 5,
    "右上包": 6,
    "左三包": 7,
    "左下包": 8,
    "上三包": 9,
    "下三包": 10,
    "全包围": 11,
    "镶嵌": 12,
}

LEGACY_STRUCTURE_LOCALIZATION = {
    "single": {
        "agent_structure": "独体字",
        "legacy_struct_type": 0,
        "agent_struct_type": 0,
        "confidence": 1.0,
        "rule": "direct semantic equivalent",
    },
    "up-down": {
        "agent_structure": "上下",
        "legacy_struct_type": 3,
        "agent_struct_type": 1,
        "confidence": 1.0,
        "rule": "legacy English label maps to allowed Chinese structure",
    },
    "up-mid-down": {
        "agent_structure": "上中下",
        "legacy_struct_type": 4,
        "agent_struct_type": 2,
        "confidence": 1.0,
        "rule": "legacy English label maps to allowed Chinese structure",
    },
    "left-right": {
        "agent_structure": "左右",
        "legacy_struct_type": 1,
        "agent_struct_type": 3,
        "confidence": 1.0,
        "rule": "legacy English label maps to allowed Chinese structure",
    },
    "left-mid-right": {
        "agent_structure": "左中右",
        "legacy_struct_type": 2,
        "agent_struct_type": 4,
        "confidence": 1.0,
        "rule": "legacy English label maps to allowed Chinese structure",
    },
    "top-left-wrap": {
        "agent_structure": "左上包",
        "legacy_struct_type": 5,
        "agent_struct_type": 5,
        "confidence": 0.85,
        "rule": "legacy directional label requires project-level localization",
    },
    "top-right-wrap": {
        "agent_structure": "右上包",
        "legacy_struct_type": 6,
        "agent_struct_type": 6,
        "confidence": 0.85,
        "rule": "legacy directional label requires project-level localization",
    },
    "left-wrap": {
        "agent_structure": "左三包",
        "legacy_struct_type": 10,
        "agent_struct_type": 7,
        "confidence": 0.75,
        "rule": "legacy broad wrap label maps to closest allowed three-side structure",
    },
    "bottom-left-wrap": {
        "agent_structure": "左下包",
        "legacy_struct_type": 7,
        "agent_struct_type": 8,
        "confidence": 0.75,
        "rule": "legacy directional label maps to closest allowed lower-left structure",
    },
    "top-wrap": {
        "agent_structure": "上三包",
        "legacy_struct_type": 8,
        "agent_struct_type": 9,
        "confidence": 0.75,
        "rule": "legacy broad wrap label maps to closest allowed three-side structure",
    },
    "bottom-wrap": {
        "agent_structure": "下三包",
        "legacy_struct_type": 9,
        "agent_struct_type": 10,
        "confidence": 0.75,
        "rule": "legacy broad wrap label maps to closest allowed three-side structure",
    },
    "full-wrap": {
        "agent_structure": "全包围",
        "legacy_struct_type": 11,
        "agent_struct_type": 11,
        "confidence": 1.0,
        "rule": "direct semantic equivalent",
    },
    "triangle": {
        "agent_structure": "镶嵌",
        "legacy_struct_type": 12,
        "agent_struct_type": 12,
        "confidence": 0.65,
        "rule": "legacy nonstandard shape label requires Agent-level project mapping",
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


def format_unicode(codepoint: int) -> str:
    return f"U+{codepoint:04X}"


def build_structure_localization(cnbe_input: Path) -> dict[str, Any]:
    rows = load_json(cnbe_input)["characters"]
    raw_counts: Counter[str] = Counter()
    legacy_type_counts: Counter[str] = Counter()
    agent_type_counts: Counter[str] = Counter()
    mismatch_count = 0
    missing_labels = []
    examples: dict[str, list[dict[str, Any]]] = {label: [] for label in LEGACY_STRUCTURE_LOCALIZATION}

    for row in rows:
        label = row.get("struct_name")
        raw_counts[str(label)] += 1
        if label not in LEGACY_STRUCTURE_LOCALIZATION:
            missing_labels.append(
                {
                    "char": row.get("char"),
                    "unicode": format_unicode(row["unicode"]) if isinstance(row.get("unicode"), int) else None,
                    "legacy_struct_name": label,
                    "legacy_struct_type": row.get("struct_type"),
                }
            )
            continue
        mapping = LEGACY_STRUCTURE_LOCALIZATION[label]
        legacy_type_counts[f"{label}:{row.get('struct_type')}"] += 1
        agent_type_counts[f"{mapping['agent_structure']}:{mapping['agent_struct_type']}"] += 1
        if row.get("struct_type") != mapping["agent_struct_type"]:
            mismatch_count += 1
        if len(examples[label]) < 5:
            examples[label].append(
                {
                    "char": row.get("char"),
                    "unicode": format_unicode(row["unicode"]) if isinstance(row.get("unicode"), int) else None,
                    "legacy_struct_type": row.get("struct_type"),
                    "agent_structure": mapping["agent_structure"],
                    "agent_struct_type": mapping["agent_struct_type"],
                }
            )

    mapping_rows = []
    for legacy_label, mapping in LEGACY_STRUCTURE_LOCALIZATION.items():
        mapping_rows.append(
            {
                "legacy_structure": legacy_label,
                "legacy_struct_type": mapping["legacy_struct_type"],
                "agent_structure": mapping["agent_structure"],
                "agent_struct_type": mapping["agent_struct_type"],
                "confidence": mapping["confidence"],
                "rule": mapping["rule"],
                "row_count": raw_counts[legacy_label],
                "examples": examples[legacy_label],
                "standard_level": "agent_standard_mapping_not_national_standard",
            }
        )

    return {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": str(cnbe_input),
            "row_count": len(rows),
            "purpose": "legacy English structure label localization into Agent standard Chinese structure labels",
            "no_write": True,
        },
        "summary": {
            "row_count": len(rows),
            "legacy_label_count": len(raw_counts),
            "all_legacy_labels_mapped": not missing_labels,
            "missing_label_rows": len(missing_labels),
            "struct_type_mismatch_after_agent_mapping": mismatch_count,
            "raw_structure_counts": dict(sorted(raw_counts.items())),
            "agent_structure_type_counts": dict(sorted(agent_type_counts.items())),
        },
        "allowed_agent_structures": AGENT_ALLOWED_STRUCTURES,
        "mapping": mapping_rows,
        "missing_label_samples": missing_labels[:50],
    }


def build_agent_standard(structure_model: dict[str, Any]) -> dict[str, Any]:
    return {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "standard_name": "CNBE Hanzi Structure Agent Encoding Standard",
            "standard_level": "agent_standard_aligned_to_8105_not_national_standard",
            "version": "draft-0.1",
            "no_write": True,
        },
        "authority_layers": {
            "national_standard_baseline": "8105 通用规范汉字表 and cited GF/GB/GG standards",
            "agent_standard": "Project-level mapping aligned to 8105 rules and accepted by the CNBE Agent gates",
            "cnbe32": "Compact carrier format; not the source of linguistic authority",
            "cnbe64_cnbe128": "Extended evidence archive for fields that do not fit CNBE32",
        },
        "required_order": [
            "Unicode identity",
            "8105 or extension scope classification",
            "source-grade evidence",
            "Hanzi knowledge schema",
            "GF0017 50-point audit",
            "Agent-standard mapping for out-of-scope rows",
            "CNBE32 dry-run candidate",
            "roundtrip and batch checkpoint audit",
        ],
        "unicode_identity_rule": {
            "required_fields": ["char", "unicode", "codepoint", "normalization_status", "source_row"],
            "blocker": "Any char/codepoint mismatch blocks the batch.",
        },
        "structure_standard": {
            "allowed_structures": AGENT_ALLOWED_STRUCTURES,
            "legacy_localization": {
                row["legacy_structure"]: {
                    "agent_structure": row["agent_structure"],
                    "agent_struct_type": row["agent_struct_type"],
                    "standard_level": row["standard_level"],
                    "confidence": row["confidence"],
                }
                for row in structure_model["mapping"]
            },
            "not_allowed": [
                "Use legacy English labels as final output",
                "Use non-listed structure names as final labels",
                "Claim Agent localization as national standard",
            ],
        },
        "candidate_statuses": {
            "DIRECT_EVIDENCE_CANDIDATE": "Backed by direct or standard-derived evidence.",
            "AGENT_STANDARD_MAPPING": "Project standard output aligned to 8105 and passed by Agent gates; not national standard.",
            "SOURCE_GAP": "Required standard source is not confirmed.",
            "EVIDENCE_GAP": "Standard-side evidence is incomplete.",
            "HUMAN_REVIEW_REQUIRED": "Evidence is ambiguous or conflict-prone.",
            "BLOCKER": "Batch must stop before continuing.",
        },
        "cnbe32_carrier": {
            "bits_31_24": "radical code",
            "bits_23_19": "stroke count",
            "bits_18_15": "structure type",
            "bits_14_4": "group index",
            "bits_3_0": "extension flags",
            "rule": "CNBE32 fields may be proposed only after the evidence and Agent gates pass.",
        },
        "current_findings": {
            "legacy_rows_scanned": structure_model["summary"]["row_count"],
            "legacy_labels_all_mapped": structure_model["summary"]["all_legacy_labels_mapped"],
            "legacy_struct_type_mismatch_after_agent_mapping": structure_model["summary"][
                "struct_type_mismatch_after_agent_mapping"
            ],
            "interpretation": "Mismatch indicates old struct_type follows legacy ordering, not Agent standard ordering.",
        },
    }


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(item) for item in row) + " |")
    return "\n".join(lines)


def render_structure_markdown(model: dict[str, Any]) -> str:
    rows = [
        [
            item["legacy_structure"],
            item["legacy_struct_type"],
            item["agent_structure"],
            item["agent_struct_type"],
            item["row_count"],
            item["confidence"],
            item["standard_level"],
        ]
        for item in model["mapping"]
    ]
    summary = model["summary"]
    return "\n".join(
        [
            "# CNBE Legacy Structure Localization",
            "",
            "## Scope",
            "",
            "This report maps the legacy 20,902-row English structure labels into the Agent standard Chinese structure labels.",
            "It is read-only and does not modify `data/cnbe32.json` or any database.",
            "",
            "## Summary",
            "",
            f"- Rows scanned: {summary['row_count']}",
            f"- Legacy labels: {summary['legacy_label_count']}",
            f"- All legacy labels mapped: {summary['all_legacy_labels_mapped']}",
            f"- Missing label rows: {summary['missing_label_rows']}",
            f"- Struct type mismatch after Agent mapping: {summary['struct_type_mismatch_after_agent_mapping']}",
            "",
            "## Mapping",
            "",
            markdown_table(
                [
                    "Legacy label",
                    "Legacy type",
                    "Agent structure",
                    "Agent type",
                    "Rows",
                    "Confidence",
                    "Standard level",
                ],
                rows,
            ),
            "",
            "## Interpretation",
            "",
            "The legacy `struct_type` ordering is not the same as the Agent standard ordering.",
            "The localized Chinese structure name is suitable as Agent standard output after gates pass, but must not be described as a national-standard output.",
            "",
            "## Review Rules",
            "",
            "- Use the localized Chinese label as the Agent standard structure label.",
            "- Preserve the legacy English label as raw evidence.",
            "- Preserve the legacy `struct_type` when reporting old rows.",
            "- Use the Agent `struct_type` only in dry-run or approved repair candidates.",
            "- Do not claim this localization table is a national standard.",
            "- Do not overwrite CNBE source data from this report alone.",
            "",
            "## Next Gate",
            "",
            "After localization, every row still needs Unicode alignment, source-grade evidence, GF0017-compatible scoring, and batch checkpoint review.",
            "Rows with low-confidence localization, source gaps, or evidence gaps must remain reviewable before any source table change.",
            "",
        ]
    )


def render_standard_markdown(model: dict[str, Any]) -> str:
    structure_rows = [
        [name, type_id]
        for name, type_id in model["structure_standard"]["allowed_structures"].items()
    ]
    legacy_rows = [
        [
            legacy,
            details["agent_structure"],
            details["agent_struct_type"],
            details["confidence"],
        ]
        for legacy, details in model["structure_standard"]["legacy_localization"].items()
    ]
    return "\n".join(
        [
            "# CNBE Agent Encoding Standard",
            "",
            "## Standard Level",
            "",
            "`8105` and cited GF/GB/GG files are the national-standard baseline.",
            "This document defines the CNBE Agent standard: a project-level encoding standard aligned to 8105, not a national-standard document.",
            "",
            "## Mandatory Order",
            "",
            markdown_table(["Step", "Gate"], [[idx + 1, step] for idx, step in enumerate(model["required_order"])]),
            "",
            "## Allowed Agent Structures",
            "",
            markdown_table(["Agent structure", "Agent struct_type"], structure_rows),
            "",
            "## Legacy Localization",
            "",
            markdown_table(["Legacy label", "Agent structure", "Agent struct_type", "Confidence"], legacy_rows),
            "",
            "## CNBE32 Carrier",
            "",
            "- bits 31..24: radical code",
            "- bits 23..19: stroke count",
            "- bits 18..15: structure type",
            "- bits 14..4: group index",
            "- bits 3..0: extension flags",
            "",
            "CNBE32 is a compact carrier. It is not the linguistic authority.",
            "",
            "## Output Rule",
            "",
            "`AGENT_STANDARD_MAPPING` may be used as this Agent's standard output after Unicode, evidence, Hanzi schema, GF0017, and batch gates pass.",
            "It must be labeled as `agent_standard_aligned_to_8105_not_national_standard`.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cnbe-input", type=Path, default=DEFAULT_CNBE_INPUT)
    parser.add_argument("--standard-output", type=Path, default=DEFAULT_STANDARD_OUTPUT)
    parser.add_argument("--standard-markdown", type=Path, default=DEFAULT_STANDARD_MARKDOWN)
    parser.add_argument("--structure-output", type=Path, default=DEFAULT_STRUCTURE_OUTPUT)
    parser.add_argument("--structure-markdown", type=Path, default=DEFAULT_STRUCTURE_MARKDOWN)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    structure = build_structure_localization(args.cnbe_input)
    standard = build_agent_standard(structure)
    write_json(args.structure_output, structure)
    write_text(args.structure_markdown, render_structure_markdown(structure))
    write_json(args.standard_output, standard)
    write_text(args.standard_markdown, render_standard_markdown(standard))
    print(f"wrote {args.structure_output}")
    print(f"wrote {args.structure_markdown}")
    print(f"wrote {args.standard_output}")
    print(f"wrote {args.standard_markdown}")
    print(f"rows={structure['summary']['row_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
