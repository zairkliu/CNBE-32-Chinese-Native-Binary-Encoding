#!/usr/bin/env python3
# SCNet CNBE-MoE single-process training entry (smoke and full run).

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import torch
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.cnbe_router import build_balanced_mapping  # noqa: E402
from src.data import CodeDataset, build_vocab, id_to_code_array, load_codes  # noqa: E402
from src.train import train_eval  # noqa: E402


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="CNBE-MoE SCNet training entry")
    ap.add_argument("--config", default="/app/config/scnet_moe_config_a.yaml")
    ap.add_argument("--cnbe-paths", nargs="+", default=[])
    ap.add_argument("--output", default="/output/metrics.json")
    ap.add_argument("--smoke", action="store_true", help="run a tiny smoke test")
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    data_cfg = cfg["data"]
    model_cfg = cfg["model"]
    train_cfg = cfg["training"]

    paths = args.cnbe_paths or data_cfg["cnbe_paths"]
    if not paths:
        print("no cnbe paths", flush=True)
        return 2

    if args.smoke:
        max_train = 20_000
        max_eval = 2_000
        seq_len = 32
        batch_size = 2
        steps = 5
        d_model = 64
        d_ff = 128
        layers = 1
        heads = 2
        experts = 8
    else:
        max_train = int(data_cfg.get("max_train_tokens", 24_000_000))
        max_eval = int(data_cfg.get("max_eval_tokens", 1_200_000))
        seq_len = int(train_cfg["seq_len"])
        batch_size = int(train_cfg["batch_size"])
        steps = int(train_cfg.get("steps", 1000))
        d_model = int(model_cfg["d_model"])
        d_ff = int(model_cfg["d_ff"])
        layers = int(model_cfg["n_layers"])
        heads = int(model_cfg["n_heads"])
        experts = int(model_cfg["num_experts"])

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"loading {len(paths)} cnbe files, device={device}", flush=True)
    codes = load_codes(paths, max_train + max_eval)
    train_codes = codes[:max_train]
    eval_codes = codes[max_train : max_train + max_eval]
    vocab = build_vocab(codes)
    id_to_code = id_to_code_array(vocab).tolist()
    print(
        f"train={len(train_codes):,} eval={len(eval_codes):,} vocab={len(vocab):,}",
        flush=True,
    )

    mapping_dir = Path(os.environ.get("CNBE_MAPPING_DIR", "/app/mappings"))
    mapping_dir.mkdir(parents=True, exist_ok=True)
    mapping_path = mapping_dir / f"mapping_{experts}.json"
    mapping_path.write_text(
        json.dumps(build_balanced_mapping(train_codes, experts, mode=3), ensure_ascii=False),
        encoding="utf-8",
    )
    print("saved mapping:", mapping_path, flush=True)

    train_ds = CodeDataset(train_codes, vocab, seq_len)
    eval_ds = CodeDataset(eval_codes, vocab, seq_len)

    result = train_eval(
        train_ds,
        eval_ds,
        len(vocab),
        id_to_code,
        use_moe=True,
        mapping_path=str(mapping_path),
        num_experts=experts,
        top_k=int(model_cfg["top_k"]),
        d_model=d_model,
        d_ff=d_ff,
        n_layers=layers,
        n_heads=heads,
        batch_size=batch_size,
        steps=steps,
        device=device,
        aux_loss_weight=float(model_cfg.get("aux_loss_weight", 0.1)),
        balance_weight=float(model_cfg.get("balance_weight", 0.01)),
        learned_router=bool(model_cfg.get("learned_router", False)),
    )
    result["smoke"] = args.smoke
    result["config"] = {
        "max_train": max_train,
        "max_eval": max_eval,
        "seq_len": seq_len,
        "batch_size": batch_size,
        "steps": steps,
        "d_model": d_model,
        "d_ff": d_ff,
        "layers": layers,
        "heads": heads,
        "experts": experts,
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
    print("saved:", out, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
