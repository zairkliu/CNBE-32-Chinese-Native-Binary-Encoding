#!/usr/bin/env python3
"""Evaluate external dictionary candidates before any CNBE knowledge import."""

from __future__ import annotations

import json
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path("build/external_dictionary_candidates")
NLP = ROOT / "nlp-han-dicts"
NLP_EXTRACTED = NLP / "extracted"
KANGXI_SQL = ROOT / "kangxi" / "康熙字典.sql"
KR = ROOT / "KR1j0048"

FEATURE_TABLE = Path("reports/remaining_structure_agent_standard_feature_table.json")
HUMAN_REVIEW_PACKET = Path("reports/remaining_structure_agent_standard_human_review_packet.json")

DEFAULT_JSON_OUTPUT = Path("reports/external_dictionary_source_candidate_evaluation.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/EXTERNAL_DICTIONARY_SOURCE_CANDIDATE_EVALUATION.md")

NLP_KANGXI_DB = NLP_EXTRACTED / "kangxi.4w.db"
NLP_ZHDZD_DB = NLP_EXTRACTED / "zhdzd_simpledict.db"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def git_head(path: Path) -> str:
    head = path / ".git" / "HEAD"
    if not head.exists():
        return "UNKNOWN"
    raw = head.read_text(encoding="utf-8").strip()
    if raw.startswith("ref: "):
        ref = path / ".git" / raw.split(" ", maxsplit=1)[1]
        if ref.exists():
            return ref.read_text(encoding="utf-8").strip()
        packed = path / ".git" / "packed-refs"
        if packed.exists():
            ref_name = raw.split(" ", maxsplit=1)[1]
            for line in packed.read_text(encoding="utf-8").splitlines():
                if line.endswith(" " + ref_name):
                    return line.split(" ", maxsplit=1)[0]
    return raw


def sqlite_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False}
    with sqlite3.connect(path) as conn:
        conn.row_factory = sqlite3.Row
        tables = [row[0] for row in conn.execute("select name from sqlite_master where type='table' order by name")]
        schema = "\n".join(row[0] for row in conn.execute("select sql from sqlite_master where sql is not null order by name"))
        dict_count = conn.execute("select count(*) from Dict").fetchone()[0]
        distinct_word_count = conn.execute("select count(distinct word) from Dict").fetchone()[0]
        single_char_count = conn.execute("select count(*) from Dict where length(word)=1").fetchone()[0]
        samples = [
            {"word": row["word"], "content_preview": row["content"][:120]}
            for row in conn.execute("select word, content from Dict order by id limit 5")
        ]
    return {
        "exists": True,
        "path": str(path),
        "bytes": path.stat().st_size,
        "tables": tables,
        "schema": schema,
        "dict_count": dict_count,
        "distinct_word_count": distinct_word_count,
        "single_char_count": single_char_count,
        "samples": samples,
    }


def sqlite_word_set(path: Path) -> set[str]:
    if not path.exists():
        return set()
    with sqlite3.connect(path) as conn:
        return {row[0] for row in conn.execute("select distinct word from Dict where word is not null")}


def kangxi_sql_words(path: Path) -> set[str]:
    if not path.exists():
        return set()
    words: set[str] = set()
    for line in read_text(path).splitlines():
        if not line.startswith("INSERT INTO"):
            continue
        parts = line.split("', '")
        if len(parts) >= 2:
            words.add(parts[1])
    return words


def kr_text_hit_count(chars: set[str]) -> tuple[int, dict[str, list[str]]]:
    hits: dict[str, list[str]] = {char: [] for char in chars}
    for path in KR.glob("*.txt"):
        text = read_text(path)
        for char in chars:
            if char in text:
                hits[char].append(path.name)
    hit_chars = {char for char, files in hits.items() if files}
    sample_hits = {char: files[:5] for char, files in sorted(hits.items()) if files}
    return len(hit_chars), sample_hits


def coverage(chars: list[str], word_set: set[str]) -> dict[str, Any]:
    unique_chars = sorted(set(chars))
    hit = [char for char in unique_chars if char in word_set]
    return {
        "target_unique_chars": len(unique_chars),
        "hit_count": len(hit),
        "miss_count": len(unique_chars) - len(hit),
        "hit_rate": round(len(hit) / len(unique_chars), 6) if unique_chars else 0,
        "hit_samples": hit[:50],
        "miss_samples": [char for char in unique_chars if char not in word_set][:50],
    }


