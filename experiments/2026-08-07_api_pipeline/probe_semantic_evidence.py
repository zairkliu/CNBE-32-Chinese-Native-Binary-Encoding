#!/usr/bin/env python3
"""Read-only semantic evidence coverage probe over the 97,686 catalog.

Measures how much Unicode-side semantic evidence (definitions, readings,
variants) is available for the full catalog. This is the baseline for the
CNBE64 multimodal semantic research foundation.
"""

from __future__ import annotations

import gzip
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
EXP = Path(__file__).resolve().parent


def load_unihan(path: Path) -> dict[str, dict[str, str]]:
    fields: dict[str, dict[str, str]] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("#") or "\t" not in line:
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        fields.setdefault(parts[0], {})[parts[1]] = parts[2].strip()
    return fields


def load_catalog_ucps(path: Path) -> list[str]:
    ucps: list[str] = []
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("id,"):
                continue
            ucps.append(line.split(",")[1])
    return ucps


def main() -> int:
    base = REPO / "experiments" / "2026-08-05_scheme_comparison" / "build"
    dict_like = load_unihan(base / "Unihan_DictionaryLikeData.txt")
    readings = load_unihan(base / "Unihan_Readings.txt")
    variants = load_unihan(base / "Unihan_Variants.txt")
    irg = load_unihan(base / "Unihan_IRGSources.txt")
    ucps = load_catalog_ucps(REPO / "data" / "cnbe_catalog_fixed.csv.gz")

    def has(ucp: str, field: str, data: dict[str, dict[str, str]]) -> bool:
        return bool(data.get(ucp, {}).get(field))

    counts = {
        "kDefinition": sum(has(u, "kDefinition", readings) for u in ucps),
        "kMandarin": sum(has(u, "kMandarin", readings) for u in ucps),
        "kHanyuPinyin": sum(has(u, "kHanyuPinyin", readings) for u in ucps),
        "kCantonese": sum(has(u, "kCantonese", readings) for u in ucps),
        "kGradeLevel": sum(has(u, "kGradeLevel", dict_like) for u in ucps),
        "kTraditionalVariant": sum(has(u, "kTraditionalVariant", variants) for u in ucps),
        "kSimplifiedVariant": sum(has(u, "kSimplifiedVariant", variants) for u in ucps),
        "kSemanticVariant": sum(has(u, "kSemanticVariant", variants) for u in ucps),
        "kZVariant": sum(has(u, "kZVariant", variants) for u in ucps),
        "kRSUnicode": sum(has(u, "kRSUnicode", irg) for u in ucps),
        "kTotalStrokes": sum(has(u, "kTotalStrokes", irg) for u in ucps),
    }
    semantic_any = sum(
        1
        for u in ucps
        if has(u, "kDefinition", readings)
        or has(u, "kMandarin", readings)
        or has(u, "kHanyuPinyin", readings)
        or has(u, "kCantonese", readings)
    )
    reading_any = sum(
        1
        for u in ucps
        if has(u, "kMandarin", readings)
        or has(u, "kHanyuPinyin", readings)
        or has(u, "kCantonese", readings)
    )
    variant_any = sum(
        1
        for u in ucps
        if has(u, "kTraditionalVariant", variants)
        or has(u, "kSimplifiedVariant", variants)
        or has(u, "kSemanticVariant", variants)
        or has(u, "kZVariant", variants)
    )

    n = len(ucps)
    result = {
        "schema_version": 1,
        "scope": "full_catalog_97686",
        "rows": n,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "coverage": {
            field: {"count": count, "rate": round(count / n, 4)}
            for field, count in counts.items()
        },
        "aggregates": {
            "semantic_any": {"count": semantic_any, "rate": round(semantic_any / n, 4)},
            "reading_any": {"count": reading_any, "rate": round(reading_any / n, 4)},
            "variant_any": {"count": variant_any, "rate": round(variant_any / n, 4)},
        },
        "note": "Unihan cross-reference only; not authoritative semantics; multimodal/image evidence is a separate layer",
    }
    out = EXP / "results"
    out.mkdir(parents=True, exist_ok=True)
    (out / "semantic_evidence_probe.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
