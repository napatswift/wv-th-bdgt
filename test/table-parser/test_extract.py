from tableparser import extract_tables, is_on_line, dfs
import fitz

# is_on_line tests
def test_is_on_line():
  assert is_on_line((0, 0), (0, 0), (1, 1)) == True
  assert is_on_line((1, 1), (0, 0), (1, 1)) == True
  assert is_on_line((0, 1), (0, 0), (1, 1)) == False
  assert is_on_line((1, 1), (0, 0), (4, 4)) == True
  assert is_on_line((5, 5), (0, 0), (4, 4)) == False

def test_dfs():
  assert dfs(list(), {
      0: [],
      1: [0, 2, 3],
      2: [0, 3],
      3: [1, ],
  }, 1) == 1

  assert dfs(list(), {
      0: [],
      1: [0, 2, 3],
      2: [0, 3],
      3: [1, ],
  }, 3) == 1

  assert dfs(list(), {
      0: [4],
      1: [0, 2, 3],
      2: [0, 3],
      3: [1],
      4: [],
  }, 0) == 0

def extract_tables_test(filename: str, num_tables: int):
    doc = fitz.open(filename)
    page = doc[0]  # first page

    # get the lines
    rects = [d['rect'] for d in page.get_drawings()]
    tables = extract_tables(rects)
    assert len(tables) == num_tables

def test_extract_1_table():
  extract_tables_test("test/table-parser/pdf/pdf-1table.pdf", 1)

def test_extract_2_tables():
  extract_tables_test("test/table-parser/pdf/pdf-2table.pdf", 2)

