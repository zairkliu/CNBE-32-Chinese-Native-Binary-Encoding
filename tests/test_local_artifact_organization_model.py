import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "reports" / "local_artifact_organization_model.json"


def test_local_artifact_organization_model_records_push_boundary() -> None:
    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))

    assert model["status"] == "LOCAL_ARTIFACT_ORGANIZATION_MODEL_READY"
    assert model["branch"] == "data/basic-cjk-scope-gap"
    assert len(model["commit_groups"]) == 4
    assert model["non_goals"] == {
        "github_release": False,
        "pypi_publish": False,
        "tag": False,
        "validate_97686_full_catalog_claim": False,
    }


def test_large_full_catalog_intermediates_remain_untracked() -> None:
    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    tracked = set(
        subprocess.check_output(
            ["git", "ls-files"],
            cwd=ROOT,
            text=True,
        ).splitlines()
    )

    for item in model["excluded_large_intermediates"]:
        assert item["policy"] == "regenerate_from_script_do_not_commit"
        assert item["path"] not in tracked


def test_no_tracked_file_exceeds_github_single_file_limit() -> None:
    tracked = subprocess.check_output(
        ["git", "ls-files"],
        cwd=ROOT,
        text=True,
    ).splitlines()

    oversized = []
    for relative_path in tracked:
        path = ROOT / relative_path
        if path.is_file() and path.stat().st_size > 100_000_000:
            oversized.append(relative_path)

    assert oversized == []
