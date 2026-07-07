"""Tests for column-aware amount extraction (get_amount_from_lines).

Each budget line in an xlsx row has the *total* in its own numeric column,
rendered as a standalone 'บาท' word after the number. Descriptive text (which may
embed a per-unit price like 'ๆ ละ 6,500 บาท') lives in a single earlier word.
get_amount_from_lines reads the column total, not the embedded figure.

Word sequences below mirror real rows seen in the 2567-2570 budget files.
"""
from thbud.textextract import LineText, WordText
from thbud.textextract.pdf_to_tree import get_amount_from_lines


def line(*texts):
    """Build a LineText from cell texts, left-to-right at increasing x."""
    words = [WordText(x0=i, y0=0, x1=i + 1, y1=0, text=t) for i, t in enumerate(texts)]
    return LineText(words, page_index=0, line_index=0)


def test_ignores_embedded_per_unit_price():
    # (1.1) เตาอบไฟฟ้า ... จำนวน 22 เครื่องๆ ละ 6,500 บาท | 143,000 | บาท
    lines = [line("(1.1) เตาอบไฟฟ้าเมล็ดโกโก้ จำนวน 22 เครื่องๆ ละ 6,500 บาท",
                  "143,000", "บาท")]
    assert get_amount_from_lines(lines) == 143000.0


def test_ignores_embedded_ceiling_without_million_word():
    # Source omitted 'ล้าน': '...) 150,000 บาท' embeds a guarantee ceiling; the
    # real budget is the column total.
    lines = [line("4) โครงการ SMEs ทวีค่า (...) 150,000 บาท", "1,730,357,900", "บาท")]
    assert get_amount_from_lines(lines) == 1730357900.0


def test_ignores_embedded_fare_amount():
    # เงินอุดหนุนชดเชยมาตรการนโยบายค่าโดยสาร 20 บาท ตลอดสายของรัฐบาล | 145,337,300 | บาท
    lines = [line("2) เงินอุดหนุนชดเชยมาตรการนโยบายค่าโดยสาร 20 บาท ตลอดสายของรัฐบาล",
                  "145,337,300", "บาท")]
    assert get_amount_from_lines(lines) == 145337300.0


def test_merged_siblings_returns_first_rows_own_total():
    # A trailing extra column ('1,842') stopped the row from closing, so a sibling
    # row got merged. The item's amount is its OWN first-row total, not the sibling's.
    lines = [
        line("1) ค่าใช้จ่ายบุคลากร", "10,560,300", "บาท", "1,842"),
        line("2) ค่าใช้จ่ายดำเนินงาน", "42,550,800", "บาท"),
    ]
    assert get_amount_from_lines(lines) == 10560300.0


def test_picks_number_immediately_before_baht_among_many_columns():
    # Multiple numeric columns (e.g. multi-year); the total is the one right before บาท.
    lines = [line("1) ค่าใช้จ่ายดำเนินงาน", "2,633,636,400", "1,360,137,600", "บาท")]
    assert get_amount_from_lines(lines) == 1360137600.0


def test_baht_marker_with_asterisk():
    # '*' marks ชดเชยงบประมาณที่พับไป; the total cell renders as 'บาท *'.
    lines = [line("(1) ค่าใช้จ่ายในการออกแบบ ...", "33,447,600", "บาท *")]
    assert get_amount_from_lines(lines) == 33447600.0


def test_wrapped_description_total_on_later_line():
    # Long description wraps across rows; only the closing row carries the total.
    lines = [
        line("(1) โครงการพัฒนาศูนย์ตรวจพิสูจน์พยานหลักฐานดิจิทัล (Digital Forensic Center)"),
        line("... 1 โครงการ", "12,195,000", "บาท"),
    ]
    assert get_amount_from_lines(lines) == 12195000.0


def test_plain_single_amount_unchanged():
    lines = [line("1. งบรายจ่ายอื่น", "3,469,200", "บาท")]
    assert get_amount_from_lines(lines) == 3469200.0


def test_no_amount_returns_zero():
    lines = [line("3.2.1 ค่าจ้างเหมาบริการ", "-", "บาท")]
    assert get_amount_from_lines(lines) == 0.0
