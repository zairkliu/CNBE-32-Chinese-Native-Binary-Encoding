#!/usr/bin/env python3
"""Generate the v1 robustness reproducibility MANIFEST."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_info() -> dict:
    info = {"commit": None, "branch": None, "dirty": None}
    try:
        info["commit"] = (
            subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        )
        info["branch"] = (
            subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True
            ).strip()
        )
        info["dirty"] = bool(
            subprocess.check_output(
                ["git", "status", "--porcelain"], text=True
            ).strip()
        )
    except Exception:  # noqa: BLE001
        pass
    return info


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--dcu-root", type=Path, default=Path("/scnet_upload_package_DCU"))
    ap.add_argument("--merged-root", type=Path, default=Path("/scnet_upload_package_MERGED_DCU"))
    ap.add_argument("--data-dir", type=Path, default=Path(""))
    args = ap.parse_args()

    import torch

    dcu = args.dcu_root
    merged = args.merged_root
    data_dir = args.data_dir or dcu / "data"
    out_dir = args.output.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    v1_files = [
        "zzjh_294.cnbe",
        "luxun_18.cnbe",
        "agatha.cnbe",
        "csbook.cnbe",
        "jinyong.cnbe",
        "caixin.cnbe",
        "sushi.cnbe",
    ]

    def hashes(paths: dict[str, Path]) -> dict[str, str | None]:
        result = {}
        for name, path in paths.items():
            if path and path.exists():
                result[name] = sha256(path)
            else:
                result[name] = None
        return result

    env = {
        "python": platform.python_version(),
        "torch": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "gpu_names": [
            torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())
        ],
        "cpu": platform.processor() or platform.machine(),
        "memory_total_gb": round(os.sysconf("SC_PHYS_PAGES") * os.sysconf("SC_PAGE_SIZE") / 1024**3, 1)
        if hasattr(os, "sysconf")
        else None,
        "disk_available_gb": round(shutil.disk_usage(dcu).free / 1024**3, 1),
    }

    manifest = {
        "generated_at": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
        "git": git_info(),
        "environment": env,
        "data": {
            "v1_files": hashes({name: data_dir / name for name in v1_files}),
            "vocab": hashes(
                {
                    "dcu": dcu / "output" / "assets" / "vocab_merged.json",
                    "merged": merged / "output" / "assets" / "vocab_merged.json",
                }
            ),
            "mapping": hashes(
                {"moe128": dcu / "output" / "mappings" / "moe128" / "mapping_128.json"}
            ),
        },
        "config": hashes(
            {
                "moe128": merged / "code" / "config" / "v1_moe128_dcu2.yaml",
                "dense": merged / "code" / "config" / "v1_dense_dcu2.yaml",
                "dense_matched": merged / "code" / "config" / "v1_dense_matched_dcu2.yaml",
                "unicode": merged / "code" / "config" / "v1_unicode_dcu2.yaml",
            }
        ),
        "scripts": hashes(
            {
                "train": merged / "code" / "scripts" / "train_distributed.py",
                "eval": merged / "code" / "scripts" / "eval.py",
            }
        ),
        "checkpoints": hashes(
            {
                "moe128": dcu / "output" / "checkpoints" / "moe128" / "final.pt",
                "dense": dcu / "output" / "checkpoints" / "dense" / "final.pt",
                "dense_matched": dcu / "output" / "checkpoints" / "dense_matched" / "final.pt",
                "unicode": merged / "output" / "checkpoints" / "unicode" / "final.pt",
            }
        ),
        "metrics": hashes(
            {
                "moe128": dcu / "output" / "moe128_eval_metrics.json",
                "dense": dcu / "output" / "dense_eval_metrics.json",
                "dense_matched": dcu / "output" / "dense_matched_metrics.json",
                "unicode": merged / "output" / "unicode_eval_metrics.json",
            }
        ),
    }
    args.output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    ckpt_lines = []
    for name, digest in manifest["checkpoints"].items():
        ckpt_lines.append(f"{digest or 'MISSING'}  {name}")
    (out_dir / "CHECKPOINT_HASHES.txt").write_text(
        "\n".join(ckpt_lines) + "\n", encoding="utf-8"
    )
    print("saved", args.output)
    print("saved", out_dir / "CHECKPOINT_HASHES.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
