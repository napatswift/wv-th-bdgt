"""Tree nodes must remember which source rows they came from.

For XLSX documents LineText.line_index is the 1-based worksheet row, so the
extent of an entry's lines is the cell-range provenance of the resulting
BudgetItem (row_start/row_end). Downstream (th-budget) composes it into a
`storage_key#'Sheet'!start:end` reference.
"""
from types import SimpleNamespace

from anytree import PreOrderIter

from thbud.textextract import LineText, PageText, WordText
from thbud.textextract.pdf_to_tree import get_entries, extract_tree_levels


def make_page(rows, page_index=0, first_row=1):
    """rows: list of (indent, [cells]); line_index counts from first_row like
    worksheet rows (1-based)."""
    lines = []
    for li, (indent, cells) in enumerate(rows, start=first_row):
        words = [WordText(x0=indent + ci, y0=li, x1=indent + ci + 1, y1=li, text=t)
                 for ci, t in enumerate(cells)]
        lines.append(LineText(words, page_index=page_index, line_index=li))
    page = PageText(lines, page_index=page_index, width=100, height=100,
                    is_image=False, document=SimpleNamespace(filepath="test.xlsx"))
    for ln in lines:
        ln.page = page
    return page


def node(root, text):
    return next(n for n in PreOrderIter(root) if n.name and text in n.name)


def test_single_row_item_carries_its_worksheet_row():
    root = extract_tree_levels(get_entries(make_page([
        (0, ["1. งบเงินอุดหนุน", "105,734,900", "บาท"]),
        (1, ["1.1 เงินอุดหนุนทั่วไป", "105,734,900", "บาท"]),
    ], first_row=12).lines))

    parent = node(root, "งบเงินอุดหนุน")
    child = node(root, "เงินอุดหนุนทั่วไป")
    assert (parent.row_start, parent.row_end) == (12, 12)
    assert (child.row_start, child.row_end) == (13, 13)


def test_multi_row_item_spans_from_bullet_to_amount_row():
    # Name wraps: the bullet row has no total column, the amount lands two rows
    # below — the item's provenance is the whole span.
    root = extract_tree_levels(get_entries(make_page([
        (0, ["1. งบลงทุน", "500,000", "บาท"]),
        (1, ["1.1 ค่าก่อสร้างอาคารที่ทำการ"]),
        (1, ["พร้อมสิ่งก่อสร้างประกอบ", "500,000", "บาท"]),
    ], first_row=20).lines))

    item = node(root, "ค่าก่อสร้างอาคารที่ทำการ")
    assert (item.row_start, item.row_end) == (21, 22)


def test_synthetic_root_has_no_row_provenance():
    root = extract_tree_levels(get_entries(make_page([
        (0, ["1. งบเงินอุดหนุน", "100", "บาท"]),
    ]).lines))
    assert root.row_start is None and root.row_end is None
