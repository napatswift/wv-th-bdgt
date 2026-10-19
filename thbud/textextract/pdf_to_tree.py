from typing import List, Tuple

from ..textextract import DocumentText, PageText, LineText
from .text import is_baht_marker
from ..model import BudgetItem, FiscalYearBudget
import math
import re
import logging

logger = logging.getLogger(__name__)

"""
class LineWrapper:
    def __init__(self, line, page: PageText):
        self.line = line
        self.page = page

    def __str__(self):
        return str(self.line)

    def __repr__(self):
        return repr(self.line)
"""


class LineItem:
    def __init__(self, itemtype: str, lines: List['LineText'],
                 has_total: bool = True):
        self.itemtype = itemtype
        self.lines = lines
        # False when the entry ended without any row bearing its total column
        # (e.g. a header closed by the next bulleted row): its amount is unknown
        self.has_total = has_total
        self.page_index = lines[0].page.page_index
        self.level = None

    def set_level(self, level):
        if not isinstance(level, int):
            raise TypeError('LineItem\'s level must be int')
        self.level = level

    @property
    def x1(self):
        return max(line.x1 for line in self.lines)

    @property
    def x0(self):
        # the first row (the bullet row) sets the entry's indentation; a
        # continuation row typed into column A with leading spaces must not
        # out-dent the whole entry
        return self.lines[0].x0

    @property
    def document(self):
        for line in self.lines:
            if line.page and line.page.document:
                return line.page.document.filepath
        return None

    @property
    def _rows(self):
        # a page-spanning entry keeps only its first page's rows, so the
        # row_start:row_end extent never mixes indices of two pages/sheets
        return [line.line_index for line in self.lines
                if line.page.page_index == self.page_index]

    @property
    def row_start(self):
        return min(self._rows)

    @property
    def row_end(self):
        return max(self._rows)

    def __str__(self) -> str:
        return ' '.join(
            [str(line) for line in self.lines]
        )

    def __repr__(self) -> str:
        return 'LineItem({}, {})'.format(self.itemtype, repr(self.lines))

    def to_json(self):
        return {
            'itemtype': self.itemtype,
            'name': str(self),
            'page_index': self.page_index,
            'level': self.level,
        }


def get_amount_from_string(text: str) -> float:
    pattern = r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?) บาท'
    match = re.search(pattern, text)
    if match:
        return float(match.group(1).replace(',', ''))
    else:
        return 0.0


_AMOUNT_TOKEN = re.compile(r'^\d{1,3}(?:,\d{3})*(?:\.\d+)?$')


def _parse_amount_token(text: str):
    """Float value of a standalone amount cell, or None if it isn't one."""
    text = text.strip()
    if _AMOUNT_TOKEN.match(text):
        return float(text.replace(',', ''))
    return None


def get_amount_from_lines(lines) -> float:
    """Amount of a budget item, read from its total *column*.

    In the source xlsx each row keeps its total in a dedicated numeric column,
    flattened as a standalone 'บาท' word right after the number. Descriptive text
    (which may embed a per-unit price like 'ๆ ละ 6,500 บาท') stays inside one
    earlier word, so it is never mistaken for the total. We return the first such
    number→'บาท' pair scanning the item's lines in order: for a single row that is
    its own total; for rows that got merged (a sibling concatenated after a trailing
    extra column), it is the first row's own total, not the sibling's.

    Falls back to the legacy string scan when no total column is present.
    """
    for line in lines:
        words = [w.text for w in line.words]
        for i in range(1, len(words)):
            if is_baht_marker(words[i]):
                value = _parse_amount_token(words[i - 1])
                if value is not None:
                    return value
    bare = _bare_total(lines[0]) if lines else None
    if bare is not None:
        return bare
    return get_amount_from_string(' '.join(str(line) for line in lines))


def _from_pdf(line: 'LineText') -> bool:
    return bool(getattr(getattr(line.page, 'document', None), 'is_pdf', False))


# a PDF amount column is set well apart from the text: '… 1,968,000' leaves a
# wide gap, a number that ends a wrapped name ('…ภาค 1', 'หมายเลข 304') doesn't
_PDF_AMOUNT_GAP = 0.03
_NUMBER_OR_DASH = re.compile(r'^(-|\d{1,3}(?:,\d{3})*(?:\.\d+)?)$')


def _is_activity_table_row(line: 'LineText') -> bool:
    """A PDF row of the activity summary table: a name over four or more
    number-or-dash columns quoted in millions ('1. … - - 1.5000 - 1.5000')."""
    words = [w.text for w in line.words]
    tail = 0
    for w in reversed(words):
        if not _NUMBER_OR_DASH.match(w):
            break
        tail += 1
    return tail >= 4


def _bare_total(line: 'LineText'):
    """The total of a bulleted row whose 'บาท' cell is missing, else None.

    Some sheets leave the 'บาท' cell empty on a row that still prints its total
    ('3.3) ค่าก่อสร้างอื่นๆ | 1,968,000'). Such a row ends in a bare amount cell;
    when the sheet has several amount columns the last one is the total column.
    Only a bulleted row qualifies, so a wrapped description that happens to end
    in a number ('จำนวน | 52') never counts as a total; and only outside the
    budget-plan tables, whose rows carry several unrelated numeric columns.
    """
    if line.page is not None and getattr(line.page, 'contains_table', False):
        return None
    words = [w.text for w in line.words]
    tokens = _leading_tokens(str(line))
    if len(words) < 2 or not tokens or not get_patern_of_bullet(tokens[0])[1]:
        return None
    if any(is_baht_marker(w) for w in words):
        return None
    if _from_pdf(line) and (line.words[-1].x0 - line.words[-2].x1 < _PDF_AMOUNT_GAP
                            or _is_activity_table_row(line)):
        return None
    return _parse_amount_token(words[-1])


