"""Verify the bounded Chinese human-review packet for remaining PENC276 rows."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_penc276_remaining168_chinese_review_packet.py"
PACKET = ROOT / "review_packets" / "pending276" / "PENC276_REMAINING_168_CHINESE_HUMAN_REVIEW_PACKET_EDITABLE.csv"
REPORT = ROOT / "reports" / "PENC276_REMAINING_168_CHINESE_HUMAN_REVIEW_PACKET.json"


def test_packet_excludes_completed_t3_human_audit_and_preserves_no_write_boundary() -> None:
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True)
    with PACKET.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    result = json.loads(REPORT.read_text(encoding="utf-8"))

    assert len(rows) == 168
    assert {row["审核结论（填写）"] for row in rows} == {""}
    assert {row["编码状态"] for row in rows} == {"不生成候选CNBE；不写入源表或数据库"}
    assert not any(169 <= int(row["清单编号"].split("_")[1]) <= 276 for row in rows)
    assert result["decision"]["status"] == "PASS_REMAINING_168_CHINESE_HUMAN_REVIEW_PACKET_READY"
    assert not result["decision"]["may_generate_cnbe_candidates"]
    assert not result["decision"]["may_modify_sqlite"]
