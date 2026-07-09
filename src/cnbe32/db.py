"""CNBE-32 SQLite-backed lookup module.

Database path resolution (in priority order):
  1. CNBE32_DB_PATH environment variable
  2. cnbe32.db shipped inside the package (via importlib.resources)
  3. data/cnbe32.db relative to the repository root (source installs)
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

_conn: sqlite3.Connection | None = None
_cursor: sqlite3.Cursor | None = None


def resolve_db_path() -> Path:
    """Return the best available path to cnbe32.db.

    Resolution order:
    1. CNBE32_DB_PATH environment variable
    2. importlib.resources from the cnbe32 package (works for wheel / pip install)
    3. data/cnbe32.db found by walking up from this file's location (source repo)

    Raises :class: with a clear message if no path can be resolved.
    """
    # 1. Environment variable override
    env_path = os.environ.get("CNBE32_DB_PATH")
    if env_path:
        p = Path(env_path)
        if p.is_file():
            return p
        raise FileNotFoundError(
            f"CNBE32_DB_PATH is set to '{env_path}' but the file does not exist."
        )

    # 2. importlib.resources (works when installed as a wheel / pip install)
    try:
        from importlib.resources import files as _resources_files

        db_file = _resources_files("cnbe32") / "data" / "cnbe32.db"
        if db_file.is_file():
            return db_file
    except Exception:  # noqa: BLE001
        pass

    # 3. Walk up from __file__ to find the repo root (source installs)
    candidate = Path(__file__).resolve().parent.parent.parent / "data" / "cnbe32.db"
    if candidate.is_file():
        return candidate

    raise FileNotFoundError(
        "CNBE-32 database (cnbe32.db) not found.\n"
        "Set the CNBE32_DB_PATH environment variable to the location of cnbe32.db,\n"
        "e.g.  export CNBE32_DB_PATH=/path/to/cnbe32.db\n"
        "Or run  to generate the database in the expected location."
    )


def _ensure_db() -> None:
    global _conn, _cursor
    if _conn is not None:
        return
    db_path = resolve_db_path()
    _conn = sqlite3.connect(str(db_path))
    _conn.row_factory = sqlite3.Row
    _cursor = _conn.cursor()


def lookup(char: str) -> dict | None:
    """Look up a single CJK character. Returns dict or None."""
    _ensure_db()
    _cursor.execute("SELECT * FROM cnbe32 WHERE char = ?", (char,))
    row = _cursor.fetchone()
    return dict(row) if row else None


def search(code: int) -> dict | None:
    """Search by 32-bit CNBE code. Returns dict or None."""
    _ensure_db()
    _cursor.execute("SELECT * FROM cnbe32 WHERE cnbe = ?", (code,))
    row = _cursor.fetchone()
    return dict(row) if row else None


def batch(chars: str | list[str]) -> list[dict]:
    """Batch lookup multiple characters.

    Accepts a string (iterated per-character) or a list of strings.
    Returns an empty list when given an empty input.
    """
    if isinstance(chars, str):
        chars = list(chars)
    if not chars:
        return []
    _ensure_db()
    placeholders = ",".join("?" for _ in chars)
    _cursor.execute(
        f"SELECT * FROM cnbe32 WHERE char IN ({placeholders})", list(chars)
    )
    return [dict(row) for row in _cursor.fetchall()]


def by_radix(radix_id: int) -> list[dict]:
    """Get all characters sharing a radical. Returns list of dicts."""
    _ensure_db()
    _cursor.execute(
        "SELECT * FROM cnbe32 WHERE radix = ? ORDER BY strokes", (radix_id,)
    )
    return [dict(row) for row in _cursor.fetchall()]


def count() -> int:
    """Get total number of entries."""
    _ensure_db()
    _cursor.execute("SELECT COUNT(*) FROM cnbe32")
    return _cursor.fetchone()[0]


def stats() -> dict:
    """Get database statistics (total, stroke distribution, radices, structures)."""
    _ensure_db()
    result: dict = {}
    _cursor.execute("SELECT COUNT(*) as total FROM cnbe32")
    result["total"] = _cursor.fetchone()[0]
    _cursor.execute("SELECT MIN(strokes), MAX(strokes), AVG(strokes) FROM cnbe32")
    s = _cursor.fetchone()
    result["strokes"] = {"min": s[0], "max": s[1], "avg": round(s[2], 1)}
    _cursor.execute("SELECT COUNT(DISTINCT radix) FROM cnbe32")
    result["radices"] = _cursor.fetchone()[0]
    _cursor.execute("SELECT COUNT(DISTINCT struct_type) FROM cnbe32")
    result["structures"] = _cursor.fetchone()[0]
    return result


def close() -> None:
    """Close the module-level database connection, if open."""
    global _conn, _cursor
    if _conn:
        _conn.close()
        _conn = None
        _cursor = None
