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


def main() -> int:
    for path in TEXT_FILES:
        validate_file(path)

    require_no_tracked_binary()
    print("FORMAT INTEGRITY PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

