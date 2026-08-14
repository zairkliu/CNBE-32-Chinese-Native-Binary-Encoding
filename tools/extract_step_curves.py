#!/usr/bin/env python3
"""Extract per-step training curves from CNBE-MoE logs."""

from __future__ import annotations

import argparse
import json
import re
import statistics
from pathlib import Path

STEP_RE = re.compile(
    r"step\s+(\d+)/(\d+)\s+loss\s+([0-9.]+)(?:\s+steps/s\s+([0-9.]+))?"
)


def parse_file(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = STEP_RE.search(line)
        if not m:
            continue
        step = int(m.group(1))
        total = int(m.group(2))
        loss = float(m.group(3))
        sps = float(m.group(4)) if m.group(4) else None
        rows.append(
            {
                "step": step,
                "total": total,
                "loss": loss,
                "steps_per_sec": sps,
                "source": str(path),
            }
        )
    return rows


def summarize(rows: list[dict]) -> dict:
    if not rows:
        return {}
    losses = [r["loss"] for r in rows]
    sps = [r["steps_per_sec"] for r in rows if r.get("steps_per_sec") is not None]
    total = max(r["total"] for r in rows)
    progress = {}
    for pct in (1, 10, 25, 50, 75, 90, 95, 99, 100):
        target = max(1, round(total * pct / 100))
        match = min(rows, key=lambda r: abs(r["step"] - target))
        progress[str(pct)] = {
            "step": match["step"],
            "loss": match["loss"],
            "steps_per_sec": match.get("steps_per_sec"),
        }
    last_100 = losses[-100:] if len(losses) >= 100 else losses
    return {
        "total_steps": total,
        "logged_steps": len(rows),
        "first_loss": rows[0]["loss"],
        "last_loss": rows[-1]["loss"],
        "min_loss": min(losses),
        "max_loss": max(losses),
        "mean_last_100": round(statistics.mean(last_100), 6),
        "median_loss": round(statistics.median(losses), 6),
        "median_steps_per_sec": round(statistics.median(sps), 4) if sps else None,
        "progress_losses": progress,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, nargs="+", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--output-dir", type=Path, default=Path("."))
    args = ap.parse_args()

    rows = []
    for path in args.input:
        if path.is_dir():
            files = sorted(path.rglob("*"))
        else:
            files = [path]
        for f in files:
            if f.is_file():
                rows.extend(parse_file(f))

    rows.sort(key=lambda r: (r["total"], r["step"]))
    dedup = {}
    for r in rows:
        dedup.setdefault((r["total"], r["step"]), r)
    rows = [dedup[k] for k in sorted(dedup)]

    out_dir = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / f"{args.tag}_step_curve.csv"
    json_path = out_dir / f"{args.tag}_step_curve.json"

    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        import csv

        writer = csv.DictWriter(
            f,
            fieldnames=["step", "total", "loss", "steps_per_sec", "source"],
        )
        writer.writeheader()
        writer.writerows(rows)

    result = {
        "tag": args.tag,
        "summary": summarize(rows),
        "rows": rows,
    }
    json_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("rows:", len(rows))
    print("summary:", json.dumps(result["summary"], ensure_ascii=False))
    print("csv:", csv_path)
    print("json:", json_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
