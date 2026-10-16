"""'รายการบุคลากรภาครัฐ' opens a new unit's personnel block: a level-stack reset.

Ministry-overview (DO_) files put one unit per sheet, each starting with a
'รายการบุคลากรภาครัฐ' header row before its own '1. งบบุคลากร'. The header was
skipped as redundant, so the level stack carried over from the previous sheet and
the next unit's '1. งบบุคลากร' (a fresh '1.' list) nested under the previous unit's
last item. The header must reset the stack, without becoming a node itself.

Regression coverage for DO_13000 กระทรวงพาณิชย์ 2570 (sheets คต. -> คน.).
"""
from types import SimpleNamespace

from anytree import PreOrderIter

from thbud.textextract import LineText, PageText, WordText
from thbud.textextract.pdf_to_tree import get_entries, extract_tree_levels


def make_pages(sheets):
    """sheets: list of pages, each a list of (indent, [cells]); a cell is its text,
    or (column, text) to place it further right."""
    doc = SimpleNamespace(filepath="test.xlsx")
    all_lines = []
    for pi, rows in enumerate(sheets):
        lines = []
        for li, (indent, cells) in enumerate(rows, start=1):
            words = []
            for ci, cell in enumerate(cells):
                col, text = cell if isinstance(cell, tuple) else (ci, cell)
                words.append(WordText(x0=indent + col, y0=li, x1=indent + col + 1,
                                      y1=li, text=text))
            lines.append(LineText(words, page_index=pi, line_index=li))
        page = PageText(lines, page_index=pi, width=100, height=100,
                        is_image=False, document=doc)
        for ln in lines:
            ln.page = page
        all_lines += lines
    return all_lines


def unit_sheet(total, staff, ops, items, trailer=()):
    """One unit's sheet; `trailer` cells (e.g. a far-right level column) widen
    the sheet, which shifts the normalized x0 of every narrower sheet."""
    rows = [
        (0, ["รายการบุคลากรภาครัฐ", total, "บาท"]),
        (0, ["1. งบบุคลากร", staff, "บาท"]),
        (0, ["2. งบดำเนินงาน", ops, "บาท"]),
        (1, ["2.1 ค่าตอบแทน ใช้สอยและวัสดุ", ops, "บาท"]),
    ] + [(3, [name, amount, "บาท"]) for name, amount in items]
    return [(0, ["รายละเอียดงบประมาณจำแนกตามงบรายจ่าย"])] + [
        (indent, cells + list(trailer)) for indent, cells in rows]


SHEETS = [
    unit_sheet("300", "200", "100", [("(1) ค่าเช่าบ้าน", "60"),
                                     ("(2) เงินสมทบกองทุนประกันสังคม", "40")],
               trailer=[(9, "1")]),
    unit_sheet("50", "30", "20", [("(1) ค่าเช่าบ้าน", "20")]),
]


def test_personnel_header_is_not_a_node():
    root = extract_tree_levels(get_entries(make_pages(SHEETS)))
    assert not any(n.name and "รายการบุคลากรภาครัฐ" in n.name
                   for n in PreOrderIter(root))


def test_next_units_personnel_block_starts_at_the_top_level():
    root = extract_tree_levels(get_entries(make_pages(SHEETS)))
    tops = [n for n in root.children]
    assert [n.name.split()[0] for n in tops] == ["1.", "2.", "1.", "2."]
    for n in PreOrderIter(root):
        if n is not root and n.children:
            assert n.amount == sum(c.amount for c in n.children), n.name
