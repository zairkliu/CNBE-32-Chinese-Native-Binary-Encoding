#!/usr/bin/env python3
"""Create a no-write three-source stroke triage packet for the five T3 disagreements."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ZDIC = ROOT / "evidence" / "8105" / "pending276" / "zdic" / "T3_169_276_ZDIC_CROSS_REFERENCE.csv"
TRIAGE = ROOT / "evidence" / "8105" / "pending276" / "T3_169_276_STROKE_TRIAGE.csv"
REPORT_JSON = ROOT / "reports" / "PENC276_T3_169_276_STROKE_TRIAGE.json"
REPORT_MARKDOWN = ROOT / "reports" / "PENC276_T3_169_276_STROKE_TRIAGE.md"


def main() -> None:
    with ZDIC.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    triage = [row for row in rows if row["inventory_baseline_strokes"] != row["inventory_unihan_strokes"]]
    if len(triage) != 5:
        raise ValueError("expected five T3 baseline/Unihan stroke disagreements")
    output = []
    for row in triage:
        zdic = row["zdic_total_strokes"]
        baseline = row["inventory_baseline_strokes"]
        unihan = row["inventory_unihan_strokes"]
        relation = "BASELINE_ZDIC_AGREE_UNIHAN_DIFFERS" if zdic == baseline else "THREE_SOURCE_UNRESOLVED"
        output.append(
            {
                "row_id": row["row_id"],
                "char": row["char"],
                "unicode": row["unicode"],
                "baseline_strokes": baseline,
                "unihan_strokes": unihan,
                "zdic_strokes": zdic,
                "triage_relation": relation,
                "adjudication_status": "HUMAN_OR_GF0013_ADJUDICATION_REQUIRED",
                "candidate_cnbe_status": "NOT_GENERATED",
            }
        )
    with TRIAGE.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(output[0]))
        writer.writeheader()
        writer.writerows(output)
    counts = {key: sum(row["triage_relation"] == key for row in output) for key in sorted({row["triage_relation"] for row in output})}
    result = {
        "schema_version": "penc276-t3-stroke-triage-v1",
        "rows": len(output),
        "counts": counts,
        "decision": {"status": "STROKE_TRIAGE_READY_HUMAN_OR_GF0013_ADJUDICATION_REQUIRED", "may_generate_cnbe_candidates": False},
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT_MARKDOWN.write_text(
        "# PENC276 T3 笔画三源分歧分诊\n\n"
        "- 分歧行：`5`。\n"
        + "".join(f"- `{name}`：`{count}`。\n" for name, count in counts.items())
        + "\nZDIC 与基线一致不自动覆盖 Unihan；仍须人审或 GF 0013 逐字证据裁决。\n",
        encoding="utf-8",
    )
    print(result["decision"]["status"])


if __name__ == "__main__":
    main()
