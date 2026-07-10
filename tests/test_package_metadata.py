from __future__ import annotations

from importlib.resources import as_file, files


def test_package_data_database_resource_path_is_declared() -> None:
    resource = files("cnbe32").joinpath("data", "cnbe32.db")
    assert resource.name == "cnbe32.db"
    with as_file(resource) as path:
        assert path.is_file()
        assert path.stat().st_size > 0
