from enum import Enum
from typing import List, Optional
from anytree import NodeMixin


class BudgetType(Enum):
    ROOT = 'ROOT'
    # กระทรวง/หน่วยงานเทียบเท่ากระทรวง
    MINISTRY = 'MINISTRY'
    # หน่วยรับงบประมาณ
    BUDGETARY_UNIT = 'BUDGETARY_UNIT'
    # แผนงาน
    BUDGET_PLAN = 'BUDGET_PLAN'
    # โครงการ
    PROJECT = 'PROJECT'
    # ผลผลิต
    OUTPUT = 'OUTPUT'
    # รายการงบ
    BUDGET_DETAIL = 'BUDGET_DETAIL'

def get_level_from_columns(columns):
    for column in columns:
        if column.startswith('name_'):
            return int(column.split('_')[1])
    raise ValueError(f'Cannot find level in {columns}')

class BudgetItem(NodeMixin):
    def __init__(
        self,
        budget_type: str,
        name: str,
        amount: Optional[float],
        document: str,
        page: int,
        parent: Optional['BudgetItem'] = None,
        children: Optional[List['BudgetItem']] = None,
        fiscal_year_budget: List['FiscalYearBudget'] = None,
    ):
        super().__init__()
        if isinstance(budget_type, BudgetType):
            self.budget_type = budget_type
        elif isinstance(budget_type, str):
            self.budget_type = BudgetType(budget_type)
        else:
            raise ValueError(f'budget_type must be BudgetType or str, got {type(budget_type)}')
        if not isinstance(name, str):
            raise ValueError(f'name must be str, got {type(name)}')
        
        if amount is not None and not isinstance(amount, (int, float)):
            raise ValueError(f'amount must be int or float, got {type(amount)}')
        
        if not isinstance(document, str):
            raise ValueError(f'document must be str, got {type(document)}')
        
        if not isinstance(page, int):
            raise ValueError(f'page must be int, got {type(page)}')
        
        if not isinstance(fiscal_year_budget, list) and fiscal_year_budget is not None:
            raise ValueError(f'fiscal_year_budget must be list, got {type(fiscal_year_budget)}')
        
        self.name = name
        self.amount = amount
        self.document = document
        self.page = page
        if fiscal_year_budget is None:
            self.fiscal_year_budget = list()
        else:
            self.fiscal_year_budget = fiscal_year_budget

        self.parent = parent

        if children:
            self.children = children
    
    def _check_sum(self):
        if self.amount is None:
            if any([
                child.amount is not None
                for child in self.children
            ]):
                raise ValueError(f'amount of {self.name} is None but some of children is not None')
            
            return
        if self.children:
            if any([
                child.amount is None
                for child in self.children
            ]):
                raise ValueError(f'amount of {self.name} is {self.amount} but some of children is None')
            
            sum_amount = sum([
                child.amount
                for child in self.children
            ])
            if self.amount != sum_amount:
                raise ValueError(f'amount of {self.name} is {self.amount} but sum of children is {sum_amount}')

    def __str__(self):
        return self.name

    def __repr__(self):
        return f'BudgetItem({self.budget_type.name}, {self.name}, {self.amount})'
    
    @classmethod
    def from_json(cls, json_obj):
        return cls(
            budget_type=BudgetType(json_obj['budget_type']),
            name=json_obj.get('name'),
            amount=json_obj.get('amount'),
            document=json_obj.get('document'),
            page=json_obj.get('page'),
            fiscal_year_budget=[
                FiscalYearBudget.from_json(fyb)
                for fyb in json_obj.get('fiscal_year_budget', list())
            ],
            children=[
                cls.from_json(child)
                for child in json_obj.get('children', list())
            ]
        )
    
    @classmethod
    def build_tree_by_rows(cls, rows) -> 'BudgetItem':
        if len(rows) == 0:
            return None
        
        ancestry_stack = [
            {
                'node': cls(
                    budget_type='ROOT',
                    name='ROOT',
                    amount=None,
                    document='',
                    page=0,
                ),
                'level': 0,
            }
        ]
        for row in rows:
            if row['budget_type'] == 'FISCAL_YEAR_BUDGET':
                if len(ancestry_stack) == 0 or ancestry_stack[-1]['level'] < 1:
                    raise ValueError('FISCAL_YEAR_BUDGET must have parent')

                curr_level = get_level_from_columns(row.keys())
                if 'fiscal_year' not in row.keys():
                    raise ValueError('row {} does not contain fiscal_year'.format(row))
                if 'fiscal_year_end' not in row.keys():
                    raise ValueError('row {} does not contain fiscal_year_end'.format(row))

                ancestry_stack[-1]['node'].fiscal_year_budget.append(
                    FiscalYearBudget(
                        line=row[f'name_{curr_level}'],
                        year=row['fiscal_year'],
                        year_end=row['fiscal_year_end'],
                        amount=row['amount'],
                        ))
                continue

            curr_level = get_level_from_columns(row.keys())

            while len(ancestry_stack) > 0 and ancestry_stack[-1]['level'] >= curr_level:
                ancestry_stack.pop()

            if len(ancestry_stack) == 0:
                parent = None
            else:
                parent = ancestry_stack[-1]['node']

            try:
                node = cls(
                    budget_type=row['budget_type'],
                    name=row[f'name_{curr_level}'],
                    amount=row.get('amount'),
                    document=row.get('document'),
                    page=row.get('page'),
                    parent=parent,
                )
            except ValueError as e:
                raise ValueError(f'Error while creating node from row {row}') from e

            ancestry_stack.append({
                'node': node,
                'level': curr_level,
            })

        root = ancestry_stack[0]['node']
        if root.budget_type.name != 'ROOT':
            raise ValueError('First row must be ROOT')
        
        if len(root.children) == 1:
            return root.children[0] # if there is only one child, return it
        
        return root
    
    def to_json(self):
        return {
            'budget_type': self.budget_type.name,
            'name': self.name,
            'amount': self.amount,
            'document': self.document,
            'page': self.page,
            'fiscal_year_budget': [
                fyb.to_json()
                for fyb in self.fiscal_year_budget
            ],
            'children': [
                child.to_json()
                for child in self.children
            ]
        }
    
    def _get_error_message(self):
        error_message = ''

        try:
            self._check_sum()
        except Exception as e:
            error_message += f'While checking sum: {e}\n'

        return error_message
    
    def to_rows(self, depth=1):
        rows = [{
            'error_message': self._get_error_message(),
            'budget_type': self.budget_type.name,
            f'name_{depth}': self.name,
            'amount': self.amount,
            'document': self.document,
            'page': self.page,
        }]

        for fyb in self.fiscal_year_budget:
            rows.append(fyb.to_row(depth))

        for child in self.children:
            rows.extend(child.to_rows(depth=depth+1))

        return rows

