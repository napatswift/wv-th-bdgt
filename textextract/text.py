import re
from typing import List, Dict, Union
import logging

logger = logging.getLogger(__name__)


def mean(numbers: List[float]) -> float:
    return sum(numbers) / len(numbers)


def to_dict(obj) -> Dict:
    if isinstance(obj, list):
        list_of_dicts = []
        for o in obj:
            list_of_dicts.append(to_dict(o))
        return list_of_dicts
    if hasattr(obj, 'to_dict'):
        return obj.to_dict()
    raise Exception(f'Object {obj} does not have to_dict method')


class WordText:
    def __init__(self, x0: Union[float, int], y0: Union[float, int], x1: Union[float, int], y1: Union[float, int], text: str):
        assert isinstance(text, str)

        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1
        self.text = text

        self._assert_params()

    def _assert_params(self):
        assert isinstance(self.x0, (float, int))
        assert isinstance(self.y0, (float, int))
        assert isinstance(self.x1, (float, int))
        assert isinstance(self.y1, (float, int))
        assert isinstance(self.text, str)

    def fix_pdf_text(self,) -> str:
        """
        Fix text that is not correctly extracted from pdf.
        """
        return re.sub(r'^า', 'ำ', self.text)

    def merge_word(self, word: 'WordText', fixed_text: str):
        self.text += fixed_text
        self.x0 = min(self.x0, word.x0)
        self.x1 = max(self.x1, word.x1)
        self.y0 = min(self.y0, word.y0)
        self.y1 = max(self.y1, word.y1)

    def copy(self) -> 'WordText':
        return WordText(self.x0, self.y0, self.x1, self.y1, self.text)

    def to_dict(self) -> Dict:
        return {
            'type': 'WordText',
            'text': self.text,
            'position': {
                'x0': self.x0,
                'y0': self.y0,
                'x1': self.x1,
                'y1': self.y1,
            }
        }

    def __str__(self) -> str:
        return self.text

    def __repr__(self) -> str:
        return f"WordText({self.x0:.2f}, {self.y0:.2f}, {self.x1:.2f}, {self.y1:.2f}, '{self.text}')"


class LineText:
    def __init__(self, words: List[WordText], page_index: int, line_index: int):
        self.page_number: str = None
        self.words = self._join_words(words)
        self.page_index = page_index
        self.line_index = line_index
        self.doc_id = None

        self._assert_params()

    def _assert_params(self):
        assert isinstance(self.page_index, int)
        assert isinstance(self.line_index, int)
        assert isinstance(self.words, list)
        for word in self.words:
            assert isinstance(word, WordText)

    def get_word_with_whitespace_tokens(self) -> List[WordText]:
        threshold = 0.1
        SEP_TOKEN = '<big_sep>'

        out_words = []
        for og_word in self.words:
            word = og_word.copy()
            if len(out_words) == 0:
                # If the output list is empty, add the current word to the output list
                out_words.append(word)
                continue

            # Get the previous word
            prev_word = out_words[-1]

            if prev_word.x1 == word.x0:
                # If the current word is right next to the previous word,
                out_words.append(word)
                continue

            # Calculate the space between the current word and the previous word
            sep = word.x0 - prev_word.x1
            if sep > threshold:
                # If the space is larger than threshold, add a whitespace token
                out_words.append(
                    WordText(x0=prev_word.x1, y0=prev_word.y0,
                             x1=word.x0, y1=prev_word.y1,
                             text=SEP_TOKEN))
            out_words.append(word)

        return out_words

    def copy(self) -> 'LineText':
        return LineText([word.copy() for word in self.words], self.page_index, self.line_index)

    def __str__(self) -> str:
        return ' '.join([w.text for w in self.words])

    def __repr__(self) -> str:
        words = ', '.join([repr(w) for w in self.words])
        return 'LineText([' + words + '])'

    def _join_words(self, words: List[WordText]) -> List[WordText]:
        """
        if word starts with า, join it with previous word.
        """
        new_words = []
        for word in words:
            if (word.text.startswith('า') or
                    word.text.startswith('ำ') or
                    word.text.startswith('ํา') or
                    word.text.startswith('่') or
                    word.text.startswith('่') or
                    word.text.startswith('๋') or
                    word.text.startswith('้')):
                if len(new_words) == 0:
                    new_words.append(word)
                    continue
                prev_word = new_words[-1]
                prev_word.merge_word(word, word.fix_pdf_text())
            else:
                new_words.append(word)
        return new_words

    def to_dict(self) -> Dict:
        return {
            'type': 'LineText',
            'text': str(self),
            'docId': self.doc_id,
            'pageNumber': self.page_number,
            'pageIndex': self.page_index,
            'lineIndex': self.line_index,
            'position': {
                'x0': self.x0,
                'y0': self.y0,
                'x1': self.x1,
                'y1': self.y1,
            },
            'words': to_dict(self.words),
        }

    def __iter__(self):
        return iter(self.words)

    @property
    def x0(self) -> float:
        return self.words[0].x0

    @property
    def y0(self) -> float:
        return self.words[0].y0

    @property
    def x1(self) -> float:
        return self.words[-1].x1

    @property
    def y1(self) -> float:
        return self.words[-1].y1


