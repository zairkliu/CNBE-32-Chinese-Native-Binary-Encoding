"""Skill table utilities for CNBE-32 experiments."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .constants import BASIC_CJK_COUNT, CJK_BASE


class SkillTable:
    """A fixed-size table indexed by Basic CJK Unicode code point offset.

    Use SkillTable.empty() explicitly for tests or zero-initialized experiments.
    Use SkillTable.from_file(path) to load a real table from disk.
    """

    def __init__(self, table: np.ndarray) -> None:
        if table.shape != (BASIC_CJK_COUNT,):
            raise ValueError(
                f"SkillTable must have shape ({BASIC_CJK_COUNT},); got {table.shape}"
            )
        self.table = table.astype(np.uint32, copy=False)

    @classmethod
    def empty(cls) -> SkillTable:
        """Create an explicit all-zero skill table."""
        return cls(np.zeros(BASIC_CJK_COUNT, dtype=np.uint32))

    @classmethod
    def from_file(cls, path: str | Path) -> SkillTable:
        """Load a skill table from a .npy file."""
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"Skill table file does not exist: {file_path}")
        table = np.load(file_path)
        return cls(table)

    def lookup(self, codepoint: int) -> int:
        """Return the table value for a Basic CJK Unicode code point."""
        idx = codepoint - CJK_BASE
        if idx < 0 or idx >= BASIC_CJK_COUNT:
            raise ValueError(
                f"codepoint must be in Basic CJK range starting at U+{CJK_BASE:04X}"
            )
        return int(self.table[idx])