def _line_bears_total_column(line: 'LineText') -> bool:
    """True when a row carries its total column, so its budget item is complete.

    Two signals, unioned so this stays a strict superset of the legacy check:
      * the legacy check — the last whitespace token is the 'บาท' marker; keeps
        rows that flatten the total into one 'N บาท' cell closing as before, and
      * a standalone 'บาท'-marker *word* anywhere in the row — closes rows whose
        total cell is followed by a trailing extra column ('… บาท 1,842') or a
        trailing marker cell ('… บาท *'), which the legacy check missed and which
        caused the next sibling row to be merged into this item.

    An embedded per-unit price ('ๆ ละ 6,500 บาท') stays inside one text cell, so it
    is never a standalone marker word and does not trigger a close.

    A bulleted row whose 'บาท' cell is missing but which ends in a bare amount
    cell also bears its total (see _bare_total).
    """
    tokens = str(line).split()
    if tokens and tokens[-1].replace('-', '').replace('*', '') == 'บาท':
        return True
    if any(is_baht_marker(w.text) for w in line.words):
        return True
    return _bare_total(line) is not None


def _entry_amount(bud_item: 'LineItem'):
    """Amount of an entry, or None when it never showed a total column."""
    if not bud_item.has_total:
        return None
    return get_amount_from_lines(bud_item.lines)


def _is_column_token(text: str) -> bool:
    """A word an amount column is made of: a number, a dash, 'บาท' or a '*'."""
    return (is_baht_marker(text) or bool(_NUMBER_OR_DASH.match(text))
            or text == '*')


def _cells(line: 'LineText') -> List[List[str]]:
    """A row's cells as their whitespace tokens. An XLSX cell is one word; in a
    PDF a word set _PDF_AMOUNT_GAP apart from the previous one starts a cell."""
    if not _from_pdf(line):
        cells = [w.text.split() for w in line.words]
    else:
        cells, prev = [], None
        for w in line.words:
            if prev is None or w.x0 - prev.x1 >= _PDF_AMOUNT_GAP:
                cells.append([])
            cells[-1].append(w.text)
            prev = w
    return [c for c in cells if c]


def _entry_label(lines: List['LineText']) -> Tuple[str, str]:
    """(bullet, label) of an entry, read from its words rather than its joined
    text: the first row's bullet (glued or not) and every amount column — a cell
    of numbers, dashes and 'บาท' set apart from the text, or a row of nothing
    else — are dropped wherever they sit; the text of every row (wrapped name,
    quantity line) is kept in reading order. A number glued to the text ('…
    ตามมาตรา 40', 'ภาคที่ 5') is the name's own. bullet is None if there is none.
    """
    bullet, words, has_column = None, [], False
    for li, line in enumerate(lines):
        cells = _cells(line)
        if li == 0 and cells:
            head = _leading_tokens(' '.join(cells[0]))
            if get_patern_of_bullet(head[0])[1]:
                bullet = head.pop(0)
            cells[0] = head
            cells = [c for c in cells if c]
        whole_row = all(all(_is_column_token(t) for t in c) for c in cells)
        for ci, cell in enumerate(cells):
            if all(_is_column_token(t) for t in cell) and (ci > 0 or whole_row):
                has_column = True
                continue
            words.extend(cell)
    if not has_column and words and is_baht_marker(words[-1]):
        # an XLSX total flattened into the text cell ('… 143,000 บาท'), or a PDF
        # total printed close to the text: drop it the way the legacy string
        # scan read it, keeping a bare number that ends the name
        words.pop()
        dropped = False
        while words and _NUMBER_OR_DASH.match(words[-1]) and (
                not dropped or ',' in words[-1] or words[-1] == '-'):
            dropped = dropped or words[-1] != '-'
            words.pop()
    return bullet, ' '.join(words)


def get_year_from_string(text: str) -> Tuple[int, int]:
    # ปี 2563 ตั�งงบประมาณ 616,834,700 บาท -> 2563, 2563
    # ปี 2563-2564 ตั�งงบประมาณ 616,834,700 บาท -> 2563, 2564
    # ปี 2563 - 2564 ตั�งงบประมาณ 616,834,700 บาท -> 2563, 2564
    # "a 2563 = 2564 ตั้งงบประมาณ 616,834,700 บาท" -> 2563, 2564

    # pattern = r'ปี (\d{4})(?:\s*-\s*(\d{4}))?'
    pattern = r'(\d{4})(?:[^\d]+(\d{4}))?'

    match = re.search(pattern, text)
    if match:
        if match.group(2):
            return int(match.group(1)), int(match.group(2))
        else:
            return int(match.group(1)), int(match.group(1))
    else:
        return 0, 0


def get_patern_of_bullet(String):
    regx = [(r'[1-9][0-9]*(\.[1-9][0-9]*)*\)$', 20),
            (r'\(\d*(\.?\d*)*\)$', 50),
            (r'[1-9][0-9]*(\.[1-9][0-9]*)+$', 2),
            (r'[1-9][0-9]*\.$', 1),
            (r'[1-9][0-9]*$', 30),
            # '(2' — a parenthesised bullet whose ')' was left out
            (r'\(\d+(\.\d+)*$', 50)]

    for r, l in regx:
        if re.match(r, String):
            if l in [2, 20, 50]:
                l = String.count('.') + l
            return r, l
    return '', 0


# a bullet glued to its label: '3.งบเงินอุดหนุน', '1)ค่า…', '(1)ค่า…'. The
# bullet must end in '.' or ')' so a number glued to text ('12เดือน') stays text.
_GLUED_BULLET = re.compile(r'^(\(\d+(?:\.\d+)*\)|\d+(?:\.\d+)*[.)])(?=[^\d\s.,)])')


