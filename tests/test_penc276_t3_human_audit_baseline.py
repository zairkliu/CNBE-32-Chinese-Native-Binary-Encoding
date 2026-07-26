"""Keep the exploratory T3 baseline human-audit-first and non-promotional."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_penc276_t3_human_audit_baseline.py"
OUTPUT = ROOT / "evidence" / "8105" / "pending276" / "T3_169_276_FINAL_HUMAN_AUDIT_BASELINE.csv"
REPORT = ROOT / "reports" / "PENC276_T3_169_276_FINAL_HUMAN_AUDIT_BASELINE.json"


def test_human_audit_is_the_final_exploratory_baseline() -> None:
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True)
    with OUTPUT.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    result = json.loads(REPORT.read_text(encoding="utf-8"))

    assert len(rows) == 108
    assert {row["final_project_basis"] for row in rows} == {"HUMAN_AUDIT"}
    assert {row["external_reference_role"] for row in rows} == {"ALIGNMENT_ONLY_NOT_GOLD_STANDARD"}
    assert {row["candidate_cnbe_status"] for row in rows} == {"NOT_GENERATED"}
    assert result["decision"]["status"] == "PASS_HUMAN_AUDIT_FINAL_EXPLORATORY_BASELINE"
    assert not result["decision"]["may_claim_national_standard"]
