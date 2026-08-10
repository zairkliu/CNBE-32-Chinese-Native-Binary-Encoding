#!/usr/bin/env python3
# SCNet CNBE-MoE distributed training entry (torchrun + DDP + bf16).

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from pathlib import Path

import torch
import torch.distributed as dist
import torch.nn.functional as F
import yaml
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data import DataLoader, DistributedSampler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.cnbe_router import build_balanced_mapping  # noqa: E402
from src.data import (  # noqa: E402
    CodeDataset,
    build_vocab,
    fields_from_codes,
    id_to_code_array,
    load_codes,
)
from src.moe_model import CNBEModel  # noqa: E402


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="CNBE-MoE distributed training")
    ap.add_argument("--config", default="/app/config/scnet_moe_config_c.yaml")
    ap.add_argument("--cnbe-paths", nargs="+", default=[])
    ap.add_argument("--output", default="/output/train_metrics.json")
    ap.add_argument("--checkpoint-dir", default="/output/checkpoints")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--smoke", action="store_true")
    return ap.parse_args()


def compute_loss(
    model: CNBEModel,
    x: torch.Tensor,
    y: torch.Tensor,
    xc: torch.Tensor,
    yc: torch.Tensor,
    vocab_size: int,
    aux_weight: float,
    balance_weight: float,
    num_experts: int,
) -> tuple[torch.Tensor, torch.Tensor]:
    logits, field_logits, load = model(x, xc)
    loss = F.cross_entropy(logits.reshape(-1, vocab_size), y.reshape(-1))
    yc_flat = yc.reshape(-1)
    aux = torch.zeros((), device=x.device)
    for name, head in [("radix", 256), ("strokes", 32), ("struct", 16), ("idx", 2048)]:
        target = {
            "radix": (yc_flat >> 24) & 0xFF,
            "strokes": (yc_flat >> 19) & 0x1F,
            "struct": (yc_flat >> 15) & 0x0F,
            "idx": yc_flat & 0x7FF,
        }[name]
        aux = aux + F.cross_entropy(field_logits[name].reshape(-1, head), target)
    loss = loss + aux_weight * aux
    bal = torch.zeros((), device=x.device)
    if balance_weight > 0:
        load_sum = load.sum().clamp(min=1.0)
        target = 1.0 / num_experts
        bal = ((load / load_sum - target) ** 2).mean()
        loss = loss + balance_weight * bal
    return loss, load


