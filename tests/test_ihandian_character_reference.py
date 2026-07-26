"""Keep ihandian extraction bounded and explicitly cross-reference-only."""

from scripts.extract_ihandian_character_reference import parse_ihandian_html


SAMPLE = """
<p>〔𫠊〕字拼音是（xuán），部首是<em>马部</em>，总笔画是<em>8画</em>。</p>
<p>〔𫠊〕字是左右结构，可拆字为“<em>马、玄</em>”。</p>
<p>〔𫠊〕字仓颉码是<em>NMYVI</em>，四角号码是<em>无</em>，郑码是<em>XSZZ</em>。</p>
<p>〔𫠊〕字统一码（UNICODE）是<em>2B80A</em>，位于UNICODE的<em>中日韩统一表意文字 (扩展D)</em>，十进制：178186，UTF-32：0002B80A，UTF-8：F0ABA08A。</p>
<p>〔𫠊〕字在<em>《通用规范汉字表》</em>的<em>三级字表</em>表中，序号<em>6752</em>。</p>
"""


def test_ihandian_overview_extracts_five_field_groups_without_promotion() -> None:
    record = parse_ihandian_html("2B80A", SAMPLE, "https://www.ihandian.com/zidian/zi-2b80a.html")

    assert record["parse_status"] == "PARSED_IDENTITY_ALIGNED"
    assert record["fields"]["pinyin"] == "xuán"
    assert record["fields"]["radical"] == "马部"
    assert record["fields"]["structure"] == "左右结构"
    assert record["fields"]["decomposition"] == ["马", "玄"]
    assert record["fields"]["cangjie"] == "NMYVI"
    assert record["fields"]["utf8"] == "F0ABA08A"
    assert record["fields"]["character_table_level"] == "三级字表"
    assert record["fields"]["character_table_sequence"] == "6752"
    assert record["source_level"] == "network_dictionary_cross_reference"
    assert not record["decision"]["may_generate_cnbe_candidate"]
    assert not record["decision"]["may_claim_national_standard"]
