#!/usr/bin/env python3
"""Build the merged CNBE-MoE DCU upload package for SCNet.

Packs existing training code, merged .cnbe data, clean source text, merged
vocab/mappings, and merged corpus configs into one tar.gz.
"""

from __future__ import annotations

import json
import shutil
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "2026-08-08_cnbe_moe_scnet"
DCU_SRC = EXP / "scnet_upload_package_DCU"
NEW_CONFIGS = EXP / "config_src"
STARTUP = EXP / "scnet_startup_dcu2.sh"

WORK = Path(r"D:\训练语料")
MERGED_DATA = WORK / "出版物训练_cnbe_v2"
EXISTING_DATA = DCU_SRC / "data"
MERGED_ASSETS = WORK / "corpus_assets_merged_v2"
CLEAN_DIR = WORK / "出版物训练_clean_v2"
ENCODE_REPORT = WORK / "出版物训练_cnbe_v2" / "encode_report.json"
CORPUS_MANIFEST = MERGED_ASSETS / "corpus_manifest.json"

DST = WORK / "scnet_upload_package_MERGED_DCU_v2"
TAR = WORK / "scnet_upload_package_MERGED_DCU_v2.tar.gz"

IMAGE = "jupyterlab-pytorch:2.9.0-ubuntu22.04-dtk26.04-py3.11-devel"
RESOURCE = "113 组 hx1hgbwnormal"


def _ensure_within(parent: Path, child: Path) -> None:
    if not str(child.resolve()).startswith(str(parent.resolve())):
        raise RuntimeError(f"refusing to touch {child} outside {parent}")


def main() -> int:
    if not DCU_SRC.exists():
        print("missing DCU package:", DCU_SRC)
        return 1
    if not MERGED_DATA.exists() or not MERGED_ASSETS.exists():
        print("missing merged data/assets")
        return 1
    if not ENCODE_REPORT.exists():
        print("missing encode report:", ENCODE_REPORT)
        return 1

    _ensure_within(WORK, DST)
    if DST.exists():
        shutil.rmtree(DST)
    print("copying base DCU package...")
    shutil.copytree(DCU_SRC, DST)

    # Replace data with merged streams.
    data_dir = DST / "data"
    _ensure_within(DST, data_dir)
    if data_dir.exists():
        shutil.rmtree(data_dir)
    data_dir.mkdir(parents=True)
    for path in sorted(EXISTING_DATA.glob("*.cnbe")):
        shutil.copy2(path, data_dir / path.name)
    cnbe_files = sorted(MERGED_DATA.glob("*.cnbe"))
    for path in cnbe_files:
        shutil.copy2(path, data_dir / path.name)
    print("data files:", len(cnbe_files) + len(list(EXISTING_DATA.glob("*.cnbe"))))

    # Replace assets with merged vocab/mappings.
    assets_dir = DST / "assets"
    _ensure_within(DST, assets_dir)
    if assets_dir.exists():
        shutil.rmtree(assets_dir)
    assets_dir.mkdir(parents=True)
    for path in sorted(MERGED_ASSETS.glob("*.json")):
        shutil.copy2(path, assets_dir / path.name)

    # Replace data_src with existing 7 chars.txt + selected clean texts.
    src_dir = DST / "data_src"
    _ensure_within(DST, src_dir)
    if src_dir.exists():
        shutil.rmtree(src_dir)
    src_dir.mkdir(parents=True)
    for path in sorted((DCU_SRC / "data_src").glob("*.txt")):
        shutil.copy2(path, src_dir / path.name)
    encode_report = json.loads(ENCODE_REPORT.read_text(encoding="utf-8"))
    clean_paths = []
    for entry in encode_report["files"]:
        source = Path(entry["source"])
        if source.exists():
            shutil.copy2(source, src_dir / source.name)
            clean_paths.append(source.name)
    print("source text files:", len(cnbe_files), "clean texts:", len(clean_paths))

    # Add merged configs.
    config_dir = DST / "config"
    config_dir.mkdir(exist_ok=True)
    merged_configs = []
    config_paths = {
        p.name: p
        for p in list(NEW_CONFIGS.glob("scnet_moe_config_merged_*.yaml"))
        + list(NEW_CONFIGS.glob("scnet_moe_config_merged_*_light.yaml"))
    }
    for path in sorted(config_paths.values(), key=lambda p: p.name):
        shutil.copy2(path, config_dir / path.name)
        shutil.copy2(path, DST / "code" / "config" / path.name)
        merged_configs.append(path.name)

    shutil.copy2(STARTUP, DST / "scnet_startup_dcu2.sh")
    shutil.copy2(STARTUP, DST / "code" / "scnet_startup_dcu2.sh")

    corpus = json.loads(CORPUS_MANIFEST.read_text(encoding="utf-8"))
    manifest = {
        "package": "scnet_upload_package_MERGED_DCU_v2",
        "variant": "dcu_merged_publications_v2",
        "image": IMAGE,
        "resource_group": RESOURCE,
        "scnet_form": {
            "accelerator": "异构加速卡BW x 2",
            "gpu_memory_gb": 256,
            "cpu_cores": 30,
            "ram_gb": 118,
            "python": "3.11",
            "pytorch": "2.9.0",
            "dtk": "26.04",
            "os": "Ubuntu 22.04",
            "dev_tool": "JupyterLab",
            "base_image": IMAGE,
        },
        "corpus": {
            "total_tokens": corpus["total_tokens"],
            "train_tokens": corpus["train_tokens"],
            "eval_tokens": corpus["eval_tokens"],
            "unique_codes": corpus["unique_codes"],
            "cnbe_files": len(cnbe_files),
            "clean_text_files": len(clean_paths),
        },
        "configs": merged_configs,
        "startup": "scnet_startup_dcu2.sh",
        "default_config": "scnet_moe_config_merged_dcu2.yaml",
    }
    (DST / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("writing tar.gz...")
    if TAR.exists():
        TAR.unlink()
    with tarfile.open(TAR, "w:gz", compresslevel=1) as tf:
        tf.add(DST, arcname="scnet_upload_package_MERGED_DCU_v2")

    print("package dir:", DST)
    print("tar:", TAR, TAR.stat().st_size)
    return 0


if __name__ == "__main__":
    sys.exit(main())