def main() -> int:
    args = parse_args()
    rank = int(os.environ.get("RANK", "0"))
    local_rank = int(os.environ.get("LOCAL_RANK", "0"))
    world_size = int(os.environ.get("WORLD_SIZE", "1"))
    use_cuda = torch.cuda.is_available()
    backend = os.environ.get("DIST_BACKEND", "nccl" if use_cuda else "gloo")
    dist.init_process_group(backend=backend, rank=rank, world_size=world_size)
    if use_cuda:
        torch.cuda.set_device(local_rank)
    device = torch.device(f"cuda:{local_rank}" if use_cuda else "cpu")

    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    data_cfg = cfg["data"]
    model_cfg = cfg["model"]
    train_cfg = cfg["training"]

    paths = args.cnbe_paths or data_cfg["cnbe_paths"]
    if args.smoke:
        max_train = 2_000
        max_eval = 500
        seq_len = 16
        batch_size = 2
        epochs = 1
        d_model = 32
        d_ff = 64
        layers = 1
        heads = 2
        experts = 4
        grad_accum = 1
        log_every = 1
        checkpoint_every = 1000
    else:
        max_train = int(data_cfg.get("max_train_tokens", 24_000_000))
        max_eval = int(data_cfg.get("max_eval_tokens", 1_200_000))
        seq_len = int(train_cfg["seq_len"])
        batch_size = int(train_cfg["batch_size"])
        epochs = int(train_cfg["epochs"])
        d_model = int(model_cfg["d_model"])
        d_ff = int(model_cfg["d_ff"])
        layers = int(model_cfg["n_layers"])
        heads = int(model_cfg["n_heads"])
        experts = int(model_cfg["num_experts"])
        grad_accum = int(train_cfg.get("grad_accum_steps", 4))
        log_every = int(train_cfg.get("log_every_steps", 10))
        checkpoint_every = int(train_cfg.get("checkpoint_every_steps", 100))

    torch.manual_seed(int(cfg.get("seed", 42)))
    if rank == 0:
        print(
            f"rank={rank} world={world_size} device={device} "
            f"smoke={args.smoke} experts={experts}",
            flush=True,
        )

    codes = load_codes(paths, max_train + max_eval)
    train_codes = codes[:max_train]
    eval_codes = codes[max_train : max_train + max_eval]
    vocab = build_vocab(codes)
    id_to_code = id_to_code_array(vocab).tolist()

    mapping = build_balanced_mapping(train_codes, experts, mode=3)
    mapping_dir = Path(os.environ.get("CNBE_MAPPING_DIR", "/tmp"))
    mapping_dir.mkdir(parents=True, exist_ok=True)
    mapping_path = mapping_dir / f"mapping_{experts}.json"
    mapping_path.write_text(json.dumps(mapping, ensure_ascii=False), encoding="utf-8")

    train_ds = CodeDataset(train_codes, vocab, seq_len)
    eval_ds = CodeDataset(eval_codes, vocab, seq_len)
    sampler = DistributedSampler(
        train_ds,
        num_replicas=world_size,
        rank=rank,
        shuffle=True,
        drop_last=True,
        seed=int(cfg.get("seed", 42)),
    )
    loader = iter(
        DataLoader(
            train_ds,
            batch_size=batch_size,
            sampler=sampler,
            num_workers=0,
            drop_last=True,
        )
    )

    model = CNBEModel(
        vocab_size=len(vocab),
        d_model=d_model,
        d_ff=d_ff,
        n_layers=layers,
        n_heads=heads,
        num_experts=experts,
        top_k=int(model_cfg["top_k"]),
        use_moe=True,
        mapping_path=str(mapping_path),
        learned_router=bool(model_cfg.get("learned_router", False)),
    ).to(device)
    if use_cuda:
        model = DDP(model, device_ids=[local_rank], output_device=local_rank)
    else:
        model = DDP(model)

    opt = torch.optim.AdamW(
        model.parameters(),
        lr=float(train_cfg.get("lr", 3e-4)),
        weight_decay=float(train_cfg.get("weight_decay", 0.01)),
    )

    checkpoint_dir = Path(args.checkpoint_dir)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    ckpt_path = checkpoint_dir / "last.pt"
    start_step = 0
    if args.resume and ckpt_path.exists():
        ckpt = torch.load(ckpt_path, map_location=device)
        model.module.load_state_dict(ckpt["model"])
        opt.load_state_dict(ckpt["optimizer"])
        start_step = int(ckpt["step"])
        if rank == 0:
            print("resumed from step", start_step, flush=True)

    steps_per_epoch = max(1, len(sampler) // batch_size)
    total_steps = int(steps_per_epoch * epochs)
    if rank == 0:
        print(
            f"train_windows={len(train_ds)} eval_windows={len(eval_ds)} "
            f"steps_per_epoch={steps_per_epoch} total_steps={total_steps}",
            flush=True,
        )

    model.train()
    t0 = time.perf_counter()
    for step in range(start_step, total_steps):
        sampler.set_epoch(step)
        opt.zero_grad(set_to_none=True)
        loss_sum = 0.0
        for _ in range(grad_accum):
            try:
                x, y, xc, yc = next(loader)
            except StopIteration:
                sampler.set_epoch(step + 1)
                loader = iter(
                    DataLoader(
                        train_ds,
                        batch_size=batch_size,
                        sampler=sampler,
                        num_workers=0,
                        drop_last=True,
                    )
                )
                x, y, xc, yc = next(loader)
            x, y, xc, yc = x.to(device), y.to(device), xc.to(device), yc.to(device)
            with torch.autocast(
                device_type="cuda" if use_cuda else "cpu",
                dtype=torch.bfloat16,
                enabled=use_cuda,
            ):
                loss, _ = compute_loss(
                    model,
                    x,
                    y,
                    xc,
                    yc,
                    len(vocab),
                    float(model_cfg.get("aux_loss_weight", 0.1)),
                    float(model_cfg.get("balance_weight", 0.01)),
                    experts,
                )
            (loss / grad_accum).backward()
            loss_sum += float(loss.detach().item()) / grad_accum
        torch.nn.utils.clip_grad_norm_(model.parameters(), float(train_cfg.get("grad_clip", 1.0)))
        opt.step()

        if rank == 0:
            if (step + 1) % log_every == 0 or args.smoke:
                elapsed = time.perf_counter() - t0
                sps = (step + 1) / max(elapsed, 1e-6)
                print(
                    f"step {step+1}/{total_steps} loss {loss_sum:.4f} "
                    f"steps/s {sps:.2f}",
                    flush=True,
                )
            if (step + 1) % checkpoint_every == 0:
                torch.save(
                    {
                        "model": model.module.state_dict(),
                        "optimizer": opt.state_dict(),
                        "step": step + 1,
                        "config": {
                            "d_model": d_model,
                            "d_ff": d_ff,
                            "layers": layers,
                            "heads": heads,
                            "experts": experts,
                            "seq_len": seq_len,
                            "batch_size": batch_size,
                            "epochs": epochs,
                        },
                    },
                    ckpt_path,
                )

    dist.barrier()
    metrics: dict = {}
    if rank == 0:
        model.eval()
        total_loss = 0.0
        correct = 0
        total = 0
        cr = cs = cst = 0
        load_sum = None
        with torch.no_grad():
            for x, y, xc, yc in DataLoader(eval_ds, batch_size=batch_size, num_workers=0):
                x, y, xc, yc = x.to(device), y.to(device), xc.to(device), yc.to(device)
                logits, field_logits, load = model(x, xc)
                total_loss += (
                    F.cross_entropy(logits.reshape(-1, len(vocab)), y.reshape(-1)).item()
                    * y.numel()
                )
                pred = logits.argmax(-1)
                correct += (pred == y).sum().item()
                total += y.numel()
                pred_codes = torch.tensor(
                    [id_to_code[int(i)] for i in pred.cpu().flatten()],
                    dtype=torch.long,
                ).reshape_as(pred)
                yf = fields_from_codes(yc.cpu().numpy())
                pf = fields_from_codes(pred_codes.cpu().numpy())
                cr += int((pf["radix"] == yf["radix"]).sum())
                cs += int((pf["struct"] == yf["struct"]).sum())
                cst += int((pf["strokes"] == yf["strokes"]).sum())
                if load_sum is None:
                    load_sum = load.float().cpu()
                else:
                    load_sum += load.float().cpu()
        metrics = {
            "eval_loss": total_loss / max(1, total),
            "eval_accuracy": correct / max(1, total),
            "eval_radix_accuracy": cr / max(1, total),
            "eval_struct_accuracy": cs / max(1, total),
            "eval_strokes_accuracy": cst / max(1, total),
            "expert_gini": (
                CNBEModel.gini(load_sum) if load_sum is not None and load_sum.numel() > 1 else None
            ),
            "params": sum(p.numel() for p in model.parameters()),
            "smoke": args.smoke,
        }
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(metrics, ensure_ascii=False, indent=2), flush=True)
    dist.barrier()
    dist.destroy_process_group()
    return 0


if __name__ == "__main__":
    sys.exit(main())
