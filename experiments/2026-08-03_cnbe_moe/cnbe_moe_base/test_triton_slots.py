# -*- coding: utf-8 -*-
"""Triton vs 向量化 grouped GEMM 的槽位级对比。"""

from __future__ import annotations

import torch

from src.cnbe_router import CNBERouter
from src.moe_model import MoEFFN
from src.triton_moe import triton_grouped_moe


def main() -> int:
    torch.manual_seed(0)
    device = "cuda"
    d, ff, n_experts, top_k = 64, 128, 8, 2
    router = CNBERouter(num_experts=n_experts, num_activated=top_k)
    m = MoEFFN(d, ff, n_experts, top_k, router).to(device)

    x = torch.randn(4, 16, d, device=device)
    codes = torch.randint(0, 0xFFFFFFFF, (4, 16), dtype=torch.long, device=device)
    b, s, d = x.shape
    t = b * s
    k = top_k
    expert_idx = router.route(codes).reshape(-1)
    flat_x = x.reshape(t, d).repeat_interleave(k, dim=0)
    order = torch.argsort(expert_idx, stable=True)
    sorted_e = expert_idx[order]
    sorted_x = flat_x[order]
    counts = torch.bincount(sorted_e, minlength=n_experts)
    offsets = torch.cumsum(counts, 0) - counts
    slot_idx = torch.arange(t * k, device=device, dtype=torch.long)
    group_pos = slot_idx - offsets[sorted_e]
    w1 = torch.stack([ex.fc1.weight for ex in m.experts])
    b1 = torch.stack([ex.fc1.bias for ex in m.experts])
    w2 = torch.stack([ex.fc2.weight for ex in m.experts])
    b2 = torch.stack([ex.fc2.bias for ex in m.experts])

    y_t = triton_grouped_moe(sorted_x, sorted_e, counts, offsets, order, group_pos, w1, b1, w2, b2)

    max_c = int(counts.max().item())
    group_x = torch.zeros(n_experts, max_c, d, device=device)
    group_x[sorted_e, group_pos] = sorted_x
    h = torch.nn.functional.silu(torch.baddbmm(b1.unsqueeze(1), group_x, w1.transpose(1, 2)))
    y = torch.baddbmm(b2.unsqueeze(1), h, w2.transpose(1, 2))
    out_slots = torch.zeros(t * k, d, device=device)
    out_slots[order] = y[sorted_e, group_pos]

    diff = (y_t - out_slots).abs()
    print("slot max diff:", diff.max().item())
    if diff.max().item() > 1e-3:
        idx = (diff == diff.max()).nonzero()[0]
        i = idx[0].item()
        print("slot", i, "expert", sorted_e[i].item(), "group_pos", group_pos[i].item(), "count", counts[sorted_e[i]].item())
        print("y_t[:8]", y_t[i, :8].tolist())
        print("ref[:8]", out_slots[i, :8].tolist())
        e = sorted_e[i].item()
        r = group_pos[i].item()
        print("y_scratch[:8]", y[e, r, :8].tolist())
        print("y_ref_scratch[:8]", y[e, r, :8].tolist())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
