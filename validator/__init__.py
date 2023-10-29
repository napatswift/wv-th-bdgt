import model
import json

def read_file(filename: str) -> model.BudgetItem:
  filecontent = None
  with open(filename, 'r') as f:
    filecontent = f.read()
    jsoncontent = json.loads(filecontent)

  return model.BudgetItem.from_json(jsoncontent)