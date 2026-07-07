"""get_entries must close a budget item when a row carries its total column,
even if a trailing extra column/marker follows the 'บาท' cell. Otherwise the next
sibling row gets merged into the same node and goes missing from the tree.

Regression coverage for the sibling-merge defect (trailing-column / trailing-'*').
"""
from types import SimpleNamespace

from anytree import PreOrderIter

from thbud.textextract import LineText, PageText, WordText
from thbud.textextract.pdf_to_tree import get_entries, extract_tree_levels


def make_page(rows):
    lines = []
    for li, cells in enumerate(rows):
        words = [WordText(x0=ci, y0=li, x1=ci + 1, y1=li, text=t)
                 for ci, t in enumerate(cells)]
        lines.append(LineText(words, page_index=0, line_index=li))
    page = PageText(lines, page_index=0, width=100, height=100, is_image=False,
                    document=SimpleNamespace(filepath="test.xlsx"))
    for ln in lines:
        ln.page = page
    return page


def _names(entries):
    return [str(e) for e in entries]


def test_trailing_numeric_column_splits_siblings():
    # Row 1 keeps its total (10,560,300 บาท) but has a trailing extra column '1,842'
    # so the last whitespace token is not 'บาท'. The next sibling must NOT merge in.
    page = make_page([
        ["1) ค่าใช้จ่ายบุคลากร", "10,560,300", "บาท", "1,842"],
        ["2) ค่าใช้จ่ายดำเนินงาน", "42,550,800", "บาท"],
    ])
    entries = get_entries(page.lines)
    assert len(entries) == 2, _names(entries)
    assert "ค่าใช้จ่ายบุคลากร" in str(entries[0])
    assert "ค่าใช้จ่ายดำเนินงาน" in str(entries[1])
    # the sibling text must not leak into the first node
    assert "ค่าใช้จ่ายดำเนินงาน" not in str(entries[0])


def test_trailing_star_marker_splits_siblings():
    # Row 1's total column cell is followed by a standalone '*' cell.
    page = make_page([
        ["1) ค่าใช้จ่ายบุคลากร", "10,560,300", "บาท", "*"],
        ["2) ค่าใช้จ่ายดำเนินงาน", "42,550,800", "บาท"],
    ])
    entries = get_entries(page.lines)
    assert len(entries) == 2, _names(entries)
    assert "ค่าใช้จ่ายดำเนินงาน" not in str(entries[0])


def test_split_siblings_get_their_own_amounts():
    # End-to-end: after the split, each node carries its own column total.
    page = make_page([
        ["1) ค่าใช้จ่ายบุคลากร", "10,560,300", "บาท", "1,842"],
        ["2) ค่าใช้จ่ายดำเนินงาน", "42,550,800", "บาท"],
    ])
    root = extract_tree_levels(get_entries(page.lines))
    nodes = {n.name.split()[1]: n for n in PreOrderIter(root)
             if n.name and len(n.name.split()) > 1}
    a = next(n for n in PreOrderIter(root) if n.name and "บุคลากร" in n.name)
    b = next(n for n in PreOrderIter(root) if n.name and "ดำเนินงาน" in n.name)
    assert a.amount == 10560300.0
    assert b.amount == 42550800.0


def test_wrapped_description_stays_single_item():
    # A description that wraps across rows, with the total only on the LAST row,
    # must remain ONE item (row 1 has no total column, so it must not close).
    page = make_page([
        ["1) เงินเดือนและค่าจ้างประจำของข้าราชการ"],
        ["และลูกจ้างประจำในสังกัด", "10,560,300", "บาท"],
    ])
    entries = get_entries(page.lines)
    assert len(entries) == 1, _names(entries)
    assert "ลูกจ้างประจำ" in str(entries[0])


def test_quantity_line_attaches_not_splits():
    # A 'รวม N รายการ' quantity line following a total row attaches to that item.
    page = make_page([
        ["1) ครุภัณฑ์สำนักงาน", "5,000,000", "บาท"],
        ["รวม 117 รายการ (รวม 527 หน่วย)"],
    ])
    entries = get_entries(page.lines)
    assert len(entries) == 1, _names(entries)


def test_embedded_per_unit_price_does_not_split():
    # An embedded per-unit price ('ๆ ละ 6,500 บาท') lives inside the text cell, not a
    # standalone total column, so a row wrapping before its total must not close early.
    page = make_page([
        ["1) เตาอบไฟฟ้า จำนวน 22 เครื่องๆ ละ 6,500 บาท"],
        ["รวมเป็นเงิน", "143,000", "บาท"],
    ])
    entries = get_entries(page.lines)
    assert len(entries) == 1, _names(entries)
