"""Skill table loader (v6.0 8105-character CJK encoding).

The SkillTable maps Unicode code points in the Basic CJK range
(U+4E00-U+9FFF) to CNBE-32 codes.  It can be constructed empty for
testing, or loaded from a ``.npy`` / ``.bin`` file on disk.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

_CJK_START = 0x4E00
_CJK_END = 0x9FA5
_CJK_COUNT = 20902


class SkillTable:
    """81.6 KB lookup table for Basic CJK characters (20902 entries).

    Calling ``SkillTable()`` is **not** supported — it raises
    :exc:`TypeError`.  Use one of the factories instead:

    * :meth:`SkillTable.empty` — zero-filled table (safe for testing)
    * :meth:`SkillTable.from_file` — load a ``.npy`` / ``.bin`` from disk
    """

    def __init__(self) -> None:
        raise TypeError(
            "SkillTable() is not supported. "
            "Use SkillTable.empty() for a zero-filled table, "
            "or SkillTable.from_file(path) to load a real table from disk."
        )

    # ------------------------------------------------------------------
    # Constructors
    # ------------------------------------------------------------------

    @classmethod
    def empty(cls) -> SkillTable:
        """Return a zero-filled SkillTable.

        This is a safe default for tests and offline usage.  A zero table
        will return 0 for every lookup, which means "no encoding found".
        """
        inst = object.__new__(cls)
        inst.table = np.zeros(_CJK_COUNT, dtype=np.uint32)
        return inst

    @classmethod
    def from_file(cls, path: str | Path) -> SkillTable:
        """Load a SkillTable from a ``.npy`` or ``.bin`` file.

        Args:
            path: Path to a numpy ``.npy`` file or a raw ``.bin`` file
                  containing uint32 values.

        Returns:
            A new :class:`SkillTable` with data loaded from *path*.

        Raises:
            FileNotFoundError: If *path* does not exist.
            ValueError: If *path* has an unrecognised file extension.
        """
        path = Path(path)
        if not path.is_file():
            raise FileNotFoundError(f"SkillTable file not found: {path}")

        inst = object.__new__(cls)
        inst.table = np.zeros(_CJK_COUNT, dtype=np.uint32)
        inst._do_load(str(path))
        return inst

    # ------------------------------------------------------------------
    # I/O
    # ------------------------------------------------------------------

    def load(self, path: str) -> None:
        """Load table data from *path* (``.npy`` or ``.bin``)."""
        self._do_load(path)

    def _do_load(self, path: str) -> None:
        if path.endswith(".npy"):
            self.table = np.load(path)
        elif path.endswith(".bin"):
            self.table = np.frombuffer(
                open(path, "rb").read(), dtype=np.uint32
            )
        else:
            raise ValueError(
                f"Unsupported SkillTable file format: {path!r}. "
                "Use .npy or .bin."
            )

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def lookup(self, unicode_cp: int) -> int:
        """Return the CNBE-32 code for a Unicode code point, or 0 if not found."""
        if _CJK_START <= unicode_cp <= _CJK_END:
            idx = unicode_cp - _CJK_START
            if idx < len(self.table):
                return int(self.table[idx])
        return 0

    def __getitem__(self, char: str) -> int:
        """``table['明']`` — convenient char-to-code lookup."""
        return self.lookup(ord(char))
