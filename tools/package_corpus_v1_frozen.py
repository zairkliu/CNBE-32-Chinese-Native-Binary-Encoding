#!/usr/bin/env python3
"""Build the frozen corpus v1 SCNet upload package."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import tarfile
import time
from pathlib import Path

CORPUS = Path(r"D:\1 训练语料\CNBE中文出版物合并去重_v1")
FROZEN = CORPUS / "frozen"
WORK = Path(r"D:\1 训练语料")
PKG = WORK / "scnet_upload_package_CORPUS_V1_FROZEN"
TAR = WORK / "scnet_upload_package_CORPUS_V1_FROZEN.tar.gz"
EXP_SCRIPTS = (
    Path(r"C:\Users\zairk\Documents\Codex\2026-07-27\https-github-com-zairkliu-cnbe-32\repo")
    / "experiments"
    / "2026-08-08_cnbe_moe_scnet"
    / "scnet_cnbe_moe_bundle"
    / "scripts"
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        dst.unlink()
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def main() -> int:
    if PKG.exists():
        shutil.rmtree(PKG)
    PKG.mkdir(parents=True)

    for split in ("train", "eval", "val"):
        copy_file(FROZEN / "data" / f"{split}.cnbe", PKG / "data" / f"{split}.cnbe")
    for name in ("vocab.json", "vocab_meta.json", "mapping_128.json"):
        copy_file(FROZEN / "assets" / name, PKG / "assets" / name)
    for name in ("code0_strategy.json", "scnet_moe_config_corpus_v1_frozen.yaml"):
        copy_file(FROZEN / "config" / name, PKG / "config" / name)

    manifest_dir = PKG / "manifest"
    copy_file(FROZEN / "canonical_manifest.json", manifest_dir / "canonical_manifest.json")
    for name in ("corpus_manifest.json", "dedup_report.json", "quality_audit.json"):
        copy_file(CORPUS / name, manifest_dir / name)
    for name in (
        "quality_report.json",
        "residual_audit_v2.json",
        "residual_fix_report_v2.json",
        "residual_fix_dryrun_v2.json",
    ):
        copy_file(CORPUS / "quality_check" / name, manifest_dir / name)

    copy_file(FROZEN / "scripts" / "verify_frozen.py", PKG / "scripts" / "verify_frozen.py")
    for name in ("train_distributed.py", "eval.py"):
        src = EXP_SCRIPTS / name
        if src.exists():
            copy_file(src, PKG / "scripts" / name)
    copy_file(FROZEN / "README.md", PKG / "README.md")

    data_hashes = {}
    for split in ("train", "eval", "val"):
        path = PKG / "data" / f"{split}.cnbe"
        data_hashes[f"{split}.cnbe"] = sha256(path)
        print(split, path.stat().st_size, flush=True)

    payload = {
        "package": "scnet_upload_package_CORPUS_V1_FROZEN",
        "corpus": "CNBE中文出版物合并去重_v1",
        "frozen_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "data_sha256": data_hashes,
        "assets": [
            "assets/vocab.json",
            "assets/vocab_meta.json",
            "assets/mapping_128.json",
        ],
        "config": [
            "config/code0_strategy.json",
            "config/scnet_moe_config_corpus_v1_frozen.yaml",
        ],
        "manifests": [
            "manifest/canonical_manifest.json",
            "manifest/corpus_manifest.json",
            "manifest/quality_report.json",
            "manifest/residual_audit_v2.json",
        ],
        "scripts": ["scripts/verify_frozen.py"],
    }
    (PKG / "MANIFEST.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("writing tar.gz (compresslevel=1)...", flush=True)
    if TAR.exists():
        TAR.unlink()
    with tarfile.open(TAR, "w:gz", compresslevel=1) as tf:
        tf.add(PKG, arcname=PKG.name)
    print("tar:", TAR, TAR.stat().st_size)
    return 0


if __name__ == "__main__":
    sys.exit(main())
