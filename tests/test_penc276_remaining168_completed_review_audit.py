"""Cover no-write intake checks and deterministic ihandian sample selection."""

from scripts.audit_penc276_remaining168_completed_review import HUMAN_APPROVED_NONRENDERABLE_REFERENCE_ROWS, comparable_fixed_value, compact_decomposition, excel_date, select_stratified_smoke_sample


def test_completed_review_helpers_keep_decomposition_and_excel_date_stable() -> None:
    assert compact_decomposition("亻、 刍") == "亻刍"
    assert excel_date(46229) == "2026-07-26"
    assert comparable_fixed_value("证据边界", "国家规范、Unihan") == comparable_fixed_value("证据边界", "国家规范Unihan")
    assert "PENC_022" in HUMAN_APPROVED_NONRENDERABLE_REFERENCE_ROWS


def test_smoke_sample_covers_sparse_tiers_and_is_bounded() -> None:
    rows = []
    for tier, count in (("T0", 1), ("T1", 124), ("T2", 36), ("T3", 3), ("T4", 4)):
        rows.extend({"原始分层": tier, "清单编号": f"{tier}_{index}"} for index in range(count))
    selected = select_stratified_smoke_sample(rows)

    assert len(selected) == 14
    assert {row["原始分层"] for row in selected} == {"T0", "T1", "T2", "T3", "T4"}
