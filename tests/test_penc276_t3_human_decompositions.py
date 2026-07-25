"""Verify the owner-supplied T3 decomposition intake remains evidence-bounded."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "apply_penc276_t3_human_decompositions.py"
LEDGER = ROOT / "evidence" / "8105" / "pending276" / "T3_169_276_HUMAN_DECOMPOSITION_LEDGER.csv"
RESULT = ROOT / "reports" / "PENC276_T3_169_276_HUMAN_DECOMPOSITION_INTAKE.json"


def test_human_decomposition_intake_matches_backlog_and_preserves_stops() -> None:
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True)
    with LEDGER.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    result = json.loads(RESULT.read_text(encoding="utf-8"))

    assert len(rows) == 108
    assert result["human_decomposition_recorded"] == 105
    assert {entry["row_id"] for entry in result["pending_clarification"]} == {"PENC_194", "PENC_247", "PENC_271"}
    assert not result["decision"]["may_generate_cnbe_candidates"]
    assert not result["decision"]["may_modify_source_tables"]
    assert not result["decision"]["may_claim_national_standard"]
