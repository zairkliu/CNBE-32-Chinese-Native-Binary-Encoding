"""Tests for bounded ZDIC reference snapshot manifests."""

from __future__ import annotations

from scripts.build_zdic_reference_snapshot_manifest import build_manifest, render_markdown


def test_zdic_reference_snapshot_manifest_is_ready() -> None:
    report = build_manifest()

    assert report["overall_status"] == "PASS_ZDIC_REFERENCE_SNAPSHOT_MANIFEST_READY"
    assert report["summary"]["packet_rows"] == 212
    assert report["summary"]["lookup_rows"] == 212
    assert report["summary"]["captured_snapshot_rows"] >= 4
    assert report["summary"]["captured_packet_snapshot_rows"] >= 2
    assert report["decision"]["may_use_zdic_for_review_context"] is True


def test_zdic_reference_snapshot_manifest_keeps_authority_boundary() -> None:
    report = build_manifest()

    assert report["authority_boundary"]["zdic_is_online_cross_reference"] is True
    assert report["authority_boundary"]["zdic_is_not_national_standard_authority"] is True
    assert report["authority_boundary"]["does_not_query_full_97686_table"] is True
    assert report["decision"]["may_promote_zdic_to_national_standard"] is False
    assert report["decision"]["may_assign_gf0017_points"] is False
    assert report["decision"]["may_emit_final_structure_labels"] is False


def test_zdic_reference_snapshot_manifest_has_lookup_urls_and_snapshots() -> None:
    report = build_manifest()

    for row in report["lookup_rows"]:
        assert row["zdic_url"].startswith("https://www.zdic.net/hans/")
        assert row["authority_boundary"] == "zdic_cross_reference_only"
    snapshot_by_unicode = {row["unicode"]: row for row in report["snapshot_records"]}
    assert snapshot_by_unicode["U+946B"]["in_current_packet"] is False
    assert snapshot_by_unicode["U+3400"]["in_current_packet"] is True
    assert snapshot_by_unicode["U+946B"]["observed_fields"]["has_structure"] is True
    assert snapshot_by_unicode["U+946B"]["observed_fields"]["has_kangxi"] is True
    assert snapshot_by_unicode["U+3400"]["observed_fields"]["has_structure"] is True
    assert snapshot_by_unicode["U+323AF"]["observed_fields"]["has_unicode"] is True


def test_zdic_reference_snapshot_manifest_markdown_states_boundary() -> None:
    markdown = render_markdown(build_manifest())

    assert "# ZDIC Reference Snapshot Manifest" in markdown
    assert "online cross-reference context only" in markdown
    assert "GF0017 points assigned: 0" in markdown
