from __future__ import annotations

import ast
import json
import subprocess
import sys
import tomllib
import unicodedata
from pathlib import Path

"""

# Usage:
#   python scripts/validate_format_integrity.py
#   CI runs this on every push and pull request.
#
# This validator checks:
#   - File encoding (UTF-8, no BOM)
#   - Line endings (LF only)
#   - Hidden/control Unicode characters
#   - Minimum line counts per file type
#   - Python syntax (AST parse)
#   - TOML syntax (tomllib.parse)
#   - JSON syntax
#   - Required content fragments (CI steps, C includes, README sections)
#   - Forbidden claims (coverage, collision, proof-style wording)
#   - Tracked binary artifacts
CNBE-32 Format Integrity Validator

This script validates that all key files in the repository meet minimum
format requirements: UTF-8 encoding, LF line endings, no BOM, no hidden
control characters, valid syntax (Python AST / TOML / JSON), minimum
line counts, required content fragments, and no forbidden claims.

Run: python scripts/validate_format_integrity.py
CI:   integrated into .github/workflows/ci.yml
"""

# Usage:
#   python scripts/validate_format_integrity.py
#   CI runs this on every push and pull request.
#
# This validator checks:
#   - File encoding (UTF-8, no BOM)
#   - Line endings (LF only)
#   - Hidden/control Unicode characters
#   - Minimum line counts per file type
#   - Python syntax (AST parse)
#   - TOML syntax (tomllib.parse)
#   - JSON syntax
#   - Required content fragments (CI steps, C includes, README sections)
#   - Forbidden claims (coverage, collision, proof-style wording)
#   - Tracked binary artifacts

TEXT_FILES = [
    "pyproject.toml", ".github/workflows/ci.yml",
    "src/cnbe32/core.py", "src/cnbe32/constants.py", "src/cnbe32/exceptions.py",
    "src/cnbe32/db.py", "src/cnbe32/skill_table.py", "src/cnbe32/__init__.py",
    "tests/test_cnbe32.py", "tests/test_golden_vectors.py",
    "tests/test_install_smoke.py", "tests/test_package_metadata.py",
    "spec/golden_vectors.json", "spec/GOLDEN_VECTORS.md", "spec/IMPLEMENTATION_CONSISTENCY.md",
    "c/golden_vectors/Makefile", "c/golden_vectors/cnbe32_golden_test.c",
    "rust/golden_vectors/Cargo.toml", "rust/golden_vectors/src/lib.rs",
    "README.md", "README_EN.md", "README_ZH.md",
    "CHANGELOG.md", "RELEASE.md", "CONTRIBUTING.md", "SECURITY.md",
]

def fail(msg: str) -> None:
    """Report a format integrity failure and exit."""

# Usage:
#   python scripts/validate_format_integrity.py
#   CI runs this on every push and pull request.
#
# This validator checks:
#   - File encoding (UTF-8, no BOM)
#   - Line endings (LF only)
#   - Hidden/control Unicode characters
#   - Minimum line counts per file type
#   - Python syntax (AST parse)
#   - TOML syntax (tomllib.parse)
#   - JSON syntax
#   - Required content fragments (CI steps, C includes, README sections)
#   - Forbidden claims (coverage, collision, proof-style wording)
#   - Tracked binary artifacts
    print(f"FORMAT INTEGRITY FAIL: {msg}", file=sys.stderr)
    raise SystemExit(1)

def read_text(path):
    raw = path.read_bytes()
    if raw.startswith(b'\xef\xbb\xbf'): fail(f"{path}: BOM")
    if b'\r\n' in raw: fail(f"{path}: CRLF")
    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError as e:
        fail(f"{path}: not UTF-8: {e}")
    for i, ch in enumerate(text):
        if ch in {'\n', '\t'}: continue
        if unicodedata.category(ch) in {'Cf', 'Cc'}:
            fail(f"{path}: hidden char U+{ord(ch):04X} at pos {i}: {unicodedata.name(ch,'')}")
    return text

