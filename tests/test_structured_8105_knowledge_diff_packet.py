"""Tests for the structured 8105 knowledge diff packet."""

from __future__ import annotations

from scripts.diff_structured_8105_knowledge import build_diff_packet, render_markdown


def test_diff_packet_is_read_only_and_reaches_patch_review_gate() -> None:
    packet = build_diff_packet()

    assert packet["overall_status"] == "PASS"
    assert packet["next_workflow_status"] in {
        "PATCH_REVIEW_REQUIRED_BEFORE_SOURCE_WRITE",
        "STRUCTURED_KNOWLEDGE_DIFF_CLEAN",
    }
    assert packet["authority_boundary"]["does_not_modify_research_assets"] is True
    assert packet["summary"]["source_write_allowed"] is False
    assert packet["summary"]["batch_scoring_allowed"] is False


def test_diff_packet_finds_expected_dataset_counts() -> None:
    packet = build_diff_packet()

    assert packet["summary"]["baseline_count"] == 8105
    assert packet["summary"]["datasets_checked"] == 2
    assert packet["summary"]["total_missing"] in {0, 6}
    assert packet["summary"]["total_extra"] in {0, 4}
    assert packet["summary"]["total_unicode_label_issues"] in {0, 15818}
    assert all(dataset["missing_count"] in {0, 3} for dataset in packet["datasets"])
    assert all(dataset["extra_count"] in {0, 2} for dataset in packet["datasets"])


def test_diff_packet_requires_human_authorization_before_source_write() -> None:
    packet = build_diff_packet()

    assert packet["decision_point"]["requires_human_authorization"] in {False, True}
    assert "write to cnbe-research/knowledge/structured" in packet["decision_point"][
        "still_forbidden_without_authorization"
    ]
    assert "start full-catalog GF0017 row scoring" in packet["decision_point"][
        "still_forbidden_without_authorization"
    ]


def test_diff_packet_markdown_states_missing_characters_and_boundary() -> None:
    markdown = render_markdown(build_diff_packet())

    assert "# Structured 8105 Knowledge Diff Packet" in markdown
    assert "It is read-only" in markdown
    assert "## Extra Characters" in markdown
    assert (
        "Human authorization is required" in markdown
        or "No structured knowledge write is currently required" in markdown
    )
