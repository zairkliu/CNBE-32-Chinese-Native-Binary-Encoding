#!/usr/bin/env python3
"""Export a CNBE-MoE training round as core/normal/full three tiers."""

from __future__ import annotations

import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np


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


def copy_or_link(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        return
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def build_vocab(root: Path) -> Path:
    candidates = [
        root / "output" / "assets" / "vocab_merged.json",
        root / "output" / "vocab.json",
        root / "output" / "assets" / "vocab.json",
    ]
    for cand in candidates:
        if cand.exists():
            print("using vocab:", cand, flush=True)
            return cand

    print("building vocab from .cnbe files (may take a few minutes)", flush=True)
    chunks = []
    total = 0
    for p in sorted((root / "data").glob("*.cnbe")):
        codes = np.frombuffer(p.read_bytes(), dtype=">u4")
        chunks.append(codes)
        total += len(codes)
        print("loaded", p.name, f"{len(codes):,}", flush=True)
    codes = np.concatenate(chunks) if chunks else np.array([], dtype=np.uint32)
    unique = np.unique(codes)
    vocab = {str(int(c)): i for i, c in enumerate(unique)}
    out = root / "output" / "assets" / "vocab_merged.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(vocab, ensure_ascii=False), encoding="utf-8")
    print("saved vocab:", out, "unique", len(vocab), flush=True)
    return out


def collect_file_info(paths: dict[str, Path], skip_hash: bool = False) -> list[dict]:
    info = []
    for name, path in paths.items():
        if not path.exists():
            continue
        info.append(
            {
                "name": name,
                "path": str(path),
                "size_bytes": path.stat().st_size,
                "size_human": human_size(path.stat().st_size),
                "sha256": None if skip_hash else _sha256(path),
            }
        )
    return info


def _sha256(path: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default="/scnet_upload_package_MERGED_DCU")
    ap.add_argument("--target", default="")
    ap.add_argument("--gzip", action="store_true")
    ap.add_argument("--skip-hash", action="store_true")
    args = ap.parse_args()

    root = Path(args.root)
    target = Path(args.target) if args.target else root / "8-11_0.544Btest"
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    final_pt = root / "output" / "checkpoints" / "final.pt"
    last_pt = root / "output" / "checkpoints" / "last.pt"
    config_yaml = root / "code" / "config" / "scnet_moe_config_merged_dcu2.yaml"
    mapping = root / "output" / "mappings" / "mapping_128.json"
    train_metrics = root / "output" / "train_metrics.json"
    eval_metrics = root / "output" / "eval_metrics.json"
    smoke_metrics = root / "output" / "smoke_metrics.json"
    training_log = next(
        (
            p
            for p in [
                root / "output" / "training.log",
                root / "output" / "logs" / "training.log",
                root / "training.log",
            ]
            if p.exists()
        ),
        None,
    )
    data_manifest = next(
        (
            p
            for p in [
                root / "data" / "corpus_manifest.json",
                root / "output" / "corpus_manifest.json",
                root / "corpus_manifest.json",
            ]
            if p.exists()
        ),
        None,
    )

    if not final_pt.exists():
        print("final.pt not found:", final_pt, flush=True)
        return 2
    vocab = build_vocab(root)

    core_dir = target / "core"
    normal_dir = target / "normal"
    full_dir = target / "full"
    for d in (core_dir, normal_dir, full_dir):
        d.mkdir(parents=True, exist_ok=True)

    # Core: direct next-run inputs.
    copy_or_link(final_pt, core_dir / "final.pt")
    shutil.copy2(config_yaml, core_dir / "config.yaml")
    shutil.copy2(vocab, core_dir / "vocab.json")
    if mapping.exists():
        shutil.copy2(mapping, core_dir / "mapping_128.json")
    ckpt_files = sorted((root / "output" / "checkpoints").glob("*.pt"))
    ckpt_list = [p.name for p in ckpt_files]
    (core_dir / "checkpoint_list.txt").write_text(
        "\n".join(ckpt_list) + "\n", encoding="utf-8"
    )

    # Normal: core + metrics + log.
    for p in core_dir.iterdir():
        copy_or_link(p, normal_dir / p.name)
    for src, name in [
        (train_metrics, "train_metrics.json"),
        (eval_metrics, "eval_metrics.json"),
        (smoke_metrics, "smoke_metrics.json"),
    ]:
        if src.exists():
            shutil.copy2(src, normal_dir / name)
    if training_log:
        shutil.copy2(training_log, normal_dir / "training.log")

    # Full: normal + code + all existing checkpoints + data index.
    for p in normal_dir.iterdir():
        copy_or_link(p, full_dir / p.name)
    if (root / "code").exists():
        shutil.copytree(root / "code", full_dir / "code", dirs_exist_ok=True)
    if data_manifest:
        shutil.copy2(data_manifest, full_dir / "data_manifest.json")
    full_ckpts = full_dir / "checkpoints_all"
    full_ckpts.mkdir(parents=True, exist_ok=True)
    for p in ckpt_files:
        copy_or_link(p, full_ckpts / p.name)

    system_info = full_dir / "system_info.txt"
    lines = [f"generated_at: {now}", f"host: {os.uname().nodename if hasattr(os, 'uname') else 'unknown'}"]
    lines += [f"total_ram_bytes: {os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES') if hasattr(os, 'sysconf') else 'unknown'}"]
    system_info.write_text("\n".join(lines) + "\n", encoding="utf-8")

    metrics = eval_metrics if eval_metrics.exists() else train_metrics
    m = load_json(metrics)
    readme = f"""# CNBE-MoE 训练结果 - 2026-08-11 5.44B Token

生成时间：{now}

## 训练概况
- 语料：5.44 亿 Token，1244 个 .cnbe 文件
- 模型：d_model=1024，12 层，128 专家，Top-2 路由
- 步数：125,976
- 最终 eval_loss：{m.get('eval_loss', 'N/A')}
- 最终 next-code：{m.get('eval_accuracy', 'N/A')}
- 最终 struct：{m.get('eval_struct_accuracy', 'N/A')}
- expert_gini：{m.get('expert_gini', 'N/A')}

## 三档版本说明
| 版本 | 用途 | 包含内容 |
|---|---|---|
| core/ | 续训/微调起点 | final.pt + config + vocab + mapping |
| normal/ | 训练记录查看 | core + metrics + log |
| full/ | 审计归档 | normal + code + 全部现有检查点 + data manifest |

## 当前实际检查点
{chr(10).join('- ' + n for n in ckpt_list)}

注意：当前训练脚本每 1000 步覆盖 last.pt，因此不存在 step_*.pt 序列；
完整中间状态无法恢复，下一步训练请保留本导出目录并增加分步 checkpoint 保存。
"""
    (target / "README.md").write_text(readme, encoding="utf-8")

    manifest = {
        "generated_at": now,
        "target": str(target),
        "checkpoints": ckpt_list,
        "vocab": str(vocab),
        "files": collect_file_info(
            {
                "final.pt": final_pt,
                "last.pt": last_pt,
                "config.yaml": config_yaml,
                "mapping_128.json": mapping,
                "train_metrics.json": train_metrics,
                "eval_metrics.json": eval_metrics,
            },
            skip_hash=args.skip_hash,
        ),
    }
    (target / "MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    for tier in ("core", "normal", "full"):
        suffix = ".gz" if args.gzip else ""
        tar = target.parent / (f"8-11_0.544Btest_{tier}.tar" + suffix)
        cmd = ["tar", "-cf" if not args.gzip else "-czf", str(tar), "-C", str(target), tier]
        subprocess.run(cmd, check=True)
        print(tier, "tar:", tar, human_size(tar.stat().st_size), flush=True)

    print("target:", target, flush=True)
    print("README:", target / "README.md", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
