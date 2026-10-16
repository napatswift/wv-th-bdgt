"""An unbulleted 'รายการไม่ผูกพัน A บาท' row is a real child of its parent when the
listed items only itemise the 'รายการผูกพัน' part.

Sources split an item P into 'รายการไม่ผูกพัน A' + 'รายการผูกพัน B' (P = A + B),
then list under 'ประกอบด้วย' only the ผูกพัน items (they sum to B). Dropping the
ไม่ผูกพัน row left P short by exactly A. It is kept — levelled as a sibling of
the listed items — only when it exactly closes that gap; the ผูกพัน row (whose
amount the listed items already carry) stays dropped.

Regression coverage for the dropped-commitment-subtotal defect.
"""
from types import SimpleNamespace

from anytree import PreOrderIter

from thbud.textextract import LineText, PageText, WordText
from thbud.textextract.pdf_to_tree import get_entries, extract_tree_levels


def make_page(rows):
    """rows: list of (indent, [cells]); indent shifts every word's x0."""
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


def names(root):
    return [n.name for n in PreOrderIter(root) if n.name]


def test_uncommitted_row_closes_the_parent_gap_as_a_sibling_of_the_items():
    # สถาบันวิทยาลัยชุมชน shape (typo 'ผูกผัน'): the row is printed deeper than
    # the (1)/(2) items, yet it is their sibling — levelled by the next item, not x0.
    root = tree_of([
        (2, ["2.1 เงินอุดหนุนทั่วไป", "245,839,400", "บาท"]),
        (3, ["1) ค่าใช้จ่ายดำเนินงาน", "245,839,400", "บาท"]),
        (6, ["รายการไม่ผูกผัน", "230,368,400", "บาท"]),
        (6, ["รายการผูกพัน", "15,471,000", "บาท"]),
        (6, ["ประกอบด้วย"]),
        (5, ["(1) ค่าเช่ารถยนต์ 23 คัน", "6,831,000", "บาท"]),
        (5, ["(2) ค่าเช่าเครื่องคอมพิวเตอร์", "8,640,000", "บาท"]),
    ])
    parent = node(root, "ค่าใช้จ่ายดำเนินงาน")
    uncommitted = node(root, "รายการไม่ผูกผัน")
    assert uncommitted.parent is parent
    assert uncommitted.amount == 230_368_400
    assert node(root, "ค่าเช่ารถยนต์").parent is parent
    assert sum(c.amount for c in parent.children) == parent.amount
    assert not any(n.startswith("รายการผูกพัน") for n in names(root))


def test_two_column_stage_doc_reads_the_total_column():
    # สำนักงานเลขาธิการวุฒิสภา shape: request and total columns both printed;
    # the gap is closed by the total-column amount (507,789,000).
    root = tree_of([
        (3, ["1) ค่าใช้จ่ายดำเนินงาน", "814,231,000", "517,615,500", "บาท"]),
        (6, ["รายการไม่ผูกพัน", "804,404,500", "507,789,000", "บาท"]),
        (6, ["รายการผูกพัน", "9,826,500", "9,826,500", "บาท"]),
        (6, ["ประกอบด้วย"]),
        (6, ["(1) ค่าเช่ารถยนต์ตู้โดยสาร", "4,388,200", "4,388,200", "บาท"]),
        (8, ["ปี 2569 ตั้งงบประมาณ", "4,388,200", "บาท"]),
        (6, ["(2) ค่าเช่าเครื่องถ่ายเอกสาร", "5,438,300", "5,438,300", "บาท"]),
    ])
    parent = node(root, "ค่าใช้จ่ายดำเนินงาน")
    uncommitted = node(root, "รายการไม่ผูกพัน")
    assert uncommitted.parent is parent
    assert uncommitted.amount == 507_789_000
    assert sum(c.amount for c in parent.children) == parent.amount


def test_uncommitted_row_stays_dropped_when_it_does_not_close_the_gap():
    # สำนักงานศาลปกครอง 2570 shape: the listed items mix both groups — (2) is a
    # ไม่ผูกพัน item — so adding the ไม่ผูกพัน subtotal would double-count it.
    root = tree_of([
        (3, ["2) ค่าที่ดินและสิ่งก่อสร้าง", "529,057,800", "บาท"]),
        (6, ["รายการไม่ผูกพัน", "30,942,900", "บาท"]),
        (6, ["รายการผูกพัน", "498,114,900", "บาท"]),
        (6, ["ประกอบด้วย"]),
        (6, ["(1) ค่าก่อสร้างอาคารศาลปกครอง", "498,114,900", "บาท"]),
        (6, ["(2) ค่าปรับปรุงอาคารสำนักงาน", "14,115,200", "บาท"]),
    ])
    assert not any("ผูกพัน" in n for n in names(root))
    parent = node(root, "ค่าที่ดินและสิ่งก่อสร้าง")
    assert [c.name for c in parent.children] == [
        "(1) ค่าก่อสร้างอาคารศาลปกครอง 498,114,900 บาท",
        "(2) ค่าปรับปรุงอาคารสำนักงาน 14,115,200 บาท",
    ]
