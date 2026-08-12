#!/usr/bin/env python3
"""Demonstrate CNBE Knowledge Bridge for RAG, ancient validation, and OCR."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("CNBE32_DB_PATH", str(ROOT / "data" / "cnbe32.db"))

from cnbe32.knowledge_bridge import CNBEKnowledgeBridge  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, default=None)
    args = ap.parse_args()

    bridge = CNBEKnowledgeBridge()
    report: dict = {}

    state = bridge.lookup("明")
    print("== CNBE 状态（AI 可读） ==")
    print(state.to_ai_prompt() if state else "未覆盖")

    print("\n== 数据库自验 ==")
    validation = bridge.self_validate()
    print(
        f"rows={validation['rows']} standard={validation['standard_track']} "
        f"out_of_range={validation['out_of_range']} "
        f"reencode_mismatch={validation['reencode_mismatch']} "
        f"reverse_collisions={validation['reverse_collisions']}"
    )
    report["validation"] = validation

    print("\n== 结构最近邻（己） ==")
    nearest = bridge.nearest("己", k=5)
    for item in nearest:
        print(
            f"{item['char']} dist={item['field_weighted_distance']} "
            f"bit={item['bit_hamming_distance']} sim={item['similarity']}"
        )
    report["nearest_ji"] = nearest

    print("\n== OCR 字形候选（己 -> 已/巳/戊/戌/己） ==")
    ocr = bridge.ocr_candidates("己", ["已", "巳", "戊", "戌", "己"])
    for item in ocr:
        print(f"{item['candidate']} exact={item['exact']} dist={item['field_weighted_distance']}")
    report["ocr_candidates"] = ocr

    print("\n== 知识库检索（治水） ==")
    knowledge = [
        {"char": "治", "title": "治水", "text": "大禹治水，疏而不堵。"},
        {"char": "法", "title": "法治", "text": "治国必先治吏，治吏必先严法。"},
        {"char": "理", "title": "义理", "text": "天理人欲，存天理则近于道。"},
        {"char": "水", "title": "水部", "text": "水部汉字多与江河湖海相关。"},
    ]
    retrieved = bridge.retrieve_knowledge("治水", knowledge, top_k=3)
    for item in retrieved:
        print(f"{item['score']} {item['title']} {item['text']}")
    report["rag"] = retrieved

    print("\n== 古籍 OCR 校验（道/到） ==")
    ancient = bridge.ancient_validate("治水之到在于利民", "治水之道在于利民")
    for note in ancient["collations"]:
        print(note["kind"], note["source"], "->", note["target"])
    report["ancient"] = ancient

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print("\nsaved:", args.output)
    bridge.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
