#!/usr/bin/env python3
"""Read-only feasibility probe over the 97,686-row full catalog.

Uses the actual full-catalog char list plus local Unihan/CHISE evidence to
measure how much of the catalog can be prefilled deterministically. No LLM
calls, no database writes.
"""

from __future__ import annotations

import gzip
import json
import sqlite3
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from cnbe32 import decode_cnbe, encode_cnbe  # noqa: E402

from clients.evidence import (  # noqa: E402
    aggregate,
    deterministic_proposal,
    encode_proposal,
    load_ids,
    load_radix_name_map,
    load_unihan_irg,
)

REPO = Path(__file__).resolve().parents[2]
EXP = Path(__file__).resolve().parent


def load_catalog_rows(path: Path) -> list[dict]:
    rows = []
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("id,"):
                continue
            parts = line.split(",")
            ucp = parts[1]
            rows.append(
                {
                    "ucp": ucp,
                    "char": chr(int(ucp[2:], 16)),
                    "cnbe_hex": parts[2],
                    "r": int(parts[3]),
                    "s": int(parts[4]),
                    "g": int(parts[5]),
                    "block": parts[6],
                }
            )
    return rows


def main() -> int:
    catalog_path = REPO / "data" / "cnbe_catalog_fixed.csv.gz"
    rows = load_catalog_rows(catalog_path)
    unihan = load_unihan_irg(REPO / "experiments/2026-08-05_scheme_comparison/build/Unihan_IRGSources.txt")
    ids_map = load_ids(REPO / "experiments/2026-08-05_scheme_comparison/build/ids.txt")
    radix_name = load_radix_name_map(REPO / "evidence/8105/cnbe8105_radical_code_map.json")

    con = sqlite3.connect(str(REPO / "data" / "cnbe32.db"))
    in_db = {r[0] for r in con.execute("SELECT char FROM cnbe32")}
    con.close()

    counters = Counter()
    confidence_buckets = Counter()
    t0 = time.perf_counter()
    for row in rows:
        entry = {
            "char": row["char"],
            "unicode": row["ucp"],
            "standard_evidence": {"issues": [], "structure": None},
        }
        ev = aggregate(entry, unihan, ids_map, radix_name)
        det = deterministic_proposal(entry, ev, (ord(row["char"]) - 0x4E00) % 2048)
        encode_proposal(det)
        fields = (det.get("radix"), det.get("strokes"), det.get("struct_type"))
        counters["total"] += 1
        counters["in_runtime_db"] += int(row["char"] in in_db)
        counters["unihan_radix"] += int(ev["radix_code"] is not None and ev["radix_name"] is not None)
        counters["unihan_strokes"] += int(ev["strokes"] is not None)
        counters["ids_available"] += int(bool(ev["ids"]))
        counters["structure_available"] += int(ev["structure"] is not None)
        counters["deterministic_complete"] += int(all(v is not None for v in fields))
        if det.get("strokes") is not None and det["strokes"] > 31:
            counters["stroke_overflow"] += 1
        if det.get("roundtrip_pass"):
            counters["roundtrip_pass"] += 1
        conf = det.get("confidence", 0.0)
        if conf >= 0.95:
            confidence_buckets["high>=0.95"] += 1
        elif conf >= 0.8:
            confidence_buckets["medium>=0.8"] += 1
        else:
            confidence_buckets["low<0.8"] += 1

    elapsed = time.perf_counter() - t0
    total = counters["total"]

    def rate(key: str) -> float:
        return round(counters[key] / total, 4) if total else 0.0

    # Measured LLM profile from the 2026-08-07 20-row audit.
    llm_profile = {
        "input_tokens_avg": 205.3,
        "output_tokens_avg": 94.3,
        "total_tokens_avg": 299.6,
        "elapsed_avg_s": 1.532,
    }
    scenarios = {
        "all_rows": total,
        "below_high_confidence": counters["deterministic_complete"]
        - confidence_buckets["high>=0.95"],
        "incomplete": total - counters["deterministic_complete"],
    }
    llm_projections = {}
    for name, n in scenarios.items():
        n = max(n, 0)
        llm_projections[name] = {
            "calls": n,
            "input_tokens": round(n * llm_profile["input_tokens_avg"]),
            "output_tokens": round(n * llm_profile["output_tokens_avg"]),
            "total_tokens": round(n * llm_profile["total_tokens_avg"]),
            "sequential_hours": round(n * llm_profile["elapsed_avg_s"] / 3600, 2),
            "parallel8_hours": round(n * llm_profile["elapsed_avg_s"] / 3600 / 8, 2),
        }

    result = {
        "schema_version": 1,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "scope": "full_catalog_97686",
        "rows": total,
        "probe_elapsed_s": round(elapsed, 2),
        "coverage": {
            "in_runtime_db": counters["in_runtime_db"],
            "in_runtime_db_rate": rate("in_runtime_db"),
            "unihan_radix": counters["unihan_radix"],
            "unihan_radix_rate": rate("unihan_radix"),
            "unihan_strokes": counters["unihan_strokes"],
            "unihan_strokes_rate": rate("unihan_strokes"),
            "ids_available": counters["ids_available"],
            "ids_available_rate": rate("ids_available"),
            "structure_available": counters["structure_available"],
            "structure_available_rate": rate("structure_available"),
            "deterministic_complete": counters["deterministic_complete"],
            "deterministic_complete_rate": rate("deterministic_complete"),
            "roundtrip_pass": counters["roundtrip_pass"],
            "roundtrip_pass_rate": rate("roundtrip_pass"),
            "stroke_overflow": counters["stroke_overflow"],
        },
        "confidence_buckets": dict(confidence_buckets),
        "llm_profile_measured": llm_profile,
        "llm_projections": llm_projections,
        "write_gate": "NO_WRITE_TO_RELEASE_DB",
    }
    out = EXP / "results"
    out.mkdir(parents=True, exist_ok=True)
    (out / "full_catalog_probe.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
