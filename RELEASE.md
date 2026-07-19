# Release Process

This document describes the release checklist for CNBE-32.

The project is currently a research prototype. Releases should be treated as SDK engineering checkpoints, not as claims of full CJK coverage or production readiness.

## Release checklist

Before publishing a release candidate:

```bash
python -m pip install -U pip build pytest ruff tomli
python scripts/validate_format_integrity.py
python -m compileall src tests scripts
python -m build
python scripts/verify_release_artifacts.py
python -m pip install --force-reinstall dist/*.whl
python -c "import cnbe32; print(cnbe32.__all__)"
pytest
ruff check src tests scripts
make -C c/golden_vectors clean
make -C c/golden_vectors test
cargo test --manifest-path rust/golden_vectors/Cargo.toml
```

Public CI runs the repository-reproducible pytest subset. The complete
administrator validation may run plain `pytest` on a workstation that has the
local `cnbe-research` authority workspace mounted. Do not require public CI to
read private local knowledge assets.

Do not tag or publish unless remote `main` has passed format integrity checks.

Confirm the wheel contains expected package data:

```python
from pathlib import Path
import zipfile

wheels = sorted(Path("dist").glob("*.whl"))
if not wheels:
    raise SystemExit("No wheel found in dist/")
wheel = wheels[-1]
with zipfile.ZipFile(wheel) as zf:
    names = set(zf.namelist())
if not any(n.startswith("cnbe32/") for n in names):
    raise SystemExit("Missing cnbe32 package files in wheel")
print("Wheel content check PASS")
```

## Versioning

The Python SDK version is declared in `pyproject.toml`. Do not bump the version unless the release is intentional.

## Tagging

Only tag after all CI checks are green and the changelog is updated. Do not tag automatically unless explicitly requested.

## PyPI

Do not publish to PyPI automatically. Future PyPI releases require explicit
manual authorization, a clean release checklist, and post-upload verification.
