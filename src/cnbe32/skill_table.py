"""Skill table loader (v6.0 8105-character CJK encoding).

The SkillTable maps Unicode code points in the Basic CJK range
(U+4E00–U+9FFF) to CNBE-32 codes.  It can be constructed empty for
testing, or loaded from a ``.npy`` / ``.bin`` file on disk.

``SkillTable()`` without arguments is **not** valid.  Use the factories:

* :meth:`SkillTable.empty` — zero-filled table (safe for testing only)
* :meth:`SkillTable.from_file` — load a real table from disk
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

_CJK_START = 0x4E00
_CJK_END = 0x9FA5
_CJK_COUNT = 20902


class SkillTable:
    """81.6 KB lookup table for Basic CJK characters (20902 entries).

    The constructor requires a numpy array.  Prefer the factories:

    * :meth:`SkillTable.empty` — zero-filled table (testing only)
    * :meth:`SkillTable.from_file` — load ``.npy`` / ``.bin`` from disk

    .. note::
       An empty (zero-filled) table returns 0 for every character.
       This is safe for unit tests but should not be used for
       production lookups.  For real lookups, use
       :meth:`SkillTable.from_file` or the database APIs in
       :mod:`cnbe32.db`.
    """

    def __init__(self, table: np.ndarray) -> None:
        self.table = table

    # ------------------------------------------------------------------
    # Factories
    # ------------------------------------------------------------------

    @classmethod
    def empty(cls) -> SkillTable:
        """Return a zero-filled SkillTable.

        Safe for testing and offline usage.  All lookups return 0,
        meaning "no encoding found".
        """
        return cls(np.zeros(_CJK_COUNT, dtype=np.uint32))

    @classmethod
    def from_file(cls, path: str | Path) -> SkillTable:
        """Load a SkillTable from a ``.npy`` or ``.bin`` file.

        Args:
            path: Path to a ``.npy`` or ``.bin`` file with uint32
                  CNBE-32 codes.

        Returns:
            A new :class:`SkillTable`.

        Raises:
            FileNotFoundError: If *path* does not exist.
            ValueError: If the extension is unsupported.
        """
        path = Path(path)
        if not path.is_file():
            raise FileNotFoundError(f"SkillTable file not found: {path}")

        if path.suffix == ".npy":
            arr = np.load(path)
        elif path.suffix == ".bin":
            arr = np.frombuffer(
                open(path, "rb").read(), dtype=np.uint32
            )
        else:
            raise ValueError(
                f"Unsupported SkillTable file format: {path!r}. "
                "Use .npy or .bin."
            )
        return cls(arr)

    # ------------------------------------------------------------------
    # I/O
    # ------------------------------------------------------------------

    def load(self, path: str) -> None:
        """Load table data from *path* (``.npy`` or ``.bin``),
        replacing the current table in-place.
        """
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
        """Return the CNBE-32 code for a Unicode code point, or 0 if
        not found.
        """
        if _CJK_START <= unicode_cp <= _CJK_END:
            idx = unicode_cp - _CJK_START
            if idx < len(self.table):
                return int(self.table[idx])
        return 0

    def __getitem__(self, char: str) -> int:
        """``table['明']`` — convenient char-to-code lookup."""
        return self.lookup(ord(char))
