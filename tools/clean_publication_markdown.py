#!/usr/bin/env python3
"""Clean publication Markdown into AI-training plain text.

Removes YAML frontmatter, image links, TOC links, footnotes, watermark and
publisher metadata, HTML/CSS leftovers, page numbers, and layout placeholders.
Outputs one UTF-8 .txt file per book plus a manifest with quality statistics.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import unicodedata
from pathlib import Path

IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)|!\[[^\]]*\]\[[^\]]*\]")
INLINE_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]*\)")
FOOTNOTE_REF_RE = re.compile(r"\[\^[^\]]+\]")
FOOTNOTE_DEF_RE = re.compile(r"^\[\^[^\]]+\]:")
TOC_LINE_RE = re.compile(r"^[-*]\s*\[[^\]]+\]\(#[^)]*\)$|^\[[^\]]+\]\(#[^)]*\)$")
TOC_HEADING_RE = re.compile(r"^#{0,6}\s*(目\s*录|CONTENTS)\s*$")
HTML_TAG_RE = re.compile(r"<[^>]{0,300}>")
HTML_COMMENT_RE = re.compile(r"<!--.{0,2000}?-->", re.S)
STYLE_BLOCK_RE = re.compile(r"<style[^>]*>.*?</style>", re.S | re.I)
CSS_RULE_RE = re.compile(r"(?:^|\n)\s*@?[\w.#][\w.#-]*\s*\{[^}]{0,200}\}")
PAGE_NUMBER_RE = re.compile(r"^\d{1,4}$")
SLASH_PLACEHOLDER_RE = re.compile(r"^[\\/]{2,}$")
RULE_PLACEHOLDER_RE = re.compile(r"^[-—=*]{3,}$")
CODE_FENCE_RE = re.compile(r"^(`{3,}|~{3,})")
HEADING_RE = re.compile(r"^#{1,6}\s*")

WATERMARK_RE = re.compile(
    r"mebook\.cc|ePUBw|Kindle|Calibre|azw3|扫描|公众号|二维码|"
    r"更多.*电子书|版权|ISBN|版权所有|本书由|发布于|来源[:：]|在线阅读|下载电子|"
    r"copyright|©|all rights reserved|translation|arranged through|CIP|"
    r"图书在版编目|出\s*版\s*人|出\s*品\s*人|责任编辑|装帧设计|内文制作|发行热线|"
    r"印刷|印务|开本|印张|字数|定价|版次|印次|新华书店|桂林市|网址[:：]|www\.|"
    r"出版社，\d{4}|出版社|总目录|书名[:：]|作者[:：]|译者[:：]|书号[:：]|"
    r"电子版|制作发行|编\s*者|通讯地址|邮政编码|电\s*话|电子邮箱|"
    r"开\s*本|印\s*张|定\s*价|本书纸版由|本译丛获|赞助支持|主编|"
    r"Ⅰ[．.]|Ⅱ[．.]|Ⅲ[．.]|Ⅳ[．.]"
)
PUBLISHER_RE = re.compile(r"出版社|出版发行|印次|版次")
HTML_ENTITY_RE = re.compile(r"&(#\d+|#x[0-9a-fA-F]+|[a-zA-Z]+);")
CHAPTER_RE = re.compile(r"^第[0-9一二三四五六七八九十百千零〇两]+[章回节卷部篇集]")
CONTENT_START_RE = re.compile(r"^[序前言楔引跋后记尾声]|^献给")
PAGE_LIST_RE = re.compile(r"^[-*]\s*\d{1,4}$")
PAGE_HEADING_RE = re.compile(r"^#{1,6}\s*\d{1,4}\s*$")
SLASH_LINE_RE = re.compile(r"^[\\/]\s*$")
CIP_CLASS_RE = re.compile(r"^[ⅠⅡⅢⅣⅤ]+[．.]\s*[①②③④⑤⑥⑦⑧⑨⑩A-Z0-9]")
TABLE_PLACEHOLDER_RE = re.compile(r"^\[TABLE\]$")
FRONT_MATTER_MARKERS_RE = re.compile(
    r"内容提要|内容简介|书名原文|图书在版编目|版权页|"
    r"Ⅰ[．.]|Ⅱ[．.]|Ⅲ[．.]|Ⅳ[．.]|"
    r"图灵|人民邮电|机械工业|电子工业|清华大学出版社|北京大学出版社|"
    r"译者|著者|毕业于|丛书|"
    r"主\s*办|社长|总编辑|副总编辑|副社长|编辑出版|美术编辑|制版|"
    r"发行印制|广告部|广告经理|稿酬|邮购|新媒体部|主编|编委会"
)
STRONG_HEADING_RE = re.compile(r"^#{1,6}\s+([^#\d][^\n]*)$")
FRONT_HEADING_RE = re.compile(
    r"^(版权|版权声明|版权信息|前言|目录|致谢|导读|内容提要|内容简介|"
    r"出版说明|读者对象|主要|代码|勘误|排版|许可证|作者简介|再版|修订|"
    r"本书所获奖项和赞誉|赞誉|献给我|作者前言|前言|自序|代序|译者序|译序|"
    r"出版者的话|编辑推荐|推荐序|名家推荐|推荐语|序言)"
)
TOC_BLOCK_HEADING_RE = re.compile(r"^(总目录|目\s*录)$")
PREFACE_BLOCK_HEADING_RE = re.compile(
    r"^(理想国译丛序|丛书总序|出版说明|编辑推荐|内容提要|作者简介|"
    r"总序|序言|致谢|导读|版权信息|版权声明|前言)$"
)


def _normalize_entities(text: str) -> str:
    def _replace(match: re.Match[str]) -> str:
        value = match.group(1)
        if value.startswith("#x"):
            return chr(int(value[2:], 16))
        if value.startswith("#"):
            return chr(int(value[1:]))
        return html.unescape(f"&{value};")

    return HTML_ENTITY_RE.sub(_replace, text)


def _remove_frontmatter(text: str) -> str:
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                return "\n".join(lines[i + 1 :])
    return text


def _is_metadata(line: str) -> bool:
    if WATERMARK_RE.search(line):
        return True
    if PUBLISHER_RE.search(line) and len(line) <= 40:
        return True
    return False


def _looks_like_front_matter(line: str, started: bool) -> bool:
    if not line:
        return not started
    stripped = line.rstrip("\\/")
    if WATERMARK_RE.search(stripped):
        return True
    if PUBLISHER_RE.search(stripped) and (not started or len(stripped) <= 40):
        return True
    if SLASH_LINE_RE.match(line) or SLASH_PLACEHOLDER_RE.match(line):
        return True
    if TOC_LINE_RE.match(line):
        return True
    if PAGE_LIST_RE.match(line) or PAGE_NUMBER_RE.match(line) or PAGE_HEADING_RE.match(line):
        return True
    if CIP_CLASS_RE.match(stripped):
        return True
    if not started and FRONT_MATTER_MARKERS_RE.search(stripped):
        return True
    if re.match(r"^[（(]?[^）)]*[)）]?[^／/]*[／/]著$", stripped):
        return True
    if re.match(r"^[^／/]*[／/]译$", stripped):
        return True
    if re.match(r"^·[^·]+·$", stripped):
        return True
    if not started:
        cjk = len(re.findall(r"[\u4e00-\u9fff]", line))
        if len(line) < 40 and cjk / max(1, len(line)) < 0.3:
            return True
        if re.match(r"^[A-Za-z]", line) and len(line) < 40:
            return True
    return False


def _is_content_start(line: str) -> bool:
    if CHAPTER_RE.match(line) or CONTENT_START_RE.match(line):
        return True
    cjk = len(re.findall(r"[\u4e00-\u9fff]", line))
    return cjk >= 6 and len(line) >= 15


def _find_strong_start(lines: list[str]) -> int:
    in_toc = False
    for i, raw in enumerate(lines[:3000]):
        line = raw.strip()
        if TOC_HEADING_RE.match(line):
            in_toc = True
            continue
        if in_toc:
            if not line:
                continue
            if line.startswith("#"):
                match = STRONG_HEADING_RE.match(line)
                text = match.group(1).strip() if match else line
                if re.match(r"^第[一二三四五六七八九十]+部$", text) or TOC_HEADING_RE.match(text):
                    continue
                in_toc = False
            elif (
                CHAPTER_RE.match(line)
                or re.match(r"^第[一二三四五六七八九十]+部", line)
                or PAGE_NUMBER_RE.match(line)
            ):
                continue
            else:
                in_toc = False
        if CHAPTER_RE.match(line):
            return i
        match = STRONG_HEADING_RE.match(line)
        if not match:
            continue
        text = match.group(1).strip()
        compact = re.sub(r"\s+", "", text)
        if TOC_HEADING_RE.match(compact) or FRONT_HEADING_RE.match(compact):
            continue
        if re.fullmatch(r"\d{1,4}", text):
            continue
        if _looks_like_title_page(lines, i):
            continue
        return i
    return -1


def _looks_like_title_page(lines: list[str], idx: int) -> bool:
    seen = 0
    for raw in lines[idx + 1 : idx + 80]:
        line = raw.strip()
        if not line:
            continue
        seen += 1
        if seen > 12:
            return False
        if re.search(
            r"著|译|出版社|ISBN|版权|内容提要|作者简介|Copyright|All rights",
            line,
        ):
            return True
    return False


def _drop_front_matter(lines: list[str], stats: dict) -> list[str]:
    strong_idx = _find_strong_start(lines)
    if strong_idx >= 0:
        stats["frontmatter_lines"] += strong_idx
        out: list[str] = []
        for line in lines[strong_idx:]:
            if _looks_like_front_matter(line, True):
                stats["removed_lines"] += 1
                continue
            out.append(line)
        return out

    out: list[str] = []
    started = False
    for line in lines:
        if not started and _looks_like_front_matter(line, started):
            stats["frontmatter_lines"] += 1
            continue
        if not started and _is_content_start(line):
            started = True
            out.append(line)
            continue
        if not started:
            stats["frontmatter_lines"] += 1
            continue
        if _looks_like_front_matter(line, started):
            stats["removed_lines"] += 1
            continue
        out.append(line)
    return out


def _looks_like_strong_heading(line: str) -> bool:
    match = STRONG_HEADING_RE.match(line)
    if not match:
        return False
    text = match.group(1).strip()
    compact = re.sub(r"\s+", "", text)
    if TOC_HEADING_RE.match(compact) or FRONT_HEADING_RE.match(compact):
        return False
    if re.fullmatch(r"\d{1,4}", text):
        return False
    return True


def _is_body_start(line: str) -> bool:
    if CHAPTER_RE.match(line):
        return True
    if _looks_like_strong_heading(line):
        return True
    cjk = len(re.findall(r"[\u4e00-\u9fff]", line))
    return cjk >= 6 and len(line) >= 15


def _remove_front_blocks(lines: list[str], stats: dict) -> list[str]:
    out: list[str] = []
    block: str | None = None
    for line in lines:
        if block is None:
            if TOC_BLOCK_HEADING_RE.match(line):
                block = "toc"
                stats["removed_lines"] += 1
                continue
            if PREFACE_BLOCK_HEADING_RE.match(line):
                block = "preface"
                stats["removed_lines"] += 1
                continue
            out.append(line)
            continue
        if block == "toc":
            if _looks_like_front_matter(line, True):
                stats["removed_lines"] += 1
                continue
            if _is_body_start(line):
                block = None
                out.append(line)
                continue
            stats["removed_lines"] += 1
            continue
        if block == "preface":
            if CHAPTER_RE.match(line) or (
                _looks_like_strong_heading(line)
                and not _looks_like_front_matter(line, True)
            ):
                block = None
                out.append(line)
                continue
            stats["removed_lines"] += 1
            continue
    return out


def _clean_line(line: str, stats: dict) -> str:
    line = _normalize_entities(line)
    line = HTML_COMMENT_RE.sub("", line)
    line = HTML_TAG_RE.sub("", line)
    line = IMAGE_RE.sub("", line)
    if IMAGE_RE.search(line):
        stats["image_lines"] += 1
    line = FOOTNOTE_REF_RE.sub("", line)
    line = INLINE_LINK_RE.sub(r"\1", line)
    line = re.sub(r"\]?\(#[^)]*\)", "", line)
    anchor = re.search(r"\(#[^)]*\)", line)
    if anchor and anchor.start() <= 12:
        line = line[anchor.end() :].strip()
    line = HEADING_RE.sub("", line)
    line = re.sub(r"^>\s?", "", line)
    line = re.sub(r"[*_~`]+", "", line)
    return line.strip()


def clean_book(path: Path) -> tuple[str, dict]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    stats: dict = {
        "input_chars": len(raw),
        "image_links": len(IMAGE_RE.findall(raw)),
        "toc_links": len(TOC_LINE_RE.findall(raw)),
        "footnote_defs": len(FOOTNOTE_DEF_RE.findall(raw, re.M)),
        "html_tags": len(HTML_TAG_RE.findall(raw)),
        "removed_lines": 0,
        "frontmatter_lines": 0,
    }

    text = _remove_frontmatter(raw)
    text = HTML_COMMENT_RE.sub("", text)
    text = STYLE_BLOCK_RE.sub("", text)
    text = CSS_RULE_RE.sub("", text)
    text = HTML_TAG_RE.sub("", text)
    text = IMAGE_RE.sub("", text)

    lines = text.splitlines()
    lines = _drop_front_matter(lines, stats)
    lines = _remove_front_blocks(lines, stats)
    out: list[str] = []
    prev = None
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        if CODE_FENCE_RE.match(line):
            continue
        if FOOTNOTE_DEF_RE.match(line):
            continue
        if TOC_LINE_RE.match(line) or TOC_HEADING_RE.match(line):
            continue
        if RULE_PLACEHOLDER_RE.match(line) or TABLE_PLACEHOLDER_RE.match(line):
            continue
        if _is_metadata(line):
            stats["removed_lines"] += 1
            continue
        line = _clean_line(line, stats)
        if not line:
            continue
        if line == prev:
            continue
        out.append(line)
        prev = line

    cleaned = "\n\n".join(out) + ("\n" if out else "")
    stats["output_chars"] = len(cleaned)
    stats["output_lines"] = len(out)
    stats["cjk_chars"] = len(re.findall(r"[\u4e00-\u9fff]", cleaned))
    non_space = re.sub(r"\s+", "", cleaned)
    stats["cjk_ratio"] = round(stats["cjk_chars"] / max(1, len(non_space)), 4)
    stats["remaining_markdown"] = len(
        re.findall(r"!\[|\[[^\]]+\]\([^)]*\)|```", cleaned)
    )
    return cleaned, stats


def _slug(path: Path) -> str:
    if path.name.lower() == "book.md":
        base = path.parent.name
    else:
        base = path.stem
    slug = re.sub(r"[^\w\u4e00-\u9fff-]+", "_", base).strip("_")
    return slug or path.stem


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, required=True, help="md file or directory")
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--manifest", type=Path)
    ap.add_argument("--dry-run", action="store_true", help="only print stats")
    args = ap.parse_args()

    input_path = args.input
    files = [input_path] if input_path.is_file() else sorted(input_path.rglob("*.md"))
    if not files:
        print("no markdown files found")
        return 2
    files = [f for f in files if f.name.lower() not in ("index.md", "corpus.md")]
    if not files:
        print("no book markdown files found")
        return 2

    out_dir = args.output_dir
    if not args.dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)

    manifest: dict = {"files": [], "totals": {}}
    totals: dict = {
        "input_chars": 0,
        "output_chars": 0,
        "cjk_chars": 0,
        "image_links": 0,
        "toc_links": 0,
        "footnote_defs": 0,
        "html_tags": 0,
        "removed_lines": 0,
    }
    warnings: list[str] = []

    for path in files:
        cleaned, stats = clean_book(path)
        slug = _slug(path)
        entry = {"source": str(path), "slug": slug, **stats}
        manifest["files"].append(entry)
        for key in totals:
            totals[key] += int(stats.get(key, 0))
        if stats["cjk_ratio"] < 0.3 and stats["output_chars"] > 1000:
            warnings.append(f"low CJK ratio {stats['cjk_ratio']}: {path.name}")
        if stats["remaining_markdown"] > 50:
            warnings.append(f"markdown leftovers {stats['remaining_markdown']}: {path.name}")
        if not args.dry_run:
            out_path = out_dir / f"{slug}.txt"
            out_path.write_text(cleaned, encoding="utf-8")
            entry["output"] = str(out_path)
        print(f"{slug}: in={stats['input_chars']} out={stats['output_chars']} "
              f"cjk={stats['cjk_ratio']} img={stats['image_links']} "
              f"toc={stats['toc_links']} html={stats['html_tags']}")

    manifest["totals"] = totals
    manifest["warnings"] = warnings
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    print("files:", len(files))
    print("totals:", totals)
    if warnings:
        print("warnings:")
        for warning in warnings[:30]:
            print(" -", warning)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
