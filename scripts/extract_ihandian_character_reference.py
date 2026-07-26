#!/usr/bin/env python3
"""Extract one ihandian character overview as network-dictionary review evidence.

The output is deliberately bounded to a single character. It records webpage
fields for reviewer navigation only; it never assigns GF0017 points, emits a
CNBE candidate, writes a source table, or rebuilds a database.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CODEPOINT = "2B80A"
DEFAULT_OUTPUT = ROOT / "evidence" / "validation" / "ihandian" / "U_2B80A_IHANDIAN_REFERENCE.json"
DEFAULT_REPORT = ROOT / "reports" / "IHANDIAN_U_2B80A_REFERENCE.md"


def normalize_codepoint(value: str) -> str:
    return value.upper().removeprefix("U+")


def ihandian_url(codepoint: str) -> str:
    return f"https://www.ihandian.com/zidian/zi-{normalize_codepoint(codepoint).lower()}.html"


def text_content(fragment: str) -> str:
    value = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", " ", fragment)
    value = re.sub(r"(?s)<[^>]+>", "", value)
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def overview_paragraphs(raw_html: str) -> list[str]:
    return [text_content(item) for item in re.findall(r"(?is)<p[^>]*>(.*?)</p>", raw_html)]


def value_or_empty(match: re.Match[str] | None, group: str) -> str:
    return match.group(group).strip() if match else ""


def parse_ihandian_html(codepoint: str, raw_html: str, source_url: str) -> dict[str, Any]:
    """Parse the five-line overview and preserve field gaps without inference."""

    normalized = normalize_codepoint(codepoint)
    character = chr(int(normalized, 16))
    paragraphs = overview_paragraphs(raw_html)
    overview = [line for line in paragraphs if character in line and "字" in line]
    joined = "\n".join(overview)

    identity = re.search(
        r"字拼音是（(?P<pinyin>[^）]+)），部首是(?P<radical>[^，]+)，总笔画是(?P<strokes>\d+)画",
        joined,
    )
    structure = re.search(r"字是(?P<structure>[^，]+)，可拆字为“(?P<decomposition>[^”]+)”", joined)
    input_codes = re.search(
        r"字仓颉码是(?P<cangjie>[^，]+)，四角号码是(?P<sijiao>[^，]+)，郑码是(?P<zhengma>[^。]+)",
        joined,
    )
    unicode_line = re.search(
        r"统一码（UNICODE）是(?P<unicode>[0-9A-Fa-f]+)，位于UNICODE的(?P<cjk>[^，]+)，"
        r"十进制：(?P<decimal>\d+)，UTF-32：(?P<utf32>[0-9A-Fa-f]+)，UTF-8：(?P<utf8>[0-9A-Fa-f]+)",
        joined,
    )
    table_line = re.search(r"字在《(?P<table>[^》]+)》的(?P<level>[^中]+)中，序号(?P<sequence>\d+)", joined)
    page_unicode = value_or_empty(unicode_line, "unicode").upper()
    fields = {
        "pinyin": value_or_empty(identity, "pinyin"),
        "radical": value_or_empty(identity, "radical"),
        "total_strokes": value_or_empty(identity, "strokes"),
        "structure": value_or_empty(structure, "structure"),
        "decomposition": [item.strip() for item in value_or_empty(structure, "decomposition").split("、") if item.strip()],
        "cangjie": value_or_empty(input_codes, "cangjie"),
        "sijiao": value_or_empty(input_codes, "sijiao"),
        "zhengma": value_or_empty(input_codes, "zhengma"),
        "unicode_hex": page_unicode,
        "cjk_block": value_or_empty(unicode_line, "cjk"),
        "decimal": value_or_empty(unicode_line, "decimal"),
        "utf32": value_or_empty(unicode_line, "utf32").upper(),
        "utf8": value_or_empty(unicode_line, "utf8").upper(),
        "character_table": value_or_empty(table_line, "table"),
        "character_table_level": value_or_empty(table_line, "level").replace("表表", "表"),
        "character_table_sequence": value_or_empty(table_line, "sequence"),
    }
    identity_matches = bool(
        page_unicode
        and page_unicode == normalized
        and fields["decimal"] == str(int(normalized, 16))
        and fields["utf32"] == f"{int(normalized, 16):08X}"
        and fields["utf8"] == character.encode("utf-8").hex().upper()
    )
    found = [name for name, value in fields.items() if value not in ("", [])]
    return {
        "schema_version": "ihandian-character-reference-v1",
        "character": character,
        "unicode_codepoint": f"U+{normalized}",
        "source_url": source_url,
        "source_level": "network_dictionary_cross_reference",
        "authority_boundary": "IHANDIAN_REFERENCE_NOT_NATIONAL_STANDARD_NOT_GOLD_STANDARD",
        "page_overview_layout": [
            "拼音、部首、笔画",
            "结构、拆字结构",
            "仓颉码、四角号码、郑码",
            "统一字码、CJK、十进制、UTF-32、UTF-8",
            "汉字表格信息",
        ],
        "fields": fields,
        "identity_matches_unicode": identity_matches,
        "found_fields": found,
        "parse_status": "PARSED_IDENTITY_ALIGNED" if identity_matches else "PARSED_WITH_IDENTITY_OR_FIELD_GAPS",
        "decision": {
            "may_use_for_review_context": True,
            "may_assign_gf0017_points": False,
            "may_generate_cnbe_candidate": False,
            "may_modify_source_tables": False,
            "may_modify_sqlite": False,
            "may_claim_national_standard": False,
        },
    }


def fetch_html(url: str, timeout: int) -> str:
    import requests

    response = requests.get(
        url,
        timeout=timeout,
        headers={"User-Agent": "CNBE research ihandian reference extractor"},
    )
    response.raise_for_status()
    return response.text


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_report(path: Path, record: dict[str, Any]) -> None:
    fields = record["fields"]
    path.write_text(
        "# ihandian 单字网页交叉参考：" + record["character"] + "\n\n"
        f"- Unicode：`{record['unicode_codepoint']}`\n"
        f"- URL：<{record['source_url']}>\n"
        f"- 解析状态：`{record['parse_status']}`\n"
        f"- 来源等级：`{record['source_level']}`\n"
        f"- 权限边界：`{record['authority_boundary']}`\n\n"
        "## 页面概述字段\n\n"
        "1. 拼音、部首、笔画。\n2. 结构、拆字结构。\n3. 仓颉码、四角号码、郑码。\n"
        "4. 统一字码、CJK、十进制、UTF-32、UTF-8。\n5. 汉字表格信息。\n\n"
        "## 本次网页记录\n\n"
        f"- 拼音：`{fields['pinyin']}`；部首：`{fields['radical']}`；总笔画：`{fields['total_strokes']}`。\n"
        f"- 结构：`{fields['structure']}`；拆字：`{'、'.join(fields['decomposition'])}`。\n"
        f"- 仓颉：`{fields['cangjie']}`；四角：`{fields['sijiao']}`；郑码：`{fields['zhengma']}`。\n"
        f"- 统一码：`{fields['unicode_hex']}`；CJK：`{fields['cjk_block']}`；十进制：`{fields['decimal']}`；"
        f"UTF-32：`{fields['utf32']}`；UTF-8：`{fields['utf8']}`。\n"
        f"- 汉字表格：`《{fields['character_table']}》 {fields['character_table_level']}，序号 {fields['character_table_sequence']}`。\n\n"
        "该记录与辞书/ZDIC一样仅用于网络字典交叉参考和人工审核导航，不是国家标准、"
        "不是本探索项目的金标准，也不能自动改写人工审核、源表、SQLite 或 CNBE 候选字段。\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--codepoint", default=DEFAULT_CODEPOINT)
    parser.add_argument("--input-html", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--timeout", type=int, default=20)
    args = parser.parse_args()
    codepoint = normalize_codepoint(args.codepoint)
    url = ihandian_url(codepoint)
    if args.input_html:
        raw_html = args.input_html.read_text(encoding="utf-8")
        retrieval = {"method": "local_html_capture", "input_sha256": hashlib.sha256(args.input_html.read_bytes()).hexdigest()}
    else:
        raw_html = fetch_html(url, args.timeout)
        retrieval = {"method": "online_fetch", "response_sha256": hashlib.sha256(raw_html.encode("utf-8")).hexdigest()}
    record = parse_ihandian_html(codepoint, raw_html, url)
    record["retrieval"] = retrieval
    write_json(args.output, record)
    write_report(args.report, record)
    print(record["parse_status"])


if __name__ == "__main__":
    main()