def _leading_tokens(text: str) -> List[str]:
    """Whitespace tokens of a row, with a glued leading bullet split off."""
    tokens = text.split()
    if tokens:
        m = _GLUED_BULLET.match(tokens[0])
        if m:
            tokens = [m.group(1), tokens[0][m.end(1):]] + tokens[1:]
    return tokens


def is_quantity_string(stringToCheck):
    stringToCheck = stringToCheck.replace(',', '')
    stringToCheck = stringToCheck.strip()

    return (
        re.match(r'รวม \d+ รายการ', stringToCheck)
        or re.match(r'\(\d+ หน่วย\)', stringToCheck)
        # จำนวน 10 โครงการ
        or re.match(r'จำนวน \d+ โครงการ', stringToCheck)

    )


def is_classifier(string):
    return string in ['แห่ง', 'สายทาง']


# A section title ("1. รายละเอียดงบประมาณจำแนกตามแผนงาน และ ผลผลิต/โครงการ",
# "7. …"): it opens the detail section, it is not a budget line.
_SECTION_TITLE = re.compile(r'^(\d+\.)?รายละเอียดงบประมาณ(รายจ่าย)?จ.{1,3}แนกตาม')


def is_redundant_line(line_text: List[str]):
    if not line_text or ' '.join(line_text).isdigit():
        return True
    if _SECTION_TITLE.match(''.join(line_text)):
        return True

    for text in line_text:
        if text in ['รายละเอียดงบประมาณจำแนกตามงบรายจ่าย',
                    'รายละเอียดงบประมาณจําแนกตามงบรายจ่าย',
                    'รายละเอียดงบประมาณจ�าแนกตามงบรายจ่าย',
                    'รายละเ�ียดงบประมาณจ�าแนก�ามงบรายจ่าย',
                    'รายละเอ�ยดงบ�ระมา��ำแนก�ามงบราย��าย',
                    'รายละเอียดงบประมาณจ',
                    'รายการบุคลากรภาครัฐ',
                    'รายการบ�คลากร�าครั�',
                    'รายการบ�คลากรภาครัฐ',
                    'รายการบ�คลากร�าครัฐ',
                    'รายการบุคลากรภาครั�',
                    'วงเงินทั้งสิ้น',
                    'วงเงินทั�งสิ�น',
                    'รายละเอียดงบประมาณ',
                    'รายละเอียดงบประมาณรายจ่ายจำแนกตามแผนงาน']:
            return True
    return False


_PERSONNEL_HEADERS = (
    'รายการบุคลากรภาครัฐ',
    'รายการบ�คลากร�าครั�',
    'รายการบ�คลากรภาครัฐ',
    'รายการบ�คลากร�าครัฐ',
    'รายการบุคลากรภาครั�',
)

_OFF_BUDGET_MARKERS = ('เงินนอกงบประมาณ', 'เงินน�กงบประมาณ')


def _names_project(line: 'LineText') -> bool:
    """True when any in-cell line of the row's label starts with 'โครงการ'.

    Integrated-plan files stack the owner above the project inside one cell
    ('กระทรวง…⏎กรม…⏎โครงการX') or print a bare 'โครงการX' with no ' : '; both
    open a project just like 'โครงการ : X'. Callers apply it to unbulleted rows
    only, so an item whose description mentions a project stays an item.
    """
    if not line.words:
        return False
    return any(seg.strip().startswith('โครงการ')
               for seg in line.words[0].text.split('\n'))


def check_proj_outp(target, line_text):
    if line_text[0].replace(':', '') == target:
        return True
    if len(line_text) > 1 and line_text[1].startswith(target):
        return True
    return False


# An unbulleted 'รายการไม่ผูกพัน A บาท' row (source typo: ผูกผัน). Sources split
# an item P into 'รายการไม่ผูกพัน A' + 'รายการผูกพัน B' and often list only the
# ผูกพัน items under 'ประกอบด้วย', so the ไม่ผูกพัน row is then a real child of P.
# The 'รายการผูกพัน' row is never kept: its amount is what the listed items carry.
_UNCOMMITTED_SUBTOTAL = re.compile(r'^รายการไม่ผูก(พัน|ผัน)$')
UNCOMMITTED_SUBTOTAL = 'uncommitted_subtotal'

_HEADER_TYPES = ('budget_plan', 'PROJECT', 'OUTPUT')


# '7.4.1.5 งบประมาณรายจ่าย จำแนกตามกิจกรรม - งบรายจ่าย': the activity summary
# table, quoted in millions ('หน่วย : ล้านบาท'); its rows are not budget lines
_ACTIVITY_TABLE_TITLE = re.compile(r'จำแนกตามกิจกรรม')
_PLAN_NUMBER = re.compile(r'7\.\d+$')
# '7.1.1 โครงการที่ 1 : …', '7.1.1.1 วัตถุประสงค์': a §7 sub-heading describing a
# plan's output/project; spending lines are numbered under categories 1-5
_SECTION_SEVEN_SUBHEADING = re.compile(r'7(\.\d+){2,}$')


def _is_plan_heading(line_text: List[str], pdf: bool) -> bool:
    """A budget-plan row of a table page: '7.3 แผนงาน…', or '<bullet> แผนงาน…'.
    In a PDF the word 'แผนงาน' also turns up second in wrapped prose ('…ตาม
    อนุสัญญา แผนงาน และพันธกรณี'), so there it must follow a bullet."""
    if re.match(r'7.\d+$', line_text[0]):
        return True
    if len(line_text) < 2 or not line_text[1].startswith('แผนงาน'):
        return False
    return not pdf or bool(get_patern_of_bullet(line_text[0])[1])


