"""XLSXDocumentText: which worksheet cells become words.

Each worksheet row becomes one LineText whose words are its visible, non-empty
cells. Workbooks below reproduce real rows from the 2567-2570 budget files
(sheet, cell coordinates and values as in the source).
"""
import openpyxl

from thbud.textextract import XLSXDocumentText
from thbud.textextract.pdf_to_tree import get_amount_from_lines


def make_xlsx(tmp_path, rows, hidden_rows=()):
    """rows: {row_number: {column_letter: value}}; hidden_rows: rows to hide."""
    wb = openpyxl.Workbook()
    ws = wb.active
    for r, cells in rows.items():
        for col, value in cells.items():
            ws[f'{col}{r}'] = value
    for r in hidden_rows:
        ws.row_dimensions[r].hidden = True
    path = tmp_path / 'unit.xlsx'
    wb.save(path)
    return XLSXDocumentText(str(path))


def row(doc, r):
    return next(line for line in doc.get_lines_in_page() if line.line_index == r)


def texts(line):
    return [w.text for w in line.words]


def test_zero_total_beside_requested_column_is_the_amount(tmp_path):
    # อัยการ พื้นฐาน!69: requested D69=84,339,800, proposed (the total) E69=0.
    doc = make_xlsx(tmp_path, {69: {
        'A': '(1) ค่าก่อสร้างอาคารสำนักงานอัยการจังหวัดสมุทรสาคร',
        'D': 84339800, 'E': 0, 'F': 'บาท',
    }})
    assert get_amount_from_lines([row(doc, 69)]) == 0.0


def test_zero_total_does_not_fall_back_to_a_digit_in_the_description(tmp_path):
    # กรมชลประทาน 7.4.3ฟ!9: C9=0 D9='บาท'; the old reader dropped the 0 and the
    # string fallback read 'สัญญาที่ 2 บาท' as 2.
    doc = make_xlsx(tmp_path, {9: {
        'A': '(1) ระบบชลประทานฝั่งซ้าย สัญญาที่ 2', 'C': 0, 'D': 'บาท',
    }})
    assert get_amount_from_lines([row(doc, 9)]) == 0.0


def test_zero_outside_the_total_cell_is_not_a_word(tmp_path):
    # เทศบาลเมืองท่าช้าง Sheet1!50: requested D50=0, total E50=11,048,000. The
    # zero is not the total, so the row reads as before.
    doc = make_xlsx(tmp_path, {50: {
        'A': '1.2 เงินอุดหนุนเฉพาะกิจ', 'D': 0, 'E': 11048000, 'F': 'บาท',
    }})
    assert texts(row(doc, 50)) == ['1.2 เงินอุดหนุนเฉพาะกิจ', '11,048,000', 'บาท']
