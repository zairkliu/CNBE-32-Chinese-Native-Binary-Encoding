from __future__ import annotations


def test_import_cnbe32_smoke() -> None:
    import cnbe32
    assert "encode_cnbe" in cnbe32.__all__
    assert "decode_cnbe" in cnbe32.__all__
    assert "bit_hamming_distance" in cnbe32.__all__


def test_encode_decode_smoke() -> None:
    from cnbe32 import decode_cnbe, encode_cnbe
    encoded = encode_cnbe(radix=1, stroke=2, struct=3, index=4, ext=5)
    decoded = decode_cnbe(encoded)
    assert decoded["radix"] == 1
    assert decoded["stroke"] == 2
    assert decoded["struct"] == 3
    assert decoded["index"] == 4
    assert decoded["ext"] == 5