def _ends_section_seven(line_text: List[str], line: 'LineText') -> bool:
    """The spending detail resumes: an output/project header ('ผลผลิต : …',
    'โครงการ : …'), a plan heading, or a category total ('1. งบเงินอุดหนุน … บาท')."""
    if line_text[0].replace(':', '') in ('ผลผลิต', 'โครงการ') or _PLAN_NUMBER.match(line_text[0]):
        return True
    return (len(line_text) > 1 and line_text[1].startswith('งบ')
            and bool(get_patern_of_bullet(line_text[0])[1])
            and _line_bears_total_column(line))


def get_entries(lines: List[LineText]):
    # flags
    bullet_flag = False
    # project and output flag
    proj_outp_flag = False
    # PDF only, on pages not seen as tables: inside an activity summary table,
    # or inside a §7 sub-section's description ('7.5.1.2 สถานที่ดำเนินการ' and
    # its numbered lists) until the spending detail starts again
    in_activity_table = False
    in_section_seven = False
    # PDF only: a plan heading whose amount is on a wrapped next line
    open_plan = None

    entry = []
    entries = []
    for i, line in enumerate(lines):
        line_id = line

        # joint line together
        line_text_string = str(line)

        # then split by whitespace
        line_text = _leading_tokens(line_text_string)

        # a unit's personnel block header ('รายการบุคลากรภาครัฐ') starts a new
        # unit (one per sheet in ministry-overview files): reset the level
        # stack so its '1. งบบุคลากร' cannot nest under the previous unit
        if (line_text and line_text[0] in _PERSONNEL_HEADERS and not entry
                and not line.page.contains_table):
            entries.append(('reset', [line_id]))
            continue

        # skiping
        if is_redundant_line(line_text):
            continue

        pdf = _from_pdf(line)
        if open_plan is not None:
            if (not get_patern_of_bullet(line_text[0])[1]
                    and not _is_plan_heading(line_text, pdf)):
                open_plan.append(line_id)
                if _line_bears_total_column(line_id):
                    open_plan = None
                continue
            open_plan = None

        if pdf and not line.page.contains_table:
            if _SECTION_SEVEN_SUBHEADING.match(line_text[0]):
                if entry:
                    entries.append(
                        ('item' if bullet_flag else proj_outp_flag, entry, False))
                bullet_flag = proj_outp_flag = False
                entry = []
                in_activity_table = bool(
                    _ACTIVITY_TABLE_TITLE.search(line_text_string.replace(' ', '')))
                in_section_seven = True
                continue
            if in_section_seven:
                if not _ends_section_seven(line_text, line_id):
                    continue
                in_section_seven = in_activity_table = False
            if in_activity_table:
                if not _line_bears_total_column(line_id):
                    continue
                in_activity_table = False
            elif _ACTIVITY_TABLE_TITLE.search(line_text_string.replace(' ', '')):
                in_activity_table = True
                continue
        else:
            in_activity_table = False

        if _PLAN_NUMBER.match(line_text[0]):
            in_section_seven = False

        # budget plan: on a table page, or a '7.N แผนงาน…' heading on any PDF page
        if line.page.contains_table or (
                pdf and _PLAN_NUMBER.match(line_text[0]) and len(line_text) > 1
                and line_text[1].startswith('แผนงาน')):
            if _is_plan_heading(line_text, pdf):
                if pdf:
                    # a PDF item left open never runs on into the next plan
                    if entry:
                        entries.append(
                            ('item' if bullet_flag else proj_outp_flag, entry, False))
                    bullet_flag = proj_outp_flag = False
                    entry = []
                entries.append(('budget_plan', [line_id]))
                if pdf and not _line_bears_total_column(line_id):
                    open_plan = entries[-1][1]
            continue

        patern_of_bullet = get_patern_of_bullet(line_text[0])
        if (bullet_flag and entry and _from_pdf(line)
                and re.match(r'[1-9][0-9]*$', line_text[0])):
            # '1 อาคาร 4,922,100 บาท' under an open item is its quantity line
            patern_of_bullet = ('', 0)

        if (
            re.match(r'ป?ี \d{4} ', line_text_string)
                or 'ตั้งงบประมาณ' in line_text
                or 'ตั้งงปบระมาณ' in line_text
                or '�ั้งงบ�ร�มา�' in line_text
                or '��กพันงบ�ร�มา�' in line_text
                or 'ผูกพันงบประมาณ' in line_text
        ):
            entries.append(('fiscal_year', [line_id]))

            # DEBUG
            logger.debug('get_entries::`{}` is fiscal year'.format(line))
            continue

        if line_text[0] in _OFF_BUDGET_MARKERS and bullet_flag:
            # An off-budget row is never an item's own total. The open item
            # printed no on-budget total, i.e. it is funded off-budget only:
            # drop it rather than book the off-budget amount as its budget.
            logger.debug('get_entries::`{}` drops off-budget-only item {}'
                         .format(line, entry))
            bullet_flag = False
            proj_outp_flag = False
            entry = []
            continue

        if is_quantity_string(line_text_string):
            # 'รวม 117 รายการ (รวม 527 หน่วย)'
            if not bullet_flag:
                prev_entry = entries[-1]
                prev_entry[1].append(line_id)
                continue

        if (
            (patern_of_bullet[1] or line_text[0].startswith('กิจกรรม'))
                and (
                    len(line_text) > 1
                    and not is_classifier(line_text[1])
                )
        ):
            if entry:
                # the open entry (an item or a header) printed no total of
                # its own; it ends where the next bulleted row starts, rather
                # than swallowing that row. Its amount is unknown.
                entries.append(
                    ('item' if bullet_flag else proj_outp_flag, entry, False))
                proj_outp_flag = False
                entry = []

            bullet_flag = True

            # DEBUG
            logger.debug('get_entries::`{}` is bullet'.format(line))

        if (
            check_proj_outp('ผลผลิต', line_text)
                or check_proj_outp('ผลผลิ�', line_text)
                or check_proj_outp('�ล�ลิ�', line_text)
                or check_proj_outp('�ล�ลิต', line_text)
        ):
            proj_outp_flag = 'OUTPUT'

        if (
            check_proj_outp('โครงการ', line_text)
            or check_proj_outp('�ครงการ', line_text)
            or check_proj_outp('��รงการ', line_text)
            or (not bullet_flag and _names_project(line))
        ):
            proj_outp_flag = 'PROJECT'

        if proj_outp_flag:
            # DEBUG
            logger.debug('get_entries::`{}` is `{}`'.format(
                line, proj_outp_flag))

        if bullet_flag or proj_outp_flag:
            entry.append(line_id)
            if _line_bears_total_column(line_id):
                entries.append(
                    ('item' if bullet_flag else proj_outp_flag, entry))
                bullet_flag = False
                proj_outp_flag = False
                entry = []
        else:
            if (
                any(m in line_text for m in _OFF_BUDGET_MARKERS)
                    or 'เงินงบประมาณ' in line_text
            ):
                continue

            if (
                _UNCOMMITTED_SUBTOTAL.match(line_text[0])
                    and _line_bears_total_column(line_id)
            ):
                # kept or dropped by resolve_uncommitted_subtotals once the
                # tree's levels (and so its sums) are known
                entries.append((UNCOMMITTED_SUBTOTAL, [line_id]))
                continue

            logger.warning((
                f'SKIPPED page {line.page.page_index},'
                f' line {line.line_index} '
                f'👉🏽 {line_text_string}'
            ))

    return [LineItem(*e) for e in entries]