class FiscalYearBudget:
    """
    ข้อมูลงบผูกพันรายปี

    :param year: เลขปี
    :param year_end: หากว่าข้อมูลปีเป็นช่วงของปี
    :param amount: จำนวนงบ
    """

    def __init__(self, line: str, year: int, amount: float, year_end: Optional[int] = None):
        self.line = line
        self.year = year
        if year_end is not None:
            self.year_end = year_end
        else:
            self.year_end = year
        self.amount = amount

    def __str__(self):
        return f'{self.year} - {self.year_end}' if self.year != self.year_end else f'{self.year}'
    
    def __repr__(self):
        return f'FiscalYearBudget({self.year}, {self.year_end}, {self.amount})'
    
    @classmethod
    def from_json(cls, json_obj):
        return cls(
            line=json_obj['line'],
            year=json_obj['year'],
            year_end=json_obj.get('year_end'),
            amount=json_obj['amount'],
        )
    
    def to_json(self):
        return {
            'line': self.line,
            'year': self.year,
            'year_end': self.year_end,
            'amount': self.amount,
        }
    
    def to_row(self, depth=1):
        return {
            'error_message': '',
            'budget_type': 'FISCAL_YEAR_BUDGET',
            f'name_{depth}': self.line,
            'fiscal_year': self.year,
            'fiscal_year_end': self.year_end,
            'amount': self.amount,
        }
    