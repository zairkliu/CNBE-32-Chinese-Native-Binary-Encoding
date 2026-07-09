"""SQLite lookup helpers for CNBE-32 character metadata."""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterable
from importlib.resources import as_file, files
from pathlib import Path

from .exceptions import CNBEDatabaseError

_ENV_DB_PATH = "CNBE32_DB_PATH"
_CONN: sqlite3.Connection | None = None


def resolve_db_path() -> Path:
    """Resolve the CNBE-32 SQLite database path.

    Resolution order:
    1. CNBE32_DB_PATH
    2. package data: cnbe32/data/cnbe32.db
    3. source repository fallback: data/cnbe32.db
    """
    env_path = os.environ.get(_ENV_DB_PATH)
    if env_path:
        path = Path(env_path).expanduser()
        if path.exists():
            return path
        raise CNBEDatabaseError(
            f"{_ENV_DB_PATH} is set but file does not exist: {path}"
        )

    try:
        resource = files("cnbe32").joinpath("data", "cnbe32.db")
        with as_file(resource) as path:
            if path.exists():
                return Path(path)
    except (FileNotFoundError, ModuleNotFoundError):
        pass

    source_path = Path(__file__).resolve().parents[2] / "data" / "cnbe32.db"
    if source_path.exists():
        return source_path

    raise CNBEDatabaseError(
        "CNBE-32 database file cnbe32.db was not found. "
        f"Set {_ENV_DB_PATH}=/path/to/cnbe32.db "
        "or install the package with bundled data."
    )


def get_connection() -> sqlite3.Connection:
    """Return a cached SQLite connection."""
    global _CONN
    if _CONN is None:
        db_path = resolve_db_path()
        _CONN = sqlite3.connect(str(db_path))
        _CONN.row_factory = sqlite3.Row
    return _CONN


def close_connection() -> None:
    """Close the cached SQLite connection."""
    global _CONN
    if _CONN is not None:
        _CONN.close()
        _CONN = None


def lookup(char: str) -> dict | None:
    """Look up one CJK character in the database."""
    if len(char) != 1:
        raise ValueError("lookup() expects exactly one character")
    conn = get_connection()
    row = conn.execute("SELECT * FROM cnbe32 WHERE char = ?", (char,)).fetchone()
    return dict(row) if row is not None else None


def batch(chars: str | Iterable[str]) -> list[dict]:
    """Look up multiple characters.

    Empty input returns an empty list.
    """
    if isinstance(chars, str):
        items = list(chars)
    else:
        items = list(chars)
    if not items:
        return []
    placeholders = ",".join("?" for _ in items)
    conn = get_connection()
    rows = conn.execute(
        f"SELECT * FROM cnbe32 WHERE char IN ({placeholders})", items
    ).fetchall()
    return [dict(row) for row in rows]


def count() -> int:
    """Return the number of entries in the database."""
    conn = get_connection()
    row = conn.execute("SELECT COUNT(*) AS n FROM cnbe32").fetchone()
    return int(row["n"])