# entry types that start a fresh level stack; 'reset' does so without a node
_STACK_RESETS = ('budget_plan', 'PROJECT', 'OUTPUT', 'reset')


def add_level_to_entries_positions(entries: List[LineItem],):
    """First leveling pass: level = depth of the item's x0 on an indentation stack."""
    levels = _x0_levels(entries, _normalized_x0s(entries))
    for bud_item, level in zip(entries, levels):
        if level is not None:
            bud_item.set_level(level)


def _x0_levels(entries, xs):
    """Indentation (x0) level proposal for every entry, given normalized x0s.

    Items get the depth of their x on a stack of strictly increasing x positions
    (deeper x pushes, shallower x pops, equal x is a sibling). budget_plan /
    PROJECT / OUTPUT headers reset the stack and get -2 / -1; fiscal-year lines
    get None (they attach to the preceding node)."""
    x_diff_threshold = 0.005
    out = [None] * len(entries)

    # stores min x position
    stack_x = []

    for i, bud_item in enumerate(entries):
        # LOGGING
        logger.debug(f'extract_tree_levels::{(bud_item)}')

        if bud_item.itemtype != 'item':
            # If the budget unit is not an item,
            # then it is a budget unit header.
            # In this case, we clear the stack
            # and add a new level to the levels list.
            if bud_item.itemtype in _STACK_RESETS:
                stack_x = []

            if bud_item.itemtype == 'budget_plan':
                out[i] = -2
            elif (
                bud_item.itemtype == 'PROJECT'
                or bud_item.itemtype == 'OUTPUT'
            ):
                out[i] = -1

            continue

        # lsx is the x start position of the first line of the budget unit,
        # normalized by its page's width.
        lsx = xs[i]

        # If the previous item has an x position that is more than
        # the threshold greater than this item's x position,
        # then we pop the previous item off the stack.
        while len(stack_x) and stack_x[-1] > lsx + x_diff_threshold:
            stack_x.pop()

        # If the stack is empty or the difference between
        # the x positions of the current item
        # and the item at the top of the stack
        # is greater than the threshold,
        # then we push the current item's x position onto the stack.
        if len(stack_x) == 0 or abs(stack_x[-1] - lsx) >= x_diff_threshold:
            stack_x.append(lsx)

        # The level of the current item is the length of the stack.
        out[i] = len(stack_x)

        # LOGGING
        logger.debug('extract_tree_levels::level: {}'.format(out[i]))
    return out


def _bullet_key(bud_item):
    """(family, number components) of the item's leading bullet, or (None, None).

    family: '(N)' > 'N' > 'N)' > 'N.N' > 'N.' groups get_patern_of_bullet's codes;
    comps: the numeric path, e.g. '2.1.1' -> (2, 1, 1), '(3)' -> (3,).
    """
    toks = _leading_tokens(str(bud_item))
    if not toks:
        return None, None
    tok = toks[0].rstrip(':')
    _, code = get_patern_of_bullet(tok)
    if not code:
        return None, None
    if code >= 50:
        family = '(N)'
    elif code == 30:
        family = 'N'
    elif code >= 20:
        family = 'N)'
    elif code == 1:
        family = 'N.'
    else:
        family = 'N.N'
    m = re.match(r'\(?([0-9.]+?)\)?\.?$', tok)
    if not m:
        return family, None
    try:
        comps = tuple(int(c) for c in m.group(1).split('.') if c != '')
    except ValueError:
        return family, None
    return family, comps or None


def _normalized_x0s(entries):
    """Per-entry x0 normalized by page width, exactly as the x0 leveler does."""
    page_end_x_sr = page_x1(entries)
    page_x1_max = max(page_end_x_sr.values())
    return [e.x0 + (page_x1_max - page_end_x_sr[e.page_index]) for e in entries]


