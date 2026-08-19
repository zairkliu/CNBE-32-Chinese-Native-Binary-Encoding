"""Tests for the CNBE Knowledge Bridge (RAG / ancient / OCR integration)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from cnbe32 import CNBEKnowledgeBridge


@pytest.fixture(scope="module")
def bridge() -> CNBEKnowledgeBridge:
    db_path = Path(__file__).resolve().parents[1] / "data" / "cnbe32.db"
    os.environ["CNBE32_DB_PATH"] = str(db_path)
    b = CNBEKnowledgeBridge()
    yield b
    b.close()


def test_state_lookup_is_ai_readable(bridge: CNBEKnowledgeBridge) -> None:
    state = bridge.lookup("明")
    assert state is not None
    assert state.radix_name == "日"
    assert state.struct_name == "左右"
    assert state.validate()["valid"] is True
    assert state.to_ai_prompt().startswith("汉字 明 的 CNBE-32 状态")


def test_self_validate_reports_database_consistency(bridge: CNBEKnowledgeBridge) -> None:
    report = bridge.self_validate()
    assert report["rows"] > 20_000
    assert report["out_of_range"] == 0
    assert report["reencode_mismatch"] == 0


def test_distance_exposes_known_pseudo_metric_case(bridge: CNBEKnowledgeBridge) -> None:
    dist = bridge.distance("己", "已")
    assert dist is not None
    assert dist["field_weighted_distance"] == 0
    assert dist["bit_hamming_distance"] > 0


def test_ocr_candidates_put_exact_char_first(bridge: CNBEKnowledgeBridge) -> None:
    result = bridge.ocr_candidates("己", ["戊", "己", "巳", "戌"])
    assert result[0]["candidate"] == "己"
    assert result[0]["exact"] is True


def test_rag_retrieval_uses_structural_match(bridge: CNBEKnowledgeBridge) -> None:
    knowledge = [
        {"char": "治", "title": "治水", "text": "大禹治水，疏而不堵。"},
        {"char": "法", "title": "法治", "text": "治国必先治吏，治吏必先严法。"},
        {"char": "理", "title": "义理", "text": "天理人欲，存天理则近于道。"},
    ]
    result = bridge.retrieve_knowledge("治", knowledge, top_k=1)
    assert result
    assert result[0]["title"] == "治水"
    assert result[0]["score"] == 1.0


def test_ancient_validate_returns_collation_and_excerpt(bridge: CNBEKnowledgeBridge) -> None:
    result = bridge.ancient_validate("治水之到在于利民", "治水之道在于利民")
    assert result["total_notes"] >= 1
    assert "治水" in result["excerpt"]
