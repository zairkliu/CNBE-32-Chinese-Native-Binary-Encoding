from pathlib import Path

import scripts.validate_doc_version as doc_version

ROOT = Path(__file__).resolve().parents[1]


def test_pyproject_version_is_the_single_truth() -> None:
    version = doc_version.read_version()

    assert version == "1.0.4"
    assert (ROOT / "docs" / "releases" / f"v{version}.md").exists()


def test_doc_version_validator_accepts_current_repository() -> None:
    findings = doc_version.validate_all()

    assert findings == []


def test_readme_variants_use_the_same_current_version_set() -> None:
    version = doc_version.read_version()
    expected = {version}

    for relative_path in ("README.md", "README_EN.md", "README_ZH.md"):
        versions = set(doc_version.collect_semver_versions(ROOT / relative_path))
        assert versions == expected


def test_release_links_point_to_current_existing_release_note() -> None:
    version = doc_version.read_version()

    for relative_path in ("README.md", "README_EN.md", "README_ZH.md"):
        links = doc_version.collect_release_links(ROOT / relative_path)
        assert set(links) <= {version}
        for link_version in links:
            assert (ROOT / "docs" / "releases" / f"v{link_version}.md").exists()


def test_ignore_marker_allows_intentional_historical_mentions(tmp_path, monkeypatch) -> None:
    sample = tmp_path / "README.md"
    sample.write_text(
        "current v1.0.4\n"
        "historical v1.0.3 <!-- doc-version-ignore -->\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(doc_version, "README_PATHS", (sample,))

    assert doc_version.collect_semver_versions(sample) == {"1.0.4": [1]}
