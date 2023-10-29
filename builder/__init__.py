from anytree import PreOrderIter

from model.budget import BudgetItem

def build_csv_from_tree(
    root: 'BudgetItem',
):
  nodes = PreOrderIter(root)

def build_tree_from_csv(
    csv: str,
) -> 'BudgetItem':
  return None