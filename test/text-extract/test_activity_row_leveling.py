"""Unbulleted 'กิจกรรม…' (activity) rows printed at the same indent as numbered rows.

Highways house style (กรมทางหลวง / กรมทางหลวงชนบท, also their integrated-plan
pages) prints an activity row at the same cell indent as the dotted category rows
around it, with nothing else to say how it nests. Two orders occur:

  category-first  '2.1.1.1 ครุภัณฑ์…' then 'กิจกรรม…' (same x)  -> activity is a CHILD
  activity-first  'กิจกรรม…' then '1.1.1.1 …', '1.1.1.2 …' (same x) -> activity is the PARENT

The x0 leveler makes them siblings, so the enclosing parent double-counts. The
re-nesting is a proposal: the money invariant (parent = sum of children) vetoes
it whenever it would not reduce the reconciliation violations.
"""
from types import SimpleNamespace

from anytree import PreOrderIter

from thbud.textextract import LineText, PageText, WordText
from thbud.textextract.pdf_to_tree import get_entries, extract_tree_levels


def make_page(rows):
    """rows: list of (indent, [cells]); equal indent -> equal x0."""
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


def nodes(root, text):
    return [n for n in PreOrderIter(root) if n.name and text in n.name]


def test_category_first_activity_nests_under_its_category():
    # กรมทางหลวง 2569 'AO_ผล3' r38-r93: each 2.1.1.N category is followed by a
    # กิจกรรม row at the same indent carrying the same amount; the (N) items sit
    # one indent deeper. The activity belongs under the category, and the next
    # category is again a sibling of the first.
    root = tree_of([
        (0, ["2.1.1 ค่าครุภัณฑ์", "125,059,000", "บาท"]),
        (1, ["2.1.1.1 ครุภัณฑ์ยานพาหนะและขนส่ง", "124,709,000", "บาท"]),
        (1, ["กิจกรรมอำนวยการและสนับสนุนการอำนวยความปลอดภัยตำรวจทางหลวง", "124,709,000", "บาท"]),
        (2, ["(1) รถวิทยุตรวจการณ์", "100,000,000", "บาท"]),
        (2, ["(2) รถบรรทุก", "24,709,000", "บาท"]),
        (1, ["2.1.1.2 ครุภัณฑ์ไฟฟ้าและวิทยุ", "350,000", "บาท"]),
        (1, ["กิจกรรมป้องกันและอำนวยความปลอดภัย", "350,000", "บาท"]),
        (2, ["(1) เครื่องรับส่งวิทยุ", "350,000", "บาท"]),
    ])
    k = node(root, "2.1.1 ค่าครุภัณฑ์")
    c1 = node(root, "ครุภัณฑ์ยานพาหนะและขนส่ง")
    c2 = node(root, "ครุภัณฑ์ไฟฟ้าและวิทยุ")
    a1 = node(root, "กิจกรรมอำนวยการ")
    a2 = node(root, "กิจกรรมป้องกัน")
    assert a1.parent is c1 and a2.parent is c2
    assert c1.parent is k and c2.parent is k
    assert node(root, "รถวิทยุตรวจการณ์").parent is a1
    assert node(root, "รถบรรทุก").parent is a1
    assert node(root, "เครื่องรับส่งวิทยุ").parent is a2


def test_consecutive_activities_under_one_category_are_siblings():
    # กรมทางหลวง 2569 'AO_พัฒนา' r30-r414: one category, several กิจกรรม rows at
    # its indent (each with its own deeper items) that together make up its
    # amount; the next category closes them and is a sibling of the first.
    root = tree_of([
        (0, ["1.1.2 ค่าที่ดินและสิ่งก่อสร้าง", "160", "บาท"]),
        (1, ["1.1.2.1 ค่าก่อสร้างทางและสะพาน", "100", "บาท"]),
        (1, ["กิจกรรมก่อสร้างเพิ่มประสิทธิภาพทางหลวง", "70", "บาท"]),
        (2, ["(1) ทางหลวงหมายเลข 1", "70", "บาท"]),
        (1, ["กิจกรรมก่อสร้างเพิ่มไหล่ทาง", "30", "บาท"]),
        (2, ["(1) ทางหลวงหมายเลข 2", "30", "บาท"]),
        (1, ["1.1.2.2 ค่าสำรวจออกแบบ", "60", "บาท"]),
        (1, ["กิจกรรมพัฒนาทางหลวง", "60", "บาท"]),
    ])
    c1 = node(root, "ค่าก่อสร้างทางและสะพาน")
    assert node(root, "กิจกรรมก่อสร้างเพิ่มประสิทธิภาพทางหลวง").parent is c1
    assert node(root, "กิจกรรมก่อสร้างเพิ่มไหล่ทาง").parent is c1
    c2 = node(root, "ค่าสำรวจออกแบบ")
    assert c2.parent is node(root, "1.1.2 ค่าที่ดินและสิ่งก่อสร้าง")
    assert node(root, "กิจกรรมพัฒนาทางหลวง").parent is c2