def build_evaluation() -> dict[str, Any]:
    feature = load_json(FEATURE_TABLE)
    human = load_json(HUMAN_REVIEW_PACKET)
    feature_chars = [row["char"] for row in feature["row_records"]]
    human_chars = [row["char"] for row in human["rows"]]
    full_catalog_rows = 97_686

    nlp_kangxi = sqlite_summary(NLP_KANGXI_DB)
    nlp_zhdzd = sqlite_summary(NLP_ZHDZD_DB)
    nlp_kangxi_words = sqlite_word_set(NLP_KANGXI_DB)
    nlp_zhdzd_words = sqlite_word_set(NLP_ZHDZD_DB)
    nlp_union_words = nlp_kangxi_words | nlp_zhdzd_words
    he_words = kangxi_sql_words(KANGXI_SQL)
    kr_human_hits, kr_human_sample = kr_text_hit_count(set(human_chars))

    candidate_reports = {
        "leechenhwa2_nlp_han_dicts": {
            "repo": "https://github.com/leechenhwa2/nlp-han-dicts",
            "local_path": str(NLP),
            "head": git_head(NLP),
            "license": "BSD-2-Clause",
            "data_shape": "SQLite Dict(word, content, word1, word2) plus Kangxi volume in kangxi.4w.db",
            "source_grade_for_cnbe": "cross_reference_dictionary_context",
            "recommended_role": "primary_structured_dictionary_context_source",
            "kangxi_db": nlp_kangxi,
            "zhonghua_dazidian_db": nlp_zhdzd,
            "human_review_150_coverage": coverage(human_chars, nlp_union_words),
            "remaining_73831_coverage": coverage(feature_chars, nlp_union_words),
        },
        "he426100_kangxi": {
            "repo": "https://github.com/he426100/kangxi",
            "local_path": str(ROOT / "kangxi"),
            "head": git_head(ROOT / "kangxi"),
            "license": "not_found_in_repository_snapshot",
            "data_shape": "PostgreSQL insert dump plus MDB/EXE/ZIP assets",
            "source_grade_for_cnbe": "cross_reference_dictionary_context_with_license_blocker",
            "recommended_role": "secondary_comparison_only_until_license_and_quality_are_resolved",
            "readme_quality_note": "Repository README states one packaged database has data errors.",
            "sql_bytes": KANGXI_SQL.stat().st_size if KANGXI_SQL.exists() else 0,
            "sql_word_count": len(he_words),
            "human_review_150_coverage": coverage(human_chars, he_words),
            "remaining_73831_coverage": coverage(feature_chars, he_words),
        },
        "kanripo_KR1j0048": {
            "repo": "https://github.com/kanripo/KR1j0048",
            "local_path": str(KR),
            "head": git_head(KR),
            "license": "not_found_in_repository_snapshot",
            "data_shape": "41 plain text Mandoku/Kanripo source files for 御定康熙字典",
            "source_grade_for_cnbe": "cross_reference_primary_text_context_with_parser_required",
            "recommended_role": "primary_text_witness_for_spot_validation_after_parser_design",
            "txt_file_count": len(list(KR.glob("*.txt"))),
            "txt_total_bytes": sum(p.stat().st_size for p in KR.glob("*.txt")),
            "human_review_150_text_hit_count": kr_human_hits,
            "human_review_150_text_hit_samples": kr_human_sample,
        },
    }

    checks = {
        "nlp_kangxi_sqlite_exists": nlp_kangxi.get("exists") is True,
        "nlp_zhonghua_dazidian_sqlite_exists": nlp_zhdzd.get("exists") is True,
        "nlp_license_is_declared_bsd_2_clause": (NLP / "LICENSE").exists() and "BSD 2-Clause" in read_text(NLP / "LICENSE"),
        "human_review_packet_rows_150": len(human_chars) == 150,
        "remaining_feature_rows_73831": len(feature_chars) == 73_831,
        "no_formal_scoring_allowed": True,
        "no_knowledge_write_performed": True,
    }
    status = "PASS_EXTERNAL_DICTIONARY_SOURCE_EVALUATION_READY" if all(checks.values()) else "BLOCKED"
    return {
        "report_schema_version": "1.0",
        "mode": "read_only_external_dictionary_source_candidate_evaluation",
        "overall_status": status,
        "next_workflow_status": "DICTIONARY_CONTEXT_IMPORT_PLAN_ALLOWED_KNOWLEDGE_WRITE_BLOCKED",
        "authority_boundary": {
            "dictionary_sources_are_cross_reference_context": True,
            "not_national_standard_structure_authority": True,
            "does_not_assign_gf0017_scores": True,
            "does_not_emit_final_structure_labels": True,
            "does_not_modify_cnbe_research_knowledge": True,
            "does_not_modify_cnbe_rows": True,
            "does_not_rebuild_database": True,
        },
        "summary": {
            "full_catalog_rows": full_catalog_rows,
            "remaining_agent_standard_rows": len(feature_chars),
            "human_review_packet_rows": len(human_chars),
            "recommended_primary_source": "leechenhwa2/nlp-han-dicts",
            "recommended_supporting_source": "kanripo/KR1j0048",
            "recommended_secondary_comparison_source": "he426100/kangxi",
            "knowledge_write_allowed": False,
            "formal_gf0017_scoring_allowed": False,
        },
        "checks": checks,
        "candidates": candidate_reports,
        "decision": {
            "may_plan_dictionary_context_import": status.startswith("PASS"),
            "may_modify_cnbe_research_knowledge": False,
            "may_start_formal_gf0017_scoring": False,
            "may_emit_final_structure_labels": False,
            "recommended_next_script": "scripts/plan_external_dictionary_context_import.py",
            "reason": (
                "Use nlp-han-dicts as the primary structured dictionary context source because it "
                "contains licensed SQLite Kangxi and Zhonghua Dazidian databases. Use KR1j0048 as a "
                "primary-text witness after parser design. Keep he426100/kangxi as secondary comparison "
                "only until licensing and data-quality blockers are resolved."
            ),
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    cands = report["candidates"]
    nlp = cands["leechenhwa2_nlp_han_dicts"]
    he = cands["he426100_kangxi"]
    kr = cands["kanripo_KR1j0048"]
    lines = [
        "# External Dictionary Source Candidate Evaluation",
        "",
        "## Purpose",
        "",
        "This report evaluates external Kangxi and Zhonghua Dazidian resources",
        "as dictionary context candidates for CNBE human review and source-gap",
        "resolution.",
        "",
        "It does not write `cnbe-research/knowledge`, assign GF0017 scores, emit",
        "final structure labels, write CNBE rows, or rebuild databases.",
        "",
        "## Result",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Next workflow status: `{report['next_workflow_status']}`",
        f"- Recommended primary source: `{report['summary']['recommended_primary_source']}`",
        f"- Recommended supporting source: `{report['summary']['recommended_supporting_source']}`",
        f"- Recommended secondary comparison source: `{report['summary']['recommended_secondary_comparison_source']}`",
        "",
        "## Candidate Summary",
        "",
        "| Candidate | Role | License | Shape | Human 150 hit rate | Remaining 73,831 hit rate |",
        "|---|---|---|---|---:|---:|",
        (
            f"| leechenhwa2/nlp-han-dicts | {nlp['recommended_role']} | {nlp['license']} | "
            f"SQLite Kangxi + Zhonghua Dazidian | {nlp['human_review_150_coverage']['hit_rate']} | "
            f"{nlp['remaining_73831_coverage']['hit_rate']} |"
        ),
        (
            f"| he426100/kangxi | {he['recommended_role']} | {he['license']} | "
            f"PostgreSQL dump/MDB | {he['human_review_150_coverage']['hit_rate']} | "
            f"{he['remaining_73831_coverage']['hit_rate']} |"
        ),
        (
            f"| kanripo/KR1j0048 | {kr['recommended_role']} | {kr['license']} | "
            f"41 Mandoku text files | n/a text hits {kr['human_review_150_text_hit_count']} | n/a |"
        ),
        "",
        "## Checks",
        "",
    ]
    for check, value in report["checks"].items():
        lines.append(f"- `{check}`: {value}")
    lines.extend(["", "## Decision", "", report["decision"]["reason"], ""])
    return "\n".join(lines)


def main() -> None:
    report = build_evaluation()
    write_json(DEFAULT_JSON_OUTPUT, report)
    write_text(DEFAULT_MARKDOWN_OUTPUT, render_markdown(report))


if __name__ == "__main__":
    main()
