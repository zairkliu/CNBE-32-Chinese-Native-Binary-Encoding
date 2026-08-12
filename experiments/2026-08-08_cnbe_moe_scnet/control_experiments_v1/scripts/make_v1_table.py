#!/usr/bin/env python3
"""Generate the v1 control comparison table from eval metrics JSONs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def pct(v) -> str:
    if isinstance(v, (int, float)):
        return f"{v * 100:.2f}%" if v <= 1 else f"{v:.2f}%"
    return "N/A"


def fmt(v) -> str:
    if isinstance(v, float):
        return f"{v:.6f}"
    return str(v) if v is not None else "N/A"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()

    arms = {
        "MoE-128": "moe128",
        "Dense same-config": "dense",
        "Dense matched-params": "dense_matched",
        "Unicode Dense": "unicode",
    }
    metrics = {}
    for label, name in arms.items():
        metrics[label] = load(args.output_dir / f"{name}_eval_metrics.json")

    lines = [
        "# V1 老版本 DCU2 受控对比结果",
        "",
        "| 指标 | MoE-128 | Dense same-config | Dense matched-params | Unicode Dense |",
        "|---|---:|---:|---:|---:|",
    ]
    rows = [
        ("eval_loss", "eval_loss"),
        ("next-code / next-token", "eval_accuracy"),
        ("radix", "eval_radix_accuracy"),
        ("struct", "eval_struct_accuracy"),
        ("strokes", "eval_strokes_accuracy"),
        ("radix head", "eval_radix_head_accuracy"),
        ("struct head", "eval_struct_head_accuracy"),
        ("strokes head", "eval_strokes_head_accuracy"),
        ("expert_gini", "expert_gini"),
        ("params", "params"),
    ]
    for label, key in rows:
        values = []
        for arm_label, data in metrics.items():
            v = data.get(key)
            if key == "eval_accuracy":
                values.append(pct(v))
            elif key == "params":
                values.append(f"{v:,}" if v else "N/A")
            elif key == "expert_gini":
                values.append(fmt(v) if v is not None else "N/A")
            elif key.startswith("eval_") and key != "eval_loss":
                values.append(pct(v) if arm_label != "Unicode Dense" else "N/A")
            else:
                values.append(fmt(v))
        lines.append(f"| {label} | " + " | ".join(values) + " |")

    lines += [
        "",
        "## 判定",
        "",
        "- H1 MoE vs Dense matched-params：比较 next-code 与 struct；",
        "- H2 CNBE Dense vs Unicode Dense：比较 next-code / next-token；",
        "- 任一假设不通过，按设计文档执行停止/调整动作。",
        "",
    ]
    out = args.output_dir / "comparison_table.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print("saved:", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