def test_activity_first_activity_is_parent_of_following_categories():
    # กรมทางหลวง 2569 'AO_พัฒนา' r5-r29: the กิจกรรม row comes first, at the indent
    # of the 1.1.1.N categories that follow; its amount is their sum. The activity
    # is their parent, even though the numbering anchors 1.1.1.1 under 1.1.1.
    root = tree_of([
        (0, ["1.1 ค่าครุภัณฑ์ ที่ดินและสิ่งก่อสร้าง", "198", "บาท"]),
        (1, ["1.1.1 ค่าครุภัณฑ์", "98", "บาท"]),
        (2, ["กิจกรรมพัฒนาทางหลวง", "98", "บาท"]),
        (2, ["1.1.1.1 ครุภัณฑ์ก่อสร้าง", "35", "บาท"]),
        (3, ["(1) รถบดล้อเหล็ก", "35", "บาท"]),
        (2, ["1.1.1.2 ครุภัณฑ์สำรวจ", "13", "บาท"]),
        (2, ["1.1.1.3 ครุภัณฑ์วิทยาศาสตร์", "50", "บาท"]),
        (1, ["1.1.2 ค่าที่ดินและสิ่งก่อสร้าง", "100", "บาท"]),
        (2, ["1.1.2.1 ค่าก่อสร้างทางและสะพาน", "100", "บาท"]),
    ])
    act = node(root, "กิจกรรมพัฒนาทางหลวง")
    assert act.parent is node(root, "1.1.1 ค่าครุภัณฑ์")
    for name in ("ครุภัณฑ์ก่อสร้าง", "ครุภัณฑ์สำรวจ", "ครุภัณฑ์วิทยาศาสตร์"):
        assert node(root, name).parent is act
    assert node(root, "1.1.2 ค่าที่ดินและสิ่งก่อสร้าง").parent is node(root, "1.1 ค่าครุภัณฑ์")


def test_activity_between_budget_group_and_its_first_category():
    # กรมทางหลวงชนบท 2567 'เล่มฟ้า_โครง' r3-r5: '1. งบดำเนินงาน' -> กิจกรรม -> '1.1'
    # with the activity and 1.1 at the same indent. The numbering alone would
    # re-anchor 1.1 under '1.' and pop the activity; the sums say the activity is
    # the parent of 1.1 and 1.2.
    root = tree_of([
        (0, ["1. งบดำเนินงาน", "30", "บาท"]),
        (1, ["กิจกรรมอำนวยการและสนับสนุนการพัฒนาทางหลวงชนบท", "30", "บาท"]),
        (1, ["1.1 ค่าตอบแทน ใช้สอยและวัสดุ", "17", "บาท"]),
        (3, ["(1) ค่าเช่าบ้าน", "17", "บาท"]),
        (1, ["1.2 ค่าสาธารณูปโภค", "13", "บาท"]),
        (0, ["2. งบลงทุน", "5", "บาท"]),
        (1, ["2.1 ค่าครุภัณฑ์ ที่ดินและสิ่งก่อสร้าง", "5", "บาท"]),
    ])
    act = node(root, "กิจกรรมอำนวยการ")
    assert act.parent is node(root, "1. งบดำเนินงาน")
    assert node(root, "1.1 ค่าตอบแทน").parent is act
    assert node(root, "1.2 ค่าสาธารณูปโภค").parent is act
    assert node(root, "2. งบลงทุน").parent is node(root, "1. งบดำเนินงาน").parent


def test_activity_same_indent_as_group_nests_and_keeps_deeper_categories():
    # กรมทางหลวงชนบท 2567 'เล่มฟ้า_ยุทธ' r29-r33 / r3-r5: the กิจกรรม row sits at the
    # indent of the dotted row ABOVE it (2.1.1), and the 2.1.1.N categories are one
    # indent deeper. The activity nests under 2.1.1 and keeps the categories.
    root = tree_of([
        (0, ["2.1 ค่าครุภัณฑ์ ที่ดินและสิ่งก่อสร้าง", "400", "บาท"]),
        (1, ["2.1.1 ค่าครุภัณฑ์", "300", "บาท"]),
        (1, ["กิจกรรมบำรุงรักษาทางหลวงชนบท", "300", "บาท"]),
        (2, ["2.1.1.1 ครุภัณฑ์ยานพาหนะและขนส่ง", "120", "บาท"]),
        (2, ["2.1.1.2 ครุภัณฑ์ก่อสร้าง", "180", "บาท"]),
        (1, ["2.1.2 ค่าที่ดินและสิ่งก่อสร้าง", "100", "บาท"]),
    ])
    act = node(root, "กิจกรรมบำรุงรักษาทางหลวงชนบท")
    assert act.parent is node(root, "2.1.1 ค่าครุภัณฑ์")
    assert node(root, "ครุภัณฑ์ยานพาหนะและขนส่ง").parent is act
    assert node(root, "2.1.1.2 ครุภัณฑ์ก่อสร้าง").parent is act
    assert node(root, "2.1.2 ค่าที่ดิน").parent is node(root, "2.1 ค่าครุภัณฑ์")


