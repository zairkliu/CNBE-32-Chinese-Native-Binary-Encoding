import json
from pathlib import Path

from scripts.apply_8105_standardized_runtime_repair import render_markdown


def load_report() -> dict:
    return json.loads(Path("reports/8105_standardized_runtime_repair.json").read_text(encoding="utf-8"))


def test_standardized_runtime_repair_report_counts() -> None:
    report = load_report()
    summary = report["summary"]

    assert report["overall_status"] == "PASS_8105_STANDARDIZED_RUNTIME_REPAIR"
    assert summary["previous_patched_8105_rows"] == 6712
    assert summary["applied_repair_rows"] == 598
    assert summary["patched_8105_rows_after_repair"] == 7310
    assert summary["remaining_force_approved_not_patched_rows"] == 795
    assert summary["remaining_reason_counts"] == {
        "invalid_or_missing_stroke_count": 1,
        "missing_current_model_row": 276,
        "missing_radical_after_cross_reference_join": 486,
        "radical_resolution_blocked": 32,
    }


def test_standardized_runtime_repair_known_samples() -> None:
    samples = load_report()["known_samples"]

    assert samples["队"]["radix_name"] == "阜"
    assert samples["队"]["strokes"] == 4
    assert samples["队"]["struct_name"] == "左右"
    assert samples["玕"]["radix_name"] == "王"
    assert samples["玕"]["strokes"] == 7
    assert samples["玕"]["struct_name"] == "左右"
    assert samples["㑇"] is None
    assert samples["冁"]["struct_name"] == "single"
    assert samples["刁"]["struct_name"] == "full-wrap"


def test_standardized_runtime_repair_metadata_is_idempotent_safe() -> None:
    report = load_report()

    assert report["summary"]["previous_patched_8105_rows"] == 6712
    assert report["summary"]["applied_repair_rows"] == 598
    assert report["summary"]["patched_8105_rows_after_repair"] == 7310
    assert report["checks"]["applied_plus_remaining_matches_prior_queue"] is True
    assert report["decision"]["may_tag_release_or_publish"] is False


def test_standardized_runtime_repair_markdown_states_boundary() -> None:
    markdown = render_markdown(load_report())

    assert "# 8105 Standardized Runtime Repair" in markdown
    assert "Applied repair rows: 598" in markdown
    assert "does not" in markdown
    assert "tag, release, or PyPI publication" in markdown
    assert "missing_current_model_row" in markdown
