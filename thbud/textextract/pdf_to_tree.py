from typing import List, Tuple

from ..textextract import DocumentText, PageText, LineText
from ..model import BudgetItem, FiscalYearBudget
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

    def __str__(self) -> str:
        return ''.join(
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


def get_year_from_string(text: str) -> Tuple[int, int]:
    # ปี 2563 ตั�งงบประมาณ 616,834,700 บาท -> 2563, 2563
    # ปี 2563-2564 ตั�งงบประมาณ 616,834,700 บาท -> 2563, 2564
    pattern = r'ปี (\d{4})(?:-(\d{4}))?'

    match = re.search(pattern, text)
    if match:
        if match.group(2):
            return int(match.group(1)), int(match.group(2))
        else:
            return int(match.group(1)), int(match.group(1))
    else:
        return 0, 0

def get_patern_of_bullet(String):
    regx = [('[1-9][0-9]*(\.[1-9][0-9]*)*\)$', 20),
            ('\(\d*(\.?\d*)*\)$', 50),
            ('[1-9][0-9]*(\.[1-9][0-9]*)+$', 2),
            ('[1-9][0-9]*\.$', 1),
            ('[1-9][0-9]*$', 30)]

    for r, l in regx:
        if re.match(r, String):
            if l in [2, 20, 50]:
                l = String.count('.') + l
            return r, l
    return '', 0


def is_classifier(string):
    return string in ['แห่ง', 'สายทาง']


def is_redundant_line(line_text: List[str]):
    return (
        not line_text
        or 'รายละเอียดงบประมาณจำแนกตามงบรายจ่าย' in line_text
        or 'รายละเอียดงบประมาณจําแนกตามงบรายจ่าย' in line_text
        or 'รายการบุคลากรภาครัฐ' in line_text
        or 'วงเงินทั้งสิ้น' in line_text
        or 'วงเงินทั�งสิ�น' in line_text
        or 'รายละเอียดงบประมาณรายจ่ายจำแนกตามแผนงาน' in line_text)


def get_entries(lines: List[LineText]):
    # flags
    bullet_flag = False
    # project and output flag
    proj_outp_flag = False
    # budget place holder
    budget_plan = ''

    entry = []
    entries = []
    for i, line in enumerate(lines):
        line_id = line
        # #skip page number
        # if i[1] == 1: continue

        # joint line together
        line_text = str(line)

        if line_text == 'i ||| .':
            continue
        if line_text.isdigit():
            continue
        if line_text == '3. รายละเอียดงบประมาณ':
            continue

        # then split by whitespace
        line_text = line_text.split()

        # skiping
        if is_redundant_line(line_text):
            continue

        # budget plan
        if line.page.contains_table:
            if re.match(r'7.\d+$', line_text[0]) or (len(line_text) > 1 and line_text[1].startswith('แผนงาน')):
                entries.append(('budget_plan', [line_id]))
            continue

        patern_of_bullet = get_patern_of_bullet(line_text[0])
        if re.match(r'ป?ี \d{4} ', ' '.join(line_text)):
            entries.append(('fiscal_year', [line_id]))

            # DEBUG
            logger.debug('get_entries::`{}` is fiscal year'.format(line))
            continue

        if patern_of_bullet[1] and (len(line_text) > 1 and not is_classifier(line_text[1])):
            bullet_flag = True

            # DEBUG
            logger.debug('get_entries::`{}` is bullet'.format(line))

        if line_text[0].replace(':', '') == 'ผลผลิต' or (len(line_text) > 1 and line_text[1].replace(':', '') in 'ผลผลิต'):
            proj_outp_flag = 'OUTPUT'
        
        if line_text[0].replace(':', '') == 'โครงการ' or (len(line_text) > 1 and line_text[1].replace(':', '') in 'โครงการ'):
            proj_outp_flag = 'PROJECT'

        if proj_outp_flag:
            # DEBUG
            logger.debug('get_entries::`{}` is proj/outp'.format(line))

        if bullet_flag or proj_outp_flag:
            entry.append(line_id)
            if line_text[-1].replace('-', '') == 'บาท':
                entries.append(('item' if bullet_flag else proj_outp_flag, entry))
                bullet_flag = False
                proj_outp_flag = False
                entry = []
        else:
            if line_text[0].startswith('เงินนอกงบประมาณ'):
                continue

            # logger.debug('SKIPPED', 'page', line.page.page_index,
            #              'line', line.line.line_index, '👉🏽', *line_text)
    return [
        LineItem(t, lines) for t, lines in entries
    ]


def extract_tree_levels(bud_items: List[LineItem], x_diff_threshold=0.005) -> BudgetItem:
    """
    Extracts the levels of the budget units.
    The levels are extracted by looking at the x0 positions of the budget units.
    """

    # stores min x position
    stack_x = []

    page_end_x_sr = page_x1(bud_items)
    page_x1_max = max(page_end_x_sr.values())

    for bud_item in bud_items:
        # LOGGING
        logger.debug(f'extract_tree_levels::{(bud_item)}')

        if bud_item.itemtype != 'item':
            # If the budget unit is not an item, then it is a budget unit header.
            # In this case, we clear the stack and add a new level to the levels list.
            if bud_item.itemtype in ['budget_plan', 'PROJECT', 'OUTPUT']:
                stack_x = []
            
            if bud_item.itemtype == 'budget_plan':
                bud_item.set_level(-2)
            elif bud_item.itemtype == 'PROJECT' or bud_item.itemtype == 'OUTPUT':
                bud_item.set_level(-1)

            continue

        # pex is the x position of the end of the page that the budget unit is on.
        pex = page_end_x_sr[bud_item.page_index]

        # LOGGING
        logger.debug(
            'extract_tree_levels::page x1 max: {}'.format(page_x1_max))

        # lsx is the x position of the start of the first line of the budget unit.
        lsx = bud_item.x0 + (page_x1_max - pex)

        # LOGGING
        logger.debug(
            'extract_tree_levels::line x0: bud_item.x0={} + (page_x1_max={} - pex={}) = {}'
            .format(bud_item.x0, page_x1_max, pex, lsx))

        # If the previous item has an x position that is more than the threshold greater than this item's x position,
        # then we pop the previous item off the stack.
        while len(stack_x) and stack_x[-1] > lsx + x_diff_threshold:
            stack_x.pop()

        # If the stack is empty or the difference between the x positions of the current item and the item at the top of the stack
        # is greater than the threshold, then we push the current item's x position onto the stack.
        if len(stack_x) == 0 or abs(stack_x[-1] - lsx) >= x_diff_threshold:
            stack_x.append(lsx)

        # The level of the current item is the length of the stack.
        bud_item.set_level(len(stack_x))

        # LOGGING
        logger.debug('extract_tree_levels::level: {}'.format(bud_item.level))


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
                    year=year_start,
                    amount=get_amount_from_string(str(bud_item)),
                    year_end=year_end,
                )
            )
            continue

        while len(parent_stack) > 0 and parent_stack[-1]['level'] >= bud_item.level:
            parent_stack.pop()

        if len(parent_stack) == 0:
            parent = None
        
        else:
            parent = parent_stack[-1]['node']

        node = BudgetItem(
            budget_type=itemtype_mapper[bud_item.itemtype],
            name=str(bud_item),
            amount=get_amount_from_string(str(bud_item)),
            document=bud_item.document,
            page=bud_item.page_index,
            parent=parent,
        )

        parent_stack.append({
            'node': node,
            'level': bud_item.level,
        })
    
    if len(root.children) == 1:
        return root.children[0]
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
