"""An off-budget ('เงินนอกงบประมาณ') line is never a budget item's own total.

Unit sheets print each line item with its on-budget total, optionally followed by
an indented 'เงินนอกงบประมาณ N บาท' row. An item funded only off-budget has no
on-budget total at all, so its off-budget row used to close it, and the off-budget
amount was counted as the item's budget (parent < sum of children).

Regression coverage for ส.ป.ก. 2570 (sheet 'ใหญ่' rows 13-17).
"""
from types import SimpleNamespace

from anytree import PreOrderIter

from thbud.textextract import LineText, PageText, WordText
from thbud.textextract.pdf_to_tree import get_entries, extract_tree_levels


def make_page(rows):
    """rows: list of (indent, [cells])."""
    lines = []
    for li, (indent, cells) in enumerate(rows):
        words = [WordText(x0=indent + ci, y0=li, x1=indent + ci + 1, y1=li, text=t)
                 for ci, t in enumerate(cells)]
        lines.append(LineText(words, page_index=0, line_index=li))
    page = PageText(lines, page_index=0, width=100, height=100, is_image=False,
                    document=SimpleNamespace(filepath="test.xlsx"))
    for ln in lines:
        ln.page = page
    return page


ROWS = [
    (0, ["1.1 ค่าตอบแทน ใช้สอยและวัสดุ", "1,800,000", "บาท"]),
    (3, ["(4) ค่าใช้จ่ายในการสัมมนาและฝึกอบรม", "1,500,000", "บาท"]),
    (4, ["เงินนอกงบประมาณ", "5,854,500", "บาท"]),
    (3, ["(5) ค่าตอบแทนคณะกรรมการตรวจการจ้างและควบคุมงานก่อสร้าง"]),
    (4, ["เงินนอกงบประมาณ", "109,400", "บาท"]),
    (3, ["(6) วัสดุเชื้อเพลิงและหล่อลื่น", "300,000", "บาท"]),
]


def test_offbudget_line_does_not_close_an_amountless_item():
    entries = get_entries(make_page(ROWS).lines)
    names = [str(e) for e in entries]
    assert not any("109,400" in n for n in names), names
    assert not any("ค่าตอบแทนคณะกรรมการ" in n for n in names), names
    # the following on-budget item is unaffected
    assert any(n.startswith("(6) วัสดุเชื้อเพลิง") for n in names), names


def test_parent_reconciles_without_offbudget_only_children():
    root = extract_tree_levels(get_entries(make_page(ROWS).lines))
    parent = next(n for n in PreOrderIter(root)
                  if n.name and n.name.startswith("1.1"))
    assert [c.amount for c in parent.children] == [1500000.0, 300000.0]
