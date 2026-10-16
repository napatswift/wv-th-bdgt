from thbud.textextract.pdf_to_tree import is_redundant_line


def test_section7_title_is_not_a_budget_line():
    # อปท / AO first detail page heading; it titles §7, it is not an item
    assert is_redundant_line(['1.', 'รายละเอียดงบประมาณจำแนกตามแผนงาน', 'และ', 'ผลผลิต/โครงการ'])
    assert is_redundant_line(['7.', 'รายละเอียดงบประมาณจำแนกตามแผนงาน', 'และ', 'ผลผลิต/โครงการ'])
    assert is_redundant_line(['1.', 'รายละเอียดงบประมาณจําแนกตามแผนงาน', 'และ', 'ผลผลิต/โครงการ'])


def test_items_naming_budget_details_stay():
    assert not is_redundant_line(['1.1', 'แผนงานยุทธศาสตร์ส่งเสริมการกระจายอำนาจ', '839,827,200', 'บาท'])
    assert not is_redundant_line(['(1)', 'ค่าจ้างจัดทำรายละเอียดงบประมาณ', '50,000', 'บาท'])
