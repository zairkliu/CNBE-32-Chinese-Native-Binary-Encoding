#!/usr/bin/env python3
"""CNBE-32 v1.1 migration: WS-7 executable-subset repairs + WS-8 legacy isolation.

PDR reference: PDR_PHASE2 (approved 2026-07-25), decisions D2 (dual-source
repairs authorized, evidence tiers labeled) and D3 (legacy isolation only).

Governance:
- DRY-RUN BY DEFAULT. Nothing is written unless --apply is passed.
- --apply first copies the db to <db>.backup-<timestamp> next to the original;
  --rollback <backup-file> restores it.
- Only 8105-scope rows are repaired, and only when TWO independent
  cross-reference sources AGREE with each other and DISAGREE with the db:
    * strokes    <- baseline.stroke_count  + Unihan kTotalStrokes
    * radical    <- baseline.radix         + Unihan kRSUnicode (Kangxi scheme)
    * structure  <- baseline.structure     + cjkvi-ids leading IDC
  Dual-source disagreements and unavailable values are HUNG, not guessed.
- Every repaired row is logged with an explicit evidence tier
  "cross_reference_dual:<sources>" - never labeled as national-standard.
- Legacy isolation (WS-8): adds `track` column; standard = struct_name in the
  13 canonical labels (post-repair), legacy otherwise. No legacy row content
  is modified.
- 276 missing 8105 chars are only inserted with --with-insertions, with
  cnbe=NULL and needs_encoding=1 (encoding pass is a separate, gated step).

Usage:
    python scripts/migrate_v1_1.py --db data/cnbe32.db \
        --baseline evidence/8105/cnbe8105_standard_baseline.json \
        --ids third_party/cjkvi_ids.txt \
        --unihan-irgsources third_party/Unihan_IRGSources.txt \
        [--apply] [--with-insertions] [--plan-out migration_plan.jsonl]
    python scripts/migrate_v1_1.py --rollback data/cnbe32.db.backup-20260725T120000
"""

from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_VERSION = "1.0.0"

CN_LABELS = {
    "独体字", "上下", "上中下", "左右", "左中右", "左上包", "右上包",
    "左三包", "左下包", "上三包", "下三包", "全包围", "镶嵌",
}
EN_TO_CN = {
    "single": "独体字", "up-down": "上下", "up-mid-down": "上中下",
    "left-right": "左右", "left-mid-right": "左中右",
    "top-left-wrap": "左上包", "top-right-wrap": "右上包",
    "left-wrap": "左三包", "bottom-left-wrap": "左下包",
    "top-wrap": "上三包", "bottom-wrap": "下三包", "full-wrap": "全包围",
    "embedded": "镶嵌",
}
STRUCT_TO_TYPE = {c: i for i, c in enumerate([
    "独体字", "上下", "上中下", "左右", "左中右", "左上包", "右上包",
    "左三包", "左下包", "上三包", "下三包", "全包围", "镶嵌",
])}
IDC_TO_STRUCT = {
    "⿰": "左右", "⿱": "上下", "⿲": "左中右", "⿳": "上中下",
    "⿴": "全包围", "⿵": "上三包", "⿶": "下三包", "⿷": "左三包",
    "⿸": "左上包", "⿹": "右上包", "⿺": "左下包", "⿻": "镶嵌",
}


def load_ids(path: Path) -> dict[str, str]:
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#") or "\t" not in line:
            continue
        p = line.split("\t")
        if len(p) >= 3 and p[1] and len(p[1]) == 1 and p[2]:
            out[p[1]] = IDC_TO_STRUCT.get(p[2][0], "独体字")
    return out


