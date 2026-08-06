#!/usr/bin/env python3
"""Build GF0011/GF0013 anchoring candidates for the 812 approved provisional rows.

Reference source for the 201 radicals: GF 0011-2009 汉字部首表
(public re-publication: https://www.ichara.cn/web/account/view_article.php?art_id=110).
Stroke truth reference: Unihan kTotalStrokes (cross-reference only, not GF0013).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

EXP = Path(__file__).resolve().parent
REPO = EXP.parents[1]

# (GF0011 code, main radical, attached forms string or "")
GF201 = [
    (1, "一", ""), (2, "丨", "亅"), (3, "丿", ""), (4, "丶", ""), (5, "乛", ""),
    (6, "十", ""), (7, "厂", "⺁"), (8, "匚", ""), (9, "卜", "⺊"), (10, "冂", "⺆"),
    (11, "八", "丷"), (12, "人", "亻入"), (13, "勹", ""), (14, "儿", ""), (15, "匕", ""),
    (16, "几", "⺇"), (17, "亠", ""), (18, "冫", ""), (19, "冖", ""), (20, "凵", ""),
    (21, "卩", "⺋"), (22, "刀", "刂⺈"), (23, "力", ""), (24, "又", ""), (25, "厶", ""),
    (26, "廴", ""), (27, "干", ""), (28, "工", ""), (29, "土", "士"), (30, "艹", "艸"),
    (31, "寸", ""), (32, "廾", ""), (33, "大", ""), (34, "尢", "兀尣"), (35, "弋", ""),
    (36, "小", "⺌"), (37, "口", ""), (38, "囗", ""), (39, "山", ""), (40, "巾", ""),
    (41, "彳", ""), (42, "彡", ""), (43, "夕", ""), (44, "夂", ""), (45, "丬", "爿"),
    (46, "广", ""), (47, "门", "門"), (48, "宀", ""), (49, "辶", "辵"), (50, "彐", "彐彑"),
    (51, "尸", ""), (52, "己", "已巳"), (53, "弓", ""), (54, "子", ""), (55, "屮", ""),
    (56, "女", ""), (57, "飞", "飛"), (58, "马", "馬"), (59, "幺", ""), (60, "巛", ""),
    (61, "王", "玉"), (62, "无", "旡"), (63, "韦", "韋"), (64, "木", "朩"), (65, "支", ""),
    (66, "犬", "犭"), (67, "歹", "歺"), (68, "车", "車"), (69, "牙", ""), (70, "戈", ""),
    (71, "比", ""), (72, "瓦", ""), (73, "止", ""), (74, "攴", "攵"), (75, "日", "⺜曰"),
    (76, "贝", "貝"), (77, "水", "氵氺"), (78, "见", "見"), (79, "牛", "牜"),
    (80, "手", "扌看"), (81, "气", ""), (82, "毛", ""), (83, "长", "镸長"), (84, "片", ""),
    (85, "斤", ""), (86, "爪", "爫"), (87, "父", ""), (88, "月", "⺝"), (89, "氏", ""),
    (90, "欠", ""), (91, "风", "風"), (92, "殳", ""), (93, "文", ""), (94, "方", ""),
    (95, "火", "灬"), (96, "斗", ""), (97, "户", ""), (98, "心", "忄⺗"), (99, "毋", "母"),
    (100, "示", "礻"), (101, "甘", ""), (102, "石", ""), (103, "龙", "龍"), (104, "业", ""),
    (105, "目", ""), (106, "田", ""), (107, "罒", ""), (108, "皿", ""), (109, "生", ""),
    (110, "矢", ""), (111, "禾", ""), (112, "白", ""), (113, "瓜", ""), (114, "鸟", "鳥"),
    (115, "疒", ""), (116, "立", ""), (117, "穴", ""), (118, "疋", "⺪"), (119, "皮", ""),
    (120, "癶", ""), (121, "矛", ""), (122, "耒", ""), (123, "老", ""), (124, "耳", ""),
    (125, "臣", ""), (126, "覀", "襾西"), (127, "而", ""), (128, "页", "頁"), (129, "至", ""),
    (130, "虍", "虎"), (131, "虫", ""), (132, "肉", ""), (133, "缶", ""), (134, "舌", ""),
    (135, "竹", "⺮"), (136, "臼", "⺽"), (137, "自", ""), (138, "血", ""), (139, "舟", ""),
    (140, "色", ""), (141, "齐", "齊"), (142, "衣", "衤"), (143, "羊", "⺶⺷"), (144, "米", ""),
    (145, "聿", "肀⺻"), (146, "艮", ""), (147, "羽", ""), (148, "糸", "纟糹"),
    (149, "麦", "麥"), (150, "走", ""), (151, "赤", ""), (152, "豆", ""), (153, "酉", ""),
    (154, "辰", ""), (155, "豕", ""), (156, "卤", "鹵"), (157, "里", ""), (158, "足", "⻊"),
    (159, "邑", "阝右"), (160, "身", ""), (161, "釆", ""), (162, "谷", ""), (163, "豸", ""),
    (164, "龟", "龜"), (165, "角", ""), (166, "言", "讠"), (167, "辛", ""), (168, "青", ""),
    (169, "龺", ""), (170, "雨", ""), (171, "非", ""), (172, "齿", "齒"), (173, "黾", "黽"),
    (174, "隹", ""), (175, "阜", "阝左"), (176, "金", "钅"), (177, "鱼", "魚"), (178, "隶", ""),
    (179, "革", ""), (180, "面", ""), (181, "韭", ""), (182, "骨", ""), (183, "香", ""),
    (184, "鬼", ""), (185, "食", "饣飠"), (186, "音", ""), (187, "首", ""), (188, "髟", ""),
    (189, "鬲", ""), (190, "鬥", ""), (191, "高", ""), (192, "黄", ""), (193, "麻", ""),
    (194, "鹿", ""), (195, "鼎", ""), (196, "黑", ""), (197, "黍", ""), (198, "鼓", ""),
    (199, "鼠", ""), (200, "鼻", ""), (201, "龠", ""),
]


def build_name_map() -> dict[str, tuple[int, str]]:
    m: dict[str, tuple[int, str]] = {}
    for code, main, attached in GF201:
        m[main] = (code, main)
        for form in attached:
            m[form] = (code, main)
    return m


def load_unihan_krs_strokes(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 3 or parts[1] != "kTotalStrokes":
            continue
        result[parts[0]] = parts[2].strip()
    return result


def main() -> None:
    name_map = build_name_map()
    packet = json.loads((EXP / "coverage_remediation_packet.json").read_text(encoding="utf-8"))
    approved = [e for e in packet["entries"] if e.get("review_status") == "APPROVED"]
    strokes = load_unihan_krs_strokes(
        EXP.parent / "2026-08-05_scheme_comparison" / "build" / "Unihan_IRGSources.txt"
    )

    table = [{"code": c, "main": m, "attached": a} for c, m, a in GF201]
    (REPO / "data" / "gf0011_201_radicals.json").write_text(
        json.dumps(
            {"schema_version": 1, "source": "GF 0011-2009 汉字部首表（公开转载）",
             "source_url": "https://www.ichara.cn/web/account/view_article.php?art_id=110",
             "radicals": table},
            ensure_ascii=False, indent=2,
        ),
        encoding="utf-8",
    )

    entries = []
    mapped = 0
    for e in approved:
        review = e.get("review", {})
        name = review.get("reviewed_radix_name")
        gf = name_map.get(name) if name else None
        ucp = f"U+{ord(e['char']):04X}"
        stroke_candidate = strokes.get(ucp)
        if gf:
            mapped += 1
        entries.append(
            {
                "char": e["char"],
                "codepoint": e["codepoint"],
                "reviewed_radix_name": name,
                "gf0011_code": gf[0] if gf else None,
                "gf0011_main": gf[1] if gf else None,
                "gf0011_status": "MAPPED" if gf else "REQUIRES_GF0012_REVIEW",
                "gf0013_strokes_candidate": stroke_candidate,
                "gf0013_status": "REQUIRES_OFFICIAL_STROKE_TABLE",
                "current_radix": e.get("proposed", {}).get("radix"),
                "current_strokes": e.get("proposed", {}).get("strokes"),
            }
        )

    summary = {
        "total": len(entries),
        "gf0011_mapped": mapped,
        "gf0011_requires_review": len(entries) - mapped,
        "gf0013_strokes_candidate_available": sum(1 for e in entries if e["gf0013_strokes_candidate"]),
        "boundary": "GF0011 按 201 部首表名称/附形匹配；GF0013 笔画待权威逐字表，当前仅 Unihan 交叉参考",
    }
    out = {
        "schema_version": 1,
        "anchored_at": "2026-08-06",
        "summary": summary,
        "entries": entries,
    }
    (EXP / "gf0011_0013_anchoring_packet.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
