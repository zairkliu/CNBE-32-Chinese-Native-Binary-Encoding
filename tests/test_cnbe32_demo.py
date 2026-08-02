from cnbe32_demo.presenter import encode_text_for_demo


def test_demo_presenter_encodes_known_runtime_character() -> None:
    rows = encode_text_for_demo("中")

    assert len(rows) == 1
    row = rows[0]
    assert row.char == "中"
    assert row.unicode_hex == "U+4E2D"
    assert row.cnbe_hex == "0x022002D0"
    assert row.cnbe_binary == "00000010001000000000001011010000"
    assert row.radix_name == "丨"
    assert row.strokes == 4
    assert row.struct_name == "镶嵌"
    assert row.status == "encoded"


def test_demo_presenter_preserves_missing_character_status() -> None:
    rows = encode_text_for_demo("😀")

    assert len(rows) == 1
    row = rows[0]
    assert row.unicode_hex == "U+1F600"
    assert row.cnbe_hex is None
    assert row.status == "missing"


def test_demo_presenter_skips_whitespace() -> None:
    rows = encode_text_for_demo("中 国")

    assert [row.char for row in rows] == ["中", "国"]
