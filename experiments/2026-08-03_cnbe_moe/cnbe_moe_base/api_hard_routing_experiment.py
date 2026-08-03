# -*- coding: utf-8 -*-
"""DeepSeek V4 API 消融实验：CNBE 字段提示 vs 原文 vs Unicode 码点提示。

注意：本实验验证的是“CNBE 字段作为上下文提示能否提升 API 下游任务”，
不是真正的模型内部硬路由迁移；结论仅用于评估 API 层的可行性。
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "cnbe_moe"))

from deepseek_api_repro import DeepSeekV4, f1, punct_positions  # noqa: E402

CONFUSING_GROUPS = [
    ["己", "已", "巳"],
    ["戊", "戌", "戍"],
    ["未", "末"],
    ["治", "冶"],
    ["徒", "徙"],
    ["于", "干"],
    ["入", "人"],
    ["刀", "力"],
    ["问", "间"],
    ["天", "夭"],
    ["王", "玉"],
    ["土", "士"],
    ["大", "太"],
    ["日", "曰"],
    ["臣", "巨"],
    ["刺", "剌"],
    ["候", "侯"],
    ["采", "釆"],
    ["折", "拆"],
    ["子", "孑"],
    ["千", "干"],
    ["八", "入"],
    ["九", "丸"],
    ["竞", "竟"],
    ["市", "巿"],
    ["茶", "荼"],
    ["今", "令"],
    ["厂", "广"],
    ["历", "厉"],
    ["处", "外"],
    ["声", "生"],
    ["毛", "手"],
    ["牛", "午"],
    ["贝", "见"],
    ["鸟", "乌"],
    ["仓", "仑"],
    ["梁", "粱"],
    ["毫", "亳"],
    ["喜", "善"],
    ["管", "菅"],
    ["拔", "拨"],
    ["戌", "戍"],
    ["候", "侯"],
    ["侯", "候"],
]


def load_eval(path: str) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def build_confusable_items(corpus_paths: list[str], limit: int = 30, seed: int = 42) -> list[dict]:
    text = "\n".join(Path(p).read_text(encoding="utf-8", errors="ignore") for p in corpus_paths if Path(p).exists())
    lines = [l.strip() for l in text.splitlines() if len(l.strip()) >= 10]
    rng = random.Random(seed)
    items = []
    targets = [ch for g in CONFUSING_GROUPS for ch in g]
    rng.shuffle(targets)
    for ch in targets:
        if len(items) >= limit:
            break
        cand = [l for l in lines if ch in l]
        if not cand:
            continue
        line = rng.choice(cand)
        idx = line.find(ch)
        snippet = line[max(0, idx - 8) : idx + 9]
        group = next(g for g in CONFUSING_GROUPS if ch in g)
        wrong = rng.choice([c for c in group if c != ch])
        wrong_snippet = snippet.replace(ch, wrong, 1)
        items.append({"correct": ch, "wrong": wrong, "snippet": snippet, "wrong_snippet": wrong_snippet})
    return items


def run_punct(client: DeepSeekV4, rows: list[dict], limit: int = 10) -> dict:
    rows = rows[:limit]
    prompts = {
        "control": lambda u: f"请为以下无标点古籍添加标点：\n{u}",
        "cnbe": lambda u: (
            "请为以下无标点古籍添加标点。提示：按汉字结构字段处理，"
            "左右结构关注词语边界，上下结构关注层次停顿，包围结构关注复杂句式。\n"
            f"{u}"
        ),
        "unicode": lambda u: f"请为以下无标点古籍添加标点。提示：按 Unicode 码位顺序处理文本。\n{u}",
    }
    out = {}
    for arm, make in prompts.items():
        scores = []
        for row in rows:
            user = row["messages"][0]["content"]
            gold = row["messages"][1]["content"]
            resp = client.chat(make(user))
            pred = resp["text"] or user
            scores.append(f1(punct_positions(pred), punct_positions(gold))["f1"])
        out[arm] = round(sum(scores) / len(scores), 4)
    return out


def run_confusable(client: DeepSeekV4, items: list[dict]) -> dict:
    def make_prompt(item, arm: str) -> str:
        if arm == "control":
            return f"请纠正以下文本中的错别字：\n{item['wrong_snippet']}"
        if arm == "cnbe":
            return (
                f"请纠正以下文本中的错别字。CNBE 结构字段提示：{item['correct']} "
                f"与 {item['wrong']} 部首/结构/笔画不同，请按结构字段区分。\n"
                f"{item['wrong_snippet']}"
            )
        return (
            f"请纠正以下文本中的错别字。Unicode 码位提示：{item['correct']}="
            f"U+{ord(item['correct']):04X}，{item['wrong']}=U+{ord(item['wrong']):04X}。\n"
            f"{item['wrong_snippet']}"
        )

    out = {}
    for arm in ("control", "cnbe", "unicode"):
        ok = 0
        for item in items:
            resp = client.chat(make_prompt(item, arm))
            text = resp["text"] or ""
            if item["correct"] in text and item["wrong"] not in text:
                ok += 1
        out[arm] = round(ok / len(items), 4)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="DeepSeek V4 API CNBE 提示消融")
    parser.add_argument("--punct-jsonl", default=str(ROOT / "guji-platform" / "llm" / "data" / "eval.jsonl"))
    parser.add_argument("--punct-limit", type=int, default=10)
    parser.add_argument("--confusable-limit", type=int, default=30)
    parser.add_argument("--corpus", nargs="+", default=[
        str(ROOT / "caixin_repro" / "outputs" / "caixin_raw.txt"),
        str(ROOT / "jinyong_repro" / "outputs" / "jinyong_raw.txt"),
    ])
    parser.add_argument("--output", default=str(ROOT / "outputs" / "api_cnbe_ablation.json"))
    args = parser.parse_args()

    client = DeepSeekV4()
    rows = load_eval(args.punct_jsonl)
    punct = run_punct(client, rows, args.punct_limit)
    print("punct F1:", punct, flush=True)

    items = build_confusable_items(args.corpus, args.confusable_limit)
    conf = run_confusable(client, items)
    print("confusable acc:", conf, flush=True)

    report = {"punct_f1": punct, "confusable_accuracy": conf, "n_confusable": len(items)}
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("saved", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
