from enum import Enum
from typing import List, Optional


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


class BudgetItem:
    """
    ข้อมูลรายการงบประมาณ

    :param budget_type: ประเภทงบ
    :param name: รายละเอียดของรายการงบ
    :param amount: จำนวนงบ หรือ None หากว่างบเป็น `-`
    :param document: file path
    :param page: เลขหน้า
    :param children: รายการงบใต้รายการปัจจุบัน
    :param fiscal_year_budget: งบผูกพัน
    """

    def __init__(
        self,
        budget_type: BudgetType,
        name: str,
        amount: Optional[float],
        document: str,
        page: int,
        children: Optional[List['BudgetItem']],
        fiscal_year_budget: Optional[List['FiscalYearBudget']],
    ):
        self.budget_type = budget_type
        self.name = name
        self.amount = amount
        self.document = document
        self.page = page
        self.children = children
        self.fiscal_year_budget = fiscal_year_budget

    @classmethod
    def from_json(cls, json):
        fiscal_year_budget = json.get('fiscal_year_budget', list())
        children = json.get('children', list())
        return cls(
            budget_type=BudgetType(json['budget_type']),
            name=json['name'],
            amount=json['amount'],
            document=json['document'],
            page=json['page'],
            children=[cls.from_json(child) for child in children],
            fiscal_year_budget=[
                FiscalYearBudget.from_json(fyb) for fyb in fiscal_year_budget
            ],
        )


class FiscalYearBudget:
    """
    ข้อมูลงบผูกพันรายปี

    :param year: เลขปี
    :param year_end: หากว่าข้อมูลปีเป็นช่วงของปี
    :param amount: จำนวนงบ
    """

    def __init__(self, year: int, year_end: Optional[int], amount: float):
        self.year = year
        self.year_end = year_end
        self.amount = amount
    
    @classmethod
    def from_json(cls, json):
        return cls(
            year=json['year'],
            year_end=json.get('year_end'),
            amount=json['amount'],
        )