def _grammar_levels(entries, xs, pinned=frozenset()):
    """Bullet-grammar (numbering-aware) level proposal for every entry.

    A bulleted item anchors by its numbering:
      - sibling anchor: a stack entry of the same family, same depth, same prefix
        components and a smaller last component (strict +1 continuation preferred,
        x0-nearest tiebreak for numbering gaps) -> becomes its sibling. Several +1
        candidates mean a list restarted inside another ('(1) ค่าครุภัณฑ์' holding
        its own '(1)'): the x0-nearest wins, but only among candidates reachable
        by popping entries of the item's own family -- a +1 candidate behind a
        '1.'/'1.1' row belongs to an earlier block
      - parent anchor: a stack entry whose components equal the item's components
        minus the last one ('2.1.1' under '2.1') -> becomes its child, used only
        when there is no sibling anchor: a components-parent deeper than a sibling
        anchor is a restarted or other-family list ('(1)' inside '1.1', '(1)' inside
        '(1.1)'), never the parent of the run's continuation
      - a fresh '...1' with no anchor starts a new sub-list under the current top
      - otherwise fall back to the x0 rule
    Un-bulleted items use the x0 rule; headers reset the stack (as in
    add_level_to_entries_positions). Returns a level per entry (None where the x0
    leveler assigns none, i.e. fiscal-year lines).

    `pinned` entries (indices) are never popped by a numbering anchor while their
    x encloses the item: an anchor found beneath one nests the item under it
    instead (a grammar-blind parent, e.g. an activity row between '1.' and '1.1').
    """
    x_diff_threshold = 0.005
    out = [None] * len(entries)
    stack = []  # (family, comps, lsx, entry index)

    def anchor_cut(cut, lsx):
        # keep a pinned, x-enclosing entry at or above the anchor's cut point
        for d in range(len(stack) - 1, cut - 1, -1):
            if stack[d][3] in pinned and stack[d][2] < lsx - x_diff_threshold:
                return d + 1
        return cut

    def x_pop_and_should_push(lsx):
        while stack and stack[-1][2] > lsx + x_diff_threshold:
            stack.pop()
        return not stack or abs(stack[-1][2] - lsx) >= x_diff_threshold

    for i, bud_item in enumerate(entries):
        if bud_item.itemtype != 'item':
            if bud_item.itemtype in _STACK_RESETS:
                stack.clear()
            if bud_item.itemtype == 'budget_plan':
                out[i] = -2
            elif bud_item.itemtype in ('PROJECT', 'OUTPUT'):
                out[i] = -1
            continue

        lsx = xs[i]
        family, comps = _bullet_key(bud_item)

        if family and comps:
            sib_cands = []
            par_idx = None
            for d in range(len(stack) - 1, -1, -1):
                sfam, scomps, sx, _ = stack[d]
                if (sfam == family and scomps and len(scomps) == len(comps)
                        and scomps[:-1] == comps[:-1] and comps[-1] > scomps[-1]):
                    sib_cands.append(d)
                if par_idx is None and scomps and scomps == comps[:-1]:
                    par_idx = d
            sib_idx = None
            if sib_cands:
                plus1 = [d for d in sib_cands
                         if stack[d][1][-1] + 1 == comps[-1]]
                if plus1:
                    reach = [d for d in plus1
                             if all(stack[e][0] == family
                                    for e in range(d + 1, plus1[0] + 1))]
                    sib_idx = min(reach, key=lambda d: abs(stack[d][2] - lsx))
                else:
                    sib_idx = min(sib_cands, key=lambda d: abs(stack[d][2] - lsx))
            if sib_idx is not None:
                del stack[anchor_cut(sib_idx, lsx):]
            elif par_idx is not None:
                del stack[anchor_cut(par_idx + 1, lsx):]
            elif comps[-1] == 1:
                pass  # new sub-list: nest under the current top
            elif not x_pop_and_should_push(lsx):
                stack.pop()
            stack.append((family, comps, lsx, i))
        else:
            if not x_pop_and_should_push(lsx):
                stack.pop()
            stack.append((None, None, lsx, i))
        out[i] = len(stack)
    return out


_HEADER_TYPES = ('budget_plan', 'PROJECT', 'OUTPUT')
_CATEGORY_FAMILIES = ('N.N', 'N.', 'N)')


def _is_activity_row(bud_item):
    """An un-bulleted 'กิจกรรม…' (activity) item row."""
    if bud_item.itemtype != 'item':
        return False
    toks = str(bud_item).split()
    return (bool(toks) and toks[0].startswith('กิจกรรม')
            and _bullet_key(bud_item)[0] is None)


