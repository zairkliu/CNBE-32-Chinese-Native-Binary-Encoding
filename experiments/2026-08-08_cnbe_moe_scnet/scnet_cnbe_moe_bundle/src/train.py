# -*- coding: utf-8 -*-
"""训练与评估：Dense vs CNBE-MoE。"""

from __future__ import annotations

import time
from pathlib import Path

import torch
from torch.utils.data import DataLoader

from src.data import CodeDataset, fields_from_codes, id_to_code_array
from src.moe_model import CNBEModel


def train_eval(
    train_ds: CodeDataset,
    eval_ds: CodeDataset,
    vocab_size: int,
    id_to_code: list[int],
    *,
    use_moe: bool,
    mapping_path: str,
    num_experts: int = 8,
    top_k: int = 2,
    d_model: int = 256,
    d_ff: int = 1024,
    n_layers: int = 2,
    n_heads: int = 4,
    batch_size: int = 32,
    steps: int = 800,
    lr: float = 3e-4,
    device: str = "cuda",
    seed: int = 42,
    aux_loss_weight: float = 0.1,
    compile_model: bool = False,
    use_triton: bool = False,
    balance_weight: float = 0.0,
    learned_router: bool = False,
):
    torch.manual_seed(seed)
    model = CNBEModel(
        vocab_size=vocab_size,
        d_model=d_model,
        d_ff=d_ff,
        n_layers=n_layers,
        n_heads=n_heads,
        num_experts=num_experts,
        top_k=top_k,
        use_moe=use_moe,
        mapping_path=mapping_path,
        use_triton=use_triton,
        learned_router=learned_router,
    ).to(device)
    if compile_model:
        print("启用 torch.compile (Triton)", flush=True)
        model = torch.compile(model)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    loader = iter(DataLoader(train_ds, batch_size=batch_size, shuffle=True, drop_last=True, num_workers=0))

    model.train()
    t0 = time.perf_counter()
    losses = []
    for step in range(steps):
        try:
            x, y, xc, yc = next(loader)
        except StopIteration:
            loader = iter(DataLoader(train_ds, batch_size=batch_size, shuffle=True, drop_last=True, num_workers=0))
            x, y, xc, yc = next(loader)
        x, y, xc, yc = x.to(device), y.to(device), xc.to(device), yc.to(device)
        logits, field_logits, load = model(x, xc)
        loss = torch.nn.functional.cross_entropy(logits.reshape(-1, vocab_size), y.reshape(-1))
        yc_flat = yc.reshape(-1)
        aux = 0.0
        for name, head in [("radix", 256), ("strokes", 32), ("struct", 16), ("idx", 2048)]:
            target = {
                "radix": (yc_flat >> 24) & 0xFF,
                "strokes": (yc_flat >> 19) & 0x1F,
                "struct": (yc_flat >> 15) & 0x0F,
                "idx": yc_flat & 0x7FF,
            }[name]
            aux += torch.nn.functional.cross_entropy(
                field_logits[name].reshape(-1, head), target
            )
        loss = loss + aux_loss_weight * aux
        bal_loss = torch.zeros((), device=device)
        if use_moe and balance_weight > 0:
            if learned_router and getattr(model, "last_router_probs", None) is not None:
                probs = model.last_router_probs
                t = probs.shape[0] * probs.shape[1]
                hard = torch.argmax(probs, dim=-1)
                f = torch.bincount(hard.flatten(), minlength=num_experts).float() / max(1, t)
                p_mean = probs.mean(dim=(0, 1))
                bal_loss = num_experts * (f * p_mean).sum()
            else:
                load_sum = load.sum().clamp(min=1.0)
                target = 1.0 / num_experts
                bal_loss = ((load / load_sum - target) ** 2).mean()
            loss = loss + balance_weight * bal_loss
        opt.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        losses.append(loss.item())
        if (step + 1) % 200 == 0:
            print(f"  {use_moe and 'MoE' or 'Dense'} step {step+1}: loss {loss.item():.4f}", flush=True)
    train_sec = time.perf_counter() - t0
    train_steps_per_sec = steps / train_sec

    model.eval()
    total_loss = 0.0
    correct = 0
    total = 0
    correct_radix = correct_struct = correct_strokes = 0
    correct_radix_h = correct_struct_h = correct_strokes_h = 0
    load_sum = None
    with torch.no_grad():
        for x, y, xc, yc in DataLoader(eval_ds, batch_size=batch_size, num_workers=0):
            x, y, xc, yc = x.to(device), y.to(device), xc.to(device), yc.to(device)
            logits, field_logits, load = model(x, xc)
            total_loss += torch.nn.functional.cross_entropy(logits.reshape(-1, vocab_size), y.reshape(-1)).item() * y.numel()
            pred = logits.argmax(-1)
            correct += (pred == y).sum().item()
            total += y.numel()
            pred_codes = torch.tensor([id_to_code[int(i)] for i in pred.cpu().flatten()], dtype=torch.long).reshape_as(pred)
            yf = fields_from_codes(yc.cpu().numpy())
            pf = fields_from_codes(pred_codes.cpu().numpy())
            correct_radix += int((pf["radix"] == yf["radix"]).sum())
            correct_struct += int((pf["struct"] == yf["struct"]).sum())
            correct_strokes += int((pf["strokes"] == yf["strokes"]).sum())
            yc_np = yc.cpu().numpy()
            correct_radix_h += int(((field_logits["radix"].argmax(-1).cpu().numpy() == ((yc_np >> 24) & 0xFF)).sum()))
            correct_struct_h += int(((field_logits["struct"].argmax(-1).cpu().numpy() == ((yc_np >> 15) & 0x0F)).sum()))
            correct_strokes_h += int(((field_logits["strokes"].argmax(-1).cpu().numpy() == ((yc_np >> 19) & 0x1F)).sum()))
            if load_sum is None:
                load_sum = load.float().cpu()
            else:
                load_sum += load.float().cpu()

    return {
        "use_moe": use_moe,
        "avg_train_loss": sum(losses[-100:]) / max(1, len(losses[-100:])),
        "eval_loss": total_loss / max(1, total),
        "eval_accuracy": correct / max(1, total),
        "eval_radix_accuracy": correct_radix / max(1, total),
        "eval_struct_accuracy": correct_struct / max(1, total),
        "eval_strokes_accuracy": correct_strokes / max(1, total),
        "eval_radix_head_accuracy": correct_radix_h / max(1, total),
        "eval_struct_head_accuracy": correct_struct_h / max(1, total),
        "eval_strokes_head_accuracy": correct_strokes_h / max(1, total),
        "train_steps_per_sec": round(train_steps_per_sec, 3),
        "expert_gini": round(CNBEModel.gini(load_sum), 4) if load_sum is not None and load_sum.numel() > 1 else None,
        "params": sum(p.numel() for p in model.parameters()),
    }
