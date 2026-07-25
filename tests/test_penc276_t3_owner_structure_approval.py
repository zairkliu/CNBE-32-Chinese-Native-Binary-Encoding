"""Ensure owner structure approval cannot silently approve other encoding gates."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "apply_penc276_t3_owner_structure_approval.py"
LEDGER = ROOT / "evidence" / "8105" / "pending276" / "T3_169_276_STRUCTURE_OWNER_APPROVAL.csv"
RESULT = ROOT / "reports" / "PENC276_T3_169_276_STRUCTURE_APPROVAL.json"


def test_owner_structure_approval_preserves_the_remaining_gates() -> None:
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True)
    with LEDGER.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    result = json.loads(RESULT.read_text(encoding="utf-8"))

    assert len(rows) == 108
    assert {row["approval_scope"] for row in rows} == {"structure_label_only"}
    assert {row["decomposition_status"] for row in rows} == {"PENDING_DECOMPOSITION_TREE"}
    assert {row["candidate_cnbe_status"] for row in rows} == {"NOT_GENERATED"}
    assert result["decision"]["may_use_structure_label_in_future_review"]
    assert not result["decision"]["may_treat_as_dual_source_structure"]
    assert not result["decision"]["may_generate_cnbe_candidates"]
    assert not result["decision"]["may_modify_source_tables"]
