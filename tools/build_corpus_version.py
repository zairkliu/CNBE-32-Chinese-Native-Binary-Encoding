#!/usr/bin/env python3
"""One-shot corpus build pipeline: clean -> encode -> subsets -> merge."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = Path(__file__).resolve().parent
EXP = ROOT / "experiments" / "2026-08-08_cnbe_moe_scnet"


def run(args: list[str]) -> None:
    print("RUN:", " ".join(str(a) for a in args), flush=True)
    subprocess.run([sys.executable, *map(str, args)], check=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--md-dir", type=Path, required=True, help="new publication MD directory")
    ap.add_argument("--version", required=True, help="e.g. v3")
    ap.add_argument("--work-dir", type=Path, required=True, help="e.g. D:\\训练语料")
    ap.add_argument("--db", type=Path, default=ROOT / "data" / "cnbe32.db")
    ap.add_argument("--existing-data-dir", type=Path)
    ap.add_argument("--skip-dedup", action="store_true")
    args = ap.parse_args()

    work = args.work_dir
    clean_dir = work / f"出版物训练_clean_{args.version}"
    cnbe_dir = work / f"出版物训练_cnbe_{args.version}"
    subsets_dir = work / f"corpus_subsets_{args.version}"
    assets_dir = work / f"corpus_assets_merged_{args.version}"
    clean_manifest = clean_dir / "manifest.json"
    encode_report = cnbe_dir / "encode_report.json"

    run(
        [
            TOOLS / "clean_publication_markdown.py",
            "--input", args.md_dir,
            "--output-dir", clean_dir,
            "--manifest", clean_manifest,
        ]
    )
    run(
        [
            TOOLS / "batch_encode_publications.py",
            "--manifest", clean_manifest,
            "--db", args.db,
            "--output-dir", cnbe_dir,
            "--report", encode_report,
        ]
    )
    run(
        [
            TOOLS / "build_corpus_subsets.py",
            "--clean-manifest", clean_manifest,
            "--encode-report", encode_report,
            "--output-dir", subsets_dir,
        ]
    )
    core_subset = subsets_dir / "core_chinese_subset.json"
    run(
        [
            TOOLS / "compute_cjk_coverage.py",
            "--subset", core_subset,
            "--db", args.db,
            "--output", subsets_dir / "core_cjk_coverage.json",
        ]
    )
    if not args.skip_dedup:
        run(
            [
                TOOLS / "dedup_corpus_minhash.py",
                "--subset", core_subset,
                "--output", subsets_dir / "core_minhash_dedup.json",
            ]
        )

    existing_dir = args.existing_data_dir or (EXP / "scnet_upload_package" / "data")
    run(
        [
            EXP / "scripts_src" / "merge_publication_corpus.py",
            "--existing-dir", existing_dir,
            "--new-dir", cnbe_dir,
            "--output-dir", assets_dir,
            "--experts", "128", "256",
        ]
    )

    print("\n== corpus version ready ==")
    print("clean:", clean_dir)
    print("cnbe:", cnbe_dir)
    print("subsets:", subsets_dir)
    print("assets:", assets_dir)
    print("next: update prepare_merged_dcu_package.py paths or package manually")
    return 0


if __name__ == "__main__":
    sys.exit(main())
