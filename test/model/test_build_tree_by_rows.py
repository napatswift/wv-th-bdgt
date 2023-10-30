from model import BudgetItem
from model.budget import get_level_from_columns

import pytest

def test_single_column_with_level_0():
    # Test case 1: Single column with level 0
    columns = ['name_0']
    assert get_level_from_columns(columns) == 0

def test_single_column_with_level_1():
    # Test case 2: Multiple columns with level 1
    columns = ['other_column', 'name_1', 'another_column']
    assert get_level_from_columns(columns) == 1
    
def test_multiple_columns_with_level_2():
    # Test case 3: Multiple columns with level 2
    columns = ['other_column', 'name_2', 'another_column']
    assert get_level_from_columns(columns) == 2
    
def test_no_columns_with_name_prefix():
    # Test case 4: No columns with 'name_' prefix
    columns = ['other_column', 'another_column']
    try:
        get_level_from_columns(columns)
    except ValueError as e:
        assert str(e) == "Cannot find level in ['other_column', 'another_column']"

def test_build_single_node():
  rows = [
    {
      'budget_type': 'MINISTRY',
      'name_1': 'Ministry of Finance',
      'amount': 1000,
      'document': 'path/to/test.pdf',
      'page': 1,
    }
  ]

  root = BudgetItem.build_tree_by_rows(rows)

  assert root.budget_type.name == 'MINISTRY'
  assert root.name == 'Ministry of Finance'
  assert root.amount == 1000
  assert root.document == 'path/to/test.pdf'
  assert root.page == 1
  assert len(root.children) == 0

def test_build_tree_with_children():
  rows = [
    {
      'budget_type': 'MINISTRY',
      'name_1': 'Ministry of Finance',
      'amount': 1000,
      'document': 'path/to/test.pdf',
      'page': 1,
    },
    {
      'budget_type': 'BUDGETARY_UNIT',
      'name_2': 'Budgetary Unit 1',
      'amount': 500,
      'document': 'path/to/test.pdf',
      'page': 1,
    },
    {
      'budget_type': 'BUDGETARY_UNIT',
      'name_2': 'Budgetary Unit 2',
      'amount': 500,
      'document': 'path/to/test.pdf',
      'page': 1,
    },
  ]

  root = BudgetItem.build_tree_by_rows(rows)

  assert root.budget_type.name == 'MINISTRY'
  assert root.name == 'Ministry of Finance'
  assert root.amount == 1000
  assert root.document == 'path/to/test.pdf'
  assert root.page == 1
  assert len(root.children) == 2
  # assert children #1
  child_1 = root.children[0]
  assert child_1.budget_type.name == 'BUDGETARY_UNIT'
  assert child_1.name == 'Budgetary Unit 1'
  assert child_1.amount == 500
  assert child_1.document == 'path/to/test.pdf'
  assert child_1.page == 1
  assert len(child_1.children) == 0
  # assert children #2
  child_2 = root.children[1]
  assert child_2.budget_type.name == 'BUDGETARY_UNIT'
  assert child_2.name == 'Budgetary Unit 2'
  assert child_2.amount == 500
  assert child_2.document == 'path/to/test.pdf'
  assert child_2.page == 1
  assert len(child_2.children) == 0

def test_build_tree_complex_tree():
  # parent 1
  #   - child 1
  #     - grandchild 1
  #     - grandchild 2
  #   - child 2

  rows = [
    {
      'budget_type': 'MINISTRY',
      'name_1': 'Ministry of Finance',
      'amount': 1000,
      'document': 'path/to/test.pdf',
      'page': 1,
    },
    {
      'budget_type': 'BUDGETARY_UNIT',
      'name_2': 'Budgetary Unit 1',
      'amount': 500,
      'document': 'path/to/test.pdf',
      'page': 1,
    },
    {
      'budget_type': 'PROJECT',
      'name_3': 'Project 1',
      'amount': 500,
      'document': 'path/to/test.pdf',
      'page': 1,
    },
    {
      'budget_type': 'PROJECT',
      'name_3': 'Project 2',
      'amount': 500,
      'document': 'path/to/test.pdf',
      'page': 1,
    },
    {
      'budget_type': 'BUDGETARY_UNIT',
      'name_2': 'Budgetary Unit 2',
      'amount': 500,
      'document': 'path/to/test.pdf',
      'page': 1,
    },
    {
      'budget_type': 'OUTPUT',
      'name_3': 'Output 1',
      'amount': 500,
      'document': 'path/to/test.pdf',
      'page': 1,
    }
  ]

  node = BudgetItem.build_tree_by_rows(rows)

  assert len(node.children) == 2
  # assert children #1
  child_1 = node.children[0]
  assert len(child_1.children) == 2
  # assert grandchild #1
  grandchild_1 = child_1.children[0]
  assert len(grandchild_1.children) == 0
  assert grandchild_1.budget_type.name == 'PROJECT'
  assert grandchild_1.name == 'Project 1'
  assert grandchild_1.amount == 500
  assert grandchild_1.document == 'path/to/test.pdf'
  assert grandchild_1.page == 1
  # assert grandchild #2
  grandchild_2 = child_1.children[1]
  assert len(grandchild_2.children) == 0
  assert grandchild_2.budget_type.name == 'PROJECT'
  assert grandchild_2.name == 'Project 2'
  assert grandchild_2.amount == 500
  assert grandchild_2.document == 'path/to/test.pdf'
  assert grandchild_2.page == 1
  # assert children #2
  child_2 = node.children[1]
  assert len(child_2.children) == 1
  # assert grandchild #1
  grandchild_1 = child_2.children[0]
  assert len(grandchild_1.children) == 0
  assert grandchild_1.budget_type.name == 'OUTPUT'
  assert grandchild_1.name == 'Output 1'
  assert grandchild_1.amount == 500
  assert grandchild_1.document == 'path/to/test.pdf'
  assert grandchild_1.page == 1


def test_build_tree_no_rows():
  rows = []
  assert BudgetItem.build_tree_by_rows(rows) is None

def test_build_tree_with_fiscal_year():
  rows = [
    {
      'budget_type': 'MINISTRY',
      'name_1': 'Ministry of Finance',
      'amount': 1000,
      'document': 'path/to/test.pdf',
      'page': 1,
    },
    {
      'budget_type': 'FISCAL_YEAR_BUDGET',
      'name_1': '2020',
      'amount': 100,
      'fiscal_year': 2020,
      'fiscal_year_end': 2020,
    },
    {
      'budget_type': 'FISCAL_YEAR_BUDGET',
      'name_1': '2021',
      'amount': 200,
      'fiscal_year': 2021,
      'fiscal_year_end': 2021,
    },
    {
      'budget_type': 'FISCAL_YEAR_BUDGET',
      'name_1': '2022',
      'amount': 300,
      'fiscal_year': 2022,
      'fiscal_year_end': 2022,
    }
  ]

  root = BudgetItem.build_tree_by_rows(rows)

  assert root.budget_type.name == 'MINISTRY'
  assert root.name == 'Ministry of Finance'
  assert root.amount == 1000
  assert root.document == 'path/to/test.pdf'
  assert root.page == 1
  assert len(root.children) == 0
  assert len(root.fiscal_year_budget) == 3

def test_build_tree_child_with_fiscal_year_budget():
  rows = [
    {
      'budget_type': 'MINISTRY',
      'name_1': 'Ministry of Finance',
      'amount': 1000,
      'document': 'path/to/test.pdf',
      'page': 1,
    },
    {
      'budget_type': 'BUDGETARY_UNIT',
      'name_2': 'Budgetary Unit 1',
      'amount': 500,
      'document': 'path/to/test.pdf',
      'page': 1,
    },
    {
      'budget_type': 'FISCAL_YEAR_BUDGET',
      'name_2': '2020',
      'amount': 100,
      'fiscal_year': 2020,
      'fiscal_year_end': 2020,
    },
    {
      'budget_type': 'FISCAL_YEAR_BUDGET',
      'name_2': '2021',
      'amount': 200,
      'fiscal_year': 2021,
      'fiscal_year_end': 2021,
    },
    {
      'budget_type': 'FISCAL_YEAR_BUDGET',
      'name_2': '2022',
      'amount': 300,
      'fiscal_year': 2022,
      'fiscal_year_end': 2022,
    },
    {
      'budget_type': 'BUDGETARY_UNIT',
      'name_2': 'Budgetary Unit 2',
      'amount': 500,
      'document': 'path/to/test.pdf',
      'page': 1,
    },
    {
      'budget_type': 'OUTPUT',
      'name_3': 'Output 1',
      'amount': 500,
      'document': 'path/to/test.pdf',
      'page': 1,
    }
  ]

  root = BudgetItem.build_tree_by_rows(rows)

  assert root.budget_type.name == 'MINISTRY'
  assert root.name == 'Ministry of Finance'
  assert root.amount == 1000
  assert root.document == 'path/to/test.pdf'
  assert root.page == 1
  assert len(root.children) == 2

  # assert children #1
  child_1 = root.children[0]
  assert len(child_1.children) == 0
  assert len(child_1.fiscal_year_budget) == 3
  assert child_1.budget_type.name == 'BUDGETARY_UNIT'

  # assert children #2
  child_2 = root.children[1]
  assert len(child_2.children) == 1
  assert len(child_2.fiscal_year_budget) == 0

  # assert grandchild #1
  grandchild_1 = child_2.children[0]
  assert len(grandchild_1.children) == 0
  assert len(grandchild_1.fiscal_year_budget) == 0
  assert grandchild_1.budget_type.name == 'OUTPUT'
  assert grandchild_1.name == 'Output 1'
  assert grandchild_1.amount == 500
  assert grandchild_1.document == 'path/to/test.pdf'
  assert grandchild_1.page == 1

def test_should_raise_error_when_fiscal_budget_is_the_first_row():
  rows = [
    {
      'budget_type': 'FISCAL_YEAR_BUDGET',
      'name_1': '2020',
      'amount': 100,
      'fiscal_year': 2020,
      'fiscal_year_end': 2020,
    },
    {
      'budget_type': 'MINISTRY',
      'name_1': 'Ministry of Finance',
      'amount': 1000,
      'document': 'path/to/test.pdf',
      'page': 1,
    },
  ]

  with pytest.raises(ValueError) as e:
    BudgetItem.build_tree_by_rows(rows)
    assert str(e.value) == 'FISCAL_YEAR_BUDGET must have parent'