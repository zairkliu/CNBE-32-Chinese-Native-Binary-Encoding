import json
import sqlite3
from pathlib import Path

from cnbe32.db import close_connection, lookup


def load_runtime() -> dict:
    return json.loads(Path("data/cnbe32.json").read_text(encoding="utf-8"))


def test_runtime_json_contains_promoted_8105_samples() -> None:
    model = load_runtime()
    by_char = {row["char"]: row for row in model["characters"]}

    assert model["metadata"]["runtime_promotion"] == "8105_human_force_approved_cnbe32_runtime"
    assert model["metadata"]["patched_8105_rows"] == 6712
    assert model["metadata"]["force_approved_not_patched_rows"] == 1393
    assert len(model["characters"]) == 20902
    assert by_char["家"]["radix_name"] == "宀"
    assert by_char["家"]["strokes"] == 10
    assert by_char["家"]["struct_name"] == "上下"
    assert by_char["侵"]["struct_name"] == "左右"
    assert by_char["偶"]["struct_name"] == "左右"
    assert by_char["孓"]["struct_name"] == "独体字"


def test_runtime_json_bitfields_recompute() -> None:
    for row in load_runtime()["characters"]:
        ext = row["cnbe"] & 0x0F
        recomputed = (
            (row["radix"] << 24)
            | (row["strokes"] << 19)
            | (row["struct_type"] << 15)
            | (row["index"] << 4)
            | ext
        )
        assert recomputed == row["cnbe"]


def test_rebuilt_databases_match_runtime_samples() -> None:
    expected = {
        "家": (23478, "家", 676387680, 40, "宀", 10, 1, "上下", 1462),
        "侵": (20405, "侵", 155818832, 9, "亻", 9, 3, "左右", 437),
        "偶": (20598, "偶", 156870496, 9, "亻", 11, 3, "左右", 630),
        "孓": (23379, "孓", 655906096, 39, "子", 3, 0, "独体字", 1363),
    }
    for db_path in (Path("data/cnbe32.db"), Path("src/cnbe32/data/cnbe32.db")):
        with sqlite3.connect(db_path) as connection:
            assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
            assert connection.execute("SELECT COUNT(*) FROM cnbe32").fetchone()[0] == 20902
            for char, row in expected.items():
                assert (
                    connection.execute(
                        "SELECT unicode, char, cnbe, radix, radix_name, strokes, struct_type, struct_name, idx "
                        "FROM cnbe32 WHERE char = ?",
                        (char,),
                    ).fetchone()
                    == row
                )


def test_sdk_lookup_can_read_promoted_runtime_database(monkeypatch) -> None:
    monkeypatch.setenv("CNBE32_DB_PATH", str(Path("data/cnbe32.db").resolve()))
    close_connection()
    try:
        assert lookup("家")["struct_name"] == "上下"
        assert lookup("侵")["struct_name"] == "左右"
        assert lookup("偶")["struct_name"] == "左右"
        assert lookup("孓")["struct_name"] == "独体字"
    finally:
        close_connection()
