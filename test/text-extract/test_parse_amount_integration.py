"""End-to-end: get_entries -> extract_tree_levels must assign the column total as a
node's amount, not an embedded per-unit price. Guards the wiring at the call site."""
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


def _find(root, needle):
    return next(n for n in PreOrderIter(root) if needle in (n.name or ""))


def test_parse_uses_column_total_not_embedded_per_unit():
    # Old code read the first '<num> บาท' = the embedded 6,500 per-unit price.
    page = make_page([
        ["(1.1) เตาอบไฟฟ้าเมล็ดโกโก้ จำนวน 22 เครื่องๆ ละ 6,500 บาท", "143,000", "บาท"],
    ])
    root = extract_tree_levels(get_entries(page.lines))
    node = _find(root, "เตาอบไฟฟ้าเมล็ดโกโก้")
    assert node.amount == 143000.0


def test_fiscal_year_amount_from_column_not_embedded():
    # A forward-commitment line ('ปี YYYY ตั้งงบประมาณ N บาท') keeps its total in the
    # same numeric column. If the text cell embeds another '<num> บาท', the commitment
    # amount must still be the column total, not the embedded figure.
    page = make_page([
        ["1) ค่าเช่าที่ราชพัสดุ 30,000 บาท", "30,000", "บาท"],
        ["ปี 2569 ตั้งงบประมาณ (อัตรา 20 บาท ต่อหน่วย)", "83,137,500", "บาท"],
    ])
    root = extract_tree_levels(get_entries(page.lines))
    node = _find(root, "ค่าเช่าที่ราชพัสดุ")
    assert len(node.fiscal_year_budget) == 1
    assert node.fiscal_year_budget[0].amount == 83137500.0
