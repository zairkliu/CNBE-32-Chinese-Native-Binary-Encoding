from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_repository_publishes_current_agent_skill() -> None:
    text = read_text("skill/cnbe-hanzi-structure-encoding-agent/SKILL.md")

    assert "name: cnbe-hanzi-structure-encoding-agent" in text
    assert "CNBE Hanzi Structure Encoding Agent" in text
    assert "Always start with Unicode alignment" in text
    assert "Treat `v1.0.4` as the current published SDK checkpoint" in text
    assert "Treat 8105 as the national-standard baseline" in text
    assert "Do not generate CNBE fields from visual intuition or LLM memory" in text
    assert "Do not let CNBE32 bit pressure override Hanzi evidence" in text
    assert "Do not rewrite CNBE databases or source encoding tables" in text
    assert "publishing to PyPI" in text


def test_repository_agent_skill_declares_invocation_contract() -> None:
    text = read_text("skill/cnbe-hanzi-structure-encoding-agent/SKILL.md")

    for required_field in (
        "run_id",
        "operator_role",
        "input_scope",
        "input_artifacts",
        "unicode_gate",
        "authority_order",
        "allowed_outputs",
        "forbidden_outputs",
        "stop_conditions",
        "verification_commands",
    ):
        assert required_field in text


def test_skill_directory_separates_current_agent_from_legacy_experiment_skill() -> None:
    text = read_text("skill/README.md")

    assert "Current Operational Agent" in text
    assert "skill/cnbe-hanzi-structure-encoding-agent/SKILL.md" in text
    assert "Historical Experiment Skill" in text
    assert "must not be used as authority" in text


def test_public_docs_link_to_repository_agent_skill() -> None:
    for relative_path in ("README.md", "README_EN.md", "README_ZH.md"):
        text = read_text(relative_path)
        assert "skill/cnbe-hanzi-structure-encoding-agent/SKILL.md" in text

    structure_doc = read_text("docs/REPOSITORY_STRUCTURE.md")
    assert "Skill Layer" in structure_doc
    assert "Repository-published total-control Agent" in structure_doc

