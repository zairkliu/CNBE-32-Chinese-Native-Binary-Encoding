#!/usr/bin/env python3
"""Audit a completed PENC276 review export and smoke-test bounded ihandian use.

This script consumes a read-only JSON export of the reviewer workbook. It does
not alter the workbook, review packet, CNBE source table, or SQLite database.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import Any

try:
    from scripts.extract_ihandian_character_reference import fetch_html, ihandian_url, parse_ihandian_html
except ModuleNotFoundError:  # Direct execution from the repository root.
    from extract_ihandian_character_reference import fetch_html, ihandian_url, parse_ihandian_html


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_PACKET = ROOT / "review_packets" / "pending276" / "PENC276_REMAINING_168_CHINESE_HUMAN_REVIEW_PACKET_EDITABLE.csv"
DEFAULT_REPORT_JSON = ROOT / "reports" / "PENC276_REMAINING_168_HUMAN_REVIEW_INTAKE_AUDIT.json"
DEFAULT_REPORT_MD = ROOT / "reports" / "PENC276_REMAINING_168_HUMAN_REVIEW_INTAKE_AUDIT.md"
EDITABLE_FIELDS = {
    "审核结构（填写）",
    "审核拆解或部件（填写）",
    "审核笔画数（填写）",
    "审核部首（填写）",
    "审核结论（填写）",
    "审核说明（填写）",
    "审核人（填写）",
    "审核日期（填写）",
}
HUMAN_APPROVED_NONRENDERABLE_REFERENCE_ROWS = {
    "PENC_022": "网页拆字含暂时不可显现的组件字形；保留人工拆解，不计为参考差异。",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def compact_decomposition(value: object) -> str:
    return re.sub(r"[\s、，,;；+＋]", "", str(value or ""))


def excel_date(value: object) -> str:
    if isinstance(value, (float, int)) or (isinstance(value, str) and value.isdigit()):
        return str(date(1899, 12, 30) + timedelta(days=int(value)))
    return str(value or "")


def comparable_fixed_value(field: str, value: object) -> str:
    """Permit only the known punctuation-only evidence-boundary presentation variant."""

    text = str(value or "")
    return text.replace("、", "") if field == "证据边界" else text


def select_stratified_smoke_sample(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Use all scarce tiers and three deterministic T1/T2 representatives."""

    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row["原始分层"])].append(row)
    selected: list[dict[str, Any]] = []
    for tier in ("T0", "T1", "T2", "T3", "T4"):
        group = groups[tier]
        if len(group) <= 4:
            selected.extend(group)
            continue
        indices = (0, len(group) // 2, len(group) - 1)
        selected.extend(group[index] for index in indices)
    return selected


def audit_rows(rows: list[dict[str, Any]], canonical: list[dict[str, str]]) -> dict[str, Any]:
    canonical_by_id = {row["清单编号"]: row for row in canonical}
    required = {
        "审核结构（填写）",
        "审核拆解或部件（填写）",
        "审核笔画数（填写）",
        "审核部首（填写）",
        "审核结论（填写）",
        "审核说明（填写）",
        "审核人（填写）",
        "审核日期（填写）",
    }
    if len(rows) != 168 or len(canonical_by_id) != 168 or any(field not in row for field in required for row in rows):
        raise ValueError("completed review export does not match the expected 168-row Chinese packet schema")

    row_ids = {str(row["清单编号"]) for row in rows}
    fixed_mismatch_rows: list[str] = []
    presentation_variations: dict[str, int] = defaultdict(int)
    for row in rows:
        reference = canonical_by_id.get(str(row["清单编号"]))
        if reference is None:
            fixed_mismatch_rows.append(str(row["清单编号"]))
            continue
        for field, expected in reference.items():
            if field in EDITABLE_FIELDS:
                continue
            actual = str(row.get(field, ""))
            if actual != str(expected):
                if comparable_fixed_value(field, actual) == comparable_fixed_value(field, expected):
                    presentation_variations[field] += 1
                    continue
                fixed_mismatch_rows.append(str(row["清单编号"]))
                break
    conclusions = [str(row["审核结论（填写）"]).strip() for row in rows]
    decomposition_complete = all(compact_decomposition(row["审核拆解或部件（填写）"]) for row in rows)
    status_fill_mode = all(
        str(row[field]).strip() == "通过"
        for row in rows
        for field in ("审核结构（填写）", "审核笔画数（填写）", "审核部首（填写）")
    )
    reviewer_dates = sorted({excel_date(row["审核日期（填写）"]) for row in rows})
    return {
        "rows": len(rows),
        "row_ids_match_canonical": row_ids == set(canonical_by_id),
        "fixed_column_mismatch_rows": sorted(set(fixed_mismatch_rows)),
        "fixed_column_presentation_variations": dict(presentation_variations),
        "all_conclusions_pass": set(conclusions) == {"通过"},
        "all_decompositions_nonempty": decomposition_complete,
        "status_fill_mode": status_fill_mode,
        "reviewer_ids": sorted({str(row["审核人（填写）"]).strip() for row in rows}),
        "review_dates": reviewer_dates,
    }


def smoke_test_ihandian(rows: list[dict[str, Any]], timeout: int) -> list[dict[str, Any]]:
    results = []
    for row in select_stratified_smoke_sample(rows):
        codepoint = str(row["Unicode"]).removeprefix("U+")
        attempts = 0
        try:
            for attempts in range(1, 3):
                try:
                    raw_html = fetch_html(ihandian_url(codepoint), timeout)
                    break
                except Exception:
                    if attempts == 2:
                        raise
            record = parse_ihandian_html(codepoint, raw_html, ihandian_url(codepoint))
            fields = record["fields"]
            human_decomposition = compact_decomposition(row["审核拆解或部件（填写）"])
            web_decomposition = compact_decomposition("".join(fields["decomposition"]))
            results.append(
                {
                    "row_id": row["清单编号"],
                    "character": row["汉字"],
                    "unicode": row["Unicode"],
                    "tier": row["原始分层"],
                    "parse_status": record["parse_status"],
                    "identity_matches_unicode": record["identity_matches_unicode"],
                    "web_structure": fields["structure"],
                    "web_decomposition": fields["decomposition"],
                    "human_decomposition": row["审核拆解或部件（填写）"],
                    "decomposition_exact_match": bool(web_decomposition) and human_decomposition == web_decomposition,
                    "source_level": record["source_level"],
                    "retrieval_attempts": attempts,
                }
            )
        except Exception as exc:  # noqa: BLE001 - preserve bounded network gap for review.
            results.append(
                {
                    "row_id": row["清单编号"],
                    "character": row["汉字"],
                    "unicode": row["Unicode"],
                    "tier": row["原始分层"],
                    "parse_status": "NETWORK_OR_PARSE_GAP",
                    "identity_matches_unicode": False,
                    "error": f"{type(exc).__name__}: {exc}",
                    "source_level": "network_dictionary_cross_reference",
                    "retrieval_attempts": attempts,
                }
            )
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("review_export", type=Path, help="JSON exported from the completed XLSX through artifact-tool")
    parser.add_argument("--source-workbook", type=Path, help="optional original completed XLSX for provenance hashing")
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--report-json", type=Path, default=DEFAULT_REPORT_JSON)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_MD)
    args = parser.parse_args()
    exported = json.loads(args.review_export.read_text(encoding="utf-8"))
    rows = exported["rows"]
    review = audit_rows(rows, read_csv(CANONICAL_PACKET))
    sample = smoke_test_ihandian(rows, args.timeout)
    sample_success = [row for row in sample if row["parse_status"] == "PARSED_IDENTITY_ALIGNED"]
    raw_reference_difference_rows = [row["row_id"] for row in sample if row.get("web_decomposition") and not row.get("decomposition_exact_match")]
    approved_display_exception_rows = [
        row_id for row_id in raw_reference_difference_rows if row_id in HUMAN_APPROVED_NONRENDERABLE_REFERENCE_ROWS
    ]
    reference_difference_rows = [
        row_id for row_id in raw_reference_difference_rows if row_id not in HUMAN_APPROVED_NONRENDERABLE_REFERENCE_ROWS
    ]
    review_is_complete = (
        review["row_ids_match_canonical"]
        and not review["fixed_column_mismatch_rows"]
        and review["all_conclusions_pass"]
        and review["all_decompositions_nonempty"]
    )
    extractor_is_operational = len(sample_success) == len(sample)
    if review_is_complete and extractor_is_operational:
        status = (
            "PASS_COMPLETED_HUMAN_REVIEW_IHANDIAN_OPERATIONAL_WITH_HUMAN_APPROVED_DISPLAY_EXCEPTION"
            if approved_display_exception_rows
            else "PASS_COMPLETED_HUMAN_REVIEW_IHANDIAN_OPERATIONAL_WITH_REFERENCE_DIFFERENCE"
            if reference_difference_rows
            else "PASS_COMPLETED_HUMAN_REVIEW_IHANDIAN_OPERATIONAL"
        )
    else:
        status = "REVIEW_REQUIRED"
    report = {
        "schema_version": "penc276-remaining168-completed-human-review-intake-audit-v1",
        "review_export_sha256": sha256(args.review_export),
        "source_workbook": {
            "name": args.source_workbook.name,
            "sha256": sha256(args.source_workbook),
        }
        if args.source_workbook
        else None,
        "canonical_packet_sha256": sha256(CANONICAL_PACKET),
        "review": review,
        "ihandian_smoke_test": {
            "sample_size": len(sample),
            "identity_aligned_records": len(sample_success),
            "records_with_web_decomposition": sum(bool(row.get("web_decomposition")) for row in sample),
            "exact_human_decomposition_matches": sum(bool(row.get("decomposition_exact_match")) for row in sample),
            "reference_difference_rows": reference_difference_rows,
            "human_approved_nonrenderable_reference_rows": {
                row_id: HUMAN_APPROVED_NONRENDERABLE_REFERENCE_ROWS[row_id]
                for row_id in approved_display_exception_rows
            },
            "records": sample,
            "authority_boundary": "network_dictionary_cross_reference_only_not_gold_standard",
        },
        "decision": {
            "status": status,
            "may_generate_cnbe_candidates": False,
            "may_modify_source_tables": False,
            "may_modify_sqlite": False,
            "may_claim_national_standard": False,
        },
    }
    args.report_json.parent.mkdir(parents=True, exist_ok=True)
    args.report_json.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.report_md.write_text(
        "# PENC276 剩余 168 字已完成人工审核导入审计\n\n"
        f"- 原审核工作簿 SHA-256：`{report['source_workbook']['sha256'] if report['source_workbook'] else '未提供'}`。\n"
        f"- 审核行数：`{review['rows']}`；与原审核包行号一致：`{review['row_ids_match_canonical']}`。\n"
        f"- 固定证据列差异行：`{len(review['fixed_column_mismatch_rows'])}`。\n"
        f"- 仅排版/标点等价差异：`{review['fixed_column_presentation_variations']}`。\n"
        f"- 审核结论全部通过：`{review['all_conclusions_pass']}`；人工拆解全部非空：`{review['all_decompositions_nonempty']}`。\n"
        f"- 审核人：`{', '.join(review['reviewer_ids'])}`；审核日期：`{', '.join(review['review_dates'])}`。\n"
        f"- 状态填法：结构/笔画/部首列均填“通过”=`{review['status_fill_mode']}`，表示人工确认现有字段，不作为新的字段值。\n\n"
        "## ihandian 有界冒烟测试\n\n"
        f"- 按 T0–T4 分层抽样：`{len(sample)}` 字。\n"
        f"- 网页解析与 Unicode 对齐成功：`{len(sample_success)} / {len(sample)}`。\n"
        f"- 网页提供拆字：`{report['ihandian_smoke_test']['records_with_web_decomposition']} / {len(sample)}`；"
        f"与人工拆字逐字串完全一致：`{report['ihandian_smoke_test']['exact_human_decomposition_matches']} / {len(sample)}`。\n\n"
        f"- 保留的网页参考差异行：`{', '.join(reference_difference_rows) if reference_difference_rows else '无'}`。\n"
        f"- 人工确认的不可显现组件字形例外：`{', '.join(approved_display_exception_rows) if approved_display_exception_rows else '无'}`。"
        "此类例外不替代人工拆解，也不计为网页参考差异。\n\n"
        "本测试只证明 ihandian 的单字提取器可为审核导航提供字段；它是网络字典交叉参考，"
        "不是国家标准或金标准。人工审核结果不会被网页自动覆盖，且本轮不生成 CNBE 候选、"
        "不修改源表或 SQLite。\n",
        encoding="utf-8",
    )
    print(report["decision"]["status"])


if __name__ == "__main__":
    main()
