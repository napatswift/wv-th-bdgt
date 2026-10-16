"""A bulleted row that starts while an item is still open begins a new item.

A header row printed without a total ('2.1 ค่าครุภัณฑ์' with an empty amount cell)
never closes, so get_entries kept appending rows to it and the next bullet's
total closed the merged entry: the header vanished into its first child, and the
child's siblings nested under the merged node. The open entry must be flushed
first, as its own node with an unknown (None) amount.

Regression coverage for ศูนย์คุณธรรม 2569 ('7.2.1 สนับสนุน' rows 14-19) and
สถาบันวัคซีนแห่งชาติ 2570 ('bพฐ' rows 16-20).
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
    (2, ["2) ค่าใช้จ่ายลงทุน", "928,600", "บาท"]),
    (2, ["  2.1 ค่าครุภัณฑ์"]),
    (4, ["(1) ครุภัณฑ์สำนักงานที่มีราคาต่อหน่วยต่ำกว่า 1 ล้านบาท", "851,000", "บาท"]),
    (5, ["รวม 8 รายการ (รวม 193 หน่วย)"]),
    (4, ["(2) ครุภัณฑ์งานบ้านงานครัวที่มีราคาต่อหน่วยต่ำกว่า 1 ล้านบาท", "77,600", "บาท"]),
    (5, ["รวม 3 รายการ (รวม 4 หน่วย)"]),
]


def node(root, text):
    return next(n for n in PreOrderIter(root) if n.name and text in n.name)


def test_amountless_header_is_not_merged_into_its_first_child():
    entries = get_entries(make_page(ROWS).lines)
    names = [str(e).strip() for e in entries]
    assert names[1] == "2.1 ค่าครุภัณฑ์", names
    assert names[2].startswith("(1) ครุภัณฑ์สำนักงาน"), names


def test_amountless_header_parents_the_items_below_it():
    root = extract_tree_levels(get_entries(make_page(ROWS).lines))
    header = node(root, "2.1 ค่าครุภัณฑ์")
    assert header.amount is None
    assert header.parent is node(root, "2) ค่าใช้จ่ายลงทุน")
    assert [c.amount for c in header.children] == [851000.0, 77600.0]


def test_wrapped_description_without_a_bullet_still_merges():
    page = make_page([
        (2, ["1) เงินเดือนและค่าจ้างประจำของข้าราชการ"]),
        (2, ["และลูกจ้างประจำในสังกัด", "10,560,300", "บาท"]),
        (2, ["2) ค่าตอบแทนพนักงานราชการ", "100", "บาท"]),
    ])
    names = [str(e) for e in get_entries(page.lines)]
    assert len(names) == 2, names
    assert "ลูกจ้างประจำในสังกัด" in names[0]


def test_amountless_header_is_vetoed_like_its_filled_amount():
    # อปท 2570 files repeat the plan heading on a duplicate sheet: a fresh
    # '1. รายละเอียด…' list with no total of its own. The bullet grammar would
    # nest it under the last '(1)' leaf; the money veto must weigh the header
    # at the sum of its children (as autofix will fill it), not ignore it.
    root = extract_tree_levels(get_entries(make_page([
        (0, ["ผลผลิต : ผลผลิตการจัดบริการสาธารณะ", "100", "บาท"]),
        (0, ["1. งบเงินอุดหนุน", "100", "บาท"]),
        (1, ["1.1 เงินอุดหนุนเฉพาะกิจ", "100", "บาท"]),
        (2, ["1) ค่าที่ดิน/สิ่งก่อสร้าง", "100", "บาท"]),
        (4, ["(1) ค่าปรับปรุงทางและสะพาน", "100", "บาท"]),
        (0, ["1. รายละเอียดงบประมาณจำแนกตามแผนงาน และ ผลผลิต/โครงการ"]),
        (1, ["1.1 แผนงานยุทธศาสตร์ส่งเสริมการกระจายอำนาจ", "250", "บาท"]),
    ]).lines))
    assert node(root, "(1) ค่าปรับปรุงทางและสะพาน").children == ()
