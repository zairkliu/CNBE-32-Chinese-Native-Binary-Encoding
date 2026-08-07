"""Tests for the CNBE64 codec."""

from __future__ import annotations

import pytest

from cnbe64 import GB18030_STATUS, pack, pointer_for_char, unpack, validate


def test_roundtrip_pack_unpack() -> None:
    code = pack(cnbe32=0x01280000, gb18030_pointer=12439, status=GB18030_STATUS.MAPPED, present=True)
    fields = unpack(code)
    assert fields["version"] == 1
    assert fields["gb18030_pointer"] == 12439
    assert fields["gb18030_present"] == 1
    assert fields["gb18030_status"] == GB18030_STATUS.MAPPED
    assert fields["cnbe32"] == 0x01280000
    assert code == 0x10184BC001280000


def test_validate_rejects_missing_pointer_with_present() -> None:
    code = pack(cnbe32=0, present=True, status=GB18030_STATUS.MAPPED)
    ok, errors = validate(code)
    assert ok is False
    assert "present_without_pointer" in errors


def test_pointer_for_char_two_and_four_byte() -> None:
    ptr, four = pointer_for_char("\u6ca5")  # 沥
    assert four is False
    assert ptr == 12259
    ptr, four = pointer_for_char("\u3400")
    assert four is True
    assert ptr == 12439


def test_field_bounds() -> None:
    with pytest.raises(ValueError):
        pack(cnbe32=1 << 32)
    with pytest.raises(ValueError):
        pack(cnbe32=0, gb18030_pointer=1 << 21)
