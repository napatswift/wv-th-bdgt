from thbud.tableparser import extract_tables, is_on_line, dfs
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

def is_rect_inside_page(rect, page_width, page_height):
    return rect.x0 >= 0 and rect.x1 <= page_width and rect.y0 >= 0 and rect.y1 <= page_height

def extract_tables_test(filename: str, num_tables: int):
    doc = fitz.open(filename)
    page = doc[0]  # first page

    # get the lines
    rects = [d['rect'] for d in page.get_drawings() if is_rect_inside_page(d['rect'], page.rect.width, page.rect.height)]
    tables = extract_tables(rects)
    print([[r.width*r.height for r in tab.rects] for tab in tables])
    assert len(tables) == num_tables

def test_extract_1_table():
  extract_tables_test("test/table-parser/pdf/pdf-1table.pdf", 1)

def test_extract_2_tables():
  extract_tables_test("test/table-parser/pdf/pdf-2table.pdf", 2)

def test_extract_0_table():
  extract_tables_test("test/table-parser/pdf/pdf-0table-contain-outside-page-table.pdf", 0)

