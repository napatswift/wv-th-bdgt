"""normalize_thai puts typed Thai into the one order written Thai and Unicode use, so equal words compare equal."""
import pytest

from thbud.textextract.thaifont import normalize_thai


@pytest.mark.parametrize('typed, written', [
    ('แม่เเจ่ม', 'แม่แจ่ม'),                  # two sara e typed for sara ae
    ('ต้นเเบบเเละ', 'ต้นแบบและ'),
    ('เคร่ือง', 'เครื่อง'),                   # tone typed before the vowel above
    ('ท่ี', 'ที่'),
    ('รวมท้ังส้ิน', 'รวมทั้งสิ้น'),
    ('ต่ํา', 'ต่ำ'),                          # sara am typed as nikhahit + sara aa, tone either side
    ('ทางน้ํา', 'ทางน้ำ'),
    ('ดําเนิน', 'ดำเนิน'),
    ('พันธ์ุพืช', 'พันธุ์พืช'),               # thanthakhat typed before the vowel below
])
def test_typed_order_becomes_written_order(typed, written):
    assert normalize_thai(typed) == written


@pytest.mark.parametrize('text', ['เครื่องคอมพิวเตอร์', 'ที่', 'แผนงาน', 'ต่ำกว่า', 'Thai 2570', 'เเ'])
def test_written_thai_is_left_alone(text):
    # a lone 'เเ' (no consonant after it) is not a word, so it is left as it is
    assert normalize_thai(text) == text
