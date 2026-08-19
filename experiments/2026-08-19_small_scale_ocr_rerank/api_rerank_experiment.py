#!/usr/bin/env python3
"""DeepSeek V4 API reranking experiment: plain vs Unicode vs CNBE hints."""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "experiments/2026-08-07_api_pipeline/clients"))

from cnbe32 import CNBEKnowledgeBridge  # noqa: E402
from llm_client import DeepSeekV4Client  # noqa: E402


CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def first_cjk(text: str) -> str:
    m = CJK_RE.search(text or "")
    return m.group(0) if m else ""


def call_with_retry(client: DeepSeekV4Client, prompt: str, retries: int = 3) -> dict:
    last = None
    for attempt in range(retries):
        try:
            resp = client.chat(prompt)
            return {
                "pred": first_cjk(resp.text),
                "status": resp.status,
                "elapsed": round(resp.elapsed, 2),
            }
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(2 * (attempt + 1))
    return {"pred": "", "status": f"error:{last}", "elapsed": 0.0}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=40)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument(
        "--output",
        default=str(Path(__file__).parent / "api_rerank_results.json"),
    )
    args = ap.parse_args()
    out = Path(args.output)

    bridge = CNBEKnowledgeBridge()
    client = DeepSeekV4Client()
    if not client.available:
        print("NO_KEY")
        return 1

    pairs = json.loads(
        (Path(__file__).parent / "all_substitutions.json").read_text(encoding="utf-8")
    )
    standard_pool = [r["char"] for r in bridge._all_rows() if r.get("track") == "standard"]
    page_chars: dict[int, list[str]] = defaultdict(list)
    page_text: dict[int, str] = {}
    for p in pairs:
        if p["truth"] not in page_chars[p["page"]]:
            page_chars[p["page"]].append(p["truth"])
    pages_dir = REPO / "experiments/2026-08-06_paddleocr_vl16" / "pages"
    for page in page_chars:
        md = pages_dir / f"page_{page:03d}.md"
        if md.exists():
            page_text[page] = re.sub(r"[^\u4e00-\u9fff]", "", md.read_text(encoding="utf-8"))

    eligible = [
        p
        for p in pairs
        if bridge.lookup(p["ocr"]) is not None and bridge.lookup(p["truth"]) is not None
    ]
    shape = [p for p in eligible if p["label"] == "shape_confusable"]
    others = [p for p in eligible if p["label"] != "shape_confusable"]
    rng = random.Random(args.seed)
    rng.shuffle(others)
    sample = shape[: min(len(shape), args.limit // 2)] + others[: max(0, args.limit - len(shape[: args.limit // 2]))]
    sample = sample[: args.limit]

    rows = []
    for i, p in enumerate(sample):
        ocr, truth, page = p["ocr"], p["truth"], p["page"]
        text = page_text.get(page, "")
        idx = text.find(ocr)
        left = text[idx - 1] if idx > 0 else ""
        right = text[idx + 1] if 0 <= idx + 1 < len(text) else ""
        page_cands = [c for c in page_chars[page] if c not in (ocr, truth)]
        need = max(0, 15 - len(page_cands) - 1)
        distractor_pool = [c for c in standard_pool if c not in (ocr, truth) and c not in page_cands]
        distractors = rng.sample(distractor_pool, min(need, len(distractor_pool)))
        candidates = [truth] + page_cands + distractors
        rng.shuffle(candidates)

        plain_prompt = (
            f"古籍 OCR 把「{ocr}」识别成了「{left}{ocr}{right}」中的「{ocr}」。"
            f"请从候选汉字中选出最可能的正确字，只输出一个汉字，不要解释。\n候选："
            + " ".join(candidates)
        )
        unicode_prompt = plain_prompt + "\n候选 Unicode：\n" + "\n".join(
            f"{c} U+{ord(c):04X}" for c in candidates
        )
        cnbe_lines = []
        for c in candidates:
            s = bridge.lookup(c)
            if s is None:
                continue
            cnbe_lines.append(
                f"{c} 部首{s.radix} 笔画{s.stroke} 结构{s.struct_name or s.struct} "
                f"索引{s.index} 码{s.hex}"
            )
        cnbe_prompt = plain_prompt + "\n候选 CNBE 结构字段：\n" + "\n".join(cnbe_lines)

        row = {"page": page, "ocr": ocr, "truth": truth, "label": p["label"], "predictions": {}}
        prompts = [
            ("plain", plain_prompt),
            ("unicode", unicode_prompt),
            ("cnbe", cnbe_prompt),
        ]
        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = {
                pool.submit(call_with_retry, client, prompt): cond for cond, prompt in prompts
            }
            for fut, cond in futures.items():
                pred = fut.result()
                row["predictions"][cond] = {
                    **pred,
                    "correct": pred["pred"] == truth,
                }
        rows.append(row)
        out.write_text(
            json.dumps(
                {"limit": args.limit, "n": len(rows), "rows": rows},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"[{i+1}/{len(sample)}] {ocr}->{truth} {row['predictions']}", flush=True)

    summary = {}
    for cond in ("plain", "unicode", "cnbe"):
        preds = [r["predictions"][cond] for r in rows]
        valid = [p for p in preds if p["pred"]]
        summary[cond] = {
            "top1_accuracy": sum(p["correct"] for p in valid) / len(valid) if valid else 0.0,
            "parsed": len(valid),
            "total": len(rows),
        }

    result = {"limit": args.limit, "n": len(rows), "summary": summary, "rows": rows}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("saved:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
