#!/usr/bin/env python3
"""Compute CJK-only CNBE coverage for a corpus subset."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from batch_encode_publications import FastCNBEEncoder


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--subset", type=Path, required=True)
    ap.add_argument("--db", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    subset = json.loads(args.subset.read_text(encoding="utf-8"))
    encoder = FastCNBEEncoder(str(args.db))
    report: dict = {"files": [], "totals": {}}
    totals = {"cjk_chars": 0, "covered_cjk": 0}

    for item in subset["items"]:
        path = Path(item["source"])
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        cps = np.frombuffer(text.encode("utf-32-le"), dtype="<u4").astype(np.int64)
        cjk_mask = (
            ((cps >= 0x4E00) & (cps <= 0x9FFF))
            | ((cps >= 0x3400) & (cps <= 0x4DBF))
            | ((cps >= 0xF900) & (cps <= 0xFAFF))
        )
        cjk = cps[cjk_mask]
        if len(cjk) == 0:
            continue
        covered = int((encoder.table[cjk] != 0).sum())
        totals["cjk_chars"] += int(len(cjk))
        totals["covered_cjk"] += covered
        report["files"].append(
            {
                "slug": item["slug"],
                "cjk_chars": int(len(cjk)),
                "covered_cjk": covered,
                "cjk_coverage": round(covered / len(cjk), 6),
            }
        )

    totals["cjk_coverage"] = round(
        totals["covered_cjk"] / max(1, totals["cjk_chars"]), 6
    )
    report["totals"] = totals
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("files", len(report["files"]), "totals", totals)
    return 0


if __name__ == "__main__":
    sys.exit(main())
