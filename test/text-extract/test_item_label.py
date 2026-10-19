"""A node's label is its description read from the words themselves: the bullet
word and the amount column(s) with their 'บาท' markers are dropped wherever they
sit in the entry, every other word of every line is kept in reading order. The
raw `name` (every word joined) stays as is, for audit.

The amount column is found by position, not by "is this token a number": in a PDF
it is set well apart from the text, in an XLSX it is its own cell. So a name that
ends in its own number ('…ตามมาตรา 40', '…ภาคที่ 5') keeps it, and a quantity line
printed after the amount row ('รวม 1 รายการ (รวม 2 หน่วย)') stays in the label.

Regression coverage for the PDF line-item tree ground truths (FY2550-2570).
"""
from test_get_entries_split import make_page
from test_pdf_line_rules import make_pdf_page, _w

from thbud.textextract.pdf_to_tree import get_entries, extract_tree_levels


def _nodes(page):
    root = extract_tree_levels(get_entries(page.lines))
    return list(root.descendants)


def test_quantity_line_after_the_amount_row_stays_in_the_label():
    page = make_pdf_page([
        [("(1)", 0.163, 0.178), ("ครุภัณฑ์คอมพิวเตอร์ที่มีราคาต่อหน่วยต่ำกว่า", 0.183, 0.426),
         ("1", 0.431, 0.438), ("ล้านบาท", 0.443, 0.489),
         ("62,000", 0.830, 0.868), ("บาท", 0.877, 0.900)],
        [("รวม", 0.174, 0.196), ("1", 0.201, 0.208), ("รายการ", 0.213, 0.254),
         ("(รวม", 0.259, 0.286), ("2", 0.291, 0.297), ("หน่วย)", 0.302, 0.339)],
    ])
    (node,) = _nodes(page)
    assert node.label == ("ครุภัณฑ์คอมพิวเตอร์ที่มีราคาต่อหน่วยต่ำกว่า 1 ล้านบาท"
                          " รวม 1 รายการ (รวม 2 หน่วย)")
    assert node.bullet == "(1)"
    assert node.amount == 62000.0
    assert node.name == ("(1) ครุภัณฑ์คอมพิวเตอร์ที่มีราคาต่อหน่วยต่ำกว่า 1 ล้านบาท 62,000 บาท"
                         " รวม 1 รายการ (รวม 2 หน่วย)")


def test_a_name_keeps_its_own_trailing_number():
    page = make_pdf_page([
        [("1)", 0.144, 0.155), ("เงินสมทบกองทุนประกันสังคมผู้ประกันตนตามมาตรา", 0.160, 0.451),
         ("40", 0.456, 0.471), ("723,479,200", 0.819, 0.890), ("บาท", 0.899, 0.922)],
        [("(3)", 0.174, 0.188), ("อาคารชุดพักอาศัยสำนักงานสรรพสามิตภาคที่", 0.193, 0.523),
         ("5", 0.528, 0.534), ("7,000,000", 0.787, 0.838), ("บาท", 0.846, 0.867)],
    ])
    assert [n.label for n in _nodes(page)] == [
        "เงินสมทบกองทุนประกันสังคมผู้ประกันตนตามมาตรา 40",
        "อาคารชุดพักอาศัยสำนักงานสรรพสามิตภาคที่ 5"]


def test_dash_and_second_amount_columns_are_dropped():
    page = make_pdf_page([
        [("2)", 0.144, 0.155), ("ค่าครุภัณฑ์", 0.160, 0.22),
         ("4,300,000", 0.70, 0.76), ("-", 0.85, 0.855), ("บาท", 0.89, 0.91)],
        [("3)", 0.144, 0.155), ("ค่าที่ดินและสิ่งก่อสร้าง", 0.160, 0.30),
         ("1,200,000", 0.70, 0.76), ("1,100,000", 0.80, 0.86), ("บาท", 0.89, 0.91)],
        [("4)", 0.144, 0.155), ("ก่อสร้างหอประชุม", 0.160, 0.30), ("1", 0.305, 0.31),
         ("หลัง", 0.315, 0.34), ("-", 0.843, 0.847), ("บาท", 0.855, 0.876)],
    ])
    assert [n.label for n in _nodes(page)] == [
        "ค่าครุภัณฑ์", "ค่าที่ดินและสิ่งก่อสร้าง", "ก่อสร้างหอประชุม 1 หลัง"]


def test_glued_bullet_is_split_off_and_wrapped_lines_are_kept():
    page = make_pdf_page([
        [("1)ค่าก่อสร้างอาคาร", 0.144, 0.30), ("แขวงลาดยาว", 0.305, 0.36)],
        _w("กรุงเทพมหานคร 1 รายการ", 0.16) + [("54,207,500", 0.815, 0.879), ("บาท", 0.884, 0.907)],
    ])
    (node,) = _nodes(page)
    assert node.bullet == "1)"
    assert node.label == "ค่าก่อสร้างอาคาร แขวงลาดยาว กรุงเทพมหานคร 1 รายการ"


def test_header_without_a_bullet_keeps_its_keyword():
    page = make_pdf_page([
        _w("ผลผลิต : การคุ้มครองสิทธิ", 0.1) + [("1,500,000", 0.82, 0.89), ("บาท", 0.89, 0.91)],
    ])
    (node,) = _nodes(page)
    assert node.bullet is None
    assert node.label == "ผลผลิต : การคุ้มครองสิทธิ"


def test_xlsx_amount_cells_are_dropped_and_text_cells_kept_whole():
    page = make_page([
        # an embedded per-unit price lives inside the text cell: it is text
        ["(1.1) เตาอบไฟฟ้า จำนวน 22 เครื่องๆ ละ 6,500 บาท", "143,000", "บาท"],
        # a trailing extra column after the 'บาท' cell is not text either
        ["(1.2)", "ค่าใช้จ่ายบุคลากร", "10,560,300", "บาท", "1,842"],
    ])
    assert [(n.bullet, n.label) for n in _nodes(page)] == [
        ("(1.1)", "เตาอบไฟฟ้า จำนวน 22 เครื่องๆ ละ 6,500 บาท"),
        ("(1.2)", "ค่าใช้จ่ายบุคลากร")]


def test_xlsx_total_flattened_into_the_text_cell_is_dropped():
    # no separate amount cell: the row's total is the text cell's own 'N บาท' tail
    page = make_page([["1) ค่าตอบแทน 143,000 บาท"]])
    (node,) = _nodes(page)
    assert node.label == "ค่าตอบแทน"
