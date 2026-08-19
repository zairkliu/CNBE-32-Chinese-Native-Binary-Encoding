#!/usr/bin/env python3
"""Package a CNBE-MoE training round and generate a detailed knowledge report."""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

PREVIOUS_L20 = {
    "round": "L20-128",
    "eval_loss": 6.5821259756709525,
    "eval_accuracy": 0.1911648967427804,
    "eval_radix_accuracy": 0.20234322531900603,
    "eval_struct_accuracy": 0.34139418233713903,
    "eval_strokes_accuracy": 0.24380876427132303,
    "expert_gini": 0.2070654034614563,
    "params": 289920031,
}

PERCENT_KEYS = {
    "eval_accuracy",
    "eval_radix_accuracy",
    "eval_struct_accuracy",
    "eval_strokes_accuracy",
    "eval_radix_head_accuracy",
    "eval_struct_head_accuracy",
    "eval_strokes_head_accuracy",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.2f} {unit}" if unit != "B" else f"{n} B"
        n /= 1024
    return f"{n:.2f} TB"


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default="/scnet_upload_package_MERGED_DCU")
    ap.add_argument("--output-dir", default="")
    ap.add_argument("--round-name", default="round2-dcu128")
    ap.add_argument("--include-checkpoint", dest="include_checkpoint", action="store_true", default=True)
    ap.add_argument("--no-checkpoint", dest="include_checkpoint", action="store_false")
    ap.add_argument("--gzip", action="store_true")
    ap.add_argument("--skip-hash", action="store_true")
    args = ap.parse_args()

    root = Path(args.root)
    out = Path(args.output_dir) if args.output_dir else root / "output" / "package_round2_dcu128"
    out.mkdir(parents=True, exist_ok=True)

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    files = {
        "train_metrics.json": root / "output" / "train_metrics.json",
        "eval_metrics.json": root / "output" / "eval_metrics.json",
        "smoke_metrics.json": root / "output" / "smoke_metrics.json",
        "mapping_128.json": root / "output" / "mappings" / "mapping_128.json",
        "config.yaml": root / "code" / "config" / "scnet_moe_config_merged_dcu2.yaml",
        "train_distributed.py": root / "code" / "scripts" / "train_distributed.py",
        "eval.py": root / "code" / "scripts" / "eval.py",
    }
    if args.include_checkpoint:
        files["final.pt"] = root / "output" / "checkpoints" / "final.pt"

    inventory = []
    missing = []
    for name, src in files.items():
        if not src.exists():
            missing.append(str(src))
            continue
        dst = out / "artifacts" / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        info = {
            "name": name,
            "path": str(src),
            "size_bytes": src.stat().st_size,
            "size_human": human_size(src.stat().st_size),
            "sha256": sha256(src) if not args.skip_hash else None,
        }
        inventory.append(info)
        print("packed", name, info["size_human"], flush=True)

    train_metrics = load_json(root / "output" / "train_metrics.json")
    eval_metrics = load_json(root / "output" / "eval_metrics.json")
    metrics = eval_metrics or train_metrics
    config_path = root / "code" / "config" / "scnet_moe_config_merged_dcu2.yaml"
    try:
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        config = {}

    timeline = [
        ("2026-08-11 01:11", "正式训练启动，grad_accum=1，双卡 DCU BW"),
        ("2026-08-11 19:34", "训练到达 125,975 步，末尾 NCCL barrier 超时"),
        ("2026-08-11 20:03", "补丁后从 last.pt（step 120,000）续训"),
        ("2026-08-11 21:00", "续训完成 step 125,976，保存 final.pt"),
        ("2026-08-11 22:25", "eval.py 全量评估完成，写出 eval_metrics.json"),
    ]

    conclusions = [
        "5.44 亿 token + 626M 参数模型使结构字段准确率显著提升，struct 解码准确率 44.07%，head 准确率 47.10%，已超过 40% 目标。",
        "next-code 23.56%、radix 24.09%、strokes 26.04%，均高于 L20 128 专家第一轮。",
        "expert_gini 0.2971 高于上一轮 0.2071，路由集中度升高，下一轮必须优先做路由均衡。",
        "训练尾部 NCCL barrier 超时问题已通过续训 + final.pt 强制保存解决；后续训练需保留最终 checkpoint 保存逻辑。",
        "本轮与 L20 参数规模不同，结论不能单独归因于 MoE，必须补同参数 Dense 对照。",
    ]

    next_round = [
        "以 final.pt 作为下一轮初始权重，保持同一 eval split（27,000,000 token）以便严格对比。",
        "先跑同参数 Dense 对照，验证 MoE 相对收益。",
        "提高 balance_weight 或改用 learned router，目标 expert_gini <= 0.20。",
        "路由均衡达标后再评估 256 专家。",
        "继续使用本脚本打包下一轮，形成可复现实验档案。",
    ]

    report_lines = [
        f"# CNBE-MoE {args.round_name} 训练结果与知识报告",
        "",
        f"生成时间：{now}",
        f"包目录：{out}",
        "",
        "## 一、训练环境",
        "",
        "| 项 | 值 |",
        "|---|---|",
        "| 硬件 | 异构加速卡 BW x 2（DCU） |",
        "| 镜像 | jupyterlab-pytorch:2.9.0-ubuntu22.04-dtk26.04-py3.11-devel |",
        "| 模型 | d_model=1024, d_ff=2048, 12 层, 16 头 |",
        "| MoE | 128 专家, Top-2, 三字段硬路由 |",
        "| 数据 | 5.44 亿 token, vocab=17,474 |",
        "| 总步数 | 125,976 |",
        "| final checkpoint | output/checkpoints/final.pt |",
        "",
        "## 二、训练时间线",
        "",
        "| 时间 | 事件 |",
        "|---|---|",
    ]
    for ts, event in timeline:
        report_lines.append(f"| {ts} | {event} |")

    report_lines += [
        "",
        "## 三、最终评估指标",
        "",
        "| 指标 | 值 |",
        "|---|---:|",
    ]
    metric_keys = [
        ("eval_loss", "eval_loss"),
        ("eval_accuracy", "next-code"),
        ("eval_radix_accuracy", "radix"),
        ("eval_struct_accuracy", "struct"),
        ("eval_strokes_accuracy", "strokes"),
        ("eval_radix_head_accuracy", "radix head"),
        ("eval_struct_head_accuracy", "struct head"),
        ("eval_strokes_head_accuracy", "strokes head"),
        ("expert_gini", "expert_gini"),
        ("params", "params"),
    ]
    for key, label in metric_keys:
        if key in metrics:
            value = metrics[key]
            if key in PERCENT_KEYS and isinstance(value, float):
                value = f"{value * 100:.2f}%"
            if isinstance(value, float):
                value = f"{value:.6f}"
            report_lines.append(f"| {label} | {value} |")

    report_lines += [
        "",
        "## 四、与 L20 128 第一轮对比",
        "",
        "| 指标 | 本轮 DCU 128 | L20 128 |",
        "|---|---:|---:|",
    ]
    compare_keys = [
        ("eval_loss", "eval_loss"),
        ("eval_accuracy", "eval_accuracy"),
        ("eval_radix_accuracy", "eval_radix_accuracy"),
        ("eval_struct_accuracy", "eval_struct_accuracy"),
        ("eval_strokes_accuracy", "eval_strokes_accuracy"),
        ("expert_gini", "expert_gini"),
        ("params", "params"),
    ]
    for key, prev_key in compare_keys:
        if key in metrics:
            cur = metrics[key]
            prev = PREVIOUS_L20[prev_key]
            if key in PERCENT_KEYS:
                cur_s = f"{cur * 100:.2f}%" if isinstance(cur, float) else str(cur)
                prev_s = f"{prev * 100:.2f}%" if isinstance(prev, float) else str(prev)
            else:
                cur_s = f"{cur:.6f}" if isinstance(cur, float) else str(cur)
                prev_s = f"{prev:.6f}" if isinstance(prev, float) else str(prev)
            report_lines.append(f"| {key} | {cur_s} | {prev_s} |")

    report_lines += [
        "",
        "## 五、本轮知识沉淀",
        "",
    ]
    report_lines += [f"{i}. {item}" for i, item in enumerate(conclusions, 1)]
    report_lines += [
        "",
        "## 六、下一轮训练要求",
        "",
    ]
    report_lines += [f"{i}. {item}" for i, item in enumerate(next_round, 1)]
    report_lines += [
        "",
        "## 七、文件清单",
        "",
        "| 文件 | 大小 | SHA256 |",
        "|---|---:|---|",
    ]
    for info in inventory:
        digest = info["sha256"] or "-"
        report_lines.append(f"| {info['name']} | {info['size_human']} | {digest} |")
    report_lines.append("")
    report = "\n".join(report_lines)

    knowledge = {
        "round": args.round_name,
        "generated_at": now,
        "environment": "DCU BW x2",
        "config": config,
        "train_metrics": train_metrics,
        "eval_metrics": eval_metrics,
        "previous_round": PREVIOUS_L20,
        "timeline": [{"time": t, "event": e} for t, e in timeline],
        "conclusions": conclusions,
        "next_round_requirements": next_round,
        "files": inventory,
        "missing_files": missing,
    }

    (out / "ROUND_REPORT.md").write_text(report, encoding="utf-8")
    (out / "ROUND_KNOWLEDGE.json").write_text(
        json.dumps(knowledge, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    log_lines = [
        f"# CNBE-MoE {args.round_name} 训练日志",
        "",
        f"生成时间：{now}",
        "",
        "## 时间线",
        "",
    ]
    log_lines += [f"- {t}: {e}" for t, e in timeline]
    log_lines.append("")
    (out / "TRAINING_LOG.md").write_text("\n".join(log_lines), encoding="utf-8")

    tar_name = f"{args.round_name}_{now[:10]}.tar" + (".gz" if args.gzip else "")
    tar_path = out.parent / tar_name
    cmd = ["tar", "-cf" if not args.gzip else "-czf", str(tar_path), "-C", str(out), "."]
    subprocess.run(cmd, check=True)
    print("report:", out / "ROUND_REPORT.md", flush=True)
    print("knowledge:", out / "ROUND_KNOWLEDGE.json", flush=True)
    print("package:", tar_path, flush=True)
    print("missing:", missing, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
