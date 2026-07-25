"""Guard the T3 ZDIC/Unihan radical adjudication as a read-only evidence step."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "adjudicate_penc276_t3_radicals.py"
ADJUDICATION = ROOT / "evidence" / "8105" / "pending276" / "T3_169_276_RADICAL_ADJUDICATION.csv"
RESULT = ROOT / "reports" / "PENC276_T3_169_276_RADICAL_ADJUDICATION.json"


def test_radical_adjudication_covers_all_t3_rows_without_candidate_generation() -> None:
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True)
    with ADJUDICATION.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    result = json.loads(RESULT.read_text(encoding="utf-8"))

    assert len(rows) == 108
    assert sum(result["counts"].values()) == 108
    assert {row["candidate_cnbe_status"] for row in rows} == {"NOT_GENERATED"}
    assert not result["decision"]["may_generate_cnbe_candidates"]
    assert not result["decision"]["may_modify_source_tables"]
