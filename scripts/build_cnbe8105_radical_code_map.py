#!/usr/bin/env python3
"""Build a conservative radical-name to numeric-code map for 8105 candidates."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_CANDIDATE_INPUT = Path("evidence/8105/cnbe8105_auto_fix_candidates.json")
DEFAULT_MAPPING_OUTPUT = Path("evidence/8105/cnbe8105_radical_code_map.json")
DEFAULT_MARKDOWN_OUTPUT = Path("evidence/8105/CNBE8105_RADICAL_CODE_MAP.md")
KNOWLEDGE_BASE = Path("/Users/liuzhaoqi/Documents/cnbe-research/knowledge/knowledge_base_v2.json")

SAMPLE_LIMIT = 30

# Conservative aliases only. Position-sensitive or weak aliases stay blocked.
RADICAL_ALIASES = {
    "⺀": "冫",
    "⺊": "卜",
    "⺌": "小",
    "⺗": "心",
    "⺮": "竹",
    "⺳": "网",
    "⺼": "肉",
    "㔾": "卩",
    "丬": "爿",
    "亻": "人",
    "刂": "刀",
    "卤": "鹵",
    "川": "巛",
    "彑": "彐",
    "忄": "心",
    "户": "戶",
    "扌": "手",
    "攵": "攴",
    "氵": "水",
    "氺": "水",
    "灬": "火",
    "爫": "爪",
    "犭": "犬",
    "玉": "王",
    "礻": "示",
    "纟": "糸",
    "罒": "网",
    "耂": "老",
    "艹": "艸",
    "虎": "虍",
    "衤": "衣",
    "覀": "西",
    "见": "見",
    "讠": "言",
    "贝": "貝",
    "车": "車",
    "辶": "辵",
    "钅": "金",
    "门": "門",
    "韦": "韋",
    "页": "頁",
    "风": "風",
    "饣": "食",
    "马": "馬",
    "鱼": "魚",
    "鸟": "鳥",
    "麦": "麥",
    "黄": "黃",
    "黾": "黽",
    "齐": "齊",
    "齿": "齒",
    "龙": "龍",
    "龟": "龜",
}

BLOCKED_RADICALS = {
    "阝": "position-sensitive: left 阝 is 阜, right 阝 is 邑; source does not preserve side.",
    "丷": "component-like label; no conservative modern radical code assignment in this phase.",
    "乚": "stroke/component-like label; no conservative radical assignment in this phase.",
    "乛": "stroke/component-like label; no conservative radical assignment in this phase.",
    "兀": "component-like label; ambiguous against 儿 in this evidence layer.",
    "巳": "ambiguous against 己/已/巳 shape group in this evidence layer.",
    "民": "component-like label; not a Kangxi radical main-form in the mapping source.",
}


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


def load_radical_code_source(path: Path) -> dict[str, Any]:
    data = load_json(path)
    radical_chars = data["concepts"]["bushou"]["radical_chars"]
    code_to_radical = {int(code): radical for code, radical in radical_chars.items()}
    radical_to_code = {radical: code for code, radical in code_to_radical.items()}
    return {
        "metadata": {
            "source": path.as_posix(),
            "declared_count": data["concepts"]["bushou"].get("count"),
            "actual_count": len(code_to_radical),
            "max_code": max(code_to_radical),
        },
        "code_to_radical": code_to_radical,
        "radical_to_code": radical_to_code,
    }


def candidate_radical_counts(candidate_model: dict[str, Any]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for record in candidate_model.get("candidates", []):
        radical = record.get("proposed", {}).get("radix_name")
        if radical:
            counts[radical] += 1
    return counts


def resolve_radical(radical: str, radical_to_code: dict[str, int]) -> dict[str, Any]:
    if radical in radical_to_code:
        return {
            "radical": radical,
            "status": "DIRECT",
            "canonical_radical": radical,
            "code": radical_to_code[radical],
            "reason": "main-form radical found in mapping source",
        }
    alias = RADICAL_ALIASES.get(radical)
    if alias and alias in radical_to_code:
        return {
            "radical": radical,
            "status": "ALIAS",
            "canonical_radical": alias,
            "code": radical_to_code[alias],
            "reason": "conservative variant or simplified radical alias",
        }
    return {
        "radical": radical,
        "status": "BLOCKED",
        "canonical_radical": alias,
        "code": None,
        "reason": BLOCKED_RADICALS.get(radical, "no conservative mapping rule in this phase"),
    }


def build_radical_mapping(candidate_model: dict[str, Any], radical_source: dict[str, Any]) -> dict[str, Any]:
    radical_to_code = radical_source["radical_to_code"]
    counts = candidate_radical_counts(candidate_model)
    records = []
    status_counts: Counter[str] = Counter()
    ready_candidate_rows = 0
    blocked_candidate_rows = 0

    for radical, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        record = resolve_radical(radical, radical_to_code)
        record["candidate_rows"] = count
        records.append(record)
        status_counts[record["status"]] += 1
        if record["status"] in {"DIRECT", "ALIAS"}:
            ready_candidate_rows += count
        else:
            blocked_candidate_rows += count

    blocked_records = [record for record in records if record["status"] == "BLOCKED"]
    alias_records = [record for record in records if record["status"] == "ALIAS"]
    direct_records = [record for record in records if record["status"] == "DIRECT"]

    return {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "scope": "radical numeric code readiness for 8105 auto-fix candidates",
            "source": radical_source["metadata"],
            "apply_gate": "NO_APPLY_IN_THIS_PHASE",
            "rule": "Only direct main-form radicals and conservative aliases are radix-ready.",
        },
        "summary": {
            "candidate_rows": sum(counts.values()),
            "unique_candidate_radicals": len(counts),
            "direct_radical_names": len(direct_records),
            "alias_radical_names": len(alias_records),
            "blocked_radical_names": len(blocked_records),
            "ready_candidate_rows": ready_candidate_rows,
            "blocked_candidate_rows": blocked_candidate_rows,
            "resolution_status_counts": dict(sorted(status_counts.items())),
            "source_declared_count": radical_source["metadata"]["declared_count"],
            "source_actual_count": radical_source["metadata"]["actual_count"],
            "source_count_consistent": radical_source["metadata"]["declared_count"]
            == radical_source["metadata"]["actual_count"],
        },
        "blocked_radicals": blocked_records,
        "alias_radicals": alias_records,
        "direct_radicals": direct_records,
        "records": records,
    }


def render_markdown_report(mapping_model: dict[str, Any]) -> str:
    summary = mapping_model["summary"]
    blocked_rows = [
        [record["radical"], record["candidate_rows"], record["reason"]]
        for record in mapping_model["blocked_radicals"][:SAMPLE_LIMIT]
    ]
    alias_rows = [
        [record["radical"], record["canonical_radical"], record["code"], record["candidate_rows"]]
        for record in mapping_model["alias_radicals"][:SAMPLE_LIMIT]
    ]
    return "\n".join(
        [
            "# CNBE-32 8105 Radical Code Map",
            "",
            "## Scope",
            "",
            "This report validates whether proposed radical names in the 8105 auto-fix candidates can be assigned numeric radical codes.",
            "It does not modify source CNBE data and does not recalculate 32-bit CNBE values.",
            "",
            "## Source Gate",
            "",
            f"- Source declared count: {summary['source_declared_count']}",
            f"- Source actual count: {summary['source_actual_count']}",
            f"- Source count consistent: {summary['source_count_consistent']}",
            "",
            "## Candidate Gate",
            "",
            f"- Candidate rows: {summary['candidate_rows']}",
            f"- Unique candidate radicals: {summary['unique_candidate_radicals']}",
            f"- Direct radical names: {summary['direct_radical_names']}",
            f"- Alias radical names: {summary['alias_radical_names']}",
            f"- Blocked radical names: {summary['blocked_radical_names']}",
            f"- Ready candidate rows: {summary['ready_candidate_rows']}",
            f"- Blocked candidate rows: {summary['blocked_candidate_rows']}",
            "",
            "## Alias Samples",
            "",
            markdown_table(["Variant", "Canonical", "Code", "Candidate Rows"], alias_rows),
            "",
            "## Blocked Radicals",
            "",
            markdown_table(["Radical", "Candidate Rows", "Reason"], blocked_rows),
            "",
            "## Decision",
            "",
            "The radical-code gate is not fully closed while blocked radicals remain.",
            "A later dry-run patch may only use candidates whose proposed radical resolves as DIRECT or ALIAS.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-input", type=Path, default=DEFAULT_CANDIDATE_INPUT)
    parser.add_argument("--knowledge-base", type=Path, default=KNOWLEDGE_BASE)
    parser.add_argument("--mapping-output", type=Path, default=DEFAULT_MAPPING_OUTPUT)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        candidate_model = load_json(args.candidate_input)
        radical_source = load_radical_code_source(args.knowledge_base)
        mapping_model = build_radical_mapping(candidate_model, radical_source)
    except Exception as exc:  # pragma: no cover - command-line guard
        print(f"CNBE8105 RADICAL CODE MAP FAIL: {exc}", file=sys.stderr)
        return 1

    write_json(args.mapping_output, mapping_model)
    write_text(args.markdown_output, render_markdown_report(mapping_model))
    summary = mapping_model["summary"]
    print("CNBE8105 RADICAL CODE MAP PASS")
    print(f"Candidate rows: {summary['candidate_rows']}")
    print(f"Ready candidate rows: {summary['ready_candidate_rows']}")
    print(f"Blocked candidate rows: {summary['blocked_candidate_rows']}")
    print(f"Blocked radical names: {summary['blocked_radical_names']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
