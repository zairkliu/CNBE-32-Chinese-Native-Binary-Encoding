# -*- coding: utf-8 -*-
"""Triton grouped GEMM kernel for MoE FFN（前向） + 向量化反向。"""

from __future__ import annotations

import torch

try:
    import triton
    import triton.language as tl
    TRITON_AVAILABLE = True
except Exception:  # noqa: BLE001
    TRITON_AVAILABLE = False


if TRITON_AVAILABLE:

    @triton.jit
    def _moe_gemm1_kernel(
        x_ptr, w1_ptr, b1_ptr, pre_ptr,
        offsets_ptr, counts_ptr,
        D: tl.constexpr, FF: tl.constexpr, MAX_C: tl.constexpr,
        BLOCK_M: tl.constexpr, BLOCK_N: tl.constexpr, BLOCK_K: tl.constexpr,
    ):
        pid = tl.program_id(0)
        num_n = tl.cdiv(FF, BLOCK_N)
        num_m = tl.cdiv(MAX_C, BLOCK_M)
        expert = pid // (num_n * num_m)
        rem = pid % (num_n * num_m)
        n_block = rem % num_n
        m_block = rem // num_n
        count = tl.load(counts_ptr + expert)
        off = tl.load(offsets_ptr + expert)
        m = m_block * BLOCK_M + tl.arange(0, BLOCK_M)
        n = n_block * BLOCK_N + tl.arange(0, BLOCK_N)
        mask_m = m < count
        mask_n = n < FF
        acc = tl.zeros((BLOCK_M, BLOCK_N), dtype=tl.float32)
        b = tl.load(b1_ptr + expert * FF + n, mask=mask_n, other=0.0)
        acc += b[None, :]
        for k0 in range(0, D, BLOCK_K):
            k = k0 + tl.arange(0, BLOCK_K)
            x = tl.load(
                x_ptr + (off + m)[:, None] * D + k[None, :],
                mask=mask_m[:, None] & (k[None, :] < D),
                other=0.0,
            )
            w = tl.load(
                w1_ptr + expert * FF * D + n[:, None] * D + k[None, :],
                mask=mask_n[:, None] & (k[None, :] < D),
                other=0.0,
            )
            acc += tl.dot(x, tl.trans(w), input_precision="ieee")
        acc = tl.where(mask_m[:, None], acc, 0.0)
        tl.store(
            pre_ptr + expert * MAX_C * FF + m[:, None] * FF + n[None, :],
            acc.to(x_ptr.dtype.element_ty),
            mask=mask_m[:, None] & mask_n[None, :],
        )

    @triton.jit
    def _moe_gemm2_kernel(
        pre_ptr, w2_ptr, b2_ptr, y_ptr,
        offsets_ptr, counts_ptr,
        D: tl.constexpr, FF: tl.constexpr, MAX_C: tl.constexpr,
        BLOCK_M: tl.constexpr, BLOCK_N: tl.constexpr, BLOCK_K: tl.constexpr,
    ):
        pid = tl.program_id(0)
        num_n = tl.cdiv(D, BLOCK_N)
        num_m = tl.cdiv(MAX_C, BLOCK_M)
        expert = pid // (num_n * num_m)
        rem = pid % (num_n * num_m)
        n_block = rem % num_n
        m_block = rem // num_n
        count = tl.load(counts_ptr + expert)
        off = tl.load(offsets_ptr + expert)
        m = m_block * BLOCK_M + tl.arange(0, BLOCK_M)
        n = n_block * BLOCK_N + tl.arange(0, BLOCK_N)
        mask_m = m < count
        mask_n = n < D
        acc = tl.zeros((BLOCK_M, BLOCK_N), dtype=tl.float32)
        b = tl.load(b2_ptr + expert * D + n, mask=mask_n, other=0.0)
        acc += b[None, :]
        for k0 in range(0, FF, BLOCK_K):
            k = k0 + tl.arange(0, BLOCK_K)
            pre = tl.load(
                pre_ptr + expert * MAX_C * FF + m[:, None] * FF + k[None, :],
                mask=mask_m[:, None] & (k[None, :] < FF),
                other=0.0,
            )
            h = pre * tl.sigmoid(pre)
            w = tl.load(
                w2_ptr + expert * D * FF + n[:, None] * FF + k[None, :],
                mask=mask_n[:, None] & (k[None, :] < FF),
                other=0.0,
            )
            acc += tl.dot(h, tl.trans(w), input_precision="ieee")
        acc = tl.where(mask_m[:, None], acc, 0.0)
        tl.store(
            y_ptr + expert * MAX_C * D + m[:, None] * D + n[None, :],
            acc.to(pre_ptr.dtype.element_ty),
            mask=mask_m[:, None] & mask_n[None, :],
        )


