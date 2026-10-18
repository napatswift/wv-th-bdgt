"""thaiorth names the character sequences that cannot occur in written Thai (WTT 2.0 / TIS 1566 classes)."""
import pytest

from thbud.textextract.thaiorth import violations


def rules(text: str) -> set[str]:
    return {rule for rule, _ in violations(text)}


@pytest.mark.parametrize('text', [
    'วิสัยทัศน์', 'พันธกิจ', 'ผลสัมฤทธิ์', 'สำนักงานปลัดกระทรวง', 'ต่ำกว่า', 'น้ำ', 'เป็น', 'ก็', 'พันธุ์',
    'กรมทรัพย์สินทางปัญญา', 'ฤดูกาล', 'งบประมาณรายจ่าย 1,234,500 บาท', 'ไม่น้อยกว่า', 'เครื่องคอมพิวเตอร์',
])
def test_written_thai_has_no_violations(text):
    assert rules(text) == set()


@pytest.mark.parametrize('text, rule', [
    ('สารบััญ', 'doubled_mark'),            # two mai han-akat
    ('สำนักข่่าวกรอง', 'doubled_mark'),
    ('เปรีียบเทียบ', 'doubled_mark'),
    ('ทัี', 'two_vowels'),
    ('กุิ', 'two_vowels'),
    ('ที่้', 'two_tones'),
    ('ว่ิ', 'tone_before_vowel'),           # Unicode puts the vowel before the tone
    ('หน์้า', 'mark_after_thanthakhat'),
    ('เป็่น', 'maitaikhu_combo'),
    ('่อน', 'orphan_mark'),                 # a mark with no consonant under it
    ('ทางน้ํา', 'uncomposed_am'),           # tone typed before the nikhahit of sara am
    ('ํับ', 'stray_nikhahit'),
    ('ต่ํา', 'uncomposed_am'),
    ('กิำ', 'am_after_vowel'),
    ('แม่เเจ่ม', 'leading_vowel_no_cons'),  # 'เเ' typed for แ
    ('เคลื่Lอน', 'latin_in_thai'),
    ('การท่อàĕðĎ่ûĀ', 'latin_in_thai'),
    ('ประจำ�ปี', 'replacement_char'),
    ('หนา', 'pua'),
    ('\x1fงบ', 'control_char'),
])
def test_impossible_sequences_are_named(text, rule):
    assert rule in rules(text)


def test_a_violation_reports_where_it_is():
    assert ('doubled_mark', 4) in list(violations('สารบััญ'))
