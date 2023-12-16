from typing import List, Optional, Callable, Tuple
import fitz
from .text import WordText, PageText, LineText
from ..tableparser import (
    extract_tables
)
from typing import List


def group_text_by_line(text_list: List[WordText], threshold=0.01):
    """
    Group text by line

    Args:
      text_list (List[WordText]): list of WordText objects representing text in pdf file.
      threshold (float, optional): threshold to group text. Defaults to 0.01.

    Returns:
      List[List[WordText]]: a list of lines, where each line is a list of WordText objects.
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

    Raises:
        TypeError: If page is not a fitz.Page object.
    """
    if not isinstance(page, fitz.Page):
        raise TypeError('page must be a fitz.Page object.')

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


def page_contains_table(page: fitz.Page) -> bool:
    rects = [d['rect'] for d in page.get_drawings()]
    return len(extract_tables(rects)) > 0


def defualt_words_loader(page: fitz.Page) -> List[Tuple[float, float, float, float, str]]:
    word_tuples = page.get_text_words()
    words = []
    for word in word_tuples:
        x0, y0, x1, y1, text = word[:5]
        words.append((x0, y0, x1, y1, text))

    return words


class DocumentText:
    def __init__(
        self,
        filepath: str,
        words_loader: Optional[Callable[[fitz.Page], List[Tuple[float, float, float, float, str]]]] = None,
        lazy: bool = False,
    ) -> 'DocumentText':
        self.filepath = filepath
        self.page_label_to_index = dict()  # str as key
        self.lazy = lazy
        self.doc = None
        self.pages = []
        if words_loader is None:
            words_loader = defualt_words_loader
        self.words_loader = words_loader
        self._read_pdf_file()
        

    def _read_pdf_file(self,) -> List['PageText']:
        try:
            doc: fitz.Document = fitz.open(self.filepath)
        except fitz.fitz.FileNotFoundError as e:
            raise FileNotFoundError('File not found.') from e

        self.doc = doc

        for pidx, page in enumerate(doc.pages()):
            self.page_label_to_index[page.get_label()] = pidx
            self.pages.append(None)
            if self.lazy:
                continue
            self._load_page(pidx)

    def _load_page(self, page_index: int) -> 'PageText':
        for pidx, page in enumerate(self.doc.pages()):
            if pidx != page_index or self.pages[pidx] is not None:
                continue
            
            word_tuples = self.words_loader(page)
            page_width = page.rect.width
            page_height = page.rect.height

            words = []
            for word in word_tuples:
                x0, y0, x1, y1, text = word
                x0 = x0 / page_width
                x1 = x1 / page_width
                y0 = y0 / page_height
                y1 = y1 / page_height
                words.append(WordText(x0, y0, x1, y1, text))
            grouped_lines = group_text_by_line(words, 0.01)
            list_of_line: List['LineText'] = []

            for lidx, words in enumerate(grouped_lines):
                if words:
                    list_of_line.append(LineText(words, pidx, lidx))

            pagetext = PageText(lines=list_of_line,
                                page_index=pidx,
                                width=page.rect.width,
                                height=page.rect.height,
                                is_image=is_image_page(page),
                                document=self,)

            for line in pagetext.lines:
                line.page = pagetext

            pagetext.contains_table = page_contains_table(page)
            self.pages[pidx] = pagetext

    def get_page(self: 'DocumentText', page_index: int) -> 'PageText':
        if page_index < 0 or page_index >= len(self.pages):
            raise IndexError('page_index must be in range [0, {})'.format(
                len(self.pages)))
        if self.pages[page_index] is None:
            self._load_page(page_index)
        return self.pages[page_index]

    def get_lines_in_page(self: 'DocumentText', start: Optional[int] = None, end: Optional[int] = None) -> List['LineText']:
        if start is None:
            start = 0
        elif isinstance(start, str):
            start = self.page_label_to_index.get(start)
            if start is None:
                raise IndexError(
                    'page {} not found in the doc'.format(repr(start)))
        if end is None:
            end = len(self.pages)
        elif isinstance(end, str):
            end = self.page_label_to_index.get(end)
            if end is None:
                raise IndexError(
                    'page {} not found in the doc'.format(repr(end)))

        if start < 0 or start >= len(self.pages):
            raise IndexError('start must be in range [0, {})'.format(
                len(self.pages)))

        if end < 0 or end > len(self.pages):
            raise IndexError('end must be in range [0, {})'.format(
                len(self.pages)))

        lines = []
        for idx in range(start, end):
            page = self.get_page(idx)
            lines.extend(page.lines)

        return lines
