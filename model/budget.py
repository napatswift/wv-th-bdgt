from enum import Enum
from typing import List, Optional
from anytree import NodeMixin


class BudgetType(Enum):
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
        fiscal_year_budget: Optional[List['FiscalYearBudget']] = list(),
    ):
        super().__init__()
        if isinstance(budget_type, BudgetType):
            self.budget_type = budget_type
        elif isinstance(budget_type, str):
            self.budget_type = BudgetType(budget_type)
        else:
            raise ValueError(f'budget_type must be BudgetType or str, got {type(budget_type)}')
        
        self.name = name
        self.amount = amount
        self.document = document
        self.page = page
        self.fiscal_year_budget = fiscal_year_budget

        self.parent = parent

        if children:
            self.children = children

    def __str__(self):
        return self.budget_item.name

    def __repr__(self):
        return self.budget_item.name
    
    @classmethod
    def from_json(cls, json_obj):
        return cls(
            budget_type=BudgetType(json_obj['budget_type']),
            name=json_obj['name'],
            amount=json_obj.get('amount'),
            document=json_obj['document'],
            page=json_obj['page'],
            fiscal_year_budget=[
                FiscalYearBudget.from_json(fyb)
                for fyb in json_obj['fiscal_year_budget']
            ],
            children=[
                cls.from_json(child)
                for child in json_obj['children']
            ]
        )
    
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
    
    def to_table_rows(self):
        rows = [{
            'budget_type': self.budget_type.name,
            'name': self.name,
            'amount': self.amount,
            'document': self.document,
            'page': self.page,
        }]

        for fyb in self.fiscal_year_budget:
            rows.append(fyb.to_table_row())

        for child in self.children:
            rows.extend(child.to_table_rows())

        return rows

class FiscalYearBudget:
    """
    ข้อมูลงบผูกพันรายปี

    :param year: เลขปี
    :param year_end: หากว่าข้อมูลปีเป็นช่วงของปี
    :param amount: จำนวนงบ
    """

    def __init__(self, year: int, amount: float, year_end: Optional[int] = None):
        self.year = year
        self.year_end = year_end
        self.amount = amount
    
    @classmethod
    def from_json(cls, json_obj):
        return cls(
            year=json_obj['year'],
            year_end=json_obj.get('year_end'),
            amount=json_obj['amount'],
        )
    
    def to_json(self):
        return {
            'year': self.year,
            'year_end': self.year_end,
            'amount': self.amount,
        }
    
    def to_table_row(self):
        return {
            'budget_type': 'FISCAL_YEAR_BUDGET',
            'name': f'{self.year} - {self.year_end}' if self.year_end else f'{self.year}', # for reading
            'fiscal_year': self.year,
            'fiscal_year_end': self.year_end,
            'amount': self.amount,
        }