def load_unihan(path: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#") or "\t" not in line:
            continue
        p = (line.rstrip("\n").split("\t") + ["", ""])[:3]
        if not p[0].startswith("U+"):
            continue
        ch = chr(int(p[0][2:], 16))
        e = out.setdefault(ch, {})
        if p[1] == "kRSUnicode":
            try:
                e["radical"] = int(p[2].split()[0].split("'")[0].split(".")[0])
            except ValueError:
                pass
        elif p[1] == "kTotalStrokes":
            try:
                e["strokes"] = int(p[2].split()[0])
            except ValueError:
                pass
    return out


def current_structure(row: dict) -> str | None:
    sn = row["struct_name"]
    if sn in CN_LABELS:
        return sn
    return EN_TO_CN.get(sn)  # None for triangle


def build_plan(db_path: Path, baseline: dict, ids: dict, unihan: dict,
               with_insertions: bool) -> tuple[list[dict], dict]:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(cnbe32)")}
    rows = {r["char"]: dict(r) for r in conn.execute("SELECT * FROM cnbe32")}
    conn.close()

    scope = set(baseline.keys())
    plan: list[dict] = []
    hang = Counter()

    for ch in sorted(scope):
        b = baseline[ch]
        row = rows.get(ch)
        if row is None:
            if with_insertions:
                plan.append({
                    "char": ch, "op": "insert", "evidence_tier":
                    f"baseline:{b['evidence_status']}",
                    "payload": {
                        "unicode": b["codepoint"], "char": ch, "cnbe": None,
                        "radix": b["radix"], "radix_name": b["radical"],
                        "strokes": b["stroke_count"],
                        "struct_type": STRUCT_TO_TYPE.get(b["structure"]),
                        "struct_name": b["structure"],
                        "idx": (b["codepoint"] - 0x4E00) % 2048,
                    },
                    "needs_encoding": True,
                    "note": "cnbe encoding pass is a separate gated step",
                })
            continue

        e = unihan.get(ch, {})
        # --- strokes ---
        if b["stroke_count"] and e.get("strokes"):
            if b["stroke_count"] == e["strokes"] and row["strokes"] != b["stroke_count"]:
                plan.append({"char": ch, "op": "update", "field": "strokes",
                             "old": row["strokes"], "new": b["stroke_count"],
                             "evidence_tier": "cross_reference_dual:baseline+unihan_kTotalStrokes"})
            elif b["stroke_count"] != e["strokes"] and row["strokes"] != b["stroke_count"]:
                hang["strokes_dual_disagree"] += 1
        # --- radical (Kangxi scheme) ---
        if b["radix"] and e.get("radical"):
            if b["radix"] == e["radical"] and row["radix"] != b["radix"]:
                plan.append({"char": ch, "op": "update", "field": "radix",
                             "old": row["radix"], "new": b["radix"],
                             "evidence_tier": "cross_reference_dual:baseline+unihan_kRSUnicode(kangxi)"})
            elif b["radix"] != e["radical"] and row["radix"] != b["radix"]:
                hang["radical_dual_disagree"] += 1
        # --- structure ---
        cur = current_structure(row)
        if b["structure"] and ch in ids:
            if b["structure"] == ids[ch] and cur != b["structure"]:
                plan.append({"char": ch, "op": "update", "field": "structure",
                             "old": row["struct_name"], "new": b["structure"],
                             "new_struct_type": STRUCT_TO_TYPE[b["structure"]],
                             "evidence_tier": "cross_reference_dual:baseline+cjkvi_ids"})
            elif b["structure"] != ids[ch] and cur != b["structure"]:
                hang["structure_dual_disagree"] += 1
        elif not b["structure"] and cur is None:
            hang["structure_no_baseline_value"] += 1

    summary = {
        "script_version": SCRIPT_VERSION,
        "planned_at": datetime.now(timezone.utc).isoformat(),
        "db": str(db_path),
        "scope_rows": len(scope),
        "with_insertions": with_insertions,
        "ops": dict(Counter(
            f"{p['op']}:{p.get('field', 'row')}" for p in plan)),
        "hangs": dict(hang),
    }
    return plan, summary


def apply_plan(db_path: Path, plan: list[dict]) -> dict:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    backup = db_path.with_suffix(f".backup-{ts}.db")
    shutil.copy2(db_path, backup)

    conn = sqlite3.connect(str(db_path))
    cols = {r[1] for r in conn.execute("PRAGMA table_info(cnbe32)")}
    if "track" not in cols:
        conn.execute("ALTER TABLE cnbe32 ADD COLUMN track TEXT")
    if "needs_encoding" not in cols:
        conn.execute("ALTER TABLE cnbe32 ADD COLUMN needs_encoding INTEGER DEFAULT 0")

    n_upd = n_ins = 0
    with conn:
        for p in plan:
            if p["op"] == "update":
                if p["field"] == "structure":
                    conn.execute(
                        "UPDATE cnbe32 SET struct_name=?, struct_type=? WHERE char=?",
                        (p["new"], p["new_struct_type"], p["char"]))
                else:
                    conn.execute(
                        f"UPDATE cnbe32 SET {p['field']}=? WHERE char=?",
                        (p["new"], p["char"]))
                n_upd += 1
            elif p["op"] == "insert":
                pl = p["payload"]
                conn.execute(
                    "INSERT INTO cnbe32 (unicode, char, cnbe, radix, radix_name,"
                    " strokes, struct_type, struct_name, idx, needs_encoding)"
                    " VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (pl["unicode"], pl["char"], pl["cnbe"], pl["radix"],
                     pl["radix_name"], pl["strokes"], pl["struct_type"],
                     pl["struct_name"], pl["idx"], 1))
                n_ins += 1
        # WS-8 track marking, AFTER repairs. Three tiers:
        #   standard    = struct_name in the 13 canonical labels
        #   provisional = inserted 8105 rows still missing standard values
        #                 (baseline REVIEW_REQUIRED; pending completion)
        #   legacy      = English/triangle runtime rows (isolate, do not alter)
        conn.execute("UPDATE cnbe32 SET track=NULL")
        conn.execute(
            "UPDATE cnbe32 SET track='standard' WHERE struct_name IN (%s)"
            % ",".join("?" * len(CN_LABELS)), tuple(CN_LABELS))
        conn.execute(
            "UPDATE cnbe32 SET track='provisional'"
            " WHERE track IS NULL AND struct_name IS NULL")
        conn.execute("UPDATE cnbe32 SET track='legacy' WHERE track IS NULL")
        conn.execute(
            "CREATE TABLE IF NOT EXISTS migration_meta"
            " (version TEXT, applied_at TEXT, script_version TEXT,"
            "  updates INT, inserts INT, backup TEXT)")
        conn.execute(
            "INSERT INTO migration_meta VALUES (?,?,?,?,?,?)",
            ("v1.1-ws7ws8", datetime.now(timezone.utc).isoformat(),
             SCRIPT_VERSION, n_upd, n_ins, str(backup)))
    track_counts = dict(conn.execute(
        "SELECT track, COUNT(*) FROM cnbe32 GROUP BY track"))
    conn.close()
    return {"backup": str(backup), "updates": n_upd, "inserts": n_ins,
            "track": track_counts}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path)
    ap.add_argument("--baseline", type=Path)
    ap.add_argument("--ids", type=Path)
    ap.add_argument("--unihan-irgsources", type=Path)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--with-insertions", action="store_true")
    ap.add_argument("--plan-out", type=Path, default=Path("migration_plan.jsonl"))
    ap.add_argument("--rollback", type=Path)
    args = ap.parse_args()

    if args.rollback:
        # backup name: <name>.backup-<ts>.db ; original: <name>.db
        s = str(args.rollback)
        if ".backup-" not in s or not s.endswith(".db"):
            sys.exit("not a migration backup file (expected <name>.backup-<ts>.db)")
        target = Path(s.split(".backup-")[0] + ".db")
        shutil.copy2(args.rollback, target)
        print(f"rolled back {target} <- {args.rollback}")
        return

    for f in (args.db, args.baseline, args.ids, args.unihan_irgsources):
        if not f or not f.exists():
            sys.exit(f"missing input: {f}")

    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))["characters"]
    ids = load_ids(args.ids)
    unihan = load_unihan(args.unihan_irgsources)

    plan, summary = build_plan(args.db, baseline, ids, unihan,
                               args.with_insertions)
    with args.plan_out.open("w", encoding="utf-8") as fh:
        for p in plan:
            fh.write(json.dumps(p, ensure_ascii=False) + "\n")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"plan rows written: {len(plan)} -> {args.plan_out}")

    if args.apply:
        result = apply_plan(args.db, plan)
        print(json.dumps({"applied": result}, ensure_ascii=False, indent=2))
    else:
        print("DRY-RUN only. Re-run with --apply to execute (a timestamped"
              " backup is created first).")


if __name__ == "__main__":
    main()