def test_sums_veto_activity_renesting_that_does_not_reconcile():
    # Same shape as category-first, but here the กิจกรรม row is a genuine sibling:
    # 2.1.1 = 60 (category) + 40 (activity). Nesting the activity under 2.1.1.1
    # would break both parents, so the money invariant keeps the x0 tree.
    root = tree_of([
        (0, ["2.1.1 ค่าครุภัณฑ์", "100", "บาท"]),
        (1, ["2.1.1.1 ครุภัณฑ์ยานพาหนะและขนส่ง", "60", "บาท"]),
        (2, ["(1) รถบรรทุก", "60", "บาท"]),
        (1, ["กิจกรรมพิเศษ", "40", "บาท"]),
        (2, ["(1) รถตรวจการณ์", "40", "บาท"]),
    ])
    k = node(root, "2.1.1 ค่าครุภัณฑ์")
    assert node(root, "กิจกรรมพิเศษ").parent is k
    assert node(root, "ครุภัณฑ์ยานพาหนะและขนส่ง").parent is k


def test_activity_printed_at_item_indent_rejoins_its_sibling_activities():
    # กรมทางหลวง 2570 'บำรุง' r10-r154: A11/A121 sit at the category's indent (3),
    # but A142/A153 are printed at the (N)-item indent (4), inside A121's items.
    # A กิจกรรม never nests inside another กิจกรรม: they are all children of
    # 1.1.2.1 (2,503 + 574 + 202 + 27,494 = 30,774 in the source, scaled here).
    root = tree_of([
        (0, ["1.1.2 ค่าที่ดินและสิ่งก่อสร้าง", "100", "บาท"]),
        (1, ["1.1.2.1 ค่าบำรุงรักษาทางและสะพาน", "100", "บาท"]),
        (1, ["กิจกรรมบูรณะโครงข่ายทางหลวง", "25", "บาท"]),
        (2, ["(1) งานบูรณะทางหลวง", "25", "บาท"]),
        (1, ["กิจกรรมบำรุงรักษาสะพาน", "5", "บาท"]),
        (2, ["(1) งานบำรุงรักษาสะพาน", "5", "บาท"]),
        (2, ["กิจกรรมแก้ปัญหาการระบายน้ำ", "2", "บาท"]),
        (2, ["(1) งานแก้ปัญหาการระบายน้ำ", "2", "บาท"]),
        (2, ["กิจกรรมบำรุงรักษาทางหลวง", "68", "บาท"]),
        (2, ["(1) งานบำรุงปกติ", "68", "บาท"]),
    ])
    cat = node(root, "1.1.2.1 ค่าบำรุงรักษา")
    for name in ("กิจกรรมบูรณะ", "กิจกรรมบำรุงรักษาสะพาน",
                 "กิจกรรมแก้ปัญหา", "กิจกรรมบำรุงรักษาทางหลวง"):
        assert node(root, name).parent is cat
    assert node(root, "งานแก้ปัญหาการระบายน้ำ").parent is node(root, "กิจกรรมแก้ปัญหา")
    assert node(root, "งานบำรุงปกติ").parent is node(root, "กิจกรรมบำรุงรักษาทางหลวง")


def test_activity_at_parenthesized_category_indent_nests_under_it():
    # กรมทางหลวง 2569 'AO_บำรุง' r1557-r1565: under '1) ค่าที่ดิน/สิ่งก่อสร้าง' the
    # first กิจกรรม is one indent deeper, the second is printed at the 1) indent;
    # both are its children (88,450,000 + 92,357,400 = 180,807,400).
    root = tree_of([
        (0, ["2. งบรายจ่ายอื่น", "180", "บาท"]),
        (2, ["1) ค่าที่ดิน/สิ่งก่อสร้าง", "180", "บาท"]),
        (3, ["กิจกรรมบำรุงรักษาทางหลวง", "88", "บาท"]),
        (4, ["(1) โครงการค่าสำรวจ", "88", "บาท"]),
        (2, ["กิจกรรมการควบคุมน้ำหนักยานพาหนะบนทางหลวง", "92", "บาท"]),
        (4, ["(1) ค่าที่ดินและสิ่งก่อสร้าง", "92", "บาท"]),
    ])
    k = node(root, "1) ค่าที่ดิน")
    assert node(root, "กิจกรรมบำรุงรักษาทางหลวง").parent is k
    assert node(root, "กิจกรรมการควบคุมน้ำหนัก").parent is k