class PageText:
    """
    A class representing a page of text.

    Attributes:
        lines (List[LineText]): A list of LineText objects representing each line of text on the page.
        page_number (str): The page number of the page.
        page_index (int): The index of the page in the document.
        width (float): The width of the page.
        height (float): The height of the page.
        is_image (bool): Whether the page is an image.
    """

    def __init__(self, lines: List[LineText], page_index: int, width: Union[float, int], height: Union[float, int], is_image: bool,):
        assert isinstance(lines, list)
        for line in lines:
            assert isinstance(line, LineText)
        assert isinstance(page_index, int)
        assert isinstance(is_image, bool)
        assert isinstance(width, (float, int)) and width > 0
        assert isinstance(height, (float, int)) and height > 0

        self.lines = lines
        self.page_index = page_index
        self.width = width
        self.height = height
        self.is_image = is_image
        self.is_skipped = False
        self._page_number = -1

    @property
    def page_number(self) -> str:
        if self._page_number == -1:
            return ''
        return self._page_number

    @page_number.setter
    def page_number(self, value: str):
        self._page_number = value
        for line in self.lines:
            line.page_number = value

    def __str__(self) -> str:
        return '\n'.join([str(line) for line in self.lines])

    def __repr__(self) -> str:
        return f'PageText({self.lines})'

    def get_lines_with_begin_tokens(self, x0_tolerance=0.005) -> List[LineText]:
        TOKENS = ['<begin>', '<begin_indent>']
        x0_list = []
        sorted_x0_list = [line.x0 for line in self.lines]
        for line_x0 in sorted_x0_list:
            found = False
            for i, x0 in enumerate(x0_list):
                if abs(line_x0 - mean(x0)) < x0_tolerance:
                    found = True
                    # recaluclate x0
                    x0_list[i].append(line_x0)
                    break
            if not found:
                x0_list.append([line_x0])
        x0_list = [mean(x0) for x0 in x0_list]
        x0_list.sort()
        x0_list.append(self.width)
        logger.debug(f'x0_list={x0_list}')
        out_lines = []
        for og_line in self.lines:
            word_list = og_line.get_word_with_whitespace_tokens()
            first_word = word_list[0]
            indent_lev = get_smallest_indent(
                first_word.x0, x0_list=x0_list)
            logger.debug(
                f'indent_lev={indent_lev} for x0={first_word.x0} line={og_line}')
            begining_tokens = [
                WordText(x0=0.0, y0=first_word.y0,
                         x1=x0_list[0], y1=first_word.y1,
                         text=TOKENS[0]), ]
            for i in range(indent_lev):
                begining_tokens.append(
                    WordText(x0=x0_list[i], y0=first_word.y0,
                             x1=x0_list[i+1], y1=first_word.y1,
                             text=TOKENS[1]))
            out_lines.append(
                LineText(words=begining_tokens+word_list, page_index=og_line.page_index, line_index=og_line.line_index))
        return out_lines

    def to_dict(self) -> Dict:
        return {
            'type': 'PageText',
            'docId': self.doc_id,
            'pageIndex': self.page_index,
            'pageNumber': self.page_number,
            'lines': to_dict(self.lines),
            'size': {
                'width': self.width,
                'height': self.height
            },
            'isImage': self.is_image,
            'isSkipped': self.is_skipped,
        }

def get_smallest_indent(x0, x0_list):
    for i, x in enumerate(x0_list):
        if x0 <= x:
            # if the diff of x0[i-1] less than x0[i]
            if i > 0 and abs(x0 - x0_list[i-1]) < abs(x0 - x):
                return i-1
            return i
    return len(x0_list)
