# -*- coding: utf-8 -*-
"""Triton grouped GEMM 与向量化实现的前向/反向一致性测试。"""

from __future__ import annotations

import torch

from src.cnbe_router import CNBERouter
from src.moe_model import MoEFFN


def main() -> int:
    torch.manual_seed(0)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    d, ff, n_experts, top_k = 64, 128, 8, 2
    router = CNBERouter(num_experts=n_experts, num_activated=top_k)
    m1 = MoEFFN(d, ff, n_experts, top_k, router, use_triton=False).to(device)
    m2 = MoEFFN(d, ff, n_experts, top_k, router, use_triton=True).to(device)
    m2.load_state_dict(m1.state_dict())

    x = torch.randn(4, 16, d, device=device, requires_grad=True)
    codes = torch.randint(0, 0xFFFFFFFF, (4, 16), dtype=torch.long, device=device)

    y1, _ = m1(x, codes)
    y2, _ = m2(x, codes)
    diff = (y1 - y2).abs().max().item()
    print("forward max diff:", diff)
    if diff >= 1e-3:
        d = (y1 - y2).abs()
        idx = (d == d.max()).nonzero()[0]
        print("mismatch at", idx.tolist(), "v1", y1[tuple(idx)].item(), "v2", y2[tuple(idx)].item())
    assert diff < 1e-3, "forward mismatch"

    loss1 = y1.sum()
    loss1.backward()
    g1 = x.grad.clone()
    x.grad = None
    loss2 = y2.sum()
    loss2.backward()
    g2 = x.grad
    gdiff = (g1 - g2).abs().max().item()
    print("backward grad max diff:", gdiff)
    assert gdiff < 1e-3, "backward mismatch"
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
