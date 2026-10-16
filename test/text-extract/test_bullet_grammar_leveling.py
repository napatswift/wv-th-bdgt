"""Leveling must respect the bullet grammar, not only x0 indentation.

The x0-based leveler collapses rows of different bullet styles printed at (near-)equal
indentation into siblings; the bullet numbering says they are parent/child. The grammar
proposes a re-leveling per header segment and the money invariant (parent = sum of
children) vetoes proposals that break reconciliation.

Regression coverage for the mixed-bullet-family sibling defect.
"""
from types import SimpleNamespace

from anytree import PreOrderIter

from thbud.textextract import LineText, PageText, WordText
from thbud.textextract.pdf_to_tree import get_entries, extract_tree_levels


def make_page(rows):
    """rows: list of (indent, [cells]). indent shifts every word's x0, so rows with
    equal indent have equal x0 regardless of their bullet."""
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


def test_dotted_child_nests_under_numbered_parent_despite_equal_x0():
    # '1.1' is grammatically a child of '1.' even when the sheet prints both at the
    # same indentation (the dominant prod failure: they came out as siblings).
    root = tree_of([
        (0, ["1. งบเงินอุดหนุน", "105,734,900", "บาท"]),
        (0, ["1.1 เงินอุดหนุนทั่วไป", "105,734,900", "บาท"]),
    ])
    parent = node(root, "งบเงินอุดหนุน")
    child = node(root, "เงินอุดหนุนทั่วไป")
    assert child.parent is parent


def test_four_bullet_families_at_equal_x0_form_a_chain():
    # The canonical collapse: 1. / 1.1 / 1) / (1) all printed at the same x0 must
    # come out as a 4-deep chain, not 4 siblings.
    root = tree_of([
        (0, ["1. งบเงินอุดหนุน", "100", "บาท"]),
        (0, ["1.1 เงินอุดหนุนทั่วไป", "100", "บาท"]),
        (0, ["1) ค่าใช้จ่ายดำเนินงาน", "100", "บาท"]),
        (0, ["(1) ค่าตอบแทนกรรมการ", "100", "บาท"]),
    ])
    a = node(root, "งบเงินอุดหนุน")
    b = node(root, "เงินอุดหนุนทั่วไป")
    c = node(root, "ค่าใช้จ่ายดำเนินงาน")
    d = node(root, "ค่าตอบแทนกรรมการ")
    assert b.parent is a and c.parent is b and d.parent is c


def test_parenthesized_list_nests_inside_parenthesized_item():
    # (N) legitimately contains (N): a repeated (1) cannot be a sibling — it starts
    # a nested list under the current item; (2)/(3) continue it (กองทัพบก pattern).
    root = tree_of([
        (0, ["1.1 ค่าตอบแทน ใช้สอยและวัสดุ", "60", "บาท"]),
        (2, ["(1) รายการไม่ผูกพัน", "60", "บาท"]),
        (3, ["(1) ค่าเบี้ยเลี้ยงทหาร", "40", "บาท"]),
        (3, ["(2) ค่าซ่อมแซมอาคาร", "20", "บาท"]),
    ])
    outer = node(root, "รายการไม่ผูกพัน")
    assert node(root, "ค่าเบี้ยเลี้ยงทหาร").parent is outer
    assert node(root, "ค่าซ่อมแซมอาคาร").parent is outer
    assert outer.parent is node(root, "ค่าตอบแทน ใช้สอยและวัสดุ")


def test_sibling_continuation_survives_noisy_x0():
    # สงขลา pattern: '(1)' printed at a SHALLOWER x than its true parent '1)', and
    # '2)' printed deeper than where its list started. Numbering continuation must
    # bring 2) back as the sibling of 1), with each (1) nested under its 'ค่า' item.
    root = tree_of([
        (1, ["1.2 เงินอุดหนุนเฉพาะกิจ", "100", "บาท"]),
        (2, ["1) ค่าครุภัณฑ์", "60", "บาท"]),
        (0, ["(1) ครุภัณฑ์อื่นที่มีราคาต่อหน่วยต่ำกว่า 1 ล้านบาท", "60", "บาท"]),
        (2, ["2) ค่าที่ดินและสิ่งก่อสร้าง", "40", "บาท"]),
        (0, ["(1) ค่าปรับปรุงทางและสะพาน", "40", "บาท"]),
    ])
    k1 = node(root, "ค่าครุภัณฑ์")
    k2 = node(root, "ค่าที่ดินและสิ่งก่อสร้าง")
    assert k1.parent is node(root, "เงินอุดหนุนเฉพาะกิจ")
    assert k2.parent is k1.parent
    assert node(root, "ครุภัณฑ์อื่นที่มีราคาต่อหน่วยต่ำกว่า").parent is k1
    assert node(root, "ค่าปรับปรุงทางและสะพาน").parent is k2


def test_sums_veto_a_wrong_grammar_proposal():
    # '(3)' continues the (1),(2) numbering, so the grammar wants it as their
    # sibling — but the indentation nests it under (2), and only that nesting
    # reconciles the amounts (1) = 60+30 = 90 and (2) = 30. The money invariant
    # must veto the grammar and keep the x0 levels.
    root = tree_of([
        (0, ["1) รายการหลัก", "90", "บาท"]),
        (2, ["(1) รายการย่อยหนึ่ง", "60", "บาท"]),
        (2, ["(2) รายการย่อยสอง", "30", "บาท"]),
        (4, ["(3) รายการย่อยของสอง", "30", "บาท"]),
    ])
    assert node(root, "รายการย่อยของสอง").parent is node(root, "รายการย่อยสอง")


