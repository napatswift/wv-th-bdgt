"""Slightly malformed bullets are still bullets.

A bullet glued to its label ('3.งบเงินอุดหนุน') or missing its closing
parenthesis ('(2 ปรับปรุง…') failed the bullet patterns, so the row was skipped
as unrecognised text and its amount disappeared from the tree.

Regression coverage for มรภ.กาญจนบุรี 2567 ('บุค' row 14) and
กรมทางหลวงชนบท 2569 ('เล่มฟ้า_ ยุทธปลอดภัย' row 178).
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


def tree_of(rows):
    return extract_tree_levels(get_entries(make_page(rows).lines))


def node(root, text):
    return next(n for n in PreOrderIter(root) if n.name and text in n.name)


def test_bullet_glued_to_its_label_is_a_bullet():
    root = tree_of([
        (0, ["2. งบดำเนินงาน", "9,237,800", "บาท"]),
        (1, ["2.1 ค่าตอบแทน ใช้สอยและวัสดุ", "9,237,800", "บาท"]),
        (0, ["3.งบเงินอุดหนุน", "145,002,000", "บาท"]),
        (1, ["3.1 เงินอุดหนุนทั่วไป", "145,002,000", "บาท"]),
    ])
    top = node(root, "งบเงินอุดหนุน")
    assert top.amount == 145002000.0
    assert top.parent is root
    assert node(root, "3.1 เงินอุดหนุนทั่วไป").parent is top


def test_parenthesised_bullet_missing_its_close_paren_is_a_bullet():
    root = tree_of([
        (3, ["กิจกรรมปรับปรุงจุดเสี่ยงจุดอันตราย", "314,561,000", "บาท"]),
        (4, ["(1) ค่าปรับปรุงทางและสะพานที่มีราคาต่อหน่วยต่ำกว่า 10 ล้านบาท"]),
        (5, ["รวม 34 รายการ (รวม 41 หน่วย)", "199,561,000", "บาท"]),
        (4, ["(2 ปรับปรุงจุดเสี่ยงจุดอันตราย ถนนสาย กบ.1002", "20,000,000", "บาท"]),
        (4, ["(3) ปรับปรุงจุดเสี่ยงจุดอันตราย ถนนสาย นบ.3021", "95,000,000", "บาท"]),
    ])
    parent = node(root, "กิจกรรมปรับปรุงจุดเสี่ยง")
    assert [c.amount for c in parent.children] == [
        199561000.0, 20000000.0, 95000000.0]


def test_number_glued_to_text_is_not_a_bullet():
    # a description continuation starting with a bare number is not a bullet
    page = make_page([
        (2, ["1) ค่าจ้างเหมาบริการ"]),
        (2, ["12เดือน", "120,000", "บาท"]),
    ])
    assert len(get_entries(page.lines)) == 1
