#!/usr/bin/env python3
"""Conservatively remove residual copyright/watermark blocks from corpus v1.

Dry-run by default.  Use --apply to write files, update the manifest and save a
backup of every changed file under quality_check/residual_fix_backup_<ts>/.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import time
from pathlib import Path

import numpy as np

STRONG_HEADER_PATTERNS = [
    "版權信息",
    "版权信息",
    "版权声明",
    "版权所有",
    "版权页",
    "版權頁",
    "CAEBN",
    "CIP",
    "ISBN",
    "书号",
    "書號",
    "定价",
    "定價",
    "互联网出版许可证",
    "互聯網出版許可證",
    "首次发布",
    "首次發佈",
    "更新时间",
    "更新時間",
    "上架建议",
    "上架建議",
    "北京中文在线数字出版股份有限公司",
    "本电子书由",
    "本電子書由",
    "本书著作权为",
    "本書著作權為",
    "非经书面授权",
    "非經書面授權",
    "DNA-BN",
    "电子邮箱",
    "電子郵箱",
    "service@",
    "客服热线",
    "客服熱線",
    "团购热线",
    "團購熱線",
]

STRONG_FOOTER_PATTERNS = [
    "All rights reserved",
    "ALL RIGHTS RESERVED",
    "No part of this",
    "版本：v1.0",
    "本书仅供个人学习之用",
    "请购买正版书籍",
    "制作说明",
    "製作說明",
    "青苹果数据中心",
    "客服热线",
    "客服熱線",
    "团购热线",
    "團購熱線",
    "版权所有",
    "版权信息",
    "版權信息",
    "出版信息",
    "Table of Contents",
    "所有权利",
    "翻印必究",
    "本电子书由",
    "本電子書由",
    "非经书面授权",
    "非經書面授權",
    "本书著作权为",
    "本書著作權為",
    "DNA-BN",
]

TITLE_PAGE_LINE_RE = re.compile(
    r"(?:"
    r"版權信息|版权信息|版权声明|版权所有|版权页|版權頁|"
    r"CAEBN|CIP|ISBN|书号|書號|定价|定價|"
    r"互联网出版许可证|互聯網出版許可證|首次发布|首次發佈|更新时间|更新時間|"
    r"上架建议|上架建議|北京中文在线数字出版股份有限公司|本电子书由|本電子書由|"
    r"本书著作权为|本書著作權為|非经书面授权|非經書面授權|DNA-BN|"
    r"电子邮箱|電子郵箱|service@|客服热线|客服熱線|团购热线|團購熱線|"
    r"出版社|出版[：:︰]|出版时间|出版時間|出版公司|著作权合同登记号|著作权合同|"
    r"版次|字数|分類号|分类号|发行|發行|特邀编辑|特邀編輯|责任编辑|責任編輯|"
    r"图书在版编目|圖書在版編目|地址|邮编|郵編|电话|電話|传真|傳真|邮箱|郵箱|网址|網址|"
    r"著者：|著者:|译者：|譯者：|电子书排版|電子書排版|官方微博|官方微信|"
    r"印数|印數|图字|圖字|承印厂|承印廠|质量科|質量科|"
    r"CITIC Publishing|Hachette|Penguin|Random House|清华大学出版社|北京大学出版社|"
    r"人民邮电出版社|机械工业出版社|化学工业出版社|电子工业出版社|上海世纪出版|南海出版公司|中信出版社|"
    r"後學|后学|(?:著|譯|译|編|選|选|編著|编著|註|注)\s*$"
    r")"
)

GENERIC_STRONG_MARKER_RE = re.compile(
    r"(?:"
    r"版權信息|版权信息|版权声明|版权所有|版权页|版權頁|CAEBN|CIP|ISBN|"
    r"书号[:：]?\s*[0-9A-Za-z]|書號[:：]?\s*[0-9A-Za-z]|定价|定價|"
    r"互联网出版许可证|互聯網出版許可證|首次发布|首次發佈|"
    r"更新时间|更新時間|上架建议|上架建議|北京中文在线数字出版股份有限公司|"
    r"本电子书由|本電子書由|本书著作权为|本書著作權為|非经书面授权|非經書面授權|"
    r"DNA-BN|电子邮箱|電子郵箱|service@|客服热线|客服熱線|团购热线|團購熱線|"
    r"著作权合同登记号|著作权合同|版次|字数|分類号|分类号|图书在版编目|圖書在版編目|"
    r"著者：|著者:|译者：|譯者：|責任編輯：|责任编辑：|特邀编辑|特邀編輯|"
    r"电子书排版|電子書排版|官方微博|官方微信|印数|印數|图字|圖字|"
    r"承印厂|承印廠|质量科|質量科|清华大学出版社|北京大学出版社|人民邮电出版社|"
    r"机械工业出版社|化学工业出版社|电子工业出版社|上海世纪出版|南海出版公司|中信出版社"
    r")"
)

PUBLISHER_RE = re.compile(r"(?:出版社|出版公司|出版集团|出版有限公司|出版股份有限公司|出\s*版)")


def is_strong_title_marker(line: str) -> bool:
    s = line.strip()
    if not s or len(s) > 160:
        return False
    if GENERIC_STRONG_MARKER_RE.search(s):
        return True
    if PUBLISHER_RE.search(s) and not s.endswith(("。", "！", "？")):
        return True
    return False


COPYRIGHT_FOOTER_RE = re.compile(
    r"(?:"
    r"All rights reserved|ALL RIGHTS RESERVED|No part of this|版本：v1.0|"
    r"本书仅供个人学习之用|请购买正版书籍|制作说明|製作說明|青苹果数据中心|"
    r"客服热线|客服熱線|团购热线|團購熱線|版权所有|版权信息|版權信息|出版信息|"
    r"Table of Contents|所有权利|翻印必究|本电子书由|本電子書由|"
    r"非经书面授权|非經書面授權|本书著作权为|本書著作權為|DNA-BN|"
    r"数字出版|數字出版|電子書出版|电子书出版|出版服务|出版服務|"
    r"注册时间|注册地址|二维码|二維碼|"
    r"一校|二校|三校|校对|校對|说明[:：]|說明[:：]|声明[:：]|聲明[:：]"
    r")"
)

DATE_RE = re.compile(r"\d{4}\s*[年./-]\s*\d{1,2}\s*[月./-]?\s*\d{0,2}\s*日?")
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
URL_RE = re.compile(r"^(?:https?://|www\.)", re.IGNORECASE)

HEADING_RE = re.compile(
    r"^(?:"
    r"第[一二三四五六七八九十百千0-9]+[章卷节部回集篇]"
    r"|[（(]?[0-9]+[)）]?[、.．\s]"
    r"|[一二三四五六七八九十]+[、]"
    r"|.*(?:前言|序言|引言|导言|導言|自序|代序|后记|後記|附录|附錄|"
    r"目录|目錄|楔子|引子|尾声|尾聲|跋|題記|题记|附记|附記)(?:\s|$)"
    r")"
)

WATERMARK_PATTERNS = [
    re.compile(r"【更多新书朋友圈[^】]*】"),
    re.compile(r"【更多新書朋友圈[^】]*】"),
    re.compile(r"更多新书朋友圈免费首发，微信[^\s，。；】]*"),
    re.compile(r"更多新書朋友圈免費首發，微信[^\s，。；】]*"),
]


def cjk_count(text: str) -> int:
    cps = np.frombuffer(text.encode("utf-32-le"), dtype="<u4").astype(np.int64)
    mask = (
        ((cps >= 0x4E00) & (cps <= 0x9FFF))
        | ((cps >= 0x3400) & (cps <= 0x4DBF))
        | ((cps >= 0xF900) & (cps <= 0xFAFF))
    )
    return int(mask.sum())


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def is_header_metadata_line(line: str) -> bool:
    s = line.strip()
    if not s or len(s) > 220:
        return False
    if TITLE_PAGE_LINE_RE.search(line):
        return True
    if DATE_RE.search(line) and len(s) <= 110:
        return True
    if EMAIL_RE.search(s) or URL_RE.search(s):
        return True
    if re.match(
        r"^(?:作者|著者|译者|譯者|主编|主編|编著|編著|编辑|編輯|"
        r"責任編輯|责任编辑|特邀编辑|策划|策劃|书评|書評)\s*[:：]?",
        s,
    ):
        return True
    return False


def is_footer_metadata_line(line: str) -> bool:
    s = line.strip()
    if not s or len(s) > 220:
        return False
    if COPYRIGHT_FOOTER_RE.search(line):
        return True
    if re.match(r"^(?:微博|微信)\s*[@：:]\s*\S+", s):
        return True
    if EMAIL_RE.search(s) or URL_RE.search(s):
        return True
    if re.match(
        r"^(?:官方|客服|电话|電話|传真|傳真|地址|邮编|郵編|"
        r"邮箱|郵箱|网址|網址|QQ|读者|讀者|会员|會員|注册|註冊|登录|登錄|"
        r"本电子书|本電子書|本书著作权|本書著作權|非经书面|非經書面)",
        s,
    ):
        return True
    return False


def next_nonblank(lines: list[str], start: int) -> int:
    i = start
    while i < len(lines) and not lines[i].strip():
        i += 1
    return i


def is_heading(line: str) -> bool:
    s = line.strip()
    return bool(s and len(s) <= 80 and HEADING_RE.match(s))


def header_cut(lines: list[str]) -> tuple[int, int] | None:
    """Return (start, end) line interval to drop, or None when no header block."""
    head = lines[:80]
    block_start = next(
        (i for i, line in enumerate(head) if is_strong_title_marker(line)),
        None,
    )
    if block_start is None:
        return None
    if any(len(lines[i].strip()) > 300 for i in range(block_start)):
        return None
    # Walk backwards over short title/author lines directly before the marker.
    while block_start > 0:
        j = block_start - 1
        while j > 0 and not lines[j].strip():
            j -= 1
        prev = lines[j].strip()
        if (
            prev
            and len(prev) <= 100
            and not prev.endswith(("。", "！", "？", ".", "！"))
        ):
            block_start = j
        else:
            break
    start = block_start
    i = start
    while i < len(lines):
        s = lines[i].strip()
        if not s:
            i += 1
            continue
        if is_heading(s) or len(s) > 300:
            return (start, i) if i > start else None
        if is_header_metadata_line(lines[i]):
            i += 1
            continue
        j = next_nonblank(lines, i + 1)
        if j < len(lines) and is_header_metadata_line(lines[j]):
            # Short title/author line inside a metadata block.
            i += 1
            continue
        return (start, i) if i > start else None
    return (start, len(lines)) if len(lines) > start else None


def footer_cut(lines: list[str]) -> int:
    """Return number of trailing lines to drop, or 0 when no footer block."""
    tail = lines[-80:]
    if not any(COPYRIGHT_FOOTER_RE.search(line) for line in tail):
        return 0
    end = len(lines)
    while end > 0 and not lines[end - 1].strip():
        end -= 1
    i = end - 1
    while i >= 0:
        s = lines[i].strip()
        if not s:
            i -= 1
            continue
        if is_footer_metadata_line(lines[i]) or re.match(
            r"^(?:微博|微信)\s*[@：:]", s
        ):
            i -= 1
            continue
        break
    removed = end - i - 1
    return removed if removed > 0 else 0


def clean_text(text: str) -> tuple[str, dict]:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    watermark_removed = 0
    for pattern in WATERMARK_PATTERNS:
        watermark_removed += len(pattern.findall(text))
        text = pattern.sub("", text)
    lines = text.split("\n")
    head_block = header_cut(lines)
    cut_foot = footer_cut(lines)
    if head_block or cut_foot:
        if head_block:
            start, end = head_block
            lines = lines[:start] + lines[end:]
        if cut_foot:
            lines = lines[: len(lines) - cut_foot]
        text = "\n".join(lines)
    text = text.strip("\n") + "\n"
    return text, {
        "header_lines": (head_block[1] - head_block[0]) if head_block else 0,
        "footer_lines": cut_foot,
        "watermark_removed": watermark_removed,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--report", type=Path)
    args = ap.parse_args()

    manifest_path = args.root / "corpus_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    changes: list[dict] = []
    changed_slugs: list[str] = []

    for entry in manifest:
        path = args.root / entry["bucket"] / f"{entry['slug']}.txt"
        text = path.read_text(encoding="utf-8", errors="replace")
        cleaned, stats = clean_text(text)
        if cleaned == text:
            continue
        changed = {
            "slug": entry["slug"],
            "bucket": entry["bucket"],
            **stats,
            "old_chars": len(text),
            "new_chars": len(cleaned),
            "old_cjk": cjk_count(text),
            "new_cjk": cjk_count(cleaned),
        }
        changes.append(changed)
        changed_slugs.append(entry["slug"])

        if args.apply:
            backup_dir = args.root / "quality_check" / "residual_fix_backup_latest"
            backup_path = backup_dir / entry["bucket"] / path.name
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            if not backup_path.exists():
                shutil.copy2(path, backup_path)
            with path.open("w", encoding="utf-8", newline="\n") as fh:
                fh.write(cleaned)
            cjk = cjk_count(cleaned)
            entry["chars"] = len(cleaned)
            entry["cjk"] = cjk
            entry["cjk_ratio"] = round(cjk / max(1, len(cleaned)), 4)
            entry["meta_hits"] = 0
            entry["sha256"] = sha256(cleaned)

    print("files with proposed changes:", len(changes), flush=True)
    print("total header lines:", sum(c["header_lines"] for c in changes), flush=True)
    print("total footer lines:", sum(c["footer_lines"] for c in changes), flush=True)
    report_path = args.report or (
        args.root
        / "quality_check"
        / ("residual_fix_dryrun_v2.json" if not args.apply else "residual_fix_report_v2.json")
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(
            {
                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "count": len(changes),
                "header_files": sum(1 for c in changes if c["header_lines"] > 0),
                "footer_files": sum(1 for c in changes if c["footer_lines"] > 0),
                "watermark_files": sum(
                    1 for c in changes if c.get("watermark_removed", 0) > 0
                ),
                "changed_slugs": changed_slugs,
                "changes": changes,
                "backup": "quality_check/residual_fix_backup_latest",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    if not args.apply:
        print("dry-run only; rerun with --apply to write files", flush=True)
        print("report saved:", report_path, flush=True)
        return 0

    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("manifest updated:", manifest_path, flush=True)
    print("report saved:", report_path, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
