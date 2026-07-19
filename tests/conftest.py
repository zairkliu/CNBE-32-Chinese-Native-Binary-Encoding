from __future__ import annotations

import os
from pathlib import Path

import pytest

LOCAL_KNOWLEDGE_ROOT = Path(
    os.environ.get(
        "CNBE_RESEARCH_KNOWLEDGE_ROOT",
        "/Users/liuzhaoqi/Documents/cnbe-research/knowledge",
    )
)

LOCAL_KNOWLEDGE_TESTS = {
    "test_300_character_pilot_evidence_join.py",
    "test_8105_approved_cnbe32_dry_run_patch.py",
    "test_8105_bounded_standardizer_pilot.py",
    "test_8105_core_standard_source_join_for_pilot.py",
    "test_8105_core_structure_decomposition_source_extraction_plan.py",
    "test_8105_gap_priority_reference_candidates.py",
    "test_dictionary_context_knowledge_merge_audit.py",
    "test_dictionary_context_knowledge_merge_plan.py",
    "test_external_dictionary_context_review_join.py",
    "test_external_dictionary_context_staging.py",
    "test_external_dictionary_source_candidate_evaluation.py",
    "test_full_catalog_gf0017_source_join_batch.py",
    "test_full_catalog_gf0017_source_mapping.py",
    "test_remaining_structure_source_acquisition_plan.py",
    "test_structure_decomposition_dictionary_gap_extractor.py",
    "test_structure_decomposition_evidence_parser.py",
    "test_structure_decomposition_source_gap_resolution_plan.py",
    "test_structured_8105_knowledge_diff_packet.py",
    "test_structured_8105_knowledge_patch.py",
    "test_unified_hanzi_evidence_index.py",
    "test_unified_hanzi_evidence_index_plan.py",
    "test_wikipedia_structure_cross_reference_index.py",
    "test_wikipedia_structure_cross_reference_index_plan.py",
}


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if LOCAL_KNOWLEDGE_ROOT.exists():
        return

    reason = "requires local cnbe-research knowledge workspace"
    marker = pytest.mark.skip(reason=reason)
    for item in items:
        if Path(str(item.fspath)).name in LOCAL_KNOWLEDGE_TESTS:
            item.add_marker(marker)
