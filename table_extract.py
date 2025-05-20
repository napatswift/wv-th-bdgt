import fitz
from thbud.tableparser import extract_tables

def extract_tables_test(filename: str, num_tables: int):
    doc = fitz.open(filename)
    page = doc[0]  # first page

    # get the lines
    rects = [d['rect'] for d in page.get_drawings()]
    page_width = page.rect.width
    page_height = page.rect.height
    # filter out the lines that are outside the page

    print(len(rects))

    def is_rect_inside_page(rect):
        return rect.x0 >= 0 and rect.x1 <= page_width and rect.y0 >= 0 and rect.y1 <= page_height

    def is_rect_wider_than(rect, width):
        return rect.width > width

    def is_rect_taller_than(rect, height):
        return rect.height > height

    rects = list(filter(is_rect_inside_page, rects))

    # filter out the lines that are too short
    rects = list(
        filter(
            lambda r: (
                is_rect_wider_than(r, page.rect.width*.1)
                and is_rect_taller_than(r, page.rect.height*.2)
                ),
            rects
            )
    )

    print('width', [r.width for r in rects])
    tables = extract_tables(rects)
    print([[r.width*r.height for r in tab.rects] for tab in tables])
    assert len(tables) == num_tables

# extract_tables_test('test/table-parser/pdf/pdf-0table.pdf', 0)
# extract_tables_test('test/table-parser/pdf/pdf-0table.pdf', 2)
extract_tables_test('test/table-parser/pdf/pdf-1table.pdf', 1)