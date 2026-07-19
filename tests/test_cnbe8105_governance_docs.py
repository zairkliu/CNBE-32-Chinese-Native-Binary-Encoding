from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_readmes_declare_8105_core_and_runtime_boundary() -> None:
    for relative_path in ("README.md", "README_EN.md", "README_ZH.md"):
        text = read_text(relative_path)
        lower_text = text.lower()
        assert "8105" in text
        assert "national-standard core" in text or "国家标准核心" in text
        assert "7829" in text
        assert "276" in text
        assert "97,686" in text
        assert "runtime promotion" in lower_text or "运行时提升" in text
        assert "release" in text or "发布" in text


def test_governance_doc_records_runtime_promotion_boundary() -> None:
    text = read_text("docs/CNBE8105_ENCODING_GOVERNANCE.md")
    assert "8105 common standardized Chinese character table" in text
    assert "national-standard core" in text
    assert "standards-aligned, Agent-operated, human-reviewable" in text
    assert "Agent-standard rows as national-standard rows" in text
    assert "src/cnbe32/data/cnbe32.db" in text
    assert "Unicode code point" in text
    assert "SQLite rebuild is a separate authorized step" in text
    assert "8105 runtime promotion" in text
    assert "release, tag, and PyPI publication: not performed" in text
    assert "97,686-row validation claims" in text
    assert "Research Reproducibility Boundary" in text


def test_repository_structure_points_to_8105_governance() -> None:
    text = read_text("docs/REPOSITORY_STRUCTURE.md")
    assert "docs/CNBE8105_ENCODING_GOVERNANCE.md" in text
    assert "docs/CNBE_REPRODUCIBLE_AGENT_WORKFLOW.md" in text
    assert "8105 layer is the current national-standard core" in text
    assert "Source catalog rewrites and SQLite database rebuilds" in text


def test_reproducible_agent_workflow_declares_stop_conditions() -> None:
    text = read_text("docs/CNBE_REPRODUCIBLE_AGENT_WORKFLOW.md")
    assert "Authority Order" in text
    assert "Unicode identity and code point compatibility" in text
    assert "8105 common standardized Chinese character table" in text
    assert "Stop Conditions" in text
    assert "dictionary context is being promoted as national-standard evidence" in text
    assert "Large full-catalog intermediate files should not be committed" in text
