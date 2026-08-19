#!/usr/bin/env python3
"""Dense Unicode-codepoint baseline for CNBE vs Unicode comparison.

Single-process, single-GPU training on 4-byte Unicode codepoint streams.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from pathlib import Path

import torch
import torch.nn.functional as F
import yaml
import numpy as np
from torch.utils.data import DataLoader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data import CodeDataset, build_vocab  # noqa: E402
from src.moe_model import CNBEModel  # noqa: E402


def load_codepoints(paths: list[str], max_tokens: int | None = None) -> list[int]:
    chunks = []
    total = 0
    for p in paths:
        data = Path(p).read_bytes()
        codes = np.frombuffer(data, dtype=">u4").astype(np.int64)
        if max_tokens and total + len(codes) > max_tokens:
            codes = codes[: max_tokens - total]
        chunks.append(codes)
        total += len(codes)
        if max_tokens and total >= max_tokens:
            break
    return list(np.concatenate(chunks)) if chunks else []


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Dense Unicode baseline")
    ap.add_argument("--config", default="/app/config/scnet_moe_config_unicode_l20.yaml")
    ap.add_argument("--codepoint-paths", nargs="+", required=True)
    ap.add_argument("--output", default="/output/unicode_metrics.json")
    ap.add_argument("--checkpoint-dir", default="/output/unicode_checkpoints")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--steps", type=int, default=0, help="override total training steps")
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    data_cfg = cfg["data"]
    model_cfg = cfg["model"]
    train_cfg = cfg["training"]

    device = "cuda" if torch.cuda.is_available() else "cpu"
    torch.manual_seed(int(cfg.get("seed", 42)))

    max_train = 20_000 if args.smoke else int(data_cfg.get("max_train_tokens", 24_000_000))
    max_eval = 2_000 if args.smoke else int(data_cfg.get("max_eval_tokens", 1_200_000))
    seq_len = 32 if args.smoke else int(train_cfg["seq_len"])
    batch_size = 2 if args.smoke else int(train_cfg["batch_size"])
    grad_accum = 1 if args.smoke else int(train_cfg.get("grad_accum_steps", 8))
    epochs = 1 if args.smoke else int(train_cfg.get("epochs", 2))
    d_model = 64 if args.smoke else int(model_cfg["d_model"])
    d_ff = 128 if args.smoke else int(model_cfg["d_ff"])
    layers = 1 if args.smoke else int(model_cfg["n_layers"])
    heads = 2 if args.smoke else int(model_cfg["n_heads"])

    print(f"unicode baseline device={device} smoke={args.smoke}", flush=True)
    codes = load_codepoints(args.codepoint_paths, max_train + max_eval)
    train_codes = codes[:max_train]
    eval_codes = codes[max_train : max_train + max_eval]
    vocab = build_vocab(np.array(codes))
    print(f"train={len(train_codes):,} eval={len(eval_codes):,} vocab={len(vocab):,}", flush=True)

    train_ds = CodeDataset(train_codes, vocab, seq_len)
    eval_ds = CodeDataset(eval_codes, vocab, seq_len)
    model = CNBEModel(
        vocab_size=len(vocab),
        d_model=d_model,
        d_ff=d_ff,
        n_layers=layers,
        n_heads=heads,
        num_experts=1,
        top_k=1,
        use_moe=False,
        mapping_path=None,
        learned_router=False,
    ).to(device)
    opt = torch.optim.AdamW(
        model.parameters(),
        lr=float(train_cfg.get("lr", 3e-4)),
        weight_decay=float(train_cfg.get("weight_decay", 0.01)),
    )

    checkpoint_dir = Path(args.checkpoint_dir)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    loader = iter(
        DataLoader(
            train_ds,
            batch_size=batch_size,
            shuffle=True,
            drop_last=True,
            num_workers=0,
        )
    )
    steps_per_epoch = max(1, len(train_ds) // batch_size)
    total_steps = args.steps or (steps_per_epoch * epochs)
    print(f"train_windows={len(train_ds)} eval_windows={len(eval_ds)} total_steps={total_steps}", flush=True)

    model.train()
    t0 = time.perf_counter()
    for step in range(total_steps):
        opt.zero_grad(set_to_none=True)
        loss_sum = 0.0
        for _ in range(grad_accum):
            try:
                x, y, _, _ = next(loader)
            except StopIteration:
                loader = iter(
                    DataLoader(
                        train_ds,
                        batch_size=batch_size,
                        shuffle=True,
                        drop_last=True,
                        num_workers=0,
                    )
                )
                x, y, _, _ = next(loader)
            x, y = x.to(device), y.to(device)
            with torch.autocast(
                device_type="cuda" if torch.cuda.is_available() else "cpu",
                dtype=torch.bfloat16,
                enabled=torch.cuda.is_available(),
            ):
                logits, _, _ = model(x, torch.zeros_like(x))
                loss = F.cross_entropy(logits.reshape(-1, len(vocab)), y.reshape(-1))
            (loss / grad_accum).backward()
            loss_sum += float(loss.detach().item()) / grad_accum
        torch.nn.utils.clip_grad_norm_(model.parameters(), float(train_cfg.get("grad_clip", 1.0)))
        opt.step()
        if (step + 1) % int(train_cfg.get("log_every_steps", 10)) == 0:
            sps = (step + 1) / max(time.perf_counter() - t0, 1e-6)
            print(f"step {step+1}/{total_steps} loss {loss_sum:.4f} steps/s {sps:.2f}", flush=True)
        if (step + 1) % int(train_cfg.get("checkpoint_every_steps", 100)) == 0:
            torch.save(
                {
                    "model": model.state_dict(),
                    "optimizer": opt.state_dict(),
                    "step": step + 1,
                    "vocab_size": len(vocab),
                },
                checkpoint_dir / "last.pt",
            )

    model.eval()
    total_loss = 0.0
    correct = 0
    total = 0
    with torch.no_grad():
        for x, y, _, _ in DataLoader(eval_ds, batch_size=batch_size, num_workers=0):
            x, y = x.to(device), y.to(device)
            logits, _, _ = model(x, torch.zeros_like(x))
            total_loss += F.cross_entropy(logits.reshape(-1, len(vocab)), y.reshape(-1)).item() * y.numel()
            correct += (logits.argmax(-1) == y).sum().item()
            total += y.numel()
    metrics = {
        "baseline": "unicode_dense",
        "eval_loss": total_loss / max(1, total),
        "eval_accuracy": correct / max(1, total),
        "params": sum(p.numel() for p in model.parameters()),
        "smoke": args.smoke,
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
