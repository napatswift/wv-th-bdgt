"""Project headers are recognised however the owner prefixes them.

Integrated-plan (BO) files, and some unit files, open each project with an
unbulleted row whose cell stacks owner and project on separate in-cell lines
('กระทรวง…⏎กรม…⏎โครงการX'), or print a bare 'โครงการX' with no space after
'โครงการ'. Only 'โครงการ : X' was recognised, so these rows were skipped and their
'1. งบ…' subtrees attached to the previous project. A project header that carries
no total of its own must still become a PROJECT node (amount unknown, None) when
the next bulleted row starts, instead of being merged into that row.
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


def test_owner_prefixed_multiline_cell_is_a_project_header():
    # 04_บูรณาการเตรียมความพร้อมเพื่อรองรับสังคมสูงวัย 2569, 'เป้าหมายที่ 1' r9-r16
    root = tree_of([
        (0, ["สำนักงานคณะกรรมการสุขภาพแห่งชาติ\nโครงการสานพลังขับเคลื่อนนโยบาย",
             "5,408,700", "บาท"]),
        (0, ["1. งบเงินอุดหนุน", "5,408,700", "บาท"]),
        (1, ["1.1 เงินอุดหนุนทั่วไป", "5,408,700", "บาท"]),
        (0, ["กระทรวงการพัฒนาสังคมและความมั่นคงของมนุษย์\nกรมกิจการผู้สูงอายุ\n"
             "โครงการเตรียมความพร้อมเพื่อรองรับสังคมสูงวัย", "2,047,600", "บาท"]),
        (0, ["1. งบดำเนินงาน", "2,047,600", "บาท"]),
        (1, ["1.1 ค่าตอบแทน ใช้สอยและวัสดุ", "2,047,600", "บาท"]),
    ])
    first = node(root, "สำนักงานคณะกรรมการสุขภาพแห่งชาติ")
    second = node(root, "กรมกิจการผู้สูงอายุ")
    assert first.budget_type.name == second.budget_type.name == "PROJECT"
    assert [c.amount for c in first.children] == [5408700.0]
    assert [c.amount for c in second.children] == [2047600.0]


def test_bare_project_name_without_space_is_a_project_header():
    # B05 integration 2570, 'เป้า 5' r91: 'โครงการระบบติดตาม…' (no ' : ')
    root = tree_of([
        (0, ["โครงการ : โครงการเฝ้าระวังคุณภาพน้ำบาดาล", "300", "บาท"]),
        (0, ["1. งบรายจ่ายอื่น", "300", "บาท"]),
        (0, ["โครงการระบบติดตามระดับน้ำบาดาล", "100", "บาท"]),
        (0, ["1. งบรายจ่ายอื่น", "100", "บาท"]),
    ])
    header = node(root, "โครงการระบบติดตาม")
    assert header.budget_type.name == "PROJECT"
    assert [c.amount for c in node(root, "โครงการเฝ้าระวัง").children] == [300.0]
    assert [c.amount for c in header.children] == [100.0]


def test_project_header_without_total_closes_at_next_bullet():
    # B08 2569, 'เล่มฟ้า' r266-r269: owner/project rows carry no total; the
    # '1. งบรายจ่ายอื่น' row must not be merged into the project header
    root = tree_of([
        (0, ["กระทรวงแรงงาน\nโครงการยกระดับผลิตภาพและพัฒนากำลังคน"]),
        (0, ["กรมพัฒนาฝีมือแรงงาน"]),
        (0, ["โครงการ : โครงการยกระดับผลิตภาพและพัฒนากำลังคน"]),
        (0, ["1. งบรายจ่ายอื่น", "144,910,000", "บาท"]),
        (2, ["1) ค่าใช้จ่ายในการพัฒนาสมรรถนะบุคลากร", "144,910,000", "บาท"]),
    ])
    project = node(root, "กระทรวงแรงงาน")
    assert project.budget_type.name == "PROJECT"
    assert project.amount is None
    assert "งบรายจ่ายอื่น" not in project.name
    assert [c.amount for c in project.children] == [144910000.0]


def test_bulleted_row_mentioning_a_project_stays_an_item():
    root = tree_of([
        (0, ["1. งบรายจ่ายอื่น", "100", "บาท"]),
        (2, ["1) ค่าใช้จ่าย\nโครงการพัฒนาบุคลากร", "100", "บาท"]),
    ])
    assert node(root, "โครงการพัฒนาบุคลากร").budget_type.name == "BUDGET_DETAIL"
