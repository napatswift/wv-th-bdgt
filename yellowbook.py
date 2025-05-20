from thbud.textextract import DocumentText, LineText
from thbud.textextract import LineItem, extract_tree_levels
from typing import List
import logging
import re
import pandas as pd
logger = logging.getLogger(__name__)


class YBLineItem(LineItem):
    def __init__(self, itemtype: str, line_text: List[LineText]):
        super().__init__(itemtype, line_text)

    def __str__(self):
        amount = 0
        words = []
        for idx, line in enumerate(self.lines):
            if idx == 0:
                words += line.words
                amount = words.pop()
            else:
                words += line.words

        return (' '.join([str(w) for w in words])
                + ' |$| '
                + str(amount)
                + ' บาท')


def get_entries(lines: List[LineText]):
    objective_or_kpi = False

    entry = []
    entries = []
    for line in lines:
        line_text = str(line)
        last_word = line.words[-1]

        if line_text.isdigit():
            continue
        if line.line_index < 3:
            continue

        if (
            line_text.startswith('เป้าหมาย')
            or line_text.startswith('ตัวชี้วัด')
            or line_text.startswith('- ')
            or line_text.startswith('วัตถุประสงค์')
        ):
            objective_or_kpi = True

        contains_amount = False
        if (re.match('^[0-9,]+\.\d+$', last_word.text)
                and last_word.x1 > 0.85):
            contains_amount = True

        if (
            re.match('^[^-].*[\d,]+\.\d+$', line_text)
            and contains_amount
        ):
            if entry:
                entries.append(('item', entry))
                entry = []
            objective_or_kpi = False

        if (objective_or_kpi):
            print('objective_or_kpi', line_text)
            continue
        entry.append(line)

        # then split by whitespace
        line_text = line_text.split()

    if entry:
        entries.append(('item', entry))

    return [
        YBLineItem(t, lines) for t, lines in entries
    ]


data_list = [
    # dict(pdf_file_path='2562.4.pdf', page_range=('29', '274')),
    # dict(pdf_file_path='2563.4.pdf', page_range=('6', '234')),
    # dict(pdf_file_path='2564.4.pdf', page_range=('8', '234')),
    # dict(pdf_file_path='2565.4.pdf', page_range=('9', '226')),
    # dict(pdf_file_path='2566.4.pdf', page_range=('15', '296')),
    dict(pdf_file_path='yellow68.pdf', page_range=('15', '407')),
]

for data in data_list:
    doc = DocumentText(data['pdf_file_path'], lazy=True)
    text_lines = doc.get_lines_in_page(*data['page_range'])
    entries = get_entries(text_lines)
    root = extract_tree_levels(entries)
    df = pd.DataFrame(root.to_rows())
    df.to_csv(
        data['pdf_file_path'].replace('.pdf', '.csv'),
        index=False,
        encoding='utf-8-sig'
    )
    with open('yellowbook.txt', 'w') as f:
        f.write('\n'.join([str(l) for l in entries]))
