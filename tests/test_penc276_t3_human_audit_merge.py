"""Verify the merged T3 audit ledger preserves every remaining evidence gate."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "merge_penc276_t3_human_audit.py"
MERGED = ROOT / "evidence" / "8105" / "pending276" / "T3_169_276_HUMAN_AUDIT_MERGED.csv"
RESULT = ROOT / "reports" / "PENC276_T3_169_276_HUMAN_AUDIT_MERGE.json"


def test_merged_human_audit_preserves_all_evidence_boundaries() -> None:
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True)
    with MERGED.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    result = json.loads(RESULT.read_text(encoding="utf-8"))

    assert len(rows) == 108
    assert {row["structure_status"] for row in rows} == {"HUMAN_APPROVED"}
    assert sum(row["decomposition_status"] == "HUMAN_DECOMPOSITION_RECORDED" for row in rows) == 105
    assert sum(row["decomposition_status"] == "HUMAN_APPROVED_NONRENDERABLE_COMPONENT_GLYPH" for row in rows) == 3
    assert {row["candidate_cnbe_status"] for row in rows} == {"NOT_GENERATED"}
    assert not result["decision"]["may_generate_cnbe_candidates"]
    assert not result["decision"]["may_modify_source_tables"]