def test_numbering_gap_still_continues_the_sibling_run():
    # A skipped row (parse loss) leaves a numbering gap: (4) after (2) must still
    # rejoin the run as a sibling, not nest under (2) by its deeper x0.
    root = tree_of([
        (0, ["1) รายการหลัก", "90", "บาท"]),
        (2, ["(1) รายการย่อยหนึ่ง", "60", "บาท"]),
        (2, ["(2) รายการย่อยสอง", "10", "บาท"]),
        (3, ["(4) รายการย่อยสี่", "20", "บาท"]),
    ])
    assert (node(root, "รายการย่อยสี่").parent
            is node(root, "รายการย่อยหนึ่ง").parent)


def test_unbulleted_activity_rows_keep_indentation_scoping():
    # กิจกรรม rows carry no bullet: they must keep the x0 behavior — the second
    # กิจกรรม pops back to the first's level, and each 1. list nests under its own
    # กิจกรรม (the numbering restart must not anchor across the กิจกรรม boundary).
    root = tree_of([
        (0, ["กิจกรรมหลักที่หนึ่ง", "100", "บาท"]),
        (1, ["1. งบดำเนินงาน", "100", "บาท"]),
        (0, ["กิจกรรมหลักที่สอง", "50", "บาท"]),
        (1, ["1. งบลงทุน", "50", "บาท"]),
    ])
    a1 = node(root, "กิจกรรมหลักที่หนึ่ง")
    a2 = node(root, "กิจกรรมหลักที่สอง")
    assert a1.parent is a2.parent
    assert node(root, "งบดำเนินงาน").parent is a1
    assert node(root, "งบลงทุน").parent is a2


def test_continuation_beats_a_deeper_components_parent():
    # อย. pattern: '1.2' must continue the 1.1 run, not nest under the deeper '(1)'
    # just because (1,) == (1, 2)[:-1]. The noisy x0 of '(2)' under 2.1 gives the
    # grammar a reconciliation win elsewhere in the segment, so the money veto
    # cannot be relied on to block the misnesting.
    root = tree_of([
        (4, ["1. งบบุคลากร", "100", "บาท"]),
        (5, ["1.1 เงินเดือนและค่าจ้างประจำ", "60", "บาท"]),
        (7, ["(1) อัตราเดิม", "60", "บาท"]),
        (5, ["1.2 ค่าตอบแทนพนักงานราชการ", "40", "บาท"]),
        (7, ["(1) ค่าตอบแทนพนักงานราชการ", "40", "บาท"]),
        (4, ["2. งบดำเนินงาน", "30", "บาท"]),
        (5, ["2.1 ค่าตอบแทน ใช้สอยและวัสดุ", "30", "บาท"]),
        (7, ["(1) ค่าเช่าบ้าน", "10", "บาท"]),
        (4, ["(2) เงินเพิ่มพิเศษ", "15", "บาท"]),
        (7, ["(3) เงินสมทบกองทุน", "5", "บาท"]),
    ])
    k12 = node(root, "1.2 ค่าตอบแทนพนักงานราชการ")
    assert k12.parent is node(root, "งบบุคลากร")
    k21 = node(root, "ค่าตอบแทน ใช้สอยและวัสดุ")
    assert node(root, "เงินเพิ่มพิเศษ").parent is k21
    assert node(root, "เงินสมทบกองทุน").parent is k21


def test_continuation_beats_a_restarted_list_nested_in_the_sibling():
    # ตราด pattern: under '(1.1)' the projects restart at '(1)'; that '(1)' has
    # comps (1,) == (1, 2)[:-1], but it sits INSIDE the '(1.1)' run, so '(1.2)'
    # continues the run as its sibling rather than nesting under the project.
    root = tree_of([
        (0, ["2) ค่าที่ดิน/สิ่งก่อสร้าง", "100", "บาท"]),
        (2, ["(1) ค่าก่อสร้างอื่นๆ", "100", "บาท"]),
        (4, ["(1.1) เงินอุดหนุนด้านการศึกษา", "60", "บาท"]),
        (2, ["(1) พัฒนาโรงเรียน", "60", "บาท"]),
        (4, ["(1.2) เงินอุดหนุนด้านโครงสร้างพื้นฐาน", "40", "บาท"]),
        (2, ["(1) ปรับปรุงระบบไฟฟ้า", "40", "บาท"]),
    ])
    k11 = node(root, "เงินอุดหนุนด้านการศึกษา")
    k12 = node(root, "เงินอุดหนุนด้านโครงสร้างพื้นฐาน")
    assert k12.parent is k11.parent is node(root, "ค่าก่อสร้างอื่นๆ")
    assert node(root, "พัฒนาโรงเรียน").parent is k11
    assert node(root, "ปรับปรุงระบบไฟฟ้า").parent is k12


def test_mis_bulleted_child_still_anchors_on_a_cross_family_parent():
    # ศูนย์คุณธรรม pattern: the sheet writes '1.1' where '1.1)' is meant, under
    # '1) ค่าใช้จ่ายลงทุน'. With no '1.1' run to continue (the earlier '1.1' has the
    # same number), the nearest components-parent '1)' is the right anchor even
    # though it is another bullet family.
    root = tree_of([
        (0, ["1. งบเงินอุดหนุน", "100", "บาท"]),
        (1, ["1.1 เงินอุดหนุนทั่วไป", "100", "บาท"]),
        (2, ["1) ค่าใช้จ่ายลงทุน", "100", "บาท"]),
        (2, ["1.1 ค่าครุภัณฑ์", "100", "บาท"]),
        (4, ["(1) การพัฒนาระบบศูนย์กลางข้อมูล", "100", "บาท"]),
    ])
    assert node(root, "ค่าครุภัณฑ์").parent is node(root, "ค่าใช้จ่ายลงทุน")
