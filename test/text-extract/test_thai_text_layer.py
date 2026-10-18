"""DocumentText reads Thai correctly from budget PDFs whose text layer maps glyphs to the wrong characters.

Each fixture is one page cut from a bb.go.th budget document (เอกสารงบประมาณ ฉบับที่ ๓). Every one is set in
DilleniaUPC, whose glyph ids mean the same glyph in every year, while the PDF producers label some of those glyphs
with the wrong Unicode: Microsoft Thai PUA tone marks (FY2550-2552), no label at all (FY2554), and the nikhahit of
sara am labelled as a space (FY2570)."""
from thbud.textextract import DocumentText

DATA = 'test/text-extract/data/thai-layer/'


def page_text(name: str) -> str:
    page = DocumentText(DATA + name).get_page(0)
    return '\n'.join(str(line) for line in page.lines)


def test_pua_tone_marks_read_as_thai():
    text = page_text('fy2552-pua.pdf')
    assert 'หน่วยงาน' in text
    assert 'งบประมาณรายจ่าย' in text
    assert not any(0xF700 <= ord(c) <= 0xF8FF for c in text)


def test_unlabelled_tone_marks_read_as_thai():
    text = page_text('fy2554-missing-tounicode.pdf')
    assert 'งบรายจ่ายอื่น' in text
    assert 'รวมทั้งสิ้น' in text
    assert not any(c in text for c in 'ÉÊËÌÍ�')


def test_sara_am_reads_whole_when_its_nikhahit_is_labelled_a_space():
    text = page_text('fy2570-nikhahit-space.pdf')
    assert 'ต่ำกว่า' in text
    assert 'ครุภัณฑ์สำนักงาน' in text
    assert 'ต ่า' not in text and 'ต่า ' not in text


def test_a_correctly_labelled_page_keeps_every_word_where_pymupdf_puts_it():
    import fitz
    path = DATA + 'fy2558-clean.pdf'
    expected = [w[:4] for w in fitz.open(path)[0].get_text_words()]
    document = DocumentText(path)
    read = [w[:4] for w in document.words_loader(document.doc[0])]
    assert read == expected
    assert 'เงินเดือนและค่าจ้างประจำ' in page_text('fy2558-clean.pdf')


def test_dillenia_embedded_without_its_name_is_still_read_as_thai():
    # FY2570 pages 585-621 embed DilleniaUPC as 'CIDFont+F1'/'CIDFont+F2': same outlines at the same glyph ids,
    # its upper tone marks unlabelled.
    text = page_text('fy2570-cidfont.pdf')
    assert 'ที่นำมาสมทบ' in text
    assert 'ผลสัมฤทธิ์' in text
    assert not any(c in text for c in 'ÉÊËÌÍ�')


def test_a_compacted_dillenia_subset_is_read_by_its_glyphs_not_its_codes():
    # FY2570 เล่มที่ ๑๓(๑) pages 533-549: DilleniaUPC subsets renumbered to 73-85 glyphs, so a code there is not
    # DilleniaUPC's glyph id. Its tone marks still read as Thai, and its other glyphs are left alone.
    text = page_text('fy2570-compacted-subset.pdf')
    assert 'งบประมาณรายจ่าย' in text
    assert 'ผลสัมฤทธิ์หรือประโยชน์ที่คาดว่าจะได้รับ' in text
    assert not any(0xF700 <= ord(c) <= 0xF8FF for c in text)


def test_a_glyph_whose_actualtext_is_the_replacement_character_adds_no_text():
    # FY2570 front matter (THSarabunPSK) draws sara am as a glyph labelled ำ plus a sara aa wrapped in
    # /ActualText (U+FFFD), meant to hide it; read as is, 'ประจำปี' becomes 'ประจำ�ปี'.
    text = page_text('fy2570-actualtext-fffd.pdf')
    assert 'ความเชื่อมโยงงบประมาณรายจ่ายประจำปีงบประมาณ' in text
    assert 'สำนักงานปลัดกระทรวงการคลัง' in text
    assert '�' not in text
