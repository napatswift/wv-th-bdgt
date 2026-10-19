"""PDF rows are positioned words, not spreadsheet cells, so some XLSX row rules
misread them:

* a wrapped name that ends in a number ('…ภาค 1', '…ชั้น 8', 'ทางหลวงหมายเลข
  304') is not an item whose 'บาท' cell is missing: the number is glued to the
  text, not set apart in the amount column;
* a line led by a plain integer while an item is open ('1 อาคาร 4,922,100 บาท',
  '2 เครื่อง') is the item's quantity line, not a new item.

Regression coverage for FY2570 enacted-budget PDFs (สำนักงานทรัพยากรน้ำแห่งชาติ,
vol. 1, p. 298: 'ค่าก่อสร้างอาคารที่ทำการ … ภาค 1' booked at 1 baht).
"""
from types import SimpleNamespace

from thbud.textextract import LineText, PageText, WordText
from thbud.textextract.pdf_to_tree import get_entries, extract_tree_levels, _entry_amount


def make_pdf_page(rows):
    """rows: lists of (text, x0, x1) words, x in page fractions as the PDF reader gives."""
    lines = []
    for li, words in enumerate(rows):
        y = 0.1 + li * 0.02
        lines.append(LineText([WordText(x0, y, x1, y + 0.015, t) for t, x0, x1 in words],
                              page_index=0, line_index=li))
    page = PageText(lines, page_index=0, width=595, height=842, is_image=False,
                    document=SimpleNamespace(filepath="vol.pdf", is_pdf=True))
    for ln in lines:
        ln.page = page
    return page


WRAPPED_WITH_NUMBER = [
    [("2.1.1.1", 0.16, 0.20), ("ค่าก่อสร้างอาคารที่ทำการ", 0.20, 0.47),
     ("30,655,400", 0.82, 0.89), ("บาท", 0.89, 0.91)],
    [("(1)", 0.17, 0.19), ("ค่าก่อสร้างอาคารที่ทำการ", 0.19, 0.33),
     ("สำนักงานทรัพยากรน้ำแห่งชาติภาค", 0.33, 0.52), ("1", 0.525, 0.53)],
    [("และงานประกอบ", 0.19, 0.27), ("ตำบลกล้วยแพะ", 0.27, 0.35)],
    [("1", 0.17, 0.18), ("อาคาร", 0.19, 0.22), ("4,922,100", 0.83, 0.89), ("บาท", 0.89, 0.91)],
]


def test_wrapped_name_ending_in_a_number_takes_its_total_from_the_quantity_line():
    entries = get_entries(make_pdf_page(WRAPPED_WITH_NUMBER).lines)
    assert [e.itemtype for e in entries] == ["item", "item"]
    item = entries[1]
    assert item.has_total
    assert "และงานประกอบ" in str(item) and "อาคาร" in str(item)


def test_the_wrapped_item_carries_the_quantity_line_amount():
    root = extract_tree_levels(get_entries(make_pdf_page(WRAPPED_WITH_NUMBER).lines))
    parent = root.children[0]
    assert [c.amount for c in parent.children] == [4922100.0]


def _w(text, x0=0.16):
    """A text-column row: words laid out left to right from x0."""
    words, x = [], x0
    for t in text.split():
        words.append((t, x, x + 0.01 * len(t)))
        x += 0.01 * len(t) + 0.005
    return words


def _amount_row(text, amount, x0=0.16):
    return _w(text, x0) + [(amount, 0.82, 0.89), ("บาท", 0.89, 0.91)]


def test_activity_summary_table_on_a_text_page_is_not_budget_lines():
    page = make_pdf_page([
        _amount_row("1) ค่าครุภัณฑ์", "5,400,000"),
        _w("7.4.1.5 งบประมาณรายจ่าย จำแนกตามกิจกรรม - งบรายจ่าย"),
        _w("หน่วย : ล้านบาท", 0.8),
        _w("กิจกรรม งบรายจ่าย", 0.26),
        _w("รวมทั้งสิ้น - - 1.5000 - 1.5000", 0.25),
        _w("1. โครงการการจัดทำบรรทัดฐานคำวินิจฉัยศาลรัฐธรรมนูญ", 0.1)
        + [("-", 0.6, 0.61), ("-", 0.67, 0.68), ("1.5000", 0.74, 0.79), ("-", 0.82, 0.83), ("1.5000", 0.86, 0.91)],
        _amount_row("ผลผลิต : การคุ้มครองสิทธิและเสรีภาพของประชาชน", "1,500,000", 0.1),
    ])
    entries = get_entries(page.lines)
    assert [e.itemtype for e in entries] == ["item", "OUTPUT"]


