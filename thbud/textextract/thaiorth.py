"""The character sequences that cannot occur in written Thai, to measure how well a text layer was read.

Classes follow WTT 2.0 / TIS 1566 input-sequence checking. A consonant carries at most one above or below vowel
(ั ิ ี ึ ื ุ ู ฺ), then one tone mark (่ ้ ๊ ๋), then optionally thanthakhat (์), in that order; mai taikhu (็) stands
alone; nikhahit only belongs to sara am, which is one character (ำ).
"""
import re
from typing import Iterator, Tuple

_CONS = 'ก-ฮ'
_LEADING = 'เ-ไ'
_ABOVE = 'ัิ-ื'
_BELOW = 'ุ-ฺ'
_TONE = '่-๋'
_TAIKHU = '็'
_THANTHAKHAT = '์'
_NIKHAHIT = 'ํ'
_MARK = f'{_ABOVE}{_BELOW}{_TONE}{_TAIKHU}{_THANTHAKHAT}{_NIKHAHIT}๎'
_VOWEL = f'{_ABOVE}{_BELOW}{_TAIKHU}'
_THAI = 'ก-๛'
_LATIN = 'A-Za-zÀ-ɏ'

RULES = {
    'doubled_mark': re.compile(f'([{_MARK}])\\1'),
    'two_vowels': re.compile(f'[{_VOWEL}][{_TONE}{_THANTHAKHAT}]?[{_VOWEL}]'),
    'two_tones': re.compile(f'[{_TONE}][{_ABOVE}{_BELOW}{_THANTHAKHAT}]?[{_TONE}]'),
    'tone_before_vowel': re.compile(f'[{_TONE}][{_ABOVE}{_BELOW}]'),
    'mark_after_thanthakhat': re.compile(f'{_THANTHAKHAT}[{_VOWEL}{_TONE}]'),
    'maitaikhu_combo': re.compile(f'{_TAIKHU}[{_ABOVE}{_BELOW}{_TONE}{_THANTHAKHAT}]|[{_ABOVE}{_BELOW}{_TONE}{_THANTHAKHAT}]{_TAIKHU}'),
    'orphan_mark': re.compile(f'(?:^|(?<=[^{_CONS}{_MARK}]))[{_MARK}]'),
    'uncomposed_am': re.compile(f'[{_TONE}]?{_NIKHAHIT}[{_TONE}]?า'),
    'stray_nikhahit': re.compile(f'{_NIKHAHIT}(?![{_TONE}]?า)'),
    'am_after_vowel': re.compile(f'[{_VOWEL}{_THANTHAKHAT}]ำ'),
    'leading_vowel_no_cons': re.compile(f'[{_LEADING}](?![{_CONS}])'),
    'latin_in_thai': re.compile(f'(?<=[{_THAI}])[{_LATIN}]|[{_LATIN}](?=[{_THAI}])'),
    'latin1_symbol': re.compile('[\u0080-¿]'),
    'replacement_char': re.compile('�'),
    'pua': re.compile('[-]'),
    'control_char': re.compile('[\x00-\x08\x0b-\x1f]'),
}


def violations(text: str) -> Iterator[Tuple[str, int]]:
    """(rule, offset) for each impossible sequence in `text`."""
    for rule, pattern in RULES.items():
        for match in pattern.finditer(text):
            yield rule, match.start()
