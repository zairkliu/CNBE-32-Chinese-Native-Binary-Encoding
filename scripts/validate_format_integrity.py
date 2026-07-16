from __future__ import annotations

import ast
import json
import subprocess
import sys
import unicodedata
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 compatibility
    import tomli as tomllib


# Read version at module scope for dynamic file lists
_pyproject = tomllib.loads((Path(__file__).resolve().parent.parent / "pyproject.toml").read_text(encoding="utf-8"))
version = _pyproject["project"]["version"]

TEXT_FILES = [
    ".gitattributes",
    "MANIFEST.in",
    "pyproject.toml",
    ".github/workflows/ci.yml",
    "src/cnbe32/core.py",
    "src/cnbe32/constants.py",
    "src/cnbe32/exceptions.py",
    "src/cnbe32/db.py",
    "src/cnbe32/encoders.py",
    "src/cnbe32/skill_table.py",
    "src/cnbe32/__init__.py",
    "tests/test_cnbe32.py",
    "tests/test_golden_vectors.py",
    "tests/test_install_smoke.py",
    "tests/test_package_metadata.py",
    "spec/golden_vectors.json",
    "spec/GOLDEN_VECTORS.md",
    "spec/IMPLEMENTATION_CONSISTENCY.md",
    f"docs/releases/v{version}.md",
    "docs/releases/v1.0.2.md",
    "llm_experiments/v1_v4_redesign/README.md",
    "llm_experiments/v1_v4_redesign/datasets/annotation_schema.json",
    "llm_experiments/v1_v4_redesign/datasets/sampling_plan.md",
    "llm_experiments/v1_v4_redesign/evaluation/judge_prompt.md",
    "llm_experiments/v1_v4_redesign/evaluation/metrics.md",
    "llm_experiments/v1_v4_redesign/evaluation/rubric.md",
    "llm_experiments/v1_v4_redesign/prompts/v1_single_char.yaml",
    "llm_experiments/v1_v4_redesign/prompts/v2_sentence.yaml",
    "llm_experiments/v1_v4_redesign/prompts/v3_format_ablation.yaml",
    "llm_experiments/v1_v4_redesign/prompts/v4_long_context.yaml",
    "llm_experiments/v1_v4_redesign/protocol.md",
    "llm_experiments/v1_v4_redesign/reports/v1_protocol.md",
    "llm_experiments/v1_v4_redesign/reports/v2_protocol.md",
    "llm_experiments/v1_v4_redesign/reports/v3_protocol.md",
    "llm_experiments/v1_v4_redesign/reports/v4_protocol.md",
    "llm_experiments/v5_v10_redesign/README.md",
    "llm_experiments/v5_v10_redesign/evaluation_framework.md",
    "llm_experiments/v5_v10_redesign/experiment_map.md",
    "llm_experiments/v5_v10_redesign/protocol.md",
    "llm_experiments/v5_v10_redesign/report_template.md",
    "llm_experiments/v5_v10_redesign/reports/v5_protocol.md",
    "llm_experiments/v5_v10_redesign/reports/v6_protocol.md",
    "llm_experiments/v5_v10_redesign/reports/v7_protocol.md",
    "llm_experiments/v5_v10_redesign/reports/v8_protocol.md",
    "llm_experiments/v5_v10_redesign/reports/v9_protocol.md",
    "llm_experiments/v5_v10_redesign/reports/v10_protocol.md",
    "llm_experiments/v5_v10_redesign/risk_register.md",
    "llm_experiments/v10_cross_domain/v10_4_protein/CNBE-32_v10.4_蛋白质二级结构预测验证白皮书.md",
    "results/v10_cross_domain/CNBE-32_v10.4_蛋白质二级结构预测验证白皮书.md",
    "scripts/verify_release_artifacts.py",
    "scripts/audit_full_catalog_xlsx.py",
    "scripts/build_full_catalog_db.py",
    "scripts/query_full_catalog_db.py",
    "scripts/analyze_basic_cjk_scope_gap.py",
    "scripts/audit_mapping_provenance.py",
    "scripts/audit_full_catalog_structure.py",
    "scripts/fetch_unihan_source.py",
    "scripts/reproduce_full_catalog_audit.py",
    "scripts/generate_semantic_review_sample.py",
    "scripts/export_semantic_review_packets.py",
    "scripts/validate_semantic_review_results.py",
    "scripts/audit_cnbe_research_sources.py",
    "scripts/inventory_cnbe_research_knowledge.py",
    "scripts/audit_cnbe_research_evidence_domains.py",
    "scripts/build_hanzi_standard_learning.py",
    "scripts/audit_cnbe8105_encoding_comparison.py",
    "scripts/build_cnbe8105_auto_fix_candidates.py",
    "scripts/build_cnbe8105_radical_code_map.py",
    "scripts/build_cnbe8105_dry_run_patch.py",
    "scripts/score_cnbe8105_gf0017_normativity.py",
    "scripts/run_cnbe20902_agent_preencoding_test.py",
    "scripts/build_cnbe_agent_encoding_standard.py",
    "data/sources/unihan-17.0.0.json",
    "data/sources/cnbe-research-local.json",
    "reports/full_catalog_feasibility.json",
    "reports/full_catalog_build.json",
    "reports/basic_cjk_scope_gap.json",
    "reports/mapping_provenance_audit.json",
    "reports/MAPPING_PROVENANCE_AUDIT.md",
    "reports/full_catalog_structure_audit.json",
    "reports/full_catalog_reproduction_audit.json",
    "reports/full_catalog_semantic_review_sample.json",
    "reports/full_catalog_semantic_review_sample.csv",
    "reports/full_catalog_semantic_review_validation.json",
    "reports/FULL_CATALOG_SEMANTIC_REVIEW_PROTOCOL.md",
    "reports/FULL_CATALOG_REVIEWER_INSTRUCTIONS.md",
    "reports/ENCODING_WORK_PREP_READINESS.md",
    "reports/cnbe_research_source_audit.json",
    "reports/cnbe_research_knowledge_inventory.json",
    "reports/cnbe_research_evidence_domains.json",
    "reports/CNBE_RESEARCH_EVIDENCE_WORKFLOW.md",
    "reports/hanzi_standard_learning_audit.json",
    "reports/HANZI_STANDARD_LEARNING_PLAN.md",
    "reports/HANZI_STANDARD_TERMS.md",
    "reports/HANZI_STRUCTURE_TYPES.md",
    "data/sources/hanzi-standard-learning.json",
    "evidence/README.md",
    "evidence/8105/cnbe8105_standard_baseline.json",
    "evidence/8105/cnbe8105_current_cnbe_snapshot.json",
    "evidence/8105/cnbe8105_encoding_comparison.json",
    "evidence/8105/CNBE8105_ENCODING_COMPARISON_REPORT.md",
    "evidence/8105/cnbe8105_auto_fix_candidates.json",
    "evidence/8105/CNBE8105_AUTO_FIX_CANDIDATES.md",
    "evidence/8105/cnbe8105_radical_code_map.json",
    "evidence/8105/CNBE8105_RADICAL_CODE_MAP.md",
    "evidence/8105/cnbe8105_dry_run_patch.json",
    "evidence/8105/CNBE8105_DRY_RUN_PATCH.md",
    "evidence/gf0017/GF0017_NORMATIVE_SCORING_SOURCE_MAP.md",
    "evidence/gf0017/gf0017_cnbe50_scoring_model.json",
    "evidence/gf0017/GF0017_CNBE50_SCORING_MODEL.md",
    "evidence/gf0017/cnbe8105_gf0017_normativity_scores.json",
    "evidence/gf0017/CNBE8105_GF0017_NORMATIVITY_SCORE_REPORT.md",
    "evidence/agent-standard/cnbe20902_agent_preencoding_test.json",
    "evidence/agent-standard/cnbe20902_agent_preencoding_checkpoint.json",
    "evidence/agent-standard/CNBE20902_AGENT_PREENCODING_TEST.md",
    "evidence/agent-standard/CNBE_8105_RULE_LEARNING_TRANSFER_WORKFLOW.md",
    "evidence/agent-standard/NEXT_THREAD_HANDOFF_CNBE_GF0017.md",
    "evidence/agent-standard/cnbe_agent_encoding_standard.json",
    "evidence/agent-standard/CNBE_AGENT_ENCODING_STANDARD.md",
    "evidence/agent-standard/cnbe_legacy_structure_localization.json",
    "evidence/agent-standard/CNBE_LEGACY_STRUCTURE_LOCALIZATION.md",
    "reports/REPOSITORY_STRUCTURE_AUDIT.md",
    "reports/REPOSITORY_ASSET_INVENTORY.md",
    "docs/REPOSITORY_STRUCTURE.md",
    "docs/CNBE_VERSION_GOVERNANCE.md",
    "reports/BASELINE_VERSION_SPLIT_PLAN.md",
    "reports/DATA_ASSET_MANIFEST.md",
    "reports/data_asset_manifest.json",
    "tests/test_full_catalog_tools.py",
    "tests/test_basic_cjk_scope_gap.py",
    "tests/test_mapping_provenance.py",
    "tests/test_full_catalog_structure.py",
    "tests/test_unihan_source_workflow.py",
    "tests/test_semantic_review_sample.py",
    "tests/test_semantic_review_packets.py",
    "tests/test_semantic_review_validation.py",
    "tests/test_cnbe_research_source_audit.py",
    "tests/test_cnbe_research_knowledge_inventory.py",
    "tests/test_cnbe_research_evidence_domains.py",
    "tests/test_hanzi_standard_learning.py",
    "tests/test_cnbe8105_encoding_comparison.py",
    "tests/test_cnbe8105_auto_fix_candidates.py",
    "tests/test_cnbe8105_radical_code_map.py",
    "tests/test_cnbe8105_dry_run_patch.py",
    "tests/test_cnbe8105_gf0017_normativity.py",
    "tests/test_cnbe20902_agent_preencoding.py",
    "tests/test_cnbe_agent_encoding_standard.py",
    "docs/FULL_CATALOG_DATABASE.md",
    "c/golden_vectors/Makefile",
    "c/golden_vectors/cnbe32_golden_test.c",
    "rust/golden_vectors/Cargo.toml",
    "rust/golden_vectors/src/lib.rs",
    "README.md",
    "README_EN.md",
    "README_ZH.md",
    "CHANGELOG.md",
    "RELEASE.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
]

