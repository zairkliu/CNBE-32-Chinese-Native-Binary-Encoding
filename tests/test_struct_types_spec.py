import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "spec" / "struct_types.json"
PACKAGE_DB = ROOT / "src" / "cnbe32" / "data" / "cnbe32.db"


def load_spec() -> dict:
    return json.loads(SPEC_PATH.read_text(encoding="utf-8"))


def test_structure_spec_declares_national_standard_review_labels() -> None:
    spec = load_spec()
    target = spec["national_standard_target"]

    assert spec["schema"] == "cnbe32-structure-types-v1"
    assert "8105" in target["source"]
    assert target["allowed_review_labels"] == [
        "独体字",
        "上下",
        "上中下",
        "左右",
        "左中右",
        "左上包",
        "右上包",
        "左三包",
        "左下包",
        "上三包",
        "下三包",
        "全包围",
        "镶嵌",
    ]


def test_runtime_structure_aliases_are_explicitly_registered() -> None:
    spec = load_spec()
    runtime = spec["runtime_v1_0_4"]

    assert set(runtime) == {str(value) for value in range(13)}
    for value, entry in runtime.items():
        assert entry["canonical_review_label"]
        assert entry["canonical_review_label"] in entry["runtime_aliases"]
        assert len(entry["runtime_aliases"]) >= 1
        assert int(value) >= 0


def test_packaged_runtime_database_uses_only_registered_structure_pairs() -> None:
    spec = load_spec()["runtime_v1_0_4"]
    allowed = {
        (int(value), alias)
        for value, entry in spec.items()
        for alias in entry["runtime_aliases"]
    }

    with sqlite3.connect(PACKAGE_DB) as connection:
        pairs = set(
            connection.execute(
                "SELECT DISTINCT struct_type, struct_name FROM cnbe32"
            ).fetchall()
        )

    assert pairs
    assert pairs <= allowed


def test_structure_spec_keeps_legacy_runtime_boundary_visible() -> None:
    text = SPEC_PATH.read_text(encoding="utf-8")

    assert "runtime-compatibility-spec" in text
    assert "does not certify every legacy runtime row" in text
    assert "national_standard_target" in text
    assert "runtime_v1_0_4" in text
