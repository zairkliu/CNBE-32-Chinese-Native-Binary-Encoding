from __future__ import annotations

import tarfile
import zipfile
from pathlib import Path

REQUIRED_WHEEL_SUFFIXES = [
    "cnbe32/__init__.py",
    "cnbe32/core.py",
    "cnbe32/constants.py",
    "cnbe32/db.py",
    "cnbe32/exceptions.py",
    "cnbe32/skill_table.py",
]

REQUIRED_SDIST_SUFFIXES = [
    "pyproject.toml",
    "README.md",
    "CHANGELOG.md",
    "RELEASE.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "spec/golden_vectors.json",
    "spec/GOLDEN_VECTORS.md",
    "spec/IMPLEMENTATION_CONSISTENCY.md",
    "docs/releases/v1.0.2.md",
    "scripts/validate_format_integrity.py",
    "scripts/verify_release_artifacts.py",
]


def fail(message: str) -> None:
    raise SystemExit(f"RELEASE ARTIFACT CHECK FAILED: {message}")


def latest_file(pattern: str) -> Path:
    files = sorted(Path("dist").glob(pattern))
    if not files:
        fail(f"no artifact found for pattern: {pattern}")
    return files[-1]


def check_wheel() -> None:
    wheel = latest_file("*.whl")
    print(f"Checking wheel: {wheel}")

    with zipfile.ZipFile(wheel) as zf:
        names = set(zf.namelist())

    for suffix in REQUIRED_WHEEL_SUFFIXES:
        if not any(name.endswith(suffix) for name in names):
            fail(f"wheel missing required file ending with: {suffix}")

    db_files = sorted(name for name in names if name.endswith("cnbe32.db"))
    if db_files:
        print("Wheel database files:")
        for name in db_files:
            print(f"- {name}")
    else:
        print("WARNING: wheel does not contain cnbe32.db; external CNBE32_DB_PATH may be required.")

    print("Wheel check PASS")


def check_sdist() -> None:
    sdist = latest_file("*.tar.gz")
    print(f"Checking sdist: {sdist}")

    with tarfile.open(sdist, "r:gz") as tf:
        names = set(tf.getnames())

    for suffix in REQUIRED_SDIST_SUFFIXES:
        if not any(name.endswith(suffix) for name in names):
            fail(f"sdist missing required file ending with: {suffix}")

    print("sdist check PASS")


def main() -> None:
    check_wheel()
    check_sdist()
    print("RELEASE ARTIFACT CHECK PASS")


if __name__ == "__main__":
    main()