HISTORICAL_MARKDOWN_ROOTS = [
    "llm_experiments",
    "results",
]

MIN_LINES = {
    ".gitattributes": 10,
    "MANIFEST.in": 10,
    "pyproject.toml": 30,
    ".github/workflows/ci.yml": 35,
    "src/cnbe32/core.py": 80,
    "src/cnbe32/constants.py": 20,
    "src/cnbe32/exceptions.py": 10,
    "src/cnbe32/db.py": 80,
    "src/cnbe32/encoders.py": 60,
    "src/cnbe32/skill_table.py": 40,
    "src/cnbe32/__init__.py": 15,
    "tests/test_cnbe32.py": 80,
    "tests/test_golden_vectors.py": 60,
    "tests/test_install_smoke.py": 2,
    "tests/test_package_metadata.py": 2,
    "spec/golden_vectors.json": 150,
    "spec/GOLDEN_VECTORS.md": 40,
    "spec/IMPLEMENTATION_CONSISTENCY.md": 30,
    f"docs/releases/v{version}.md": 50,
    "docs/releases/v1.0.2.md": 50,
    "llm_experiments/v1_v4_redesign/README.md": 100,
    "llm_experiments/v1_v4_redesign/datasets/annotation_schema.json": 70,
    "llm_experiments/v1_v4_redesign/datasets/sampling_plan.md": 170,
    "llm_experiments/v1_v4_redesign/evaluation/judge_prompt.md": 100,
    "llm_experiments/v1_v4_redesign/evaluation/metrics.md": 190,
    "llm_experiments/v1_v4_redesign/evaluation/rubric.md": 160,
    "llm_experiments/v1_v4_redesign/prompts/v1_single_char.yaml": 90,
    "llm_experiments/v1_v4_redesign/prompts/v2_sentence.yaml": 80,
    "llm_experiments/v1_v4_redesign/prompts/v3_format_ablation.yaml": 90,
    "llm_experiments/v1_v4_redesign/prompts/v4_long_context.yaml": 90,
    "llm_experiments/v1_v4_redesign/protocol.md": 180,
    "llm_experiments/v1_v4_redesign/reports/v1_protocol.md": 140,
    "llm_experiments/v1_v4_redesign/reports/v2_protocol.md": 130,
    "llm_experiments/v1_v4_redesign/reports/v3_protocol.md": 130,
    "llm_experiments/v1_v4_redesign/reports/v4_protocol.md": 140,
    "llm_experiments/v5_v10_redesign/README.md": 90,
    "llm_experiments/v5_v10_redesign/evaluation_framework.md": 160,
    "llm_experiments/v5_v10_redesign/experiment_map.md": 160,
    "llm_experiments/v5_v10_redesign/protocol.md": 160,
    "llm_experiments/v5_v10_redesign/report_template.md": 130,
    "llm_experiments/v5_v10_redesign/reports/v5_protocol.md": 110,
    "llm_experiments/v5_v10_redesign/reports/v6_protocol.md": 110,
    "llm_experiments/v5_v10_redesign/reports/v7_protocol.md": 100,
    "llm_experiments/v5_v10_redesign/reports/v8_protocol.md": 100,
    "llm_experiments/v5_v10_redesign/reports/v9_protocol.md": 100,
    "llm_experiments/v5_v10_redesign/reports/v10_protocol.md": 130,
    "llm_experiments/v5_v10_redesign/risk_register.md": 170,
    "llm_experiments/v10_cross_domain/v10_4_protein/CNBE-32_v10.4_蛋白质二级结构预测验证白皮书.md": 130,
    "results/v10_cross_domain/CNBE-32_v10.4_蛋白质二级结构预测验证白皮书.md": 130,
    "scripts/verify_release_artifacts.py": 60,
    "scripts/audit_full_catalog_xlsx.py": 150,
    "scripts/build_full_catalog_db.py": 150,
    "scripts/query_full_catalog_db.py": 120,
    "scripts/analyze_basic_cjk_scope_gap.py": 180,
    "scripts/audit_mapping_provenance.py": 250,
    "scripts/audit_full_catalog_structure.py": 180,
    "scripts/fetch_unihan_source.py": 100,
    "scripts/reproduce_full_catalog_audit.py": 170,
    "scripts/generate_semantic_review_sample.py": 280,
    "scripts/export_semantic_review_packets.py": 120,
    "scripts/validate_semantic_review_results.py": 190,
    "scripts/audit_cnbe_research_sources.py": 300,
    "scripts/inventory_cnbe_research_knowledge.py": 300,
    "scripts/audit_cnbe_research_evidence_domains.py": 320,
    "scripts/build_hanzi_standard_learning.py": 450,
    "scripts/audit_cnbe8105_encoding_comparison.py": 600,
    "scripts/build_cnbe8105_auto_fix_candidates.py": 300,
    "scripts/build_cnbe8105_radical_code_map.py": 300,
    "scripts/build_cnbe8105_dry_run_patch.py": 300,
    "scripts/score_cnbe8105_gf0017_normativity.py": 350,
    "scripts/run_cnbe20902_agent_preencoding_test.py": 450,
    "scripts/build_cnbe_agent_encoding_standard.py": 400,
    "data/sources/unihan-17.0.0.json": 45,
    "data/sources/cnbe-research-local.json": 200,
    "reports/full_catalog_feasibility.json": 100,
    "reports/full_catalog_build.json": 60,
    "reports/basic_cjk_scope_gap.json": 500,
    "reports/mapping_provenance_audit.json": 100,
    "reports/MAPPING_PROVENANCE_AUDIT.md": 80,
    "reports/full_catalog_structure_audit.json": 40,
    "reports/full_catalog_reproduction_audit.json": 250,
    "reports/full_catalog_semantic_review_sample.json": 500,
    "reports/full_catalog_semantic_review_sample.csv": 500,
    "reports/full_catalog_semantic_review_validation.json": 50,
    "reports/FULL_CATALOG_SEMANTIC_REVIEW_PROTOCOL.md": 65,
    "reports/FULL_CATALOG_REVIEWER_INSTRUCTIONS.md": 65,
    "reports/ENCODING_WORK_PREP_READINESS.md": 180,
    "reports/cnbe_research_source_audit.json": 500,
    "reports/cnbe_research_knowledge_inventory.json": 500,
    "reports/cnbe_research_evidence_domains.json": 500,
    "reports/CNBE_RESEARCH_EVIDENCE_WORKFLOW.md": 180,
    "reports/hanzi_standard_learning_audit.json": 500,
    "reports/HANZI_STANDARD_LEARNING_PLAN.md": 40,
    "reports/HANZI_STANDARD_TERMS.md": 130,
    "reports/HANZI_STRUCTURE_TYPES.md": 35,
    "data/sources/hanzi-standard-learning.json": 200,
    "evidence/README.md": 80,
    "evidence/8105/cnbe8105_standard_baseline.json": 1000,
    "evidence/8105/cnbe8105_current_cnbe_snapshot.json": 1000,
    "evidence/8105/cnbe8105_encoding_comparison.json": 1000,
    "evidence/8105/CNBE8105_ENCODING_COMPARISON_REPORT.md": 60,
    "evidence/8105/cnbe8105_auto_fix_candidates.json": 1000,
    "evidence/8105/CNBE8105_AUTO_FIX_CANDIDATES.md": 60,
    "evidence/8105/cnbe8105_radical_code_map.json": 1000,
    "evidence/8105/CNBE8105_RADICAL_CODE_MAP.md": 60,
    "evidence/8105/cnbe8105_dry_run_patch.json": 1000,
    "evidence/8105/CNBE8105_DRY_RUN_PATCH.md": 60,
    "evidence/gf0017/GF0017_NORMATIVE_SCORING_SOURCE_MAP.md": 120,
    "evidence/gf0017/gf0017_cnbe50_scoring_model.json": 300,
    "evidence/gf0017/GF0017_CNBE50_SCORING_MODEL.md": 220,
    "evidence/gf0017/cnbe8105_gf0017_normativity_scores.json": 1000,
    "evidence/gf0017/CNBE8105_GF0017_NORMATIVITY_SCORE_REPORT.md": 60,
    "evidence/agent-standard/cnbe20902_agent_preencoding_test.json": 1000,
    "evidence/agent-standard/cnbe20902_agent_preencoding_checkpoint.json": 8,
    "evidence/agent-standard/CNBE20902_AGENT_PREENCODING_TEST.md": 80,
    "evidence/agent-standard/CNBE_8105_RULE_LEARNING_TRANSFER_WORKFLOW.md": 100,
    "evidence/agent-standard/NEXT_THREAD_HANDOFF_CNBE_GF0017.md": 200,
    "evidence/agent-standard/cnbe_agent_encoding_standard.json": 100,
    "evidence/agent-standard/CNBE_AGENT_ENCODING_STANDARD.md": 45,
    "evidence/agent-standard/cnbe_legacy_structure_localization.json": 150,
    "evidence/agent-standard/CNBE_LEGACY_STRUCTURE_LOCALIZATION.md": 45,
    "reports/REPOSITORY_STRUCTURE_AUDIT.md": 80,
    "reports/REPOSITORY_ASSET_INVENTORY.md": 90,
    "docs/REPOSITORY_STRUCTURE.md": 90,
    "docs/CNBE_VERSION_GOVERNANCE.md": 100,
    "reports/BASELINE_VERSION_SPLIT_PLAN.md": 100,
    "reports/DATA_ASSET_MANIFEST.md": 140,
    "reports/data_asset_manifest.json": 180,
    "tests/test_full_catalog_tools.py": 120,
    "tests/test_basic_cjk_scope_gap.py": 80,
    "tests/test_mapping_provenance.py": 30,
    "tests/test_full_catalog_structure.py": 50,
    "tests/test_unihan_source_workflow.py": 45,
    "tests/test_semantic_review_sample.py": 50,
    "tests/test_semantic_review_packets.py": 65,
    "tests/test_semantic_review_validation.py": 100,
    "tests/test_cnbe_research_source_audit.py": 60,
    "tests/test_cnbe_research_knowledge_inventory.py": 80,
    "tests/test_cnbe_research_evidence_domains.py": 50,
    "tests/test_hanzi_standard_learning.py": 80,
    "tests/test_cnbe8105_encoding_comparison.py": 40,
    "tests/test_cnbe8105_auto_fix_candidates.py": 40,
    "tests/test_cnbe8105_radical_code_map.py": 50,
    "tests/test_cnbe8105_dry_run_patch.py": 50,
    "tests/test_cnbe8105_gf0017_normativity.py": 45,
    "tests/test_cnbe20902_agent_preencoding.py": 50,
    "tests/test_cnbe_agent_encoding_standard.py": 55,
    "docs/FULL_CATALOG_DATABASE.md": 140,
    "c/golden_vectors/Makefile": 15,
    "c/golden_vectors/cnbe32_golden_test.c": 120,
    "rust/golden_vectors/Cargo.toml": 8,
    "rust/golden_vectors/src/lib.rs": 100,
    "README.md": 120,
    "README_EN.md": 120,
    "README_ZH.md": 120,
    "CHANGELOG.md": 40,
    "RELEASE.md": 40,
    "CONTRIBUTING.md": 40,
    "SECURITY.md": 15,
}

