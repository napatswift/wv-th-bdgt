from model import BudgetItem, FiscalYearBudget, BudgetType

def test_build_table_row():
    node = BudgetItem(
        name='test',
        budget_type='MINISTRY',
        amount=1000,
        document='path/to/test.pdf',
        page=1,
    )

    row = node.to_table_rows()

    assert row == [
        {
            'name_1': 'test',
            'budget_type': 'MINISTRY',
            'amount': 1000,
            'document': 'path/to/test.pdf',
            'page': 1,
        }
    ]

def test_build_table_row_with_fiscal_year_budgets():
    node = BudgetItem(
        name='test',
        budget_type='MINISTRY',
        amount=1000,
        document='path/to/test.pdf',
        page=1,
        fiscal_year_budget=[
            FiscalYearBudget(
                year=2563,
                amount=1000,
            )
        ]
    )

    row = node.to_table_rows()

    assert row == [
        {
            'name_1': 'test',
            'budget_type': 'MINISTRY',
            'amount': 1000,
            'document': 'path/to/test.pdf',
            'page': 1,
        },
        {
            'name_1': '2563',
            'budget_type': 'FISCAL_YEAR_BUDGET',
            'amount': 1000,
            'fiscal_year': 2563,
            'fiscal_year_end': 2563,
        }
    ]

def test_build_table_row_with_2_fiscal_year_budgets():
    node = BudgetItem(
        name='test',
        budget_type='MINISTRY',
        amount=1000,
        document='path/to/test.pdf',
        page=1,
        fiscal_year_budget=[
            FiscalYearBudget(
                year=2563,
                amount=1000,
            ),
            FiscalYearBudget(
                year=2564,
                amount=1000,
            )
        ]
    )

    row = node.to_table_rows()

    assert row == [
        {
            'name_1': 'test',
            'budget_type': 'MINISTRY',
            'amount': 1000,
            'document': 'path/to/test.pdf',
            'page': 1,
        },
        {
            'name_1': '2563',
            'budget_type': 'FISCAL_YEAR_BUDGET',
            'amount': 1000,
            'fiscal_year': 2563,
            'fiscal_year_end': 2563,
        },
        {
            'name_1': '2564',
            'budget_type': 'FISCAL_YEAR_BUDGET',
            'amount': 1000,
            'fiscal_year': 2564,
            'fiscal_year_end': 2564,
        }
    ]

def test_build_table_row_with_2_fiscal_year_budgets_with_different_amount():
    node = BudgetItem(
        name='test',
        budget_type='MINISTRY',
        amount=1000,
        document='path/to/test.pdf',
        page=1,
        fiscal_year_budget=[
            FiscalYearBudget(
                year=2563,
                amount=1000,
            ),
            FiscalYearBudget(
                year=2564,
                amount=2000,
            )
        ]
    )

    row = node.to_table_rows()

    assert row == [
        {
            'name_1': 'test',
            'budget_type': 'MINISTRY',
            'amount': 1000,
            'document': 'path/to/test.pdf',
            'page': 1,
        },
        {
            'name_1': '2563',
            'budget_type': 'FISCAL_YEAR_BUDGET',
            'amount': 1000,
            'fiscal_year': 2563,
            'fiscal_year_end': 2563,
        },
        {
            'name_1': '2564',
            'budget_type': 'FISCAL_YEAR_BUDGET',
            'amount': 2000,
            'fiscal_year': 2564,
            'fiscal_year_end': 2564,
        }
    ]

def test_build_table_row_with_children():
    node = BudgetItem(
        name='test',
        budget_type='MINISTRY',
        amount=1000,
        document='path/to/test.pdf',
        page=1,
        children=[
            BudgetItem(
                name='test2',
                budget_type='MINISTRY',
                amount=1000,
                document='path/to/test.pdf',
                page=1,
            )
        ]
    )

    row = node.to_table_rows()

    assert row == [
        {
            'name_1': 'test',
            'budget_type': 'MINISTRY',
            'amount': 1000,
            'document': 'path/to/test.pdf',
            'page': 1,
        },
        {
            'name_2': 'test2',
            'budget_type': 'MINISTRY',
            'amount': 1000,
            'document': 'path/to/test.pdf',
            'page': 1,
        }
    ]

def test_build_table_row_with_children_depth_more_than_one():
    node = BudgetItem(
        name='test',
        budget_type='MINISTRY',
        amount=1000,
        document='path/to/test.pdf',
        page=1,
        children=[
            BudgetItem(
                name='test2',
                budget_type='MINISTRY',
                amount=1000,
                document='path/to/test.pdf',
                page=1,
                children=[
                    BudgetItem(
                        name='test3',
                        budget_type='MINISTRY',
                        amount=1000,
                        document='path/to/test.pdf',
                        page=1,
                    )
                ]
            ),
        ]
    )

    row = node.to_table_rows()

    assert row == [
        {
            'name_1': 'test',
            'budget_type': 'MINISTRY',
            'amount': 1000,
            'document': 'path/to/test.pdf',
            'page': 1,
        },
        {
            'name_2': 'test2',
            'budget_type': 'MINISTRY',
            'amount': 1000,
            'document': 'path/to/test.pdf',
            'page': 1,
        },
        {
            'name_3': 'test3',
            'budget_type': 'MINISTRY',
            'amount': 1000,
            'document': 'path/to/test.pdf',
            'page': 1,
        }
    ]

def test_build_table_row_with_child_that_has_fiscal_year():
    root = BudgetItem(
        name='root',
        budget_type='MINISTRY',
        amount=1000,
        document='path/to/test.pdf',
        page=1,
        children=[
            BudgetItem(
                name='child',
                budget_type='MINISTRY',
                amount=1000,
                document='path/to/test.pdf',
                page=1,
                fiscal_year_budget=[
                    FiscalYearBudget(
                        year=2563,
                        amount=1000,
                    )
                ]
            ),
        ]
    )

    row = root.to_table_rows()

    assert row == [
        {
            'name_1': 'root',
            'budget_type': 'MINISTRY',
            'amount': 1000,
            'document': 'path/to/test.pdf',
            'page': 1,
        },
        {
            'name_2': 'child',
            'budget_type': 'MINISTRY',
            'amount': 1000,
            'document': 'path/to/test.pdf',
            'page': 1,
        },
        {
            'name_2': '2563',
            'budget_type': 'FISCAL_YEAR_BUDGET',
            'amount': 1000,
            'fiscal_year': 2563,
            'fiscal_year_end': 2563,
        }
    ]