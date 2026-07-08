"""CNBE-32 SQLite-backed lookup module"""
import os, sqlite3

_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "cnbe32.db")
_conn = None
_cursor = None

def _ensure_db():
    global _conn, _cursor
    if _conn is not None:
        return
    if not os.path.exists(_DB_PATH):
        raise FileNotFoundError(f"CNBE-32 database not found: {_DB_PATH}. Run `python tools/generate_mapping.py` first.")
    _conn = sqlite3.connect(_DB_PATH)
    _conn.row_factory = sqlite3.Row
    _cursor = _conn.cursor()

def lookup(char):
    """Look up a single CJK character. Returns dict or None."""
    _ensure_db()
    _cursor.execute("SELECT * FROM cnbe32 WHERE char = ?", (char,))
    row = _cursor.fetchone()
    if row:
        return dict(row)
    return None

def search(code):
    """Search by 32-bit CNBE code. Returns dict or None."""
    _ensure_db()
    _cursor.execute("SELECT * FROM cnbe32 WHERE cnbe = ?", (code,))
    row = _cursor.fetchone()
    if row:
        return dict(row)
    return None

def batch(chars):
    """Batch lookup multiple characters. Returns list of dicts."""
    _ensure_db()
    placeholders = ",".join("?" for _ in chars)
    _cursor.execute(f"SELECT * FROM cnbe32 WHERE char IN ({placeholders})", list(chars))
    return [dict(row) for row in _cursor.fetchall()]

def by_radix(radix_id):
    """Get all characters sharing a radical. Returns list of dicts."""
    _ensure_db()
    _cursor.execute("SELECT * FROM cnbe32 WHERE radix = ? ORDER BY strokes", (radix_id,))
    return [dict(row) for row in _cursor.fetchall()]

def count():
    """Get total number of entries."""
    _ensure_db()
    _cursor.execute("SELECT COUNT(*) FROM cnbe32")
    return _cursor.fetchone()[0]

def stats():
    """Get database statistics."""
    _ensure_db()
    stats = {}
    _cursor.execute("SELECT COUNT(*) as total FROM cnbe32")
    stats["total"] = _cursor.fetchone()[0]
    _cursor.execute("SELECT MIN(strokes), MAX(strokes), AVG(strokes) FROM cnbe32")
    s = _cursor.fetchone()
    stats["strokes"] = {"min": s[0], "max": s[1], "avg": round(s[2], 1)}
    _cursor.execute("SELECT COUNT(DISTINCT radix) FROM cnbe32")
    stats["radices"] = _cursor.fetchone()[0]
    _cursor.execute("SELECT COUNT(DISTINCT struct_type) FROM cnbe32")
    stats["structures"] = _cursor.fetchone()[0]
    return stats

def close():
    global _conn, _cursor
    if _conn:
        _conn.close()
        _conn = None
        _cursor = None


