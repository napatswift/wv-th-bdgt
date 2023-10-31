import fitz
from typing import List
from .text import (
    LineText,
    WordText,
    PageText,
)
from .documenttext import DocumentText


def read_text_in_pdf_file(filepath, file_id=None) -> List[PageText]:
    try:
        doc: fitz.Document = fitz.open(filepath)
    except fitz.fitz.FileNotFoundError as e:
        raise FileNotFoundError('File not found.') from e

    page_list: List[PageText] = []
    for pidx, page in enumerate(doc):
        word_tuples = page.get_text_words()
        page_width = page.rect.width
        page_height = page.rect.height

        words = []
        for word in word_tuples:
            x0, y0, x1, y1, text = word[:5]
            x0 = x0 / page_width
            x1 = x1 / page_width
            y0 = y0 / page_height
            y1 = y1 / page_height
            words.append(WordText(x0, y0, x1, y1, text))

        grouped_lines = group_text_by_line(words, 0.01)
        list_of_line: List[LineText] = []

        for lidx, line in enumerate(grouped_lines):
            words = line
            if not words:
                continue
            list_of_line.append(LineText(words, pidx, lidx))

        page_list.append(PageText(list_of_line,
                                  pidx,
                                  page_width,
                                  page_height,
                                  is_image_page(page),
                                  file_id))

    return page_list

def group_text_by_line(text_list: List[WordText], threshold=0.01):
    """
    Group text by line

    Args:
        text_list (List[Text]): list of text in pdf file.
        threshold (int, optional): threshold to group text. Defaults to 1.
    """
    # Sort text by y0, x0.
    text_list.sort(key=lambda x: (x.y0, x.x0))
    line_list = []
    line = []
    prev_y0 = None
    for word in text_list:
        # If previous y0 is None, set it to y0.
        if prev_y0 is None:
            prev_y0 = word.y0

        # If current y0 - previous y0 > threshold,
        # add current line to line list and start a new line.
        if word.y0 - prev_y0 > threshold:
            line_list.append(line)
            line = []

        # Add current text to line.
        line.append(word)

        # Update previous y0.
        prev_y0 = word.y0

    # If line is not empty, add it to line list.
    if line:
        line_list.append(line)

    # Sort by x0
    for line in line_list:
        line.sort(key=lambda x: x.x0)

    return line_list

def is_image_page(page: fitz.Page) -> bool:
    """
    Check if a page is an image page.

    Args:
        page (fitz.Page): The page to check.

    Returns:
        bool: True if the page is an image page, False otherwise.

    """
    assert isinstance(
        page, fitz.Page), 'page must be an instance of fitz.Page.'
    theshold = 0.8
    page_size = page.rect.width * page.rect.height

    # Get images in the page.
    # images: List[(xref, smask, width, height, bpc, colorspace, alt. colorspace, name, filter, referencer)]
    images = page.get_images()
    if not images:
        return False

    image_size = 0
    for image in images:
        image_size += image[2] * image[3]

    # If the size of the images is greater than theshold of the page size,
    # then it's an image page.
    return image_size / page_size > theshold
