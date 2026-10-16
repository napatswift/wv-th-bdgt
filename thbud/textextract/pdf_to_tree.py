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
    def __init__(self, itemtype: str, lines: List['LineText']):
        self.itemtype = itemtype
        self.lines = lines
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
        return min(line.x0 for line in self.lines)

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
    return get_amount_from_string(' '.join(str(line) for line in lines))


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
    """
    tokens = str(line).split()
    if tokens and tokens[-1].replace('-', '').replace('*', '') == 'บาท':
        return True
    return any(is_baht_marker(w.text) for w in line.words)


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
            (r'[1-9][0-9]*$', 30)]

    for r, l in regx:
        if re.match(r, String):
            if l in [2, 20, 50]:
                l = String.count('.') + l
            return r, l
    return '', 0


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


def is_redundant_line(line_text: List[str]):
    if not line_text or ' '.join(line_text).isdigit():
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


def get_entries(lines: List[LineText]):
    # flags
    bullet_flag = False
    # project and output flag
    proj_outp_flag = False

    entry = []
    entries = []
    for i, line in enumerate(lines):
        line_id = line

        # joint line together
        line_text_string = str(line)

        # then split by whitespace
        line_text = line_text_string.split()

        # skiping
        if is_redundant_line(line_text):
            continue

        # budget plan
        if line.page.contains_table:
            if re.match(r'7.\d+$', line_text[0]) or (
                len(line_text) > 1 and line_text[1].startswith('แผนงาน')
            ):
                entries.append(('budget_plan', [line_id]))
            continue

        patern_of_bullet = get_patern_of_bullet(line_text[0])

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
                'เงินนอกงบประมาณ' in line_text
                    or 'เงินน�กงบประมาณ' in line_text
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

    return [
        LineItem(t, lines) for t, lines in entries
    ]


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
            if bud_item.itemtype in ['budget_plan', 'PROJECT', 'OUTPUT']:
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
    toks = str(bud_item).split()
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
        x0-nearest tiebreak for numbering gaps) -> becomes its sibling
      - parent anchor: a stack entry whose components equal the item's components
        minus the last one ('2.1.1' under '2.1') -> becomes its child
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
            if bud_item.itemtype in ('budget_plan', 'PROJECT', 'OUTPUT'):
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
                    sib_idx = plus1[0]
                else:
                    sib_idx = min(sib_cands, key=lambda d: abs(stack[d][2] - lsx))
            if sib_idx is not None and (par_idx is None or par_idx < sib_idx):
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
        category at the SAME x -> the activity is its child (+0.5); a following
        activity at that x after such a child inherits the shift (its sibling);
      - activity-first: otherwise, if the next item at the same-or-lower x is a
        category at the same x -> the activity is the parent of those (-0.5);
      - an activity printed deeper, inside the items of such a nested activity
        (at the '(N)' indent), is moved up beside it: a กิจกรรม is never the
        child of another กิจกรรม.
    Neighbours are looked up within the activity's header segment. Returns
    {entry index: dx}; empty when no activity row is printed this way."""
    eps = 0.005
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
                shifts[i] = +0.5
                nested.add(i)
            elif enclosing(i) in nested:
                # printed at the indent of a nested activity's own items
                nest_beside(i, enclosing(i))
        elif same_x_category(i, neighbour(i, +1)):
            shifts[i] = -0.5
    return shifts


def _sum_violations(item_idxs, levels, amounts):
    """# of parents (within one header segment, parentage from `levels` by the
    nearest-smaller rule) whose amount differs from the sum of their children's."""
    children = {}
    stack = []  # (idx, level)
    for i in item_idxs:
        while stack and stack[-1][1] >= levels[i]:
            stack.pop()
        if stack:
            children.setdefault(stack[-1][0], []).append(i)
        stack.append((i, levels[i]))
    bad = 0
    for p, kids in children.items():
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

    amounts = {j: get_amount_from_lines(entries[j].lines) for j in segment}

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

        node = BudgetItem(
            budget_type=itemtype_mapper[bud_item.itemtype],
            name=str(bud_item).replace('\n', '\t').strip(),
            amount=get_amount_from_lines(bud_item.lines),
            document=bud_item.document,
            page=bud_item.page_index,
            row_start=bud_item.row_start,
            row_end=bud_item.row_end,
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