def _activity_x_shifts(entries, xs):
    """x offsets that re-nest activity rows printed at a category's indent.

    Highways house style prints an un-bulleted 'กิจกรรม…' row at the very indent of
    the 'N.' / 'N.N…' / 'N)' category rows around it, so x0 alone makes them
    siblings:
      - category-first: the nearest preceding item at the same-or-lower x is a
        category at the SAME x -> the activity is its child (+half a step); a following
        activity at that x after such a child inherits the shift (its sibling);
      - activity-first: otherwise, if the next item at the same-or-lower x is a
        category at the same x -> the activity is the parent of those (-half);
      - an activity printed deeper, inside the items of such a nested activity
        (at the '(N)' indent), is moved up beside it: a กิจกรรม is never the
        child of another กิจกรรม.
    Neighbours are looked up within the activity's header segment. Returns
    {entry index: dx}; empty when no activity row is printed this way."""
    eps = 0.005
    pdf = bool(entries) and _from_pdf(entries[0].lines[0])
    shifts = {}
    nested = set()  # activities moved under their category (category-first)

    def neighbour(i, step):
        j = i + step
        while 0 <= j < len(entries):
            e = entries[j]
            if e.itemtype in _HEADER_TYPES:
                return None
            if e.itemtype == 'item' and xs[j] <= xs[i] + eps:
                return j
            j += step
        return None

    def enclosing(i):
        # nearest preceding item strictly shallower than this one (x0 parent)
        for j in range(i - 1, -1, -1):
            e = entries[j]
            if e.itemtype in _HEADER_TYPES:
                return None
            if e.itemtype == 'item' and xs[j] < xs[i] - eps:
                return j
        return None

    def same_x_category(i, j):
        return (j is not None and abs(xs[j] - xs[i]) < eps
                and _bullet_key(entries[j])[0] in _CATEGORY_FAMILIES)

    def half(i):
        # half an indent step: 0.5 of a column in an xlsx; in a PDF, where x is
        # a page fraction, half the gap to the activity's first deeper row, so
        # it lands between its category and its own '(N)' items
        if not pdf:
            return 0.5
        for j in range(i + 1, len(entries)):
            if entries[j].itemtype in _HEADER_TYPES:
                break
            if entries[j].itemtype == 'item' and xs[j] > xs[i] + eps:
                return (xs[j] - xs[i]) / 2
        return 0.5

    def nest_beside(i, a):
        shifts[i] = xs[a] + shifts[a] - xs[i]
        nested.add(i)

    for i, e in enumerate(entries):
        if not _is_activity_row(e):
            continue
        prev = neighbour(i, -1)
        if prev is not None and abs(xs[prev] - xs[i]) < eps:
            if _is_activity_row(entries[prev]):
                if prev in nested:
                    nest_beside(i, prev)
            elif same_x_category(i, prev):
                shifts[i] = +half(i)
                nested.add(i)
            elif enclosing(i) in nested:
                # printed at the indent of a nested activity's own items
                nest_beside(i, enclosing(i))
        elif same_x_category(i, neighbour(i, +1)):
            shifts[i] = -half(i)
    return shifts


def _sum_violations(item_idxs, levels, amounts):
    """# of parents (within one header segment, parentage from `levels` by the
    nearest-smaller rule) whose amount differs from the sum of their children's.

    A parent with an unknown amount (None) is weighed at the sum of its
    children, as the tree's autofix will fill it, so an amount-less header still
    counts as money when it becomes some other item's child."""
    children = {}
    stack = []  # (idx, level)
    for i in item_idxs:
        while stack and stack[-1][1] >= levels[i]:
            stack.pop()
        if stack:
            children.setdefault(stack[-1][0], []).append(i)
        stack.append((i, levels[i]))
    amounts = dict(amounts)
    # children follow their parent in document order: descending index visits
    # every child before its parent
    for p in sorted(children, reverse=True):
        if amounts[p] is None:
            ka = [amounts[k] for k in children[p]]
            if all(a is not None for a in ka):
                amounts[p] = sum(ka)
                children[p] = []  # filled from its children: nothing to check
    bad = 0
    for p, kids in children.items():
        if not kids:
            continue
        pa = amounts[p]
        ka = [amounts[k] for k in kids]
        if pa is None or any(a is None for a in ka):
            continue
        if abs(pa - sum(ka)) > 0.005:
            bad += 1
    return bad


def refine_levels_with_bullet_grammar(entries: List[LineItem]):
    """Second leveling pass: structural proposals, vetoed by the money invariant.

    Per header segment (the run of items between budget_plan/PROJECT/OUTPUT
    entries) the x0 levels (already set by add_level_to_entries_positions) are
    the incumbent, and two proposals compete with them:
      - the bullet grammar's re-leveling, adopted unless it INCREASES the number
        of parent != sum(children) violations in the segment;
      - the activity-row re-nesting (_activity_x_shifts: x0 and grammar levels
        recomputed with same-indent 'กิจกรรม…' rows moved under / above their
        category), adopted only if it STRICTLY reduces the violations of the
        level set chosen so far. It is a guess from layout, so it never wins a
        tie and can never make a segment's sums worse."""
    if not entries:
        return
    xs = _normalized_x0s(entries)
    proposed = _grammar_levels(entries, xs)

    shifts = _activity_x_shifts(entries, xs)
    activity_proposals = []
    if shifts:
        xs_act = [x + shifts.get(i, 0) for i, x in enumerate(xs)]
        activities = frozenset(i for i, e in enumerate(entries)
                               if _is_activity_row(e))
        activity_proposals = [_grammar_levels(entries, xs_act, activities),
                              _x0_levels(entries, xs_act)]

    segment = []
    for i, bud_item in list(enumerate(entries)) + [(len(entries), None)]:
        if bud_item is not None and bud_item.itemtype == 'item':
            segment.append(i)
            continue
        if bud_item is not None and bud_item.itemtype not in _HEADER_TYPES:
            continue  # fiscal-year lines and unresolved subtotals
        if segment:
            touched = any(j in shifts for j in segment)
            _adopt_vetoed_levels(entries, segment, proposed,
                                 activity_proposals if touched else [])
        segment = []


def resolve_uncommitted_subtotals(entries: List[LineItem]) -> List[LineItem]:
    """Keep each 'รายการไม่ผูกพัน' subtotal only where it closes its parent's gap.

    Runs after leveling, when parentage (and so every parent's children sum) is
    known. The candidate takes the level of the next real item — the listed items
    it is printed alongside — rather than its own x0, and is kept as an item only
    if the parent that level gives it is short by exactly its amount
    (parent - sum(children) == A). Otherwise the listed items already include the
    ไม่ผูกพัน items (or it belongs elsewhere) and it is dropped, as before.
    Returns the entries without the dropped candidates."""
    out = list(entries)
    i = 0
    while i < len(out):
        cand = out[i]
        if cand.itemtype != UNCOMMITTED_SUBTOTAL:
            i += 1
            continue
        level = _gap_closing_level(out, i)
        if level is not None:
            cand.itemtype = 'item'
            cand.set_level(level)
            i += 1
        else:
            line = cand.lines[0]
            logger.warning((
                f'SKIPPED page {line.page.page_index},'
                f' line {line.line_index} '
                f'👉🏽 {cand} (does not close its parent\'s gap)'
            ))
            del out[i]
    return out


