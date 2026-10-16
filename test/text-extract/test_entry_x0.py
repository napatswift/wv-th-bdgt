"""An entry is indented where its first row is, not where a continuation row is.

Continuation rows are sometimes typed into column A with leading spaces instead
of an indent ('               รวม 1 รายการ' at indent 0). Taking the entry's x0 as the
minimum over all its rows put the whole item at column A, so it out-dented past
its parent and the following siblings re-nested under the wrong node.

Regression coverage for สถาบันระหว่างประเทศเพื่อการค้าและการพัฒนา 2567
('DT 7.2' rows 12-17).
"""
from types import SimpleNamespace

from anytree import PreOrderIter

from thbud.textextract import LineText, PageText, WordText
from thbud.textextract.pdf_to_tree import LineItem, get_entries, extract_tree_levels


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
    (0, ["1. งบดำเนินงาน", "7,398,400", "บาท"]),
    (2, ["(2) ค่าครุภัณฑ์", "2,757,700", "บาท"]),
    (4, ["(1) ครุภัณฑ์คอมพิวเตอร์ที่มีราคาต่อหน่วยต่ำกว่า 1 ล้านบาท"]),
    (0, ["               รวม 1 รายการ (รวม 1 หน่วย)", "811,700", "บาท"]),
    (4, ["(2) จัดทำต้นแบบแพลตฟอร์มออนไลน์สินค้า BCG", "1,946,000", "บาท"]),
    (2, ["(3) ค่าใช้จ่ายด้านสื่อสารองค์กร", "2,640,700", "บาท"]),
    (2, ["(4) ค่าใช้จ่ายด้านยุทธศาสตร์", "2,000,000", "บาท"]),
]


def test_entry_x0_is_its_first_rows_x0():
    page = make_page(ROWS[2:4])
    item = LineItem('item', page.lines)
    assert item.x0 == page.lines[0].x0


def test_continuation_row_in_column_a_does_not_outdent_the_item():
    root = extract_tree_levels(get_entries(make_page(ROWS).lines))
    equipment = next(n for n in PreOrderIter(root)
                     if n.name and n.name.startswith("(2) ค่าครุภัณฑ์"))
    assert [c.amount for c in equipment.children] == [811700.0, 1946000.0]
    top = next(n for n in PreOrderIter(root)
               if n.name and n.name.startswith("1. งบดำเนินงาน"))
    assert [c.name.split()[0] for c in top.children] == ["(2)", "(3)", "(4)"]
