#!/usr/bin/env python3
"""Build a candidate DB copy from approved review results and verify roundtrip.

Reads coverage_remediation_packet.json, applies every APPROVED proposed row to a
copy of the release DB under build/, then verifies encode/decode consistency.
The release DB is never modified.
"""

from __future__ import annotations

import json
import shutil
import sqlite3
from pathlib import Path

EXP = Path(__file__).resolve().parent
REPO = EXP.parents[1]
RELEASE_DB = REPO / "data" / "cnbe32.db"
CAND_DB = EXP / "build" / "cnbe32_8105_expanded_candidate.db"


def encode(radix: int, stroke: int, struct: int, index: int, ext: int) -> int:
    return (
        (radix << 24)
        | (stroke << 19)
        | (struct << 15)
        | ((index & 0x7FF) << 4)
        | (ext & 0xF)
    )


def main() -> None:
    packet = json.loads((EXP / "coverage_remediation_packet.json").read_text(encoding="utf-8"))
    approved = [e for e in packet["entries"] if e.get("review_status") == "APPROVED" and e.get("proposed")]
    CAND_DB.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(RELEASE_DB, CAND_DB)

    con = sqlite3.connect(str(CAND_DB))
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    updated = inserted = 0
    missing = []
    for e in approved:
        c = e["char"]
        p = e["proposed"]
        if p.get("radix") is None or p.get("struct_type") is None:
            missing.append(c)
            continue
        code = encode(p["radix"], p["strokes"], p["struct_type"], p["index"], p.get("ext", 0))
        row = cur.execute("SELECT 1 FROM cnbe32 WHERE char = ?", (c,)).fetchone()
        values = (
            p["radix"], p["radix_name"], p["strokes"], p["struct_name"],
            p["struct_type"], p["index"], "provisional", code,
        )
        if row:
            cur.execute(
                "UPDATE cnbe32 SET radix=?, radix_name=?, strokes=?, struct_name=?, "
                "struct_type=?, idx=?, track=?, cnbe=? WHERE char=?",
                (*values, c),
            )
            updated += 1
        else:
            cur.execute(
                "INSERT INTO cnbe32 (unicode, char, cnbe, radix, radix_name, strokes, "
                "struct_type, struct_name, idx, track, needs_encoding) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (ord(c), c, code, p["radix"], p["radix_name"], p["strokes"],
                 p["struct_type"], p["struct_name"], p["index"], "provisional", 0),
            )
            inserted += 1
    con.commit()

    # verification
    failures = []
    for e in approved:
        c = e["char"]
        p = e["proposed"]
        row = cur.execute("SELECT * FROM cnbe32 WHERE char=?", (c,)).fetchone()
        if row is None:
            failures.append({"char": c, "reason": "missing"})
            continue
        code = encode(p["radix"], p["strokes"], p["struct_type"], p["index"], p.get("ext", 0))
        fields_ok = (
            row["radix"] == p["radix"]
            and row["strokes"] == p["strokes"]
            and row["struct_type"] == p["struct_type"]
            and row["idx"] == p["index"]
            and row["track"] == "provisional"
        )
        decode = (
            (code >> 24) & 0xFF,
            (code >> 19) & 0x1F,
            (code >> 15) & 0x0F,
            (code >> 4) & 0x7FF,
            code & 0x0F,
        )
        roundtrip_ok = decode == (
            p["radix"], p["strokes"], p["struct_type"], p["index"], p.get("ext", 0),
        )
        if not fields_ok or row["cnbe"] != code or not roundtrip_ok:
            failures.append(
                {
                    "char": c,
                    "fields_ok": fields_ok,
                    "cnbe_ok": row["cnbe"] == code,
                    "roundtrip_ok": roundtrip_ok,
                }
            )

    dup = cur.execute(
        "SELECT cnbe, COUNT(*) c FROM cnbe32 WHERE track='provisional' GROUP BY cnbe HAVING c>1"
    ).fetchall()
    total = cur.execute("SELECT COUNT(*) n FROM cnbe32").fetchone()["n"]
    con.close()

    summary = {
        "release_db": str(RELEASE_DB),
        "candidate_db": str(CAND_DB),
        "approved_rows": len(approved),
        "updated": updated,
        "inserted": inserted,
        "skipped_missing_codes": len(missing),
        "failures": len(failures),
        "duplicate_cnbe_provisional": len(dup),
        "total_rows": total,
        "failure_examples": failures[:10],
        "duplicate_examples": [dict(r) for r in dup[:10]],
    }
    (EXP / "candidate_db_verification.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