MIN_LINES = {
    "pyproject.toml": 30, ".github/workflows/ci.yml": 35,
    "src/cnbe32/core.py": 80, "src/cnbe32/constants.py": 20, "src/cnbe32/exceptions.py": 10,
    "src/cnbe32/db.py": 80, "src/cnbe32/skill_table.py": 40, "src/cnbe32/__init__.py": 15,
    "tests/test_cnbe32.py": 80, "tests/test_golden_vectors.py": 60,
    "spec/golden_vectors.json": 150, "spec/GOLDEN_VECTORS.md": 40, "spec/IMPLEMENTATION_CONSISTENCY.md": 30,
    "c/golden_vectors/Makefile": 15, "c/golden_vectors/cnbe32_golden_test.c": 120,
    "rust/golden_vectors/Cargo.toml": 8, "rust/golden_vectors/src/lib.rs": 100,
    "README.md": 120, "README_EN.md": 120, "README_ZH.md": 120,
    "CHANGELOG.md": 40, "RELEASE.md": 40, "CONTRIBUTING.md": 40, "SECURITY.md": 15,
}

README_REQUIRED = {
    "README.md": ["Coverage terminology", "Evidence level", "20,902", "97,686"],
    "README_EN.md": ["Coverage terminology", "Evidence level", "20,902", "97,686"],
    "README_ZH.md": ["覆盖范围术语", "证据等级", "20,902", "97,686"],
}

FORBIDDEN = ["full coverage verified", "0% collision", "validated on 90,000", "Proves",
             "Prove encoding", "production-ready", "CJK全量覆盖验证", "零碰撞全覆盖", "证明编码", "生产可用"]

def main() -> int:
    """Validate format integrity of all key files. Returns 0 on success."""

# Usage:
#   python scripts/validate_format_integrity.py
#   CI runs this on every push and pull request.
#
# This validator checks:
#   - File encoding (UTF-8, no BOM)
#   - Line endings (LF only)
#   - Hidden/control Unicode characters
#   - Minimum line counts per file type
#   - Python syntax (AST parse)
#   - TOML syntax (tomllib.parse)
#   - JSON syntax
#   - Required content fragments (CI steps, C includes, README sections)
#   - Forbidden claims (coverage, collision, proof-style wording)
#   - Tracked binary artifacts
    for fn in TEXT_FILES:
        p = Path(fn)
        if not p.exists(): fail(f"missing: {fn}")
        t = read_text(p)
        lines = len(t.splitlines())
        req = MIN_LINES.get(fn, 2)
        if lines < req: fail(f"{fn}: {lines} lines, need {req}+")

        # Check claims
        lower = t.lower()
        for c in FORBIDDEN:
            if c.lower() in lower: fail(f"{fn}: forbidden claim: {c}")

        # Python syntax
        if p.suffix == '.py':
            try: ast.parse(t, filename=fn)
            except SyntaxError as e: fail(f"{fn}: syntax: {e}")

        # TOML
        if fn in ('pyproject.toml', 'rust/golden_vectors/Cargo.toml'):
            try: tomllib.loads(t)
            except Exception as e: fail(f"{fn}: TOML: {e}")

        # JSON
        if p.suffix == '.json':
            try: json.loads(t)
            except Exception as e: fail(f"{fn}: JSON: {e}")

        # CI
        if fn == '.github/workflows/ci.yml':
            for term in ["python -m compileall src tests", "python -m build", "pytest",
                         "ruff check src tests", "make -C c/golden_vectors test",
                         "cargo test --manifest-path rust/golden_vectors/Cargo.toml"]:
                if term not in t: fail(f"{fn}: missing CI term: {term}")

        # C
        if fn == 'c/golden_vectors/cnbe32_golden_test.c':
            for term in ["#include <stdint.h>", "#include <stdio.h>", "#include <stdlib.h>",
                         "typedef struct", "encode_cnbe32", "decode_radix", "C golden vector consistency PASS"]:
                if term not in t: fail(f"{fn}: missing C term: {term}")

        # Makefile
        if fn == 'c/golden_vectors/Makefile':
            if "$(CC) $(CFLAGS)" not in t: fail(f"{fn}: missing compiler recipe")
            if "\n\t$(CC) $(CFLAGS)" not in t: fail(f"{fn}: tab recipe required")

        # README required
        for term in README_REQUIRED.get(fn, []):
            if term not in t: fail(f"{fn}: missing required: {term}")

    # No tracked binary
    r = subprocess.run(["git", "ls-files", "c/golden_vectors/cnbe32_golden_test"], capture_output=True, text=True)
    if r.stdout.strip():
        fail("Tracked binary: c/golden_vectors/cnbe32_golden_test")

    print("FORMAT INTEGRITY PASS")
    return 0

if __name__ == "__main__":
    sys.exit(main())
