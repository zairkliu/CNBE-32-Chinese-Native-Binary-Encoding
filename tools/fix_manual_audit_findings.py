#!/usr/bin/env python3
"""Apply fixes for the 6 books flagged by the 40-book manual audit."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

from audit_merge_corpus import META_PATTERNS, cjk_stats, metadata_hits  # noqa: E402


def clean_05993(lines: list[str]) -> list[str]:
    start_re = re.compile(
        r"^(?:\ufeff)?(?:全景二战\s*\\?|A GLOBAL HISTORY.*|A CLOBAL HISTORY.*|"
        r"A Global History.*|团购(?:部)?热线：.*)"
    )
    end_re = re.compile(r"^版\s*次：.*第1版$")
    out: list[str] = []
    dropping = False
    for line in lines:
        stripped = line.strip()
        if not dropping and start_re.match(stripped):
            dropping = True
            continue
        if dropping:
            if end_re.match(stripped):
                dropping = False
            continue
        out.append(line)
    return out


def clean_01080(lines: list[str]) -> list[str]:
    out: list[str] = []
    preface_seed: int | None = None
    i = 0
    marker = "丛书代序 对黑鹤动物小说的解读)"
    while i < len(lines):
        if lines[i].strip() == "文前彩插":
            j = i + 1
            while j < len(lines) and lines[j].strip() != marker:
                j += 1
            if j < len(lines):
                if preface_seed is None:
                    preface_seed = j + 1
                    i = j
                    continue
                k = j + 1
                p = preface_seed
                while k < len(lines) and p < len(lines) and lines[k] == lines[p]:
                    k += 1
                    p += 1
                i = k
                continue
        out.append(lines[i])
        i += 1
    return out


def clean_05910(lines: list[str]) -> list[str]:
    promo_prefix = re.compile(
        r"^(传真|地址|地\s*址|邮编|电话|热线|邮箱|投稿|博客|微博|微信|"
        r"读者|编辑|感谢|会员|关注|登录|如发现|激光防伪|著作权合同|"
        r"编读互动|亲爱的读者|其他\d*|信息卡|新浪|官方|更多好书|"
        r"All rights|No part|@|http|www)"
    )
    title_re = re.compile(r"^[\u4e00-\u9fffA-Za-z《].{2,60}[:：—]")
    out: list[str] = []
    dropping = False
    for line in lines:
        stripped = line.strip()
        if not dropping and (
            stripped.startswith("All rights reserved")
            or stripped.startswith("No part of this book")
            or re.fullmatch(r"其他\d*", stripped)
        ):
            dropping = True
            continue
        if dropping:
            if promo_prefix.match(stripped) or "信息卡" in stripped:
                continue
            if title_re.match(stripped) and len(stripped) <= 80:
                dropping = False
                out.append(line)
                continue
            continue
        out.append(line)
    return out


def clean_13617(lines: list[str]) -> list[str]:
    cut = next((i for i, line in enumerate(lines) if "客服專線" in line), len(lines))
    return lines[:cut]


def clean_06312(lines: list[str]) -> list[str]:
    cut = next(
        (i for i, line in enumerate(lines) if "位于城市边缘地带的羊坊街里" in line),
        len(lines),
    )
    return lines[cut:]


def clean_13697(text: str) -> str:
    text = re.sub(
        r"【[^】]*?(?:更多[^】]*朋友圈|微信[^】]*)】",
        "",
        text,
    )
    idx = text.find("书名原文：")
    if idx != -1:
        line_start = text.rfind("\n", 0, idx) + 1
        text = text[:line_start]
    return text


def clean_00306(lines: list[str]) -> list[str]:
    cut = next(
        (
            i
            for i, line in enumerate(lines)
            if "书名原文：Your Survival Instinct" in line
        ),
        len(lines),
    )
    return lines[:cut]


def clean_00310(lines: list[str]) -> list[str]:
    cut = next(
        (
            i
            for i, line in enumerate(lines)
            if line.strip().startswith("枪炮、病菌与钢铁：人类社会的命运/")
        ),
        len(lines),
    )
    return lines[:cut]


def clean_00505(lines: list[str]) -> list[str]:
    cut = next(
        (
            i
            for i, line in enumerate(lines)
            if "书名原文：The Empathic Civilization" in line
        ),
        len(lines),
    )
    return lines[:cut]


def clean_09443(lines: list[str]) -> list[str]:
    cut = next(
        (i for i, line in enumerate(lines) if re.sub(r"\s+", "", line) == "前言"),
        len(lines),
    )
    return lines[cut:]


def clean_09623(lines: list[str]) -> list[str]:
    cut = next(
        (i for i, line in enumerate(lines) if "制作说明" in line),
        len(lines),
    )
    return lines[:cut]


CLEANERS = {
    "05993_v2_出版物__牢记战争之痛_二战纪实全7册_txt": lambda t: clean_05993(t.splitlines()),
    "01080_v2_出版物__黑鹤动物文学精品系列_套装共6册_txt": lambda t: clean_01080(t.splitlines()),
    "05910_v2_1_生活心理学_-_英_柯瑞妮_斯威特_Corinne_Sweet_等_txt": lambda t: clean_05910(
        t.splitlines()
    ),
    "13617_v2_出版物__印加與西班牙的交錯_txt": lambda t: clean_13617(t.splitlines()),
    "06312_v2_2_半身侦探3_txt": lambda t: clean_06312(t.splitlines()),
    "13697_v2_2_知识的错觉_txt": clean_13697,
    "00306_v2_2_你的生存本能正在杀死你_修订版_txt": lambda t: clean_00306(t.splitlines()),
    "00310_v2_1_枪炮_病菌与钢铁_人类社会的命运_世纪人文系列丛书_开放人文_-_贾雷德_戴蒙德_txt": lambda t: clean_00310(
        t.splitlines()
    ),
    "00505_v2_1_同理心文明_txt": lambda t: clean_00505(t.splitlines()),
    "09443_v2_1_中国现代文学作品选评_txt": lambda t: clean_09443(t.splitlines()),
    "09623_v2_2_柴静_-_看见_txt": lambda t: clean_09623(t.splitlines()),
}


def join_lines(lines: list[str]) -> str:
    text = "\n".join(lines)
    return text if text.endswith("\n") else text + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument(
        "--backup-dir",
        type=Path,
        help="pre-fix copy of the affected books, used to compute correct deltas",
    )
    args = ap.parse_args()

    manifest_path = args.root / "corpus_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    old_by_slug = {e["slug"]: e for e in manifest}
    original_stats: dict[str, tuple[int, int]] = {}
    changed: list[dict] = []

    for slug, cleaner in CLEANERS.items():
        old = old_by_slug.get(slug)
        if old is None:
            print("missing manifest entry:", slug)
            continue
        path = args.root / old["bucket"] / f"{slug}.txt"
        raw = path.read_text(encoding="utf-8", errors="replace")
        cleaned = cleaner(raw)
        if isinstance(cleaned, list):
            cleaned = join_lines(cleaned)
        cjk, total = cjk_stats(cleaned)
        new_hash = hashlib.sha256(cleaned.encode("utf-8")).hexdigest()
        backup_path = (
            args.backup_dir / old["bucket"] / f"{slug}.txt" if args.backup_dir else None
        )
        if backup_path and backup_path.exists():
            orig_cjk, orig_total = cjk_stats(
                backup_path.read_text(encoding="utf-8", errors="replace")
            )
        else:
            orig_total, orig_cjk = old["chars"], old["cjk"]
        original_stats[slug] = (orig_total, orig_cjk)
        old["chars"] = total
        old["cjk"] = cjk
        old["cjk_ratio"] = round(cjk / max(1, total), 4)
        old["meta_hits"] = metadata_hits(cleaned)
        old["sha256"] = new_hash
        path.write_text(cleaned, encoding="utf-8")
        changed.append(
            {
                "slug": slug,
                "bucket": old["bucket"],
                "old_chars": original_stats[slug][0],
                "new_chars": total,
                "old_cjk": original_stats[slug][1],
                "new_cjk": cjk,
            }
        )
        print(slug, "->", total, "chars", cjk, "cjk")

    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Recompute stats from manifest + pre-fix backup so reruns stay idempotent.
    audit_path = args.root / "quality_audit.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    dedup_path = args.root / "dedup_report.json"
    dedup = json.loads(dedup_path.read_text(encoding="utf-8"))
    original_manifest = [
        {**entry}
        for entry in manifest
        if entry["slug"] not in original_stats
    ]
    for slug, (orig_total, orig_cjk) in original_stats.items():
        entry = next(e for e in manifest if e["slug"] == slug)
        original_manifest.append(
            {**entry, "chars": orig_total, "cjk": orig_cjk}
        )

    def totals(entries: list[dict], bucket: str) -> tuple[int, int, int]:
        selected = [e for e in entries if e["bucket"] == bucket]
        return (
            len(selected),
            sum(e["chars"] for e in selected),
            sum(e["cjk"] for e in selected),
        )

    for bucket in ("core", "technical"):
        old_files, old_chars, old_cjk = totals(original_manifest, bucket)
        new_files, new_chars, new_cjk = totals(manifest, bucket)
        audit[bucket] = {"files": new_files, "chars": new_chars, "cjk": new_cjk}
        dedup["stats"][bucket] = {
            "files": new_files,
            "chars": new_chars,
            "cjk": new_cjk,
        }

    for batch, stats in audit["by_batch"].items():
        old_entries = [e for e in original_manifest if e["batch"] == batch]
        new_entries = [e for e in manifest if e["batch"] == batch]
        stats["chars"] = stats["chars"] - sum(
            e["chars"] for e in old_entries
        ) + sum(e["chars"] for e in new_entries)
        stats["cjk"] = stats["cjk"] - sum(
            e["cjk"] for e in old_entries
        ) + sum(e["cjk"] for e in new_entries)

    audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    dedup_path.write_text(json.dumps(dedup, ensure_ascii=False, indent=2), encoding="utf-8")
    report_path = args.root / "quality_check" / "manual_audit_fix_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(
            {"fixed": changed, "count": len(changed), "time": time.strftime("%Y-%m-%d %H:%M:%S")},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print("fixed", len(changed))
    print("saved", report_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