def test_plan_heading_on_a_text_page_starts_a_plan():
    page = make_pdf_page([
        _amount_row("1) ค่าครุภัณฑ์", "5,400,000"),
        _amount_row("7.5 แผนงานยุทธศาสตร์พัฒนากฎหมายและกระบวนการยุติธรรม", "1,500,000", 0.1),
    ])
    assert [(e.itemtype, _entry_amount(e)) for e in get_entries(page.lines)][-1] == ("budget_plan", 1500000.0)


def test_wrapped_plan_heading_takes_its_amount_from_the_next_line():
    page = make_pdf_page([
        _w("7.3 แผนงานยุทธศาสตร์ส่งเสริม พัฒนาอุตสาหกรรมและบริการแห่งอนาคต และอุตสาหกรรม", 0.1),
        _amount_row("และบริการอื่น", "29,264,100", 0.1),
        _amount_row("7.3.1 โครงการที่ 1 : โครงการพัฒนาศักยภาพอุตสาหกรรมชีวภาพ", "9,992,800"),
    ])
    page.contains_table = True
    entries = get_entries(page.lines)
    assert (entries[0].itemtype, _entry_amount(entries[0])) == ("budget_plan", 29264100.0)
    assert "และบริการอื่น" in str(entries[0])


def test_prose_with_the_word_plan_on_a_table_page_is_not_a_plan():
    page = make_pdf_page([
        _w("- บริหารจัดการพื้นที่คุ้มครองให้เป็นไปตามอนุสัญญา แผนงาน และพันธกรณี", 0.22),
        _w("รวมทั้งแผน แผนงาน/งาน/โครงการ ที่มีการบูรณาการ (10)", 0.1),
    ])
    page.contains_table = True
    assert get_entries(page.lines) == []


def test_section_seven_subheadings_on_a_text_page_are_not_budget_lines():
    page = make_pdf_page([
        _amount_row("7.1 แผนงานยุทธศาสตร์พัฒนาด้านคมนาคมและระบบโลจิสติกส์", "2,355,032,800", 0.1),
        _amount_row("7.1.1 โครงการที่ 1 : โครงการรถไฟฟ้าสายสีม่วง", "2,355,032,800"),
        _w("7.1.1.1 วัตถุประสงค์"),
        _w("7.1.1.3 ระยะเวลาดำเนินการ 40 ปี (ปี 2548 ถึง ปี 2587)"),
        _amount_row("7.1.1.4 วงเงินทั้งสิ้นของโครงการ", "118,253,740,000"),
        _amount_row("โครงการ : โครงการรถไฟฟ้าสายสีม่วง", "2,355,032,800", 0.1),
        _amount_row("1. งบลงทุน", "2,355,032,800", 0.12),
    ])
    assert [e.itemtype for e in get_entries(page.lines)] == ["budget_plan", "PROJECT", "item"]


def test_numbered_lists_in_a_section_seven_description_are_not_budget_lines():
    page = make_pdf_page([
        _amount_row("7.5 แผนงานบูรณาการต่อต้านการทุจริตและประพฤติมิชอบ", "1,928,200", 0.1),
        _w("7.5.1.2 สถานที่ดำเนินการ"),
        _w("1. ภาคกลาง จำนวน 3 จังหวัด จังหวัดลพบุรี", 0.22),
        _w("2. ภาคเหนือ จำนวน 3 จังหวัด จังหวัดลำปาง", 0.22),
        _amount_row("โครงการ : โครงการ อปท. GO Clean", "1,928,200", 0.1),
        _amount_row("1. งบเงินอุดหนุน", "1,928,200", 0.12),
    ])
    assert [e.itemtype for e in get_entries(page.lines)] == ["budget_plan", "PROJECT", "item"]


def test_spending_lines_end_a_section_seven_description():
    page = make_pdf_page([
        _w("7.1.1.1 วัตถุประสงค์"),
        _w("- เพื่อเสริมสร้างความรู้", 0.22),
        _amount_row("1. งบเงินอุดหนุน", "343,386,000", 0.12),
    ])
    assert [e.itemtype for e in get_entries(page.lines)] == ["item"]


