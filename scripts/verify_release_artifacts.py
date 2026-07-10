from __future__ import annotations

import tarfile
import zipfile
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 compatibility
    import tomli as tomllib

PROJECT_NAME = "cnbe32"

REQUIRED_WHEEL_SUFFIXES = [
    "cnbe32/__init__.py",
    "cnbe32/core.py",
    "cnbe32/constants.py",
    "cnbe32/db.py",
    "cnbe32/encoders.py",
    "cnbe32/exceptions.py",
    "cnbe32/skill_table.py",
    "cnbe32/data/cnbe32.db",
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
    "docs/releases/v1.0.3.md",
    "docs/releases/v1.0.2.md",
    "src/cnbe32/encoders.py",
    "src/cnbe32/data/cnbe32.db",
    "scripts/validate_format_integrity.py",
    "scripts/verify_release_artifacts.py",
]


def fail(message: str) -> None:
    raise SystemExit(f"RELEASE ARTIFACT CHECK FAILED: {message}")


def project_version() -> str:
    data = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    version = data.get("project", {}).get("version")
    if not isinstance(version, str):
        fail("pyproject.toml missing project.version")
    return version


def exact_artifact(pattern: str, expected_name: str) -> Path:
    files = sorted(Path("dist").glob(pattern))
    if not files:
        fail(f"no artifact found for pattern: {pattern}")
    if len(files) != 1:
        fail(f"expected exactly one artifact for {pattern}; got: {', '.join(str(file) for file in files)}")
    artifact = files[0]
    if artifact.name != expected_name:
        fail(f"unexpected artifact name: {artifact.name}; expected: {expected_name}")
    return artifact


def check_wheel(version: str) -> None:
    expected_name = f"{PROJECT_NAME}-{version}-py3-none-any.whl"
    wheel = exact_artifact("*.whl", expected_name)
    print(f"Checking wheel: {wheel}")

    with zipfile.ZipFile(wheel) as zf:
        names = set(zf.namelist())

    for suffix in REQUIRED_WHEEL_SUFFIXES:
        if not any(name.endswith(suffix) for name in names):
            fail(f"wheel missing required file ending with: {suffix}")

    db_files = sorted(name for name in names if name.endswith("cnbe32.db"))
    print("Wheel database files:")
    for name in db_files:
        print(f"- {name}")

    print("Wheel check PASS")


def check_sdist(version: str) -> None:
    expected_name = f"{PROJECT_NAME}-{version}.tar.gz"
    sdist = exact_artifact("*.tar.gz", expected_name)
    print(f"Checking sdist: {sdist}")

    with tarfile.open(sdist, "r:gz") as tf:
        names = set(tf.getnames())

    for suffix in REQUIRED_SDIST_SUFFIXES:
        if not any(name.endswith(suffix) for name in names):
            fail(f"sdist missing required file ending with: {suffix}")

    print("sdist check PASS")


def main() -> None:
    version = project_version()
    check_wheel(version)
    check_sdist(version)
    print("RELEASE ARTIFACT CHECK PASS")


if __name__ == "__main__":
    main()
