from .model import BudgetItem, BudgetType
from anytree import PreOrderIter
import re

def build_csv(root: BudgetItem):
    """
    Build a list of dictionaries from a BudgetItem tree. Only leaf nodes are
    included in the result.
    """
    result = []

    for node in PreOrderIter(root):
        if node.is_leaf:
            row = dict(
                REF_DOC=node.document,
                REF_PAGE_NO=node.page,
                ITEM_DESCRIPTION=node.name,
                AMOUNT=node.amount,
                OUTPUT='',
                PROJECT='',
                FISCAL_YEAR=None,
            )

            row['OBLIGED?'] = len(node.fiscal_year_budget) > 0

            curr = node.parent
            categories = []
            while curr is not None:
                if curr.budget_type == BudgetType.MINISTRY:
                    row['MINISTRY'] = curr.name

                if curr.budget_type == BudgetType.BUDGETARY_UNIT:
                    row['BUDGETARY_UNIT'] = curr.name

                if curr.budget_type == BudgetType.BUDGET_PLAN:
                    row['BUDGET_PLAN'] = curr.name
                    row['CROSS_FUNC?'] = curr.name.startswith('แผนงานบูรณาการ')

                if curr.budget_type == BudgetType.PROJECT:
                    row['PROJECT'] = curr.name

                if curr.budget_type == BudgetType.OUTPUT:
                    row['OUTPUT'] = curr.name

                if curr.budget_type == BudgetType.BUDGET_DETAIL:
                    categories.append(curr.name)

                curr = curr.parent

            for i, category in enumerate(reversed(categories)):
                row[f'CATEGORY_LV{i+1}'] = category

            if len(node.fiscal_year_budget) > 0:
                for fy_node in node.fiscal_year_budget:
                    total_year = fy_node.year_end - fy_node.year
                    for year in range(fy_node.year, fy_node.year_end+1):
                        copy_row = row.copy()
                        copy_row['FISCAL_YEAR'] = year
                        copy_row['AMOUNT'] = fy_node.amount / max(1, total_year)
                        result.append(copy_row)
            else:
                result.append(row)

    return result

def extract_budget_item_name(line_string: str, double_amount: bool = False):
    if line_string.startswith('ผลผลิต :'):
        line_string = line_string[9:]

    line_string = re.sub(r'([0-9\.]+\s+)?ผลผลิต(ที่)?\s+(\d+\s+)?:', '', line_string)

    if line_string.startswith('โครงการ :'):
        line_string = line_string[9:]

    line_string = re.sub(r'([0-9\.]+\s+)?โครงการ(ที่)?\s+(\d+\s+)?:', '', line_string)

    # remove bullet
    regex_bullet = r'^[\d\s\(\)\. ]+'
    if re.match(regex_bullet, line_string):
        line_string = re.sub(regex_bullet, '', line_string)

    # remove amount
    line_string = line_string.rsplit('$', 1)[0].strip()
    regex_amount = r' ([\d,]+|-) บาท( บาท)*'
    if double_amount:
        regex_amount = r' ?([\d,]+|-)?' + regex_amount
    line_string = re.sub(regex_amount, '', line_string)

    line_string = re.sub(r'^[\*\-\.:\)\s]+', '', line_string)
    line_string = re.sub(r'[\*\-\.:\(\s]$', '', line_string)
    return line_string.strip()