def test_activity_rows_at_a_category_indent_nest_in_pdf_coordinates():
    # Highways style: 'กิจกรรม…' printed at the indent of the '1.1.1.N' row above
    # it; its '(1)' items sit one indent step (~0.013 of the page) deeper.
    page = make_pdf_page([
        _amount_row("1.1.1 ค่าครุภัณฑ์", "1,685,500", 0.148),
        _amount_row("1.1.1.1 ครุภัณฑ์สำรวจ", "1,600,000", 0.1605),
        _amount_row("กิจกรรมยกระดับมาตรฐานทาง", "1,600,000", 0.1605),
        _amount_row("(1) ครุภัณฑ์สำรวจที่มีราคาต่อหน่วยต่ำกว่า 1 ล้านบาท", "1,600,000", 0.1732),
        _amount_row("1.1.1.2 ครุภัณฑ์ก่อสร้าง", "85,500", 0.1605),
        _amount_row("กิจกรรมยกระดับมาตรฐานทาง", "85,500", 0.1605),
        _amount_row("(1) ครุภัณฑ์ก่อสร้างที่มีราคาต่อหน่วยต่ำกว่า 1 ล้านบาท", "85,500", 0.1732),
    ])
    root = extract_tree_levels(get_entries(page.lines))
    top = root.children[0]
    assert [c.amount for c in top.children] == [1600000.0, 85500.0]
    for category in top.children:
        (activity,) = category.children
        assert activity.name.startswith("กิจกรรม")
        assert [c.amount for c in activity.children] == [category.amount]


def test_successive_activity_rows_under_one_category_stay_siblings_in_pdf_coordinates():
    page = make_pdf_page([
        _amount_row("1.1.2 ค่าที่ดินและสิ่งก่อสร้าง", "160,000,000", 0.148),
        _amount_row("1.1.2.2 ค่าก่อสร้างทางและสะพาน", "160,000,000", 0.1605),
        _amount_row("กิจกรรมยกระดับมาตรฐานทาง", "100,000,000", 0.1605),
        _amount_row("(1) ถนนสาย ชม.1", "60,000,000", 0.1732),
        _amount_row("(2) ถนนสาย ชม.2", "40,000,000", 0.1732),
        _amount_row("กิจกรรมพัฒนาสะพานขนาดกลาง", "60,000,000", 0.1605),
        _amount_row("(1) สะพาน ลป.1", "60,000,000", 0.1732),
    ])
    root = extract_tree_levels(get_entries(page.lines))
    (category,) = root.children[0].children
    assert [(c.name.split()[0], c.amount) for c in category.children] == [
        ("กิจกรรมยกระดับมาตรฐานทาง", 100000000.0), ("กิจกรรมพัฒนาสะพานขนาดกลาง", 60000000.0)]
    assert [len(c.children) for c in category.children] == [2, 1]


def test_word_spilled_ahead_of_a_bullet_does_not_hide_the_row():
    # กรมการแพทย์แผนไทยฯ 2562 p.327: the previous item's '1 คัน' wraps its unit
    # word onto the next row, printed left of that row's bullet.
    rows = [
        _amount_row("2.1.1.1 ครุภัณฑ์ยานพาหนะและขนส่ง", "1,288,000", x0=0.177),
        _amount_row("(1) รถโดยสาร ขนาด 12 ที่นั่ง 1", "1,288,000", x0=0.165),
        [("คัน", 0.154, 0.172)] + _amount_row("2.1.1.2 ครุภัณฑ์คอมพิวเตอร์", "2,194,000",
                                             x0=0.177),
        _amount_row("(1) ครุภัณฑ์คอมพิวเตอร์ที่มีราคาต่อหน่วยต่ำกว่า 1 ล้านบาท", "2,194,000",
                    x0=0.165),
    ]
    root = extract_tree_levels(get_entries(make_pdf_page(rows).lines))
    assert [c.name.split()[:2] for c in root.children] == [
        ["2.1.1.1", "ครุภัณฑ์ยานพาหนะและขนส่ง"], ["2.1.1.2", "ครุภัณฑ์คอมพิวเตอร์"]]
    assert [c.amount for c in root.children[1].children] == [2194000.0]
    # the spilled word ends the closed item's own quantity ('1 คัน')
    assert root.children[0].children[0].label.endswith("ที่นั่ง 1 คัน")


# FY2550-2551 volumes: '6.1 แผนงบประมาณ : …' plans and '6.1.1 ผลผลิตที่ 1 : …'
# outputs, printed on a page that also holds the indicator table (so it reads
# as a table page); the expense-category detail follows on a text page
OLD_LAYOUT_HEADINGS = [
    _w("6. แผนงบประมาณ จำแนก ตามผลผลิต/โครงการ", 0.146),
    _amount_row("6.1 แผนงบประมาณ : สร้างสังคมแห่งการเรียนรู้ตลอดชีวิต", "75,710,600", 0.146),
    _w("จริยธรรม", 0.17),
    _amount_row("6.1.1 ผลผลิตที่ 1 : ผู้สำเร็จการศึกษาด้านวิทยาศาสตร์", "75,710,600", 0.205),
    _amount_row("กิจกรรม", "75,710,600", 0.228),
    _amount_row("1) จัดการศึกษาด้านวิทยาศาสตร์", "75,710,600", 0.224),
    _w("6.1.1.1 เป้าหมายผลผลิต", 0.205),
    _w("ตัวชี้วัด หน่วยนับ ปี 2549 ปี 2550", 0.273),
]
OLD_LAYOUT_DETAIL = [
    _w("6.1.1.3 รายละเอียดงบประมาณจำแนกตามงบรายจ่าย", 0.146),
    _amount_row("1. งบบุคลากร", "75,710,600", 0.146),
    _amount_row("1.1 เงินเดือนและค่าจ้างประจำ", "75,710,600", 0.155),
]


def test_old_layout_plan_and_output_headings_open_their_blocks():
    headings = make_pdf_page(OLD_LAYOUT_HEADINGS)
    headings.contains_table = True
    detail = make_pdf_page(OLD_LAYOUT_DETAIL)
    root = extract_tree_levels(get_entries(headings.lines + detail.lines))
    plan, = root.children
    assert plan.budget_type.name == "BUDGET_PLAN"
    assert plan.name.split()[:3] == ["6.1", "แผนงบประมาณ", ":"]
    assert plan.name.split()[-3:] == ["จริยธรรม", "75,710,600", "บาท"]
    output, = plan.children
    assert output.budget_type.name == "OUTPUT"
    assert output.amount == 75710600
    assert [c.name.split()[1] for c in output.children] == ["งบบุคลากร"]


def test_output_sub_heading_is_no_header_outside_the_old_layout():
    # '7.1.1 ผลผลิตที่ 1 : …' in later volumes describes an output in §7; the
    # node is its detail block's 'ผลผลิต : …' header
    page = make_pdf_page([_amount_row("7.1.1 ผลผลิตที่ 1 : ผู้สำเร็จการศึกษา", "75,710,600", 0.205)])
    page.contains_table = True
    assert get_entries(page.lines) == []


def test_header_name_wrapped_below_its_amount_row_joins_the_header():
    # สถาบันรับรองคุณภาพสถานพยาบาล 2562: the amount sits on the first row, the
    # name runs on below it
    rows = [
        _amount_row("ผลผลิต : สถานพยาบาลได้รับการประเมินและรับรองตามมาตรฐาน", "96,200,000", 0.16),
        _w("คุณภาพสถานพยาบาล", 0.22),
        _amount_row("1. งบเงินอุดหนุน", "96,200,000", 0.17),
    ]
    root = extract_tree_levels(get_entries(make_pdf_page(rows).lines))
    output, = root.children
    assert output.budget_type.name == "OUTPUT"
    assert output.label.endswith("ตามมาตรฐาน คุณภาพสถานพยาบาล")
    assert [c.label for c in output.children] == ["งบเงินอุดหนุน"]


def test_wrapped_output_header_is_not_joined_to_its_plan():
    rows = [
        _amount_row("7.2 แผนงานพื้นฐานด้านการพัฒนา", "5,000,000", 0.12),
        _w("ผลผลิต : การพัฒนาองค์กรเพื่อให้งาน", 0.16),
        _amount_row("ด้านนิติบัญญัติ", "5,000,000", 0.2),
        _amount_row("1. งบเงินอุดหนุน", "5,000,000", 0.17),
    ]
    root = extract_tree_levels(get_entries(make_pdf_page(rows).lines))
    plan, = root.children
    assert plan.label == "แผนงานพื้นฐานด้านการพัฒนา"
    assert [c.budget_type.name for c in plan.children] == ["OUTPUT"]


def test_bracketed_decimal_of_a_target_table_is_no_spilled_word():
    # มหาวิทยาลัยเทคโนโลยีราชมงคลกรุงเทพ 2561: the indicator table's '( 78.6212 )'
    rows = [
        _amount_row("1) ค่าใช้จ่ายพัฒนาคุณภาพการจัดการศึกษา", "10,000,000", 0.183),
        [("(", 0.509, 0.516), ("78.6212", 0.517, 0.55), (")", 0.559, 0.565)],
    ]
    root = extract_tree_levels(get_entries(make_pdf_page(rows).lines))
    assert [c.label for c in root.children] == ["ค่าใช้จ่ายพัฒนาคุณภาพการจัดการศึกษา"]


def test_word_ahead_of_a_decimal_on_a_table_page_is_no_spilled_word():
    # จังหวัดเพชรบุรี 2570: the target table's 'ร้อยละ 6.8 ต่อปี' follows an item
    item = make_pdf_page([_amount_row("(2) วัสดุสำนักงาน", "15,200", 0.161)])
    table = make_pdf_page([_w("ร้อยละ 6.8 ต่อปี (-)", 0.099)])
    table.contains_table = True
    root = extract_tree_levels(get_entries(item.lines + table.lines))
    assert [c.label for c in root.children] == ["วัสดุสำนักงาน"]
