import re
from thbud.textextract.pdf_to_tree import get_year_from_string

def test_get_year_from_string_single_year():
    text = "ปี 2563 ตั้งงบประมาณ 616,834,700 บาท"
    assert get_year_from_string(text) == (2563, 2563)

def test_get_year_from_string_year_range():
    text = "ปี 2563-2564 ตั้งงบประมาณ 616,834,700 บาท"
    assert get_year_from_string(text) == (2563, 2564)

def test_get_year_from_string_year_range_with_spaces():
    text = "ปี 2563 - 2564 ตั้งงบประมาณ 616,834,700 บาท"
    assert get_year_from_string(text) == (2563, 2564)

def test_get_year_from_string_year_range_with_spaces_2():
    text = "ปี 2563- 2564 ตั้งงบประมาณ 616,834,700 บาท"
    assert get_year_from_string(text) == (2563, 2564)

def test_get_year_from_string_year_range_with_bad_ocr_1():
    text = "a 2563 - 2564 ตั้งงบประมาณ 616,834,700 บาท"
    assert get_year_from_string(text) == (2563, 2564)

def test_get_year_from_string_year_range_with_bad_ocr_2():
    text = "a 2563 = 2564 ตั้งงบประมาณ 616,834,700 บาท"
    assert get_year_from_string(text) == (2563, 2564)

def test_get_year_from_string_no_year():
    text = "ไม่มีปีที่ระบุ"
    assert get_year_from_string(text) == (0, 0)