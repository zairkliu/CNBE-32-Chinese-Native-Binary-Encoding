#!/usr/bin/env python3
"""Compare learned character embeddings vs CNBE structural distance on OCR rerank."""

from __future__ import annotations

import argparse
import json
import ssl
import sys
from collections import defaultdict
from pathlib import Path

ssl._create_default_https_context = ssl._create_unverified_context

import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from cnbe32 import CNBEKnowledgeBridge  # noqa: E402


def embed_chars(model, tokenizer, chars: list[str]) -> dict[str, np.ndarray]:
    model.eval()
    result = {}
    with torch.no_grad():
        for i in range(0, len(chars), 32):
            batch = chars[i : i + 32]
            inputs = tokenizer(batch, return_tensors="pt", padding=True, truncation=True)
            out = model(**inputs).last_hidden_state
            mask = inputs["attention_mask"].unsqueeze(-1)
            vec = (out * mask).sum(1) / mask.sum(1).clamp(min=1)
            for c, v in zip(batch, vec):
                result[c] = v.float().numpy()
    return result


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def rank_of(target: str, candidates: list[dict], key) -> int:
    ordered = sorted(candidates, key=key)
    return [c["candidate"] for c in ordered].index(target) + 1


def metrics(rows):
    ranks = [r for _, r in rows]
    return {
        "top1_accuracy": sum(1 for r in ranks if r == 1) / len(ranks),
        "mean_reciprocal_rank": sum(1.0 / r for r in ranks) / len(ranks),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default="ShannonAI/ChineseBERT-base")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument(
        "--output",
        default=str(Path(__file__).parent / "embedding_baseline_results.json"),
    )
    args = ap.parse_args()

    exp = Path(__file__).resolve().parent
    records = []
    with (exp / "features.jsonl").open(encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))
    records = records[: args.limit * 20]
    chars = sorted({c for r in records for c in (r["ocr"], r["truth"], r["candidate"])})

    try:
        tokenizer = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
        model = AutoModel.from_pretrained(args.model, trust_remote_code=True)
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 1

    vectors = embed_chars(model, tokenizer, chars)
    bridge = CNBEKnowledgeBridge()
    groups = defaultdict(list)
    for r in records:
        groups[(r["page"], r["ocr"], r["truth"], r["error_label"])].append(r)

    methods = {"cnbe_hamming": [], "embedding": []}
    for (page, ocr, truth, label), cands in groups.items():
        methods["cnbe_hamming"].append(
            (
                label,
                rank_of(
                    truth,
                    cands,
                    lambda c: (c["features"]["cnbe_hamming"], ord(c["candidate"])),
                ),
            )
        )
        ov = vectors.get(ocr)
        methods["embedding"].append(
            (
                label,
                rank_of(
                    truth,
                    cands,
                    lambda c: (-cosine(ov, vectors[c["candidate"]]), ord(c["candidate"]))
                    if ov is not None and c["candidate"] in vectors
                    else (1, ord(c["candidate"])),
                ),
            )
        )

    summary = {name: metrics(rows) for name, rows in methods.items()}
    result = {
        "model": args.model,
        "chars": len(chars),
        "groups": len(groups),
        "summary": summary,
    }
    out = Path(args.output)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("saved:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
