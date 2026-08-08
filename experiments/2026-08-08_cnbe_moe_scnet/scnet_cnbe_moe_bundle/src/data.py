# -*- coding: utf-8 -*-
"""加载 .cnbe 二进制流并构造训练/评估数据。"""

from __future__ import annotations

import struct
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import Dataset


def load_codes(paths: list[str], max_tokens: int | None = None) -> np.ndarray:
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
    return np.concatenate(chunks) if chunks else np.array([], dtype=np.int64)


def build_vocab(codes: np.ndarray) -> dict[int, int]:
    unique = np.unique(codes)
    return {int(c): i for i, c in enumerate(unique)}


def id_to_code_array(vocab: dict[int, int]) -> np.ndarray:
    arr = np.zeros(max(vocab.values()) + 1, dtype=np.int64)
    for code, cid in vocab.items():
        arr[cid] = code
    return arr


def fields_from_codes(codes: np.ndarray) -> dict[str, np.ndarray]:
    return {
        "radix": (codes >> 24) & 0xFF,
        "strokes": (codes >> 19) & 0x1F,
        "struct": (codes >> 15) & 0x0F,
        "idx": codes & 0x7FF,
    }


class CodeDataset(Dataset):
    def __init__(self, codes: np.ndarray, code_to_id: dict[int, int], seq_len: int = 64):
        self.ids = np.array([code_to_id[int(c)] for c in codes], dtype=np.int64)
        self.raw = codes
        self.seq_len = seq_len
        n = (len(self.ids) - 1) // seq_len
        self.n = max(0, n)

    def __len__(self) -> int:
        return self.n

    def __getitem__(self, idx: int):
        start = idx * self.seq_len
        x = self.ids[start : start + self.seq_len]
        y = self.ids[start + 1 : start + self.seq_len + 1]
        xc = self.raw[start : start + self.seq_len]
        yc = self.raw[start + 1 : start + self.seq_len + 1]
        return (
            torch.tensor(x, dtype=torch.long),
            torch.tensor(y, dtype=torch.long),
            torch.tensor(xc, dtype=torch.long),
            torch.tensor(yc, dtype=torch.long),
        )
