#!/usr/bin/env python3
"""Evaluate a saved CNBE-MoE checkpoint on the held-out eval split."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
import yaml
from torch.utils.data import DataLoader

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
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--checkpoint", required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--cnbe-paths", nargs="+", default=[])
    ap.add_argument("--mapping", default="")
    ap.add_argument("--output", default="/output/eval_metrics.json")
    ap.add_argument("--vocab", default="")
    ap.add_argument("--limit-batches", type=int, default=0)
    ap.add_argument("--max-eval-tokens", type=int, default=0)
    return ap.parse_args()


def load_codes_u32(paths: list[str], max_tokens: int | None = None) -> object:
    chunks = []
    total = 0
    for p in paths:
        codes = np.frombuffer(Path(p).read_bytes(), dtype=">u4")
        if max_tokens and total + len(codes) > max_tokens:
            codes = codes[: max_tokens - total]
        chunks.append(codes)
        total += len(codes)
        if max_tokens and total >= max_tokens:
            break
    return np.concatenate(chunks) if chunks else np.array([], dtype=np.uint32)


def main() -> int:
    args = parse_args()
    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    data_cfg = cfg["data"]
    model_cfg = cfg["model"]
    train_cfg = cfg["training"]

    ckpt = torch.load(args.checkpoint, map_location="cpu")
    ckpt_cfg = ckpt.get("config", {}) or {}
    d_model = int(ckpt_cfg.get("d_model", model_cfg["d_model"]))
    d_ff = int(ckpt_cfg.get("d_ff", model_cfg["d_ff"]))
    n_layers = int(ckpt_cfg.get("layers", model_cfg["n_layers"]))
    n_heads = int(ckpt_cfg.get("heads", model_cfg["n_heads"]))
    num_experts = int(ckpt_cfg.get("experts", model_cfg["num_experts"]))
    seq_len = int(ckpt_cfg.get("seq_len", train_cfg["seq_len"]))
    batch_size = int(ckpt_cfg.get("batch_size", train_cfg["batch_size"]))
    top_k = int(model_cfg["top_k"])
    use_moe = bool(model_cfg.get("use_moe", True))
    learned_router = bool(model_cfg.get("learned_router", False))

    max_train = int(data_cfg.get("max_train_tokens", 24_000_000))
    max_eval = int(data_cfg.get("max_eval_tokens", 1_200_000))
    if args.max_eval_tokens:
        max_eval = args.max_eval_tokens

    paths = args.cnbe_paths or data_cfg["cnbe_paths"]
    if not paths:
        print("no cnbe paths", flush=True)
        return 2

    t0 = time.perf_counter()
    print(
        f"loading {max_train + max_eval:,} tokens as uint32 "
        f"({(max_train + max_eval) * 4 / 1024**3:.2f} GB)",
        flush=True,
    )
    codes = load_codes_u32(paths, max_train + max_eval)
    train_codes = codes[:max_train]
    eval_codes = codes[max_train : max_train + max_eval]
    vocab_size_from_ckpt = int(ckpt["model"]["embed.weight"].shape[0])
    vocab: dict[int, int] | None = None
    candidate_paths = [args.vocab] if args.vocab else []
    candidate_paths += [
        os.environ.get("CNBE_VOCAB_PATH", ""),
        str(Path(os.environ.get("CNBE_OUTPUT_DIR", "/tmp")) / "assets" / "vocab.json"),
        str(Path(os.environ.get("CNBE_OUTPUT_DIR", "/tmp")) / "vocab.json"),
    ]
    for cand in candidate_paths:
        if not cand or not Path(cand).exists():
            continue
        try:
            raw = json.loads(Path(cand).read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        if not isinstance(raw, dict):
            continue
        vocab = {int(k): int(v) for k, v in raw.items()}
        if len(vocab) == vocab_size_from_ckpt:
            print("using vocab:", cand, flush=True)
            break
        vocab = None
    if vocab is None:
        print(
            f"building vocab from {len(codes):,} codes (may take a few minutes)",
            flush=True,
        )
        unique = np.unique(codes)
        vocab = {int(c): i for i, c in enumerate(unique)}
        save_dir = Path(os.environ.get("CNBE_OUTPUT_DIR", "/tmp")) / "assets"
        save_dir.mkdir(parents=True, exist_ok=True)
        (save_dir / "vocab_merged.json").write_text(
            json.dumps(vocab, ensure_ascii=False), encoding="utf-8"
        )
        print("saved vocab:", save_dir / "vocab_merged.json", flush=True)
    id_to_code = id_to_code_array(vocab).tolist()
    eval_ds = CodeDataset(eval_codes, vocab, seq_len)
    print(
        f"train={len(train_codes):,} eval={len(eval_codes):,} "
        f"vocab={len(vocab):,} windows={len(eval_ds):,}",
        flush=True,
    )

    if args.mapping:
        mapping_path = args.mapping
    else:
        mapping_path = str(
            Path(os.environ.get("CNBE_MAPPING_DIR", "/tmp")) / f"mapping_{num_experts}.json"
        )
    if not Path(mapping_path).exists():
        mapping_path = Path(mapping_path)
        mapping_path.parent.mkdir(parents=True, exist_ok=True)
        mapping_path.write_text(
            json.dumps(
                build_balanced_mapping(train_codes, num_experts, mode=3),
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        print("rebuilt mapping:", mapping_path, flush=True)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = CNBEModel(
        vocab_size=len(vocab),
        d_model=d_model,
        d_ff=d_ff,
        n_layers=n_layers,
        n_heads=n_heads,
        num_experts=num_experts,
        top_k=top_k,
        use_moe=use_moe,
        mapping_path=str(mapping_path),
        learned_router=learned_router,
    ).to(device)
    missing, unexpected = model.load_state_dict(ckpt["model"], strict=True)
    if missing:
        print("missing keys:", len(missing), flush=True)
    if unexpected:
        print("unexpected keys:", len(unexpected), flush=True)
    model.eval()
    print(
        f"loaded checkpoint step={ckpt.get('step')} experts={num_experts} "
        f"device={device}",
        flush=True,
    )

    total_loss = 0.0
    correct = 0
    total = 0
    cr = cs = cst = 0
    cr_h = cs_h = cst_h = 0
    load_sum = None
    eval_t0 = time.perf_counter()
    loader = DataLoader(eval_ds, batch_size=batch_size, num_workers=0)
    with torch.no_grad(), torch.autocast(
        device_type="cuda" if device == "cuda" else "cpu",
        dtype=torch.bfloat16,
        enabled=device == "cuda",
    ):
        for i, (x, y, xc, yc) in enumerate(loader):
            if args.limit_batches and i >= args.limit_batches:
                break
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
            yc_np = yc.cpu().numpy()
            yf = fields_from_codes(yc_np)
            pf = fields_from_codes(pred_codes.cpu().numpy())
            cr += int((pf["radix"] == yf["radix"]).sum())
            cs += int((pf["struct"] == yf["struct"]).sum())
            cst += int((pf["strokes"] == yf["strokes"]).sum())
            cr_h += int(
                (
                    field_logits["radix"].argmax(-1).cpu().numpy()
                    == ((yc_np >> 24) & 0xFF)
                ).sum()
            )
            cs_h += int(
                (
                    field_logits["struct"].argmax(-1).cpu().numpy()
                    == ((yc_np >> 15) & 0x0F)
                ).sum()
            )
            cst_h += int(
                (
                    field_logits["strokes"].argmax(-1).cpu().numpy()
                    == ((yc_np >> 19) & 0x1F)
                ).sum()
            )
            if load_sum is None:
                load_sum = load.float().cpu()
            else:
                load_sum += load.float().cpu()
            if (i + 1) % 1000 == 0:
                sps = (i + 1) / max(1e-6, time.perf_counter() - eval_t0)
                print(
                    f"eval batch {i+1}/{len(loader)} loss "
                    f"{total_loss / max(1, total):.4f} batches/s {sps:.2f}",
                    flush=True,
                )

    metrics = {
        "checkpoint": str(Path(args.checkpoint).resolve()),
        "checkpoint_step": ckpt.get("step"),
        "eval_loss": total_loss / max(1, total),
        "eval_accuracy": correct / max(1, total),
        "eval_radix_accuracy": cr / max(1, total),
        "eval_struct_accuracy": cs / max(1, total),
        "eval_strokes_accuracy": cst / max(1, total),
        "eval_radix_head_accuracy": cr_h / max(1, total),
        "eval_struct_head_accuracy": cs_h / max(1, total),
        "eval_strokes_head_accuracy": cst_h / max(1, total),
        "expert_gini": (
            CNBEModel.gini(load_sum)
            if load_sum is not None and load_sum.numel() > 1
            else None
        ),
        "params": sum(p.numel() for p in model.parameters()),
        "tokens_evaluated": total,
        "config": {
            "max_train": max_train,
            "max_eval": max_eval,
            "seq_len": seq_len,
            "batch_size": batch_size,
            "d_model": d_model,
            "d_ff": d_ff,
            "layers": n_layers,
            "heads": n_heads,
            "experts": num_experts,
        },
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=2), flush=True)
    print("saved:", out, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
