# -*- coding: utf-8 -*-
"""小型 CNBE-MoE / Dense 对比模型：编码嵌入 + 注意力 + MoE/Dense FFN。"""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F

from src.cnbe_router import CNBERouter


class ExpertFFN(nn.Module):
    def __init__(self, d_model: int, d_ff: int, dropout: float = 0.1):
        super().__init__()
        self.fc1 = nn.Linear(d_model, d_ff)
        self.fc2 = nn.Linear(d_ff, d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.dropout(self.fc2(F.silu(self.fc1(x))))


class LearnedRouter(nn.Module):
    """CNBE 字段 -> 专家 softmax 路由（可学习）。"""

    def __init__(self, d_model: int, num_experts: int):
        super().__init__()
        self.radix_emb = nn.Embedding(256, d_model)
        self.strokes_emb = nn.Embedding(32, d_model)
        self.struct_emb = nn.Embedding(16, d_model)
        self.idx_emb = nn.Embedding(2048, d_model)
        self.mlp = nn.Sequential(
            nn.Linear(d_model, d_model),
            nn.SiLU(),
            nn.Linear(d_model, num_experts),
        )

    def forward(self, codes: torch.Tensor) -> torch.Tensor:
        radix = (codes >> 24) & 0xFF
        strokes = (codes >> 19) & 0x1F
        struct = (codes >> 15) & 0x0F
        idx = codes & 0x7FF
        h = (
            self.radix_emb(radix)
            + self.strokes_emb(strokes)
            + self.struct_emb(struct)
            + self.idx_emb(idx)
        )
        return torch.softmax(self.mlp(h), dim=-1)


class MoEFFN(nn.Module):
    def __init__(
        self,
        d_model: int,
        d_ff: int,
        num_experts: int,
        top_k: int,
        router: CNBERouter,
        use_triton: bool = False,
        learned_router: bool = False,
    ):
        super().__init__()
        self.num_experts = num_experts
        self.top_k = top_k
        self.router = router
        self.use_triton = use_triton
        self.learned_router = learned_router
        self.experts = nn.ModuleList([ExpertFFN(d_model, d_ff) for _ in range(num_experts)])
        if learned_router:
            self.router_net = LearnedRouter(d_model, num_experts)

    def _learned_forward(self, x: torch.Tensor, codes: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        b, s, d = x.shape
        weights = self.router_net(codes)  # (b, s, n)
        flat_x = x.reshape(-1, d)
        flat_w = weights.reshape(-1, self.num_experts)
        top_w, top_idx = torch.topk(flat_w, self.top_k, dim=-1)
        out = torch.zeros_like(flat_x)
        for kk in range(self.top_k):
            e_idx = top_idx[:, kk]
            w = top_w[:, kk]
            for e in range(self.num_experts):
                mask = e_idx == e
                if mask.any():
                    out[mask] += w[mask].unsqueeze(-1) * self.experts[e](flat_x[mask])
        load = weights.sum(dim=(0, 1))
        self.last_probs = weights
        return out.reshape(b, s, d), load

    def forward(self, x: torch.Tensor, codes: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        b, s, d = x.shape
        t = b * s
        k = self.top_k
        expert_idx = self.router.route(codes).reshape(-1)  # (t*k,)
        flat_x = x.reshape(t, d).repeat_interleave(k, dim=0)  # (t*k, d)
        order = torch.argsort(expert_idx, stable=True)
        sorted_e = expert_idx[order]
        sorted_x = flat_x[order]
        counts = torch.bincount(sorted_e, minlength=self.num_experts)
        offsets = torch.cumsum(counts, 0) - counts
        max_c = int(counts.max().item()) if counts.numel() else 0
        slot_idx = torch.arange(t * k, device=x.device, dtype=torch.long)
        group_pos = slot_idx - offsets[sorted_e]
        w1 = torch.stack([ex.fc1.weight for ex in self.experts])  # (n, ff, d)
        b1 = torch.stack([ex.fc1.bias for ex in self.experts])  # (n, ff)
        w2 = torch.stack([ex.fc2.weight for ex in self.experts])  # (n, d, ff)
        b2 = torch.stack([ex.fc2.bias for ex in self.experts])  # (n, d)
        if self.learned_router:
            return self._learned_forward(x, codes)
        if self.use_triton:
            from src.triton_moe import TRITON_AVAILABLE, triton_grouped_moe

            if TRITON_AVAILABLE:
                result = triton_grouped_moe(
                    sorted_x, sorted_e, counts, offsets, order, group_pos, w1, b1, w2, b2
                )
                out_slots = torch.zeros(t * k, d, device=x.device, dtype=x.dtype)
                out_slots[order] = result
            else:
                out_slots = self._vectorized(sorted_x, sorted_e, group_pos, order, counts, offsets, w1, b1, w2, b2, t, k, d)
        else:
            out_slots = self._vectorized(sorted_x, sorted_e, group_pos, order, counts, offsets, w1, b1, w2, b2, t, k, d)
        out = out_slots.view(t, k, d).sum(dim=1).reshape(b, s, d)
        return out, counts.float()

    def _vectorized(self, sorted_x, sorted_e, group_pos, order, counts, offsets, w1, b1, w2, b2, t, k, d):
        n = w1.shape[0]
        max_c = int(counts.max().item()) if counts.numel() else 0
        group_x = torch.zeros(n, max_c, d, device=sorted_x.device, dtype=sorted_x.dtype)
        group_x[sorted_e, group_pos] = sorted_x
        h = torch.baddbmm(b1.unsqueeze(1), group_x, w1.transpose(1, 2))
        h = F.silu(h)
        y = torch.baddbmm(b2.unsqueeze(1), h, w2.transpose(1, 2))
        out_slots = torch.zeros(t * k, d, device=sorted_x.device, dtype=sorted_x.dtype)
        out_slots[order] = y[sorted_e, group_pos]
        return out_slots


class Block(nn.Module):
    def __init__(
        self,
        d_model: int,
        n_heads: int,
        d_ff: int,
        use_moe: bool,
        num_experts: int,
        top_k: int,
        router: CNBERouter,
        use_triton: bool = False,
        learned_router: bool = False,
    ):
        super().__init__()
        self.attn = nn.MultiheadAttention(d_model, n_heads, batch_first=True)
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.use_moe = use_moe
        if use_moe:
            self.ffn = MoEFFN(d_model, d_ff, num_experts, top_k, router, use_triton, learned_router)
        else:
            self.ffn = ExpertFFN(d_model, d_ff)

    def forward(self, x: torch.Tensor, codes: torch.Tensor | None = None) -> tuple[torch.Tensor, torch.Tensor]:
        attn_out, _ = self.attn(x, x, x)
        x = self.norm1(x + attn_out)
        if self.use_moe and codes is not None:
            ffn_out, load = self.ffn(x, codes)
            if hasattr(self.ffn, "last_probs"):
                self.last_probs = self.ffn.last_probs
            x = self.norm2(x + ffn_out)
            return x, load
        x = self.norm2(x + self.ffn(x))
        return x, torch.zeros(self.ffn.num_experts, device=x.device) if self.use_moe else torch.tensor([0.0])


class CNBEModel(nn.Module):
    def __init__(
        self,
        vocab_size: int,
        d_model: int = 256,
        d_ff: int = 1024,
        n_layers: int = 2,
        n_heads: int = 4,
        num_experts: int = 8,
        top_k: int = 2,
        use_moe: bool = True,
        mapping_path: str | None = None,
        dropout: float = 0.1,
        use_triton: bool = False,
        learned_router: bool = False,
    ):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, d_model)
        self.pos = nn.Parameter(torch.zeros(1, 512, d_model))
        nn.init.normal_(self.pos, std=0.02)
        self.router = CNBERouter(num_experts=num_experts, mapping_path=mapping_path, num_activated=top_k)
        self.blocks = nn.ModuleList(
            [
                Block(d_model, n_heads, d_ff, use_moe, num_experts, top_k, self.router, use_triton, learned_router)
                for _ in range(n_layers)
            ]
        )
        self.norm = nn.LayerNorm(d_model)
        self.head = nn.Linear(d_model, vocab_size)
        self.radix_head = nn.Linear(d_model, 256)
        self.strokes_head = nn.Linear(d_model, 32)
        self.struct_head = nn.Linear(d_model, 16)
        self.idx_head = nn.Linear(d_model, 2048)
        self.dropout = nn.Dropout(dropout)
        self.use_moe = use_moe
        self.num_experts = num_experts
        self.d_model = d_model

    def forward(self, ids: torch.Tensor, codes: torch.Tensor) -> tuple[torch.Tensor, dict, torch.Tensor]:
        b, s = ids.shape
        x = self.dropout(self.embed(ids)) + self.pos[:, :s]
        total_load = torch.zeros(self.num_experts, device=x.device)
        for blk in self.blocks:
            x, load = blk(x, codes)
            if load.dim() > 0 and load.numel() > 1:
                total_load += load
        self.last_router_probs = getattr(self.blocks[-1], "last_probs", None)
        x = self.norm(x)
        logits = self.head(x)
        field_logits = {
            "radix": self.radix_head(x),
            "strokes": self.strokes_head(x),
            "struct": self.struct_head(x),
            "idx": self.idx_head(x),
        }
        return logits, field_logits, total_load

    @staticmethod
    def gini(load: torch.Tensor) -> float:
        s = load.float().sort()[0]
        n = s.numel()
        if s.sum() <= 0:
            return 0.0
        cum = s.cumsum(0)
        return float((n + 1 - 2 * (cum / s.sum()).sum()) / n)
