from textextract import LineItem, get_amount_from_string
import pytest
from unittest.mock import MagicMock

def test_set_level():
    mock_line_wrapper = MagicMock()
    item = LineItem('itemtype', [
        mock_line_wrapper
    ])
    item.set_level(1)
    assert item.level == 1

def test_set_level_with_non_int():
    mock_line_wrapper = MagicMock()
    item = LineItem('itemtype', [
        mock_line_wrapper
    ])
    with pytest.raises(TypeError):
        item.set_level('1')


def test_get_amount_from_string():
    assert get_amount_from_string('1. งบรายจ่ายอื่น 3,469,200 บาท') == 3469200.00
    assert get_amount_from_string('1) การสัมมนาเสริมสร้างเครือข่ายคมครองผู้บรโภคในส่วนภูมิภาค 30,000 บาท') == 30000.00

def test_get_amount_from_string_with_non_number():
    assert get_amount_from_string('3.2.1 ค่าจ้างเหมาบริการ - บาท') == 0.00