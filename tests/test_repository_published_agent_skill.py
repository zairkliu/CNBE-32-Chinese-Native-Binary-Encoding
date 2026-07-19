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
    assert "skill/agents/cnbe-hanzi-structure-encoding-agent.yaml" in text
    assert ".github/agents/cnbe-hanzi-structure-encoding-agent.agent.md" in text
    assert "Historical Experiment Skill" in text
    assert "skill/agents/openai.yaml" in text
    assert "must not be used as authority" in text


def test_github_agents_page_profile_publishes_current_agent() -> None:
    text = read_text(".github/agents/cnbe-hanzi-structure-encoding-agent.agent.md")

    assert "name: cnbe-hanzi-structure-encoding-agent" in text
    assert "description: Standards-aligned total-control Agent" in text
    assert "GitHub-native listing entry for custom Copilot" in text
    assert "Unicode identity" in text
    assert "8105" in text
    assert "GF0017" in text
    assert "outside-8105 rows as CNBE Agent-standard candidates" in text
    assert "Do not publish 97,686-row validation claims" in text
    assert "skill/cnbe-hanzi-structure-encoding-agent/SKILL.md" in text

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


def test_agents_index_publishes_current_agent_metadata() -> None:
    text = read_text("skill/agents/cnbe-hanzi-structure-encoding-agent.yaml")

    assert "CNBE Hanzi Structure Encoding Agent" in text
    assert "../cnbe-hanzi-structure-encoding-agent/SKILL.md" in text
    assert "8105 is the national-standard core" in text
    assert "outside-8105 rows remain Agent-standard candidates" in text
    assert "v1.0.4 publishes the 20,902-row runtime package" in text
    assert "not 97,686-row validation" in text


def test_public_docs_link_to_repository_agent_skill() -> None:
    for relative_path in ("README.md", "README_EN.md", "README_ZH.md"):
        text = read_text(relative_path)
        assert "skill/cnbe-hanzi-structure-encoding-agent/SKILL.md" in text

    structure_doc = read_text("docs/REPOSITORY_STRUCTURE.md")
    assert "Skill Layer" in structure_doc
    assert "Repository-published total-control Agent" in structure_doc
    assert "skill/agents/cnbe-hanzi-structure-encoding-agent.yaml" in structure_doc
    assert ".github/agents/cnbe-hanzi-structure-encoding-agent.agent.md" in structure_doc


def test_copilot_cloud_agent_limitation_is_documented_as_optional() -> None:
    text = read_text("docs/COPILOT_CLOUD_AGENT_LIMITATION.md")

    assert "optional paid integration" in text
    assert "does not" in text
    assert "require GitHub Copilot cloud agent access" in text
    assert "required CNBE project dependency" in text
    assert "No Copilot cloud agent access" in text
    assert "issue `#35`" in text
    assert "must remain reproducible without a paid GitHub Copilot cloud agent" in text
    assert "license" in text
    assert ".github/agents/cnbe-hanzi-structure-encoding-agent.agent.md" in text
    assert ".github/copilot-instructions.md" in text
    assert ".github/workflows/copilot-setup-steps.yml" in text

    for relative_path in ("README.md", "README_EN.md", "README_ZH.md"):
        readme = read_text(relative_path)
        assert "docs/COPILOT_CLOUD_AGENT_LIMITATION.md" in readme

    structure_doc = read_text("docs/REPOSITORY_STRUCTURE.md")
    assert "docs/COPILOT_CLOUD_AGENT_LIMITATION.md" in structure_doc
    assert "optional paid automation" in structure_doc
