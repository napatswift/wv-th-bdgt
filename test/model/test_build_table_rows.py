from thbud.model import BudgetItem, FiscalYearBudget, BudgetType

def test_build():
    node = BudgetItem(
        name='test',
        budget_type='MINISTRY',
        amount=1000,
        document='path/to/test.pdf',
        page=1,
    )

    row = node.to_rows()

    assert row == [
        {
            'error_message': '',
            'name_1': 'test',
            'budget_type': 'MINISTRY',
            'amount': 1000,
            'document': 'path/to/test.pdf',
            'page': 1,
        }
    ]

def test_build_with_fiscal_year_budgets():
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

    row = node.to_rows()

    assert row == [
        {
            'error_message': '',
            'name_1': 'test',
            'budget_type': 'MINISTRY',
            'amount': 1000,
            'document': 'path/to/test.pdf',
            'page': 1,
        },
        {
            'error_message': '',
            'name_1': '2563',
            'budget_type': 'FISCAL_YEAR_BUDGET',
            'amount': 1000,
            'fiscal_year': 2563,
            'fiscal_year_end': 2563,
        }
    ]

def test_build_with_2_fiscal_year_budgets():
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

    row = node.to_rows()

    assert row == [
        {
            'error_message': '',
            'name_1': 'test',
            'budget_type': 'MINISTRY',
            'amount': 1000,
            'document': 'path/to/test.pdf',
            'page': 1,
        },
        {
            'error_message': '',
            'name_1': '2563',
            'budget_type': 'FISCAL_YEAR_BUDGET',
            'amount': 1000,
            'fiscal_year': 2563,
            'fiscal_year_end': 2563,
        },
        {
            'error_message': '',
            'name_1': '2564',
            'budget_type': 'FISCAL_YEAR_BUDGET',
            'amount': 1000,
            'fiscal_year': 2564,
            'fiscal_year_end': 2564,
        }
    ]

def test_build_with_2_fiscal_year_budgets_with_different_amount():
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

    row = node.to_rows()

    assert row == [
        {
            'error_message': '',
            'name_1': 'test',
            'budget_type': 'MINISTRY',
            'amount': 1000,
            'document': 'path/to/test.pdf',
            'page': 1,
        },
        {
            'error_message': '',
            'name_1': '2563',
            'budget_type': 'FISCAL_YEAR_BUDGET',
            'amount': 1000,
            'fiscal_year': 2563,
            'fiscal_year_end': 2563,
        },
        {
            'error_message': '',
            'name_1': '2564',
            'budget_type': 'FISCAL_YEAR_BUDGET',
            'amount': 2000,
            'fiscal_year': 2564,
            'fiscal_year_end': 2564,
        }
    ]

def test_build_with_children():
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

    row = node.to_rows()

    assert row == [
        {
            'error_message': '',
            'name_1': 'test',
            'budget_type': 'MINISTRY',
            'amount': 1000,
            'document': 'path/to/test.pdf',
            'page': 1,
        },
        {
            'error_message': '',
            'name_2': 'test2',
            'budget_type': 'MINISTRY',
            'amount': 1000,
            'document': 'path/to/test.pdf',
            'page': 1,
        }
    ]

def test_build_with_children_depth_more_than_one():
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

    row = node.to_rows()

    assert row == [
        {
            'error_message': '',
            'name_1': 'test',
            'budget_type': 'MINISTRY',
            'amount': 1000,
            'document': 'path/to/test.pdf',
            'page': 1,
        },
        {
            'error_message': '',
            'name_2': 'test2',
            'budget_type': 'MINISTRY',
            'amount': 1000,
            'document': 'path/to/test.pdf',
            'page': 1,
        },
        {
            'error_message': '',
            'name_3': 'test3',
            'budget_type': 'MINISTRY',
            'amount': 1000,
            'document': 'path/to/test.pdf',
            'page': 1,
        }
    ]

