#!/usr/bin/env python3
"""Search and package the complete v1 MoE-128 / Dense / Unicode experiment."""

from __future__ import annotations

import os
import shutil
import zipfile
from pathlib import Path

ROOT_OUT = Path("/root/v1_control_complete_2026-08-12")
ZIP_OUT = Path("/root/v1_control_complete_2026-08-12.zip")
SEARCH_ROOTS = [
    Path("/scnet_upload_package_DCU"),
    Path("/scnet_upload_package_MERGED_DCU"),
    Path("/root"),
]


def find_first(names: list[str], prefer: list[str] | None = None) -> Path | None:
    hits: list[Path] = []
    for base in SEARCH_ROOTS:
        if not base.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in ("__pycache__", ".ipynb_checkpoints")]
            for name in names:
                if name in filenames:
                    hits.append(Path(dirpath) / name)
    if not hits:
        return None
    if prefer:
        for pref in prefer:
            for hit in hits:
                if pref in str(hit):
                    return hit
    return hits[0]


def find_ckpt(arm: str, prefer: list[str]) -> Path | None:
    hits: list[Path] = []
    for base in SEARCH_ROOTS:
        if not base.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in ("__pycache__", ".ipynb_checkpoints")]
            if "final.pt" in filenames and Path(dirpath).name == arm and "checkpoints" in dirpath:
                hits.append(Path(dirpath) / "final.pt")
    if not hits:
        return None
    for pref in prefer:
        for hit in hits:
            if pref in str(hit):
                return hit
    return hits[0]


def main() -> int:
    if ROOT_OUT.exists():
        shutil.rmtree(ROOT_OUT)
    dirs = [
        ROOT_OUT / "moe128",
        ROOT_OUT / "dense",
        ROOT_OUT / "unicode",
        ROOT_OUT / "artifacts",
        ROOT_OUT / "configs",
        ROOT_OUT / "code",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    dc = ["scnet_upload_package_DCU"]
    mg = ["scnet_upload_package_MERGED_DCU"]

    pairs = [
        (["moe128_metrics.json", "moe128_eval_metrics.json"], ROOT_OUT / "moe128", dc),
        (["dense_metrics.json", "dense_eval_metrics.json"], ROOT_OUT / "dense", dc),
        (["unicode_metrics.json", "unicode_eval_metrics.json"], ROOT_OUT / "unicode", mg),
        (["mapping_128.json"], ROOT_OUT / "artifacts", dc),
        (["vocab_merged.json"], ROOT_OUT / "artifacts", dc),
        (["comparison_table.md"], ROOT_OUT / "artifacts", dc),
        (["README_SCIENCE.md"], ROOT_OUT, dc),
        (["train_distributed.py"], ROOT_OUT / "code", dc),
        (["eval.py"], ROOT_OUT / "code", dc),
    ]
    for names, dst, prefer in pairs:
        src = find_first(names, prefer)
        if src:
            shutil.copy2(src, dst / src.name)
            print("found", src, flush=True)
        else:
            print("MISSING", names, flush=True)

    for arm, prefer in [("moe128", dc), ("dense", dc), ("unicode", mg)]:
        src = find_ckpt(arm, prefer)
        if src:
            shutil.copy2(src, ROOT_OUT / arm / "final.pt")
            print("found ckpt", src, flush=True)
        else:
            print("MISSING checkpoint", arm, flush=True)

    cfg_src = find_first(["v1_moe128_dcu2.yaml", "v1_dense_dcu2.yaml", "v1_unicode_dcu2.yaml", "v1_dense_matched_dcu2.yaml"], dc)
    if cfg_src:
        for p in sorted(cfg_src.parent.glob("v1_*.yaml")):
            shutil.copy2(p, ROOT_OUT / "configs" / p.name)
            print("found config", p, flush=True)
    else:
        print("MISSING v1 configs", flush=True)

    if ZIP_OUT.exists():
        ZIP_OUT.unlink()
    with zipfile.ZipFile(ZIP_OUT, "w", zipfile.ZIP_STORED) as z:
        for p in sorted(ROOT_OUT.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(ROOT_OUT.parent).as_posix())
    size = ZIP_OUT.stat().st_size
    print("zip", ZIP_OUT, size / 1024**3, "GB", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
