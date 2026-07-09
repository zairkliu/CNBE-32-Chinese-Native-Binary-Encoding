from __future__ import annotations

from importlib.resources import files


def test_package_data_database_resource_path_is_declared() -> None:
    resource = files("cnbe32").joinpath("data", "cnbe32.db")
    assert resource.name == "cnbe32.db"
