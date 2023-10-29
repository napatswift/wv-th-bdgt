from model import BudgetItem, FiscalYearBudget, BudgetType


def test_create_node():
  node = BudgetItem(
    name='test',
    budget_type='MINISTRY',
    amount=1000,
    document='path/to/test.pdf',
    page=1,
  )

  assert node.name == 'test'
  assert node.budget_type == BudgetType('MINISTRY')
  assert node.amount == 1000
  assert node.document == 'path/to/test.pdf'
  assert node.page == 1

def test_create_node_with_children():
  node = BudgetItem(
    name='test',
    budget_type='MINISTRY',
    amount=1000,
    document='path/to/test.pdf',
    page=1,
    children=[
      BudgetItem(
        name='child',
        budget_type='BUDGETARY_UNIT',
        amount=1000,
        document='path/to/test.pdf',
        page=1,
      )
    ]
  )

  assert node.name == 'test'
  assert node.budget_type == BudgetType('MINISTRY')
  assert node.amount == 1000
  assert node.document == 'path/to/test.pdf'
  assert node.page == 1
  assert node.children is not None
  assert len(node.children) == 1
  assert node.children[0].name == 'child'
  assert node.children[0].budget_type == BudgetType('BUDGETARY_UNIT')
  assert node.children[0].amount == 1000
  assert node.children[0].document == 'path/to/test.pdf'
  assert node.children[0].page == 1

def test_create_node_with_fiscal_year_budget():
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

  assert node.name == 'test'
  assert node.budget_type == BudgetType('MINISTRY')
  assert node.amount == 1000
  assert node.document == 'path/to/test.pdf'
  assert node.page == 1
  assert node.fiscal_year_budget is not None
  assert len(node.fiscal_year_budget) == 1
  assert node.fiscal_year_budget[0].year == 2563
  assert node.fiscal_year_budget[0].amount == 1000

def test_should_raise_value_error_when_budget_type_is_invalid():
  try:
    BudgetItem(
      name='test',
      budget_type='INVALID',
      amount=1000,
      document='path/to/test.pdf',
      page=1,
    )
    assert False
  except ValueError:
    assert True
  
def test_generate_json():
  node = BudgetItem(
    name='test',
    budget_type='MINISTRY',
    amount=1000,
    document='path/to/test.pdf',
    page=1,
  )

  json_obj = node.to_json()

  assert json_obj == {
    'name': 'test',
    'budget_type': 'MINISTRY',
    'amount': 1000,
    'document': 'path/to/test.pdf',
    'page': 1,
    'fiscal_year_budget': [],
    'children': [],
  }

def test_generate_json_with_children():
  node = BudgetItem(
    name='test',
    budget_type='MINISTRY',
    amount=1000,
    document='path/to/test.pdf',
    page=1,
    children=[
      BudgetItem(
        name='child',
        budget_type='BUDGETARY_UNIT',
        amount=1000,
        document='path/to/test.pdf',
        page=1,
      )
    ]
  )

  json_obj = node.to_json()

  assert json_obj == {
    'name': 'test',
    'budget_type': 'MINISTRY',
    'amount': 1000,
    'document': 'path/to/test.pdf',
    'page': 1,
    'fiscal_year_budget': [],
    'children': [
      {
        'name': 'child',
        'budget_type': 'BUDGETARY_UNIT',
        'amount': 1000,
        'document': 'path/to/test.pdf',
        'page': 1,
        'fiscal_year_budget': [],
        'children': [],
      }
    ],
  }

def test_generate_json_with_fiscal_year_budget():
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

  json_obj = node.to_json()

  assert json_obj == {
    'name': 'test',
    'budget_type': 'MINISTRY',
    'amount': 1000,
    'document': 'path/to/test.pdf',
    'page': 1,
    'fiscal_year_budget': [
      {
        'year': 2563,
        'amount': 1000,
        'year_end': None,
      }
    ],
    'children': [],
  }

def test_generate_json_with_children_and_fiscal_year_budget():
  node = BudgetItem(
    name='test',
    budget_type='MINISTRY',
    amount=1000,
    document='path/to/test.pdf',
    page=1,
    children=[
      BudgetItem(
        name='child',
        budget_type='BUDGETARY_UNIT',
        amount=1000,
        document='path/to/test.pdf',
        page=1,
      )
    ],
    fiscal_year_budget=[
      FiscalYearBudget(
        year=2563,
        amount=1000,
      )
    ]
  )

  json_obj = node.to_json()

  assert json_obj == {
    'name': 'test',
    'budget_type': 'MINISTRY',
    'amount': 1000,
    'document': 'path/to/test.pdf',
    'page': 1,
    'fiscal_year_budget': [
      {
        'year': 2563,
        'amount': 1000,
        'year_end': None,
      }
    ],
    'children': [
      {
        'name': 'child',
        'budget_type': 'BUDGETARY_UNIT',
        'amount': 1000,
        'document': 'path/to/test.pdf',
        'page': 1,
        'fiscal_year_budget': [],
        'children': [],
      }
    ],
  }

def test_generate_table_rows():
  node = BudgetItem(
    name='test',
    budget_type='MINISTRY',
    amount=1000,
    document='path/to/test.pdf',
    page=1,
  )

  rows = node.to_table_rows()

  assert rows == [
    {
      'name': 'test',
      'budget_type': 'MINISTRY',
      'amount': 1000,
      'document': 'path/to/test.pdf',
      'page': 1,
    }
  ]

def test_generate_table_rows_with_children():
  node = BudgetItem(
    name='test',
    budget_type='MINISTRY',
    amount=1000,
    document='path/to/test.pdf',
    page=1,
    children=[
      BudgetItem(
        name='child',
        budget_type='BUDGETARY_UNIT',
        amount=1000,
        document='path/to/test.pdf',
        page=1,
      )
    ]
  )

  rows = node.to_table_rows()

  assert rows == [
    {
      'name': 'test',
      'budget_type': 'MINISTRY',
      'amount': 1000,
      'document': 'path/to/test.pdf',
      'page': 1,
    },
    {
      'name': 'child',
      'budget_type': 'BUDGETARY_UNIT',
      'amount': 1000,
      'document': 'path/to/test.pdf',
      'page': 1,
    }
  ]

def test_generate_table_rows_with_fiscal_year_budget():
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

  rows = node.to_table_rows()

  assert rows == [
    {
      'name': 'test',
      'budget_type': 'MINISTRY',
      'amount': 1000,
      'document': 'path/to/test.pdf',
      'page': 1,
    },
    {
      'name': '2563',
      'budget_type': 'FISCAL_YEAR_BUDGET',
      'amount': 1000,
      'fiscal_year': 2563,
      'fiscal_year_end': None,
    }
  ]