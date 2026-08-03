# -*- coding: utf-8 -*-
"""单独调试 Triton GEMM1。"""

from __future__ import annotations

import torch

from src.triton_moe import _moe_gemm1_kernel, _moe_gemm2_kernel


def main() -> int:
    torch.manual_seed(0)
    device = "cuda"
    n, d, ff = 4, 64, 128
    max_c = 64
    counts = torch.full((n,), max_c, dtype=torch.long, device=device)
    offsets = torch.cumsum(counts, 0) - counts
    T = int(counts.sum())
    sorted_e = torch.repeat_interleave(torch.arange(n, device=device), max_c)
    sorted_x = torch.randn(T, d, device=device)
    group_pos = torch.arange(T, device=device) - offsets[sorted_e]
    w1 = torch.randn(n, ff, d, device=device)
    b1 = torch.randn(n, ff, device=device)

    pre = torch.empty(n, max_c, ff, device=device, dtype=torch.float32)
    grid = (n * ((max_c + 63) // 64) * ((ff + 63) // 64),)
    _moe_gemm1_kernel[grid](sorted_x, w1, b1, pre, offsets, counts, d, ff, max_c, 64, 64, 64)

    group_x = torch.zeros(n, max_c, d, device=device)
    group_x[sorted_e, group_pos] = sorted_x
    ref = group_x @ w1.transpose(1, 2) + b1.unsqueeze(1)
    print("pre max diff:", (pre - ref).abs().max().item())
    print("pre[0,0,:4]", pre[0, 0, :4].tolist())
    print("ref[0,0,:4]", ref[0, 0, :4].tolist())

    w2 = torch.randn(n, d, ff, device=device)
    b2 = torch.randn(n, d, device=device)
    y = torch.empty(n, max_c, d, device=device, dtype=torch.float32)
    grid_b = (n * ((max_c + 63) // 64) * ((d + 63) // 64),)
    _moe_gemm2_kernel[grid_b](pre, w2, b2, y, offsets, counts, d, ff, max_c, 64, 64, 64)
    h_ref = torch.nn.functional.silu(ref)
    y_ref = h_ref @ w2.transpose(1, 2) + b2.unsqueeze(1)
    print("y max diff:", (y - y_ref).abs().max().item())
    yd = (y - y_ref).abs()
    idx = (yd == yd.max()).nonzero()[0]
    print("y mismatch at", idx.tolist(), "val", y[tuple(idx)].item(), "ref", y_ref[tuple(idx)].item())
    print("y[0,0,:4]", y[0, 0, :4].tolist())
    print("y_ref[0,0,:4]", y_ref[0, 0, :4].tolist())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
