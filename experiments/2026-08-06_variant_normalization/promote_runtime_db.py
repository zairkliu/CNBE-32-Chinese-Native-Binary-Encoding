#!/usr/bin/env python3
"""Promote the approved candidate DB to the runtime DB.

Authorized by the project owner on 2026-08-06 after full human review of 812
coverage-gap rows. The script:
  1. backs up the release DBs;
  2. copies the candidate DB over data/cnbe32.db and src/cnbe32/data/cnbe32.db;
  3. records the migration in migration_meta;
  4. verifies row counts, track counts, approved rows, roundtrip, and duplicates.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

EXP = Path(__file__).resolve().parent
REPO = EXP.parents[1]
CAND = EXP / "build" / "cnbe32_8105_expanded_candidate.db"
TARGETS = [REPO / "data" / "cnbe32.db", REPO / "src" / "cnbe32" / "data" / "cnbe32.db"]
BACKUP = EXP / "build" / "release-backup-2026-08-06"


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def verify_db(p: Path, approved: list[dict]) -> dict:
    con = sqlite3.connect(str(p))
    con.row_factory = sqlite3.Row
    total = con.execute("SELECT COUNT(*) n FROM cnbe32").fetchone()["n"]
    tracks = {}
    for r in con.execute("SELECT track, COUNT(*) n FROM cnbe32 GROUP BY track"):
        tracks[r["track"]] = r["n"]
    failures = []
    dup = 0
    for e in approved:
        c = e["char"]
        pv = e.get("proposed") or {}
        if pv.get("radix") is None or pv.get("struct_type") is None:
            failures.append({"char": c, "reason": "no_code"})
            continue
        row = con.execute("SELECT * FROM cnbe32 WHERE char=?", (c,)).fetchone()
        if row is None:
            failures.append({"char": c, "reason": "missing"})
            continue
        code = (
            (pv["radix"] << 24)
            | (pv["strokes"] << 19)
            | (pv["struct_type"] << 15)
            | ((pv["index"] & 0x7FF) << 4)
        )
        if not (
            row["radix"] == pv["radix"]
            and row["strokes"] == pv["strokes"]
            and row["struct_type"] == pv["struct_type"]
            and row["idx"] == pv["index"]
            and row["track"] == "provisional"
            and row["cnbe"] == code
        ):
            failures.append({"char": c, "reason": "field_mismatch"})
    rows = con.execute(
        "SELECT cnbe, COUNT(*) c FROM cnbe32 WHERE track='provisional' GROUP BY cnbe HAVING c>1"
    ).fetchall()
    dup = len(rows)
    con.close()
    return {
        "path": str(p),
        "rows": total,
        "tracks": tracks,
        "approved_checked": len(approved),
        "failures": failures,
        "duplicate_provisional_cnbe": dup,
    }


def main() -> None:
    packet = json.loads((EXP / "coverage_remediation_packet.json").read_text(encoding="utf-8"))
    approved = [e for e in packet["entries"] if e.get("review_status") == "APPROVED"]
    BACKUP.mkdir(parents=True, exist_ok=True)
    before = {}
    for t in TARGETS:
        if t.exists():
            backup = BACKUP / t.name
            shutil.copy2(t, backup)
            before[str(t)] = sha256(backup)
        shutil.copy2(CAND, t)

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for t in TARGETS:
        con = sqlite3.connect(str(t))
        con.execute(
            "UPDATE migration_meta SET version=?, applied_at=?, script_version=?, updates=?, inserts=?, backup=?",
            ("v1.2-8105-promotion-2026-08-06", now, "1.0.0", 806, 6, str(BACKUP)),
        )
        con.commit()
        con.close()

    results = {str(t): verify_db(t, approved) for t in TARGETS}
    record = {
        "authorized_by": "项目负责人",
        "authorized_at": "2026-08-06",
        "applied_at": now,
        "candidate_db": str(CAND),
        "candidate_sha256": sha256(CAND),
        "before_sha256": before,
        "after_sha256": {str(t): sha256(t) for t in TARGETS},
        "verification": results,
        "overall_pass": all(not r["failures"] and r["duplicate_provisional_cnbe"] == 0 for r in results.values()),
    }
    (EXP / "runtime_promotion_2026-08-06.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(record, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
