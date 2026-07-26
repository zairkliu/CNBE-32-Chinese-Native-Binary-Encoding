"""Ensure non-renderable component approval never invents a replacement glyph."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "resolve_penc276_t3_nonrenderable_components.py"
RESOLUTION = ROOT / "evidence" / "8105" / "pending276" / "T3_169_276_NONRENDERABLE_COMPONENT_RESOLUTION.csv"
RESULT = ROOT / "reports" / "PENC276_T3_169_276_NONRENDERABLE_COMPONENT_RESOLUTION.json"


def test_nonrenderable_components_are_approved_without_substitution() -> None:
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True)
    with RESOLUTION.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    result = json.loads(RESULT.read_text(encoding="utf-8"))

    assert {row["row_id"] for row in rows} == {"PENC_194", "PENC_247", "PENC_271"}
    assert {row["resolution_status"] for row in rows} == {"HUMAN_APPROVED_NONRENDERABLE_COMPONENT_GLYPH"}
    assert {row["component_substitution"] for row in rows} == {"PROHIBITED"}
    assert result["decision"]["may_use_human_decomposition_for_review"]
    assert not result["decision"]["may_substitute_missing_component_glyphs"]
    assert not result["decision"]["may_generate_cnbe_candidates"]