README_REQUIRED = {
    "README.md": [
        "Coverage terminology",
        "Evidence level",
        "20,902",
        "97,686",
    ],
    "README_EN.md": [
        "Coverage terminology",
        "Evidence level",
        "20,902",
        "97,686",
    ],
    "README_ZH.md": [
        "覆盖范围术语",
        "证据等级",
        "20,902",
        "97,686",
    ],
}

CI_REQUIRED = [
    "python -m compileall src tests",
    "python -m build",
    "python scripts/validate_format_integrity.py",
    "python scripts/verify_release_artifacts.py",
    "python -m pip install --force-reinstall dist/*.whl",
    "pytest",
    "ruff check src tests",
    "make -C c/golden_vectors test",
    "cargo test --manifest-path rust/golden_vectors/Cargo.toml",
]

C_REQUIRED = [
    "#include <stdint.h>",
    "#include <stdio.h>",
    "#include <stdlib.h>",
    "typedef struct",
    "encode_cnbe32",
    "decode_radix",
    "C golden vector consistency PASS",
]

FORBIDDEN_CLAIMS = [
    "full coverage verified",
    "0% collision",
    "validated on 90,000",
    "Proves",
    "Prove encoding",
    "production-ready",
    "CJK全量覆盖验证",
    "CNBE-32 是一个跨领域通用编码范式",
    "具有**跨领域零样本泛化能力**",
    "零碰撞全覆盖",
    "证明编码",
    "生产可用",
    "实验证明",
    "100% 有效",
    "100% 有效率",
    "CNBE 可被零样本理解",
    "六格式全部 100% 有效",
]


