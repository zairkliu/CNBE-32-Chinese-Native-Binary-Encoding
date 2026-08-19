#!/usr/bin/env python3
"""DeepSeek V4 API reranking v2: numbered candidates, higher parse rate, resume."""

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
NUM_RE = re.compile(r"\d+")


def first_cjk(text: str) -> str:
    m = CJK_RE.search(text or "")
    return m.group(0) if m else ""


def parse_answer(text: str, candidates: list[str]) -> str:
    m = NUM_RE.search(text or "")
    if m:
        idx = int(m.group(0))
        if 1 <= idx <= len(candidates):
            return candidates[idx - 1]
    return first_cjk(text)


def call_with_retry(client: DeepSeekV4Client, prompt: str, retries: int = 3) -> dict:
    last = None
    for attempt in range(retries):
        try:
            resp = client.chat(prompt)
            return {"text": resp.text, "status": resp.status, "elapsed": round(resp.elapsed, 2)}
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(2 * (attempt + 1))
    return {"text": "", "status": f"error:{last}", "elapsed": 0.0}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=40)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument(
        "--output",
        default=str(Path(__file__).parent / "api_rerank_v2_results.json"),
    )
    args = ap.parse_args()

    out = Path(args.output)
    bridge = CNBEKnowledgeBridge()
    client = DeepSeekV4Client(max_output_tokens=2048)
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

    existing = []
    if args.resume and out.exists():
        existing = json.loads(out.read_text(encoding="utf-8")).get("rows", [])
    done = {(r["page"], r["ocr"], r["truth"]) for r in existing}

    eligible = [
        p
        for p in pairs
        if bridge.lookup(p["ocr"]) is not None and bridge.lookup(p["truth"]) is not None
    ]
    shape = [p for p in eligible if p["label"] == "shape_confusable"]
    others = [p for p in eligible if p["label"] != "shape_confusable"]
    rng = random.Random(args.seed)
    rng.shuffle(others)
    sample = shape[: args.limit // 2] + others[: args.limit - len(shape[: args.limit // 2])]
    sample = sample[: args.limit]

    rows = list(existing)
    pending = 0
    for i, p in enumerate(sample):
        key = (p["page"], p["ocr"], p["truth"])
        if key in done:
            continue
        pending += 1
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
        numbered = "\n".join(f"{i+1}. {c}" for i, c in enumerate(candidates))
        base = (
            f"OCR 识别结果为「{ocr}」，上下文为「{left}{ocr}{right}」。"
            f"候选如下，请只输出正确候选的编号（例如 3），不要解释。\n{numbered}"
        )
        unicode_lines = [f"{i+1}. {c} U+{ord(c):04X}" for i, c in enumerate(candidates)]
        cnbe_lines = []
        for i, c in enumerate(candidates):
            s = bridge.lookup(c)
            radix = s.radix if s else "?"
            stroke = s.stroke if s else "?"
            struct = (s.struct_name or s.struct) if s else "?"
            index = s.index if s else "?"
            cnbe_lines.append(f"{i+1}. {c} 部首{radix} 笔画{stroke} 结构{struct} 索引{index}")
        prompts = [
            ("plain", base),
            ("unicode", base + "\nUnicode：\n" + "\n".join(unicode_lines)),
            ("cnbe", base + "\nCNBE：\n" + "\n".join(cnbe_lines)),
        ]

        row = {"page": page, "ocr": ocr, "truth": truth, "label": p["label"], "predictions": {}}
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = {pool.submit(call_with_retry, client, prompt): cond for cond, prompt in prompts}
            for fut, cond in futures.items():
                resp = fut.result()
                pred = parse_answer(resp["text"], candidates)
                row["predictions"][cond] = {
                    "pred": pred,
                    "correct": pred == truth,
                    "status": resp["status"],
                    "elapsed": resp["elapsed"],
                    "raw": resp["text"][:200],
                }
        rows.append(row)
        done.add(key)
        out.write_text(
            json.dumps({"n": len(rows), "rows": rows}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"[{len(rows)}] {ocr}->{truth} {row['predictions']}", flush=True)

    summary = {}
    for cond in ("plain", "unicode", "cnbe"):
        preds = [r["predictions"][cond] for r in rows]
        valid = [p for p in preds if p["pred"]]
        summary[cond] = {
            "top1_accuracy": sum(p["correct"] for p in valid) / len(valid) if valid else 0.0,
            "parsed": len(valid),
            "total": len(rows),
            "parse_rate": len(valid) / len(rows) if rows else 0.0,
        }
    result = {"limit": args.limit, "n": len(rows), "pending": pending, "summary": summary, "rows": rows}
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("saved:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