class _TritonGroupedMoE(torch.autograd.Function):
    @staticmethod
    def forward(ctx, sorted_x, sorted_e, counts, offsets, order, group_pos, w1, b1, w2, b2, n, d, ff, max_c):
        dev = sorted_x.device
        pre = torch.empty((n, max_c, ff), device=dev, dtype=sorted_x.dtype)
        y = torch.empty((n, max_c, d), device=dev, dtype=sorted_x.dtype)
        bm, bn, bk = 64, 64, 64
        grid1 = (n * triton.cdiv(max_c, bm) * triton.cdiv(ff, bn),)
        _moe_gemm1_kernel[grid1](
            sorted_x, w1, b1, pre, offsets, counts, d, ff, max_c, bm, bn, bk
        )
        grid2 = (n * triton.cdiv(max_c, bm) * triton.cdiv(d, bn),)
        _moe_gemm2_kernel[grid2](
            pre, w2, b2, y, offsets, counts, d, ff, max_c, bm, bn, bk
        )
        out = y[sorted_e, group_pos]
        ctx.save_for_backward(sorted_x, sorted_e, counts, offsets, order, group_pos, w1, b1, w2, b2, pre, y)
        ctx.n = n
        ctx.d = d
        ctx.ff = ff
        ctx.max_c = max_c
        return out

    @staticmethod
    def backward(ctx, grad_out):
        sorted_x, sorted_e, counts, offsets, order, group_pos, w1, b1, w2, b2, pre, y = ctx.saved_tensors
        n, d, ff, max_c = ctx.n, ctx.d, ctx.ff, ctx.max_c
        dev = grad_out.device
        grad_y = torch.zeros((n, max_c, d), device=dev, dtype=grad_out.dtype)
        grad_y[sorted_e, group_pos] = grad_out
        sig = torch.sigmoid(pre)
        der = sig * (1 + pre * (1 - sig))
        h = torch.nn.functional.silu(pre)
        grad_h = grad_y @ w2
        grad_pre = grad_h * der
        group_x = torch.zeros((n, max_c, d), device=dev, dtype=sorted_x.dtype)
        group_x[sorted_e, group_pos] = sorted_x
        grad_x_group = grad_pre @ w1
        grad_w1 = torch.einsum("nmf,nmk->nfk", grad_pre, group_x)
        grad_b1 = grad_pre.sum(dim=1)
        grad_w2 = torch.einsum("nmd,nmf->ndf", grad_y, h)
        grad_b2 = grad_y.sum(dim=1)
        grad_sorted_x = grad_x_group[sorted_e, group_pos]
        return (
            grad_sorted_x,
            None, None, None, None, None,
            grad_w1, grad_b1, grad_w2, grad_b2,
            None, None, None, None,
        )


def triton_grouped_moe(sorted_x, sorted_e, counts, offsets, order, group_pos, w1, b1, w2, b2):
    n = w1.shape[0]
    d = w1.shape[2]
    ff = w1.shape[1]
    max_c = int(counts.max().item()) if counts.numel() else 0
    if max_c == 0:
        return torch.zeros_like(sorted_x)
    return _TritonGroupedMoE.apply(
        sorted_x, sorted_e, counts, offsets, order, group_pos,
        w1, b1, w2, b2, n, d, ff, max_c,
    )