def fail(message: str) -> None:
    print(f"FORMAT INTEGRITY FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def read_utf8_lf(path: Path) -> str:
    raw = path.read_bytes()

    if raw.startswith(b"\xef\xbb\xbf"):
        fail(f"{path}: UTF-8 BOM is not allowed")

    if b"\r\n" in raw or b"\r" in raw:
        fail(f"{path}: CRLF or CR line endings are not allowed")

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        fail(f"{path}: not valid UTF-8: {exc}")

    for offset, char in enumerate(text):
        if char in {"\n", "\t"}:
            continue
        if unicodedata.category(char) in {"Cf", "Cc"}:
            name = unicodedata.name(char, "UNKNOWN")
            fail(f"{path}: hidden/control char U+{ord(char):04X} at byte-ish offset {offset}: {name}")

    return text


def require_line_count(path: str, text: str) -> None:
    actual = len(text.splitlines())
    minimum = MIN_LINES.get(path, 2)

    if actual < minimum:
        fail(f"{path}: {actual} lines, need {minimum}+")


def require_no_forbidden_claims(path: str, text: str) -> None:
    lowered = text.lower()

    for claim in FORBIDDEN_CLAIMS:
        if claim.lower() in lowered:
            fail(f"{path}: forbidden claim: {claim}")


def require_syntax(path: str, text: str) -> None:
    suffix = Path(path).suffix

    if suffix == ".py":
        try:
            ast.parse(text, filename=path)
        except SyntaxError as exc:
            fail(f"{path}: Python syntax error: {exc}")

    if path in {"pyproject.toml", "rust/golden_vectors/Cargo.toml"}:
        try:
            tomllib.loads(text)
        except tomllib.TOMLDecodeError as exc:
            fail(f"{path}: TOML syntax error: {exc}")

    if suffix == ".json":
        try:
            json.loads(text)
        except json.JSONDecodeError as exc:
            fail(f"{path}: JSON syntax error: {exc}")


def require_terms(path: str, text: str, terms: list[str]) -> None:
    for term in terms:
        if term not in text:
            fail(f"{path}: missing required term: {term}")


def require_ci_terms(path: str, text: str) -> None:
    if path == ".github/workflows/ci.yml":
        require_terms(path, text, CI_REQUIRED)


def require_c_terms(path: str, text: str) -> None:
    if path == "c/golden_vectors/cnbe32_golden_test.c":
        require_terms(path, text, C_REQUIRED)


def require_makefile_recipe(path: str, text: str) -> None:
    if path != "c/golden_vectors/Makefile":
        return

    if "$(CC) $(CFLAGS)" not in text:
        fail(f"{path}: missing compiler recipe")

    if "\n\t$(CC) $(CFLAGS)" not in text:
        fail(f"{path}: compiler recipe must use a real tab")


def require_readme_terms(path: str, text: str) -> None:
    require_terms(path, text, README_REQUIRED.get(path, []))


def require_no_tracked_binary() -> None:
    result = subprocess.run(
        ["git", "ls-files", "c/golden_vectors/cnbe32_golden_test"],
        capture_output=True,
        check=False,
        text=True,
    )

    if result.stdout.strip():
        fail("tracked binary artifact: c/golden_vectors/cnbe32_golden_test")


def validate_file(path: str) -> None:
    file_path = Path(path)

    if not file_path.exists():
        fail(f"missing required file: {path}")

    text = read_utf8_lf(file_path)
    require_line_count(path, text)
    require_no_forbidden_claims(path, text)
    require_syntax(path, text)
    require_ci_terms(path, text)
    require_c_terms(path, text)
    require_makefile_recipe(path, text)
    require_readme_terms(path, text)


def iter_text_files() -> list[str]:
    paths = list(TEXT_FILES)
    seen = set(paths)

    for root in HISTORICAL_MARKDOWN_ROOTS:
        for markdown_path in sorted(Path(root).rglob("*.md")):
            path = markdown_path.as_posix()
            if path not in seen:
                paths.append(path)
                seen.add(path)

    return paths


def main() -> int:
    for path in iter_text_files():
        validate_file(path)

    require_no_tracked_binary()
    print("FORMAT INTEGRITY PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
