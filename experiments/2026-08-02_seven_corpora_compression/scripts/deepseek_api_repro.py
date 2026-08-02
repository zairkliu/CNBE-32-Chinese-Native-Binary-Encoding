# -*- coding: utf-8 -*-
"""DeepSeek V4 API 复现测试器。

两个任务：
- punct: 用无标点真值古文调用 DeepSeek V4，复现“句读”实验并计算标点 F1
- moe: 用真实 CNBE 字流调用 DeepSeek V4 做结构分组路由，与 CNBE 查表路由对照
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from step1_build_mapping import load_codes  # noqa: E402
from step2_cnbe_router import CNBERouter  # noqa: E402
from cnbe_volume.volume import load_maps  # noqa: E402


def load_key() -> str:
    auth = json.loads(Path.home().joinpath(".codex", "auth.json").read_text(encoding="utf-8"))
    key = auth.get("OPENAI_API_KEY", "")
    if not key:
        raise RuntimeError("auth.json 中无 OPENAI_API_KEY")
    return key


class DeepSeekV4:
    def __init__(self, model: str = "deepseek-v4-flash", base_url: str = "https://api.deepseek.com/v1/responses"):
        self.model = model
        self.base_url = base_url
        self.key = load_key()

    def chat(self, prompt: str, max_output_tokens: int = 2048) -> dict:
        payload = {
            "model": self.model,
            "input": prompt,
            "max_output_tokens": max_output_tokens,
            "temperature": 0.0,
            "reasoning": {"effort": "low"},
        }
        req = urllib.request.Request(
            self.base_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"},
            method="POST",
        )
        t0 = time.perf_counter()
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        elapsed = time.perf_counter() - t0
        text = self._extract_text(data)
        return {"text": text, "elapsed": elapsed, "usage": data.get("usage", {})}

    @staticmethod
    def _extract_text(data: dict) -> str:
        out = []
        for item in data.get("output", []):
            for content in item.get("content", []) or []:
                if content.get("type") == "output_text" and content.get("text"):
                    out.append(content["text"])
        return "\n".join(out).strip()


def punct_positions(text: str) -> list[int]:
    pos = 0
    out = []
    for ch in text:
        if ch in "。，、；：？！":
            out.append(pos)
        elif "\u3400" <= ch <= "\u9fff" or "\U00020000" <= ch <= "\U0002ebef":
            pos += 1
    return out


def f1(pred, gold):
    correct = len(set(pred) & set(gold))
    p = correct / len(pred) if pred else 0.0
    r = correct / len(gold) if gold else 0.0
    return {"precision": round(p, 4), "recall": round(r, 4), "f1": round(2 * p * r / (p + r) if p + r else 0.0, 4), "correct": correct}


def task_punct(args, client: DeepSeekV4) -> dict:
    rows = []
    with open(args.eval_jsonl, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    rows = rows[: args.limit] if args.limit else rows
    results = []
    for row in rows:
        user = row["messages"][0]["content"]
        gold = row["messages"][1]["content"]
        prompt = f"给下面的古籍原文添加现代标点并分段，只输出结果：\n{user}"
        resp = client.chat(prompt)
        pred = resp["text"] or user
        score = f1(punct_positions(pred), punct_positions(gold))
        results.append(
            {
                "input_chars": len(user),
                "gold_punct": len(punct_positions(gold)),
                "pred_punct": len(punct_positions(pred)),
                "score": score,
                "elapsed": round(resp["elapsed"], 2),
                "usage": resp["usage"],
                "gold": gold[:60],
                "pred": pred[:60],
            }
        )
    avg = {
        "precision": round(sum(r["score"]["precision"] for r in results) / len(results), 4),
        "recall": round(sum(r["score"]["recall"] for r in results) / len(results), 4),
        "f1": round(sum(r["score"]["f1"] for r in results) / len(results), 4),
    }
    report = {"n": len(results), "model": client.model, "average": avg, "samples": results}
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"n": len(results), "average": avg}, ensure_ascii=False, indent=2))
    return report


def task_moe(args, client: DeepSeekV4) -> dict:
    codes = load_codes(args.cnbe)[: args.tokens]
    map_payload = json.loads(Path(args.map).read_text(encoding="utf-8"))
    mapping = map_payload["mapping"]
    router = CNBERouter(mapping, num_experts=args.num_experts)
    radix = ((codes >> 24) & 0xFF).astype(np.int64)
    struct = ((codes >> 15) & 0x0F).astype(np.int64)
    keys = radix * 16 + struct
    cnbe_experts = [router.route_fields(radix[i], struct[i])[0] for i in range(len(codes))]

    _, forward = load_maps(args.db)
    chars = []
    for code in codes:
        ch = next((c for c, val in forward.items() if val == int(code)), None)
        chars.append(ch or f"#{int(code):08X}")

    letters = [chr(ord("A") + i) for i in range(args.num_experts)]
    groups = "\n".join(f"{letters[i]} = 专家{i+1}" for i in range(args.num_experts))
    prompt = (
        "你是一个古籍汉字结构路由专家。下面每个字属于古籍文本，请只根据其结构"
        f"（部首、笔画、结构类型）把它归入一个专家组（共{args.num_experts}组）：\n{groups}\n"
        "请按“字 组号字母”的格式逐行输出：\n" + "\n".join(chars)
    )
    resp = client.chat(prompt, max_output_tokens=args.max_output_tokens)
    text = resp["text"]
    api_experts = [None] * len(chars)
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.match(r"^([^\s:：=\-()]{1,4})\s*[：:=\-]?\s*\(?([A-Pa-p]|\d{1,2})\)?\s*$", line) or re.match(
            r"^\(?([A-Pa-p]|\d{1,2})\)?\s*[：:=\-]?\s*([^\s:：=\-()]{1,4})\s*$", line
        )
        if not m:
            continue
        g1, g2 = m.group(1), m.group(2)
        if re.fullmatch(r"[A-Pa-p]|\d{1,2}", g1):
            ch, raw = g2, g1
        else:
            ch, raw = g1, g2
        raw = raw.upper()
        idx = ord(raw) - ord("A") if raw.isalpha() else int(raw) - 1
        for pos, c in enumerate(chars):
            if c == ch and api_experts[pos] is None and 0 <= idx < args.num_experts:
                api_experts[pos] = idx
                break
    matched = [(cnbe_experts[i] == api_experts[i]) for i in range(len(chars)) if api_experts[i] is not None]
    report = {
        "n_chars": len(chars),
        "parsed": len(matched),
        "agreement": round(sum(matched) / len(matched), 4) if matched else 0.0,
        "model": client.model,
        "elapsed": round(resp["elapsed"], 2),
        "usage": resp["usage"],
        "raw_output": text[:1000],
    }
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "raw_output"}, ensure_ascii=False, indent=2))
    return report


def task_struct(args, client: DeepSeekV4) -> dict:
    codes = load_codes(args.cnbe)[: args.tokens]
    _, forward = load_maps(args.db)
    chars, gold_struct = [], []
    for code in codes:
        ch = next((c for c, val in forward.items() if val == int(code)), None)
        chars.append(ch or f"#{int(code):08X}")
        gold_struct.append((int(code) >> 15) & 0x0F)
    names = ["独体字", "左右", "左中右", "上下", "上中下", "左上包围", "右上包围", "左下包围", "上包围", "下包围", "左包围", "全包围", "品字"]
    prompt = (
        "你是汉字结构分析专家。对下面每个古籍汉字，只输出它的结构类型（13 类之一）："
        + "、".join(f"{i+1}.{n}" for i, n in enumerate(names))
        + f"\n请按“字 结构类型名”逐行输出：\n" + "\n".join(chars)
    )
    resp = client.chat(prompt, max_output_tokens=args.max_output_tokens)
    pred_struct = [None] * len(chars)
    for line in resp["text"].splitlines():
        line = line.strip()
        m = re.match(r"^([^\s]{1,4})\s*[：:=\-]?\s*([^\s]{1,6})\s*$", line)
        if not m:
            continue
        ch, name = m.group(1), m.group(2)
        idx = next((i for i, n in enumerate(names) if n.startswith(name) or name.startswith(n)), None)
        if idx is None:
            continue
        for pos, c in enumerate(chars):
            if c == ch and pred_struct[pos] is None:
                pred_struct[pos] = idx
                break
    ok = [gold_struct[i] == pred_struct[i] for i in range(len(chars)) if pred_struct[i] is not None]
    report = {
        "n_chars": len(chars),
        "parsed": len(ok),
        "structure_accuracy": round(sum(ok) / len(ok), 4) if ok else 0.0,
        "model": client.model,
        "elapsed": round(resp["elapsed"], 2),
        "usage": resp["usage"],
        "raw_output": resp["text"][:800],
    }
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "raw_output"}, ensure_ascii=False, indent=2))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="DeepSeek V4 API 复现测试")
    parser.add_argument("--task", choices=["punct", "moe", "struct"], required=True)
    parser.add_argument("--model", default="deepseek-v4-flash")
    parser.add_argument("--base-url", default="https://api.deepseek.com/v1/responses")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--eval-jsonl", default=str(ROOT / "guji-platform" / "llm" / "data" / "eval.jsonl"))
    parser.add_argument("--cnbe", default=str(ROOT / "cnbe_compression_experiment" / "outputs" / "zzjh_294.cnbe"))
    parser.add_argument("--map", default=str(ROOT / "cnbe_moe" / "outputs" / "struct_expert_map_16.json"))
    parser.add_argument("--num-experts", type=int, default=16)
    parser.add_argument("--tokens", type=int, default=20)
    parser.add_argument("--max-output-tokens", type=int, default=8192)
    parser.add_argument("--db", default=str(ROOT / "guji-ocr-corrector" / "data" / "cnbe32.db"))
    parser.add_argument("--report", default="")
    args = parser.parse_args()
    client = DeepSeekV4(model=args.model, base_url=args.base_url)
    if args.task == "punct":
        args.report = args.report or str(ROOT / "cnbe_moe" / "outputs" / "deepseek_punct_repro.json")
        task_punct(args, client)
    elif args.task == "moe":
        args.report = args.report or str(ROOT / "cnbe_moe" / "outputs" / "deepseek_moe_repro.json")
        task_moe(args, client)
    else:
        args.report = args.report or str(ROOT / "cnbe_moe" / "outputs" / "deepseek_struct_repro.json")
        task_struct(args, client)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
