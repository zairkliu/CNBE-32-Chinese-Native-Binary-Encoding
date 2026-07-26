"""Guard the no-write T3 decomposition intake for rows 169 through 276."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_penc276_t3_decomposition_intake.py"
BACKLOG = ROOT / "evidence" / "8105" / "pending276" / "T3_169_276_DECOMPOSITION_BACKLOG.csv"
RESULT = ROOT / "reports" / "PENC276_T3_169_276_DECOMPOSITION_INTAKE.json"


def test_t3_intake_is_complete_and_never_generates_candidates() -> None:
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True)
    with BACKLOG.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    result = json.loads(RESULT.read_text(encoding="utf-8"))

    assert len(rows) == 108
    assert {row["tier"] for row in rows} == {"T3"}
    assert {row["owner_audit_structure_note"] for row in rows} == {"struct_cjkvi_accurate"}
    assert {row["candidate_cnbe_status"] for row in rows} == {"NOT_GENERATED"}
    assert result["decision"]["status"] == "BACKLOG_READY_DECOMPOSITION_EVIDENCE_REQUIRED"
    assert not result["decision"]["may_generate_cnbe_candidates"]
    assert not result["decision"]["may_modify_source_tables"]
