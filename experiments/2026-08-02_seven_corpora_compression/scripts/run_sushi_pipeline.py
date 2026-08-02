# -*- coding: utf-8 -*-
"""蘇文忠公詩集 CNBE 全链路复现：编码、压缩、Volume、MoE。"""

from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "guji-ocr-corrector" / "data" / "cnbe32.db"


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=Path(__file__).parent, check=True)


def make_meta(out_dir: Path) -> None:
    chars = (out_dir / "sushi.chars.txt").read_text(encoding="utf-8")
    conn = sqlite3.connect(DB)
    rows = conn.execute("SELECT char FROM cnbe32 WHERE cnbe IS NOT NULL").fetchall()
    conn.close()
    known = {r[0] for r in rows}
    unknown = sum(1 for ch in chars if ch not in known)
    total = len(chars)
    meta = {
        "total_chars": total,
        "unique_chars": len(set(chars)),
        "coverage": round(1 - unknown / total, 6) if total else 1.0,
        "template_coverage": 0.0,
    }
    (out_dir / "compress_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("meta:", meta)


def main() -> int:
    parser = argparse.ArgumentParser(description="蘇文忠公詩集 CNBE 全链路")
    parser.add_argument("--skip-api", action="store_true")
    args = parser.parse_args()

    out = Path("outputs").resolve()
    scripts = {
        "encode": ROOT / "cnbe_compression_experiment" / "2_cnbe_encode.py",
        "templates": ROOT / "cnbe_compression_experiment" / "3_build_templates.py",
        "compress": ROOT / "cnbe_compression_experiment" / "4_predictive_compress.py",
        "bench": ROOT / "cnbe_compression_experiment" / "5_benchmark.py",
        "vol_build": ROOT / "cnbe_volume" / "build_cnbe_volume.py",
        "vol_bench": ROOT / "cnbe_volume" / "benchmark_volume.py",
        "moe16": ROOT / "cnbe_moe" / "step1_build_mapping.py",
        "moe64": ROOT / "cnbe_moe" / "step1_build_mapping.py",
        "routing": ROOT / "cnbe_moe" / "step3_benchmark.py",
        "quality": ROOT / "cnbe_moe" / "step4_downstream.py",
    }

    run([sys.executable, str(scripts["encode"]), "outputs/sushi.chars.txt", "outputs/sushi.cnbe", "--db", str(DB)])
    run([sys.executable, str(scripts["templates"]), "outputs/sushi.cnbe", "outputs/templates.json", "--top-k", "64"])
    run([sys.executable, str(scripts["compress"]), "outputs/sushi.cnbe", "outputs/templates.json", "outputs/compressed", "--level", "6"])
    make_meta(out)
    total_chars = len((out / "sushi.chars.txt").read_text(encoding="utf-8"))
    seek_pos = min(100000, max(1000, total_chars // 2))
    train_tokens = min(200000, total_chars)
    test_tokens = min(50000, total_chars)
    templates = json.loads((out / "templates.json").read_text(encoding="utf-8"))
    coverage = sum(v["freq"] for v in templates.values()) / (out / "sushi.chars.txt").read_text(encoding="utf-8").__len__()
    run(
        [
            sys.executable,
            str(scripts["bench"]),
            "outputs/sushi.chars.txt",
            "outputs/sushi.cnbe",
            "--delta",
            "outputs/compressed_delta.zlib",
            "--template",
            "outputs/compressed_template.zlib",
            "--raw-zlib",
            "outputs/compressed_raw.zlib",
            "--report",
            "outputs/compression_report.md",
            "--meta",
            "outputs/compress_meta.json",
            "--template-coverage",
            f"{coverage:.6f}",
        ]
    )
    run(
        [
            sys.executable,
            str(scripts["vol_build"]),
            "--input",
            "outputs/sushi.cnbe",
            "--output",
            "outputs/sushi_4096.cnbev",
            "--page-size",
            "4096",
        ]
    )
    run(
        [
            sys.executable,
            str(scripts["vol_bench"]),
            "--volume",
            "outputs/sushi_4096.cnbev",
            "--text",
            "outputs/sushi.chars.txt",
            "--db",
            str(DB),
            "--report",
            "outputs/volume_report.md",
            "--label",
            "蘇文忠公詩集（宋集珍本丛刊）132 页",
            "--pos",
            str(seek_pos),
        ]
    )
    run(
        [
            sys.executable,
            str(scripts["moe16"]),
            "--cnbe",
            "outputs/sushi.cnbe",
            "--output",
            "outputs/struct_expert_map_16.json",
            "--num-experts",
            "16",
        ]
    )
    run(
        [
            sys.executable,
            str(scripts["moe64"]),
            "--cnbe",
            "outputs/sushi.cnbe",
            "--output",
            "outputs/struct_expert_map_64.json",
            "--num-experts",
            "64",
        ]
    )
    run(
        [
            sys.executable,
            str(scripts["routing"]),
            "--cnbe",
            "outputs/sushi.cnbe",
            "--map",
            "outputs/struct_expert_map_16.json",
            "--report",
            "outputs/routing_benchmark.json",
        ]
    )
    run(
        [
            sys.executable,
            str(scripts["quality"]),
            "--cnbe",
            "outputs/sushi.cnbe",
            "--map",
            "outputs/struct_expert_map_16.json",
            "--report",
            "outputs/routing_quality.json",
            "--train-tokens",
            str(train_tokens),
            "--test-tokens",
            str(test_tokens),
        ]
    )
    print("本地全链路完成，产物在 outputs/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
