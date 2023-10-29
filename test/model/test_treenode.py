from model import BudgetItem

def test_create_node():
  node = BudgetItem(
    name='test',
    budget_type='MINISTRY',
    amount=1000,
    document='path/to/test.pdf',
    page=1,
  )

  assert node.name == 'test'
  assert node.budget_type == 'MINISTRY'
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
  assert node.budget_type == 'MINISTRY'
  assert node.amount == 1000
  assert node.document == 'path/to/test.pdf'
  assert node.page == 1
  assert node.children is not None
  assert len(node.children) == 1
  assert node.children[0].name == 'child'
  assert node.children[0].budget_type == 'BUDGETARY_UNIT'
  assert node.children[0].amount == 1000
  assert node.children[0].document == 'path/to/test.pdf'
  assert node.children[0].page == 1