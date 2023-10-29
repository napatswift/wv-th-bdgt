import pytest
from validator import read_file

def test_read_file_not_found():
    with pytest.raises(FileNotFoundError):
        read_file("test/validator/data/not-found.json")

def test_read_file_empty():
    with pytest.raises(ValueError):
        read_file("test/validator/data/budget-tree-empty.json")

def test_read_file_invalid():
    with pytest.raises(ValueError):
        read_file("test/validator/data/budget-tree-invalid.json")

def test_read_file():
    tree = read_file("test/validator/data/budget-tree-1.json")

    assert tree is not None
    assert tree.budget_type.name == 'MINISTRY'
    assert tree.name == "root budget"
    assert tree.amount == 100.0
    assert tree.document == '/path/to/document'
    assert tree.page == 1
    assert tree.children is not None
    assert len(tree.children) == 1
    assert tree.fiscal_year_budget is not None
    assert len(tree.fiscal_year_budget) == 0
    # assert child #1
    child = tree.children[0]
    assert child.parent == tree
    assert child.budget_type.name == 'BUDGETARY_UNIT'
    assert child.name == "child 1 budget"
    assert child.amount == 100.0
    assert child.document == '/path/to/document'
    assert child.page == 1
    assert child.children is not None
    assert len(child.children) == 0
    assert child.fiscal_year_budget is not None
    assert len(child.fiscal_year_budget) == 0