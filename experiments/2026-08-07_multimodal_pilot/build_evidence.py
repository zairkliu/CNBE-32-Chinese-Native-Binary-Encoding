#!/usr/bin/env python3
"""Build CNBE64 + GB18030 + semantic evidence for the pilot scope."""

from __future__ import annotations

import json
import sys
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


def gb18030_pointer(ch: str) -> tuple[int, bool]:
    b = ch.encode("gb18030")
    if len(b) == 4:
        ptr = (b[0] - 0x81) * 12600 + (b[1] - 0x30) * 1260 + (b[2] - 0x81) * 10 + (b[3] - 0x30)
    else:
        ptr = (b[0] - 0x81) * 190 + (b[1] - 0x40) - (1 if b[1] > 0x7F else 0)
    return ptr, len(b) == 4


def main() -> int:
    base = REPO / "experiments" / "2026-08-05_scheme_comparison" / "build"
    readings = load_unihan(base / "Unihan_Readings.txt")
    variants = load_unihan(base / "Unihan_Variants.txt")
    irg = load_unihan(base / "Unihan_IRGSources.txt")
    scope = json.loads((EXP / "results" / "pilot_scope.json").read_text(encoding="utf-8"))["entries"]
    glyph_manifest = json.loads((EXP / "glyphs" / "manifest.json").read_text(encoding="utf-8"))["entries"]
    glyph_map = {g["ucp"]: g for g in glyph_manifest}

    entries = []
    for e in scope:
        ptr, four = gb18030_pointer(e["char"])
        low32 = int(e["cnbe_hex"], 16)
        cnbe64 = (1 << 60) | (ptr << 39) | (1 << 38) | (0 << 36) | low32
        row = irg.get(e["ucp"], {})
        entries.append(
            {
                "ucp": e["ucp"],
                "char": e["char"],
                "stratum": e["stratum"],
                "cnbe32": e["cnbe_hex"],
                "cnbe64": hex(cnbe64),
                "gb18030_pointer": ptr,
                "gb18030_four_byte": four,
                "glyph": glyph_map.get(e["ucp"]),
                "semantic": {
                    "definition": readings.get(e["ucp"], {}).get("kDefinition", ""),
                    "mandarin": readings.get(e["ucp"], {}).get("kMandarin", ""),
                    "hanyu_pinyin": readings.get(e["ucp"], {}).get("kHanyuPinyin", ""),
                    "cantonese": readings.get(e["ucp"], {}).get("kCantonese", ""),
                    "traditional": variants.get(e["ucp"], {}).get("kTraditionalVariant", ""),
                    "simplified": variants.get(e["ucp"], {}).get("kSimplifiedVariant", ""),
                },
                "unihan": {
                    "radix": row.get("kRSUnicode", ""),
                    "strokes": row.get("kTotalStrokes", ""),
                },
            }
        )
    out = EXP / "results"
    out.mkdir(parents=True, exist_ok=True)
    (out / "pilot_evidence.json").write_text(
        json.dumps({"schema_version": 1, "count": len(entries), "entries": entries}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("evidence", len(entries))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