def test_build_with_child_that_has_fiscal_year():
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

    row = root.to_rows()

    assert row == [
        {
            'error_message': '',
            'name_1': 'root',
            'budget_type': 'MINISTRY',
            'amount': 1000,
            'document': 'path/to/test.pdf',
            'page': 1,
        },
        {
            'error_message': '',
            'name_2': 'child',
            'budget_type': 'MINISTRY',
            'amount': 1000,
            'document': 'path/to/test.pdf',
            'page': 1,
        },
        {
            'error_message': '',
            'name_2': '2563',
            'budget_type': 'FISCAL_YEAR_BUDGET',
            'amount': 1000,
            'fiscal_year': 2563,
            'fiscal_year_end': 2563,
        }
    ]

def test_should_add_error_message_when_sum_of_children_amount_is_not_equal_to_parent_amount():
    root = BudgetItem(
        name='root',
        budget_type='MINISTRY',
        amount=1000,
        document='path/to/test.pdf',
        page=1,
        children=[
            BudgetItem(
                name='child1',
                budget_type='MINISTRY',
                amount=1000,
                document='path/to/test.pdf',
                page=1,
            ),
            BudgetItem(
                name='child2',
                budget_type='MINISTRY',
                amount=1000,
                document='path/to/test.pdf',
                page=1,
            ),
        ]
    )

    row = root.to_rows()

    assert row == [
        {
            'error_message': 'While checking sum: amount of root is 1000 but sum of children is 2000\n',
            'name_1': 'root',
            'budget_type': 'MINISTRY',
            'amount': 1000,
            'document': 'path/to/test.pdf',
            'page': 1,
        },
        {
            'error_message': '',
            'name_2': 'child1',
            'budget_type': 'MINISTRY',
            'amount': 1000,
            'document': 'path/to/test.pdf',
            'page': 1,
        },
        {
            'error_message': '',
            'name_2': 'child2',
            'budget_type': 'MINISTRY',
            'amount': 1000,
            'document': 'path/to/test.pdf',
            'page': 1,
        }
    ]

def test_should_add_error_message_when_some_of_children_amount_is_none():
    root = BudgetItem(
        name='root',
        budget_type='MINISTRY',
        amount=1000,
        document='path/to/test.pdf',
        page=1,
        children=[
            BudgetItem(
                name='child1',
                budget_type='MINISTRY',
                amount=1000,
                document='path/to/test.pdf',
                page=1,
            ),
            BudgetItem(
                name='child2',
                budget_type='MINISTRY',
                amount=None,
                document='path/to/test.pdf',
                page=1,
            ),
        ]
    )

    row = root.to_rows()

    assert row == [
        {
            'error_message': 'While checking sum: amount of root is 1000 but some of children is None\n',
            'name_1': 'root',
            'budget_type': 'MINISTRY',
            'amount': 1000,
            'document': 'path/to/test.pdf',
            'page': 1,
        },
        {
            'error_message': '',
            'name_2': 'child1',
            'budget_type': 'MINISTRY',
            'amount': 1000,
            'document': 'path/to/test.pdf',
            'page': 1,
        },
        {
            'error_message': '',
            'name_2': 'child2',
            'budget_type': 'MINISTRY',
            'amount': None,
            'document': 'path/to/test.pdf',
            'page': 1,
        }
    ]

def test_should_add_error_message_when_parent_amount_is_none_and_children_amount_is_not_none():
    root = BudgetItem(
        name='root',
        budget_type='MINISTRY',
        amount=None,
        document='path/to/test.pdf',
        page=1,
        children=[
            BudgetItem(
                name='child1',
                budget_type='MINISTRY',
                amount=1000,
                document='path/to/test.pdf',
                page=1,
            ),
            BudgetItem(
                name='child2',
                budget_type='MINISTRY',
                amount=1000,
                document='path/to/test.pdf',
                page=1,
            ),
        ]
    )

    row = root.to_rows()

    assert row == [
        {
            'error_message': 'While checking sum: amount of root is None but some of children is not None\n',
            'name_1': 'root',
            'budget_type': 'MINISTRY',
            'amount': None,
            'document': 'path/to/test.pdf',
            'page': 1,
        },
        {
            'error_message': '',
            'name_2': 'child1',
            'budget_type': 'MINISTRY',
            'amount': 1000,
            'document': 'path/to/test.pdf',
            'page': 1,
        },
        {
            'error_message': '',
            'name_2': 'child2',
            'budget_type': 'MINISTRY',
            'amount': 1000,
            'document': 'path/to/test.pdf',
            'page': 1,
        }
    ]