def _gap_closing_level(entries: List[LineItem], ci: int):
    """The level at which candidate `ci` exactly closes its parent's gap, or None."""
    nxt = None
    for j in range(ci + 1, len(entries)):
        t = entries[j].itemtype
        if t in _HEADER_TYPES:
            return None
        if t == 'item':
            nxt = j
            break
    if nxt is None:
        return None
    level = entries[nxt].level

    def is_node(e):
        return e.itemtype == 'item' or e.itemtype in _HEADER_TYPES

    parent = next((j for j in range(ci - 1, -1, -1)
                   if is_node(entries[j]) and entries[j].level < level), None)
    if parent is None:
        return None
    # children of `parent`: by the nearest-smaller rule extract_tree_levels uses,
    # the nodes after it at levels deeper than its own whose nearest shallower
    # predecessor is `parent`
    stack = [parent]
    children = []
    for j in range(parent + 1, len(entries)):
        e = entries[j]
        if not is_node(e):
            continue
        if e.level <= entries[parent].level:
            break
        while entries[stack[-1]].level >= e.level:
            stack.pop()
        if stack[-1] == parent:
            children.append(j)
        stack.append(j)

    amount = get_amount_from_lines(entries[ci].lines)
    p_amount = get_amount_from_lines(entries[parent].lines)
    gap = p_amount - math.fsum(get_amount_from_lines(entries[j].lines)
                               for j in children)
    if amount > 0 and abs(gap - amount) <= 0.005:
        return level
    return None


def _adopt_vetoed_levels(entries, segment, grammar, activity_proposals):
    """Set one segment's levels to the best of the x0 / grammar / activity levels.

    The grammar replaces the incumbent x0 levels unless it adds violations; each
    activity proposal (in order) then replaces the result only if it has
    strictly fewer violations."""
    current = [entries[j].level for j in segment]
    wanted = [grammar[j] for j in segment]
    options = [[p[j] for j in segment] for p in activity_proposals]
    if wanted == current and not options:
        return

    amounts = {j: _entry_amount(entries[j]) for j in segment}

    def violations(levels):
        return _sum_violations(segment, dict(zip(segment, levels)), amounts)

    best, v_best = current, violations(current)
    if wanted != current:
        v_wanted = violations(wanted)
        if v_wanted <= v_best:
            best, v_best = wanted, v_wanted
    for levels in options:
        v = violations(levels)
        if v < v_best:
            best, v_best = levels, v
    if best is not current:
        for j, level in zip(segment, best):
            entries[j].set_level(level)


def extract_tree_levels(
    bud_items: List[LineItem],
) -> BudgetItem:
    """
    Extracts the levels of the budget items.
    The levels are extracted by looking at
    the x0 positions of the budget items.
    """

    add_level_to_entries_positions(bud_items)
    refine_levels_with_bullet_grammar(bud_items)
    bud_items = resolve_uncommitted_subtotals(bud_items)

    itemtype_mapper = {
        'budget_plan': 'BUDGET_PLAN',
        'PROJECT': 'PROJECT',
        'OUTPUT': 'OUTPUT',
        'item': 'BUDGET_DETAIL',
    }

    root = BudgetItem(
        budget_type='ROOT',
        name='ROOT',
        amount=None,
        document='',
        page=0,
    )

    parent_stack = [{
        'node': root,
        'level': -10,
    }]

    for bud_item in bud_items:
        if bud_item.itemtype == 'reset':
            continue

        if bud_item.itemtype == 'fiscal_year':
            last_node = parent_stack[-1]['node']
            year_start, year_end = get_year_from_string(str(bud_item))
            last_node.fiscal_year_budget.append(
                FiscalYearBudget(
                    line=str(bud_item).replace('\n', '\t').strip(),
                    year=year_start,
                    amount=get_amount_from_lines(bud_item.lines),
                    year_end=year_end,
                )
            )
            continue

        while (
            len(parent_stack) > 0
            and parent_stack[-1]['level'] >= bud_item.level
        ):
            parent_stack.pop()

        if len(parent_stack) == 0:
            parent = None

        else:
            parent = parent_stack[-1]['node']

        bullet, label = _entry_label(bud_item.lines)
        node = BudgetItem(
            budget_type=itemtype_mapper[bud_item.itemtype],
            name=str(bud_item).replace('\n', '\t').strip(),
            amount=_entry_amount(bud_item),
            document=bud_item.document,
            page=bud_item.page_index,
            row_start=bud_item.row_start,
            row_end=bud_item.row_end,
            label=label,
            bullet=bullet,
            parent=parent,
        )

        parent_stack.append({
            'node': node,
            'level': bud_item.level,
        })

    return root


def page_x1(entries: List[LineItem]):
    """
    Given a list of LineItem objects, returns a dictionary mapping each page index to the maximum x1 value
    of all LineItems on that page.

    Args:
        entries (List[LineItem]): A list of LineItem objects.

    Returns:
        dict: A dictionary mapping each page index to the maximum x1 value of all LineItems on that page.
    """
    page_to_x1 = {}
    for entry in entries:
        page = entry.page_index
        if page not in page_to_x1:
            page_to_x1[page] = [entry.x1]
        else:
            page_to_x1[page].append(entry.x1)

    page_x1_dict = {}
    for page, x1s in page_to_x1.items():
        page_x1_dict[page] = max(x1s)

    return page_x1_dict
