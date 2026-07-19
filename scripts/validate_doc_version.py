#!/usr/bin/env python3
"""Validate that public documentation follows the package version.

The project uses ``pyproject.toml`` as the single release-version source of
truth.  This script checks the public documentation surface before the package
build step so stale README or release-note links fail cheaply in CI.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 compatibility
    import tomli as tomllib


REPO_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = REPO_ROOT / "pyproject.toml"
CHANGELOG = REPO_ROOT / "CHANGELOG.md"
README_PATHS = (
    REPO_ROOT / "README.md",
    REPO_ROOT / "README_ZH.md",
)

SEMVER_RE = re.compile(r"(?<![\w.])v?(\d+\.\d+\.\d+)(?![\w.])")
RELEASE_LINK_RE = re.compile(r"docs/releases/v(\d+\.\d+\.\d+)\.md")
IGNORE_MARKER = "<!-- doc-version-ignore -->"


@dataclass(frozen=True)
class Finding:
    """One documentation version mismatch."""

    path: Path
    line_number: int | None
    message: str

    def format(self) -> str:
        relative = self.path.relative_to(REPO_ROOT)
        if self.line_number is None:
            return f"{relative}: {self.message}"
        return f"{relative}:{self.line_number}: {self.message}"


def read_version() -> str:
    """Read the current package version from pyproject.toml."""
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    version = data.get("project", {}).get("version")
    if not isinstance(version, str) or not version:
        raise ValueError("pyproject.toml must define project.version")
    return version


def iter_checked_lines(path: Path) -> list[tuple[int, str]]:
    """Return lines that are not explicitly exempted from version checking."""
    checked: list[tuple[int, str]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if IGNORE_MARKER in line:
            continue
        checked.append((line_number, line))
    return checked


def collect_semver_versions(path: Path) -> dict[str, list[int]]:
    """Collect semver-like versions from a documentation file."""
    versions: dict[str, list[int]] = {}
    for line_number, line in iter_checked_lines(path):
        for match in SEMVER_RE.finditer(line):
            version = match.group(1)
            versions.setdefault(version, []).append(line_number)
    return versions


def collect_release_links(path: Path) -> dict[str, list[int]]:
    """Collect docs/releases/vX.Y.Z.md links from a documentation file."""
    versions: dict[str, list[int]] = {}
    for line_number, line in iter_checked_lines(path):
        for match in RELEASE_LINK_RE.finditer(line):
            version = match.group(1)
            versions.setdefault(version, []).append(line_number)
    return versions


def validate_changelog(version: str) -> list[Finding]:
    """Ensure CHANGELOG contains the current release section."""
    if not CHANGELOG.exists():
        return [Finding(CHANGELOG, None, "missing CHANGELOG.md")]

    expected_heading = f"## [{version}]"
    text = CHANGELOG.read_text(encoding="utf-8")
    if expected_heading not in text:
        return [Finding(CHANGELOG, None, f"missing current section {expected_heading}")]
    return []


def validate_release_note(version: str) -> list[Finding]:
    """Ensure docs/releases/v<version>.md exists."""
    release_note = REPO_ROOT / "docs" / "releases" / f"v{version}.md"
    if release_note.exists():
        return []
    return [Finding(release_note, None, "missing current release note")]


def validate_readme_versions(path: Path, version: str) -> list[Finding]:
    """Validate semver mentions and release links in one README."""
    findings: list[Finding] = []
    versions = collect_semver_versions(path)

    if version not in versions:
        findings.append(
            Finding(
                path,
                None,
                f"no current-version marker found; expected cnbe32=={version} or v{version}",
            )
        )

    for found_version, line_numbers in sorted(versions.items()):
        if found_version == version:
            continue
        for line_number in line_numbers:
            findings.append(
                Finding(
                    path,
                    line_number,
                    f"stale version {found_version!r}, expected {version!r}",
                )
            )

    release_links = collect_release_links(path)
    for link_version, line_numbers in sorted(release_links.items()):
        for line_number in line_numbers:
            release_path = REPO_ROOT / "docs" / "releases" / f"v{link_version}.md"
            if link_version != version:
                findings.append(
                    Finding(
                        path,
                        line_number,
                        f"stale release link docs/releases/v{link_version}.md, expected v{version}.md",
                    )
                )
            if not release_path.exists():
                findings.append(
                    Finding(
                        path,
                        line_number,
                        f"release link target does not exist: docs/releases/v{link_version}.md",
                    )
                )

    return findings


def validate_readme_agreement(version: str) -> list[Finding]:
    """Ensure README variants mention the same version set."""
    findings: list[Finding] = []
    version_sets = {
        path.name: set(collect_semver_versions(path))
        for path in README_PATHS
    }
    expected = {version}
    for name, versions in sorted(version_sets.items()):
        if versions != expected:
            findings.append(
                Finding(
                    REPO_ROOT / name,
                    None,
                    f"README variant versions disagree: {sorted(versions)} != {sorted(expected)}",
                )
            )
    return findings


def validate_all() -> list[Finding]:
    """Run every documentation version check."""
    version = read_version()
    findings: list[Finding] = []
    findings.extend(validate_changelog(version))
    findings.extend(validate_release_note(version))
    for readme_path in README_PATHS:
        findings.extend(validate_readme_versions(readme_path, version))
    findings.extend(validate_readme_agreement(version))
    return findings


def main() -> int:
    """CLI entry point."""
    findings = validate_all()
    if findings:
        print(f"DOC VERSION CHECK FAIL: {len(findings)} version inconsistency issue(s)", file=sys.stderr)
        for finding in findings:
            print(f"  - {finding.format()}", file=sys.stderr)
        return 1

    print("DOC VERSION CHECK PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
