#!/usr/bin/env python3
"""Split cleaned publication corpus into core Chinese / technical / excluded."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--clean-manifest", type=Path, required=True)
    ap.add_argument("--encode-report", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()

    clean = json.loads(args.clean_manifest.read_text(encoding="utf-8"))
    encode = json.loads(args.encode_report.read_text(encoding="utf-8"))
    coverage = {entry["slug"]: entry.get("coverage", 0.0) for entry in encode["files"]}

    core: list[dict] = []
    technical: list[dict] = []
    excluded: list[dict] = []
    for entry in clean["files"]:
        slug = entry["slug"]
        out_chars = int(entry.get("output_chars", 0))
        cjk_ratio = float(entry.get("cjk_ratio", 0.0))
        item = {
            "slug": slug,
            "source": entry.get("output"),
            "output_chars": out_chars,
            "cjk_chars": int(entry.get("cjk_chars", 0)),
            "cjk_ratio": cjk_ratio,
            "coverage": coverage.get(slug, 0.0),
        }
        if out_chars < 1000:
            excluded.append(item)
        elif cjk_ratio >= 0.7:
            core.append(item)
        elif cjk_ratio >= 0.3:
            technical.append(item)
        else:
            excluded.append(item)

    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)

    def save(name: str, items: list[dict]) -> None:
        total_chars = sum(i["output_chars"] for i in items)
        total_cjk = sum(i["cjk_chars"] for i in items)
        payload = {
            "name": name,
            "files": len(items),
            "total_chars": total_chars,
            "total_cjk": total_cjk,
            "cjk_ratio": round(total_cjk / max(1, total_chars), 4),
            "items": items,
        }
        (out / f"{name}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(name, "files", len(items), "chars", total_chars, "cjk", total_cjk)

    save("core_chinese_subset", core)
    save("technical_subset", technical)
    save("excluded_subset", excluded)
    print("saved:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
