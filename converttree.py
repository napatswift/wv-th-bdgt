from thbud.model.budget import BudgetType, BudgetItem
from thbud.textextract import DocumentText, get_entries, extract_tree_levels
import logging
import json
import pandas as pd
import os
import time
import re
import fitz
import subprocess

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

root_pdf_dir = 'toc/PDF'
contents_filepath = 'toc/toc_output/toc.json'

tess = "tesseract stdin stdout --psm 7 -l tha+eng"
mat = fitz.Matrix(2.5, 2.5)  # high resolution matrix

def get_tessocr(page, bbox):
    """Return OCR-ed span text using Tesseract.

    Args:
        page: fitz.Page
        bbox: fitz.Rect or its tuple
    Returns:
        The OCR-ed text of the bbox.
    """
    global tess, mat
    # Step 1: Make a high-resolution image of the bbox.

    pix = page.get_pixmap(
        colorspace=fitz.csGRAY,  # we need no color
        matrix=mat,
        clip=bbox,
    )

    pix.pil_save(f'{repr(bbox[:2])}.png')
    image = pix.tobytes("png")  # make a PNG image

    # Step 2: Invoke Tesseract to OCR the image. Text is stored in stdout.
    rc = subprocess.run(
        tess,  # the command
        input=image,  # the pixmap image
        stdout=subprocess.PIPE,  # find the text here
        shell=True,
    )

    # because we told Tesseract to interpret the image as one line, we now need
    # to strip off the line break characters from the tail.
    text = rc.stdout.decode()  # convert to string
    text = text.strip()  # remove line breaks
    return text

def find_page_range(budgetary_unit_contents):
    start, end = None, None
    for contents in budgetary_unit_contents:
        if contents['title'].startswith('7.'):
            start = str(contents['page_num'][0])
        if contents['title'].startswith('8.'):
            end = str(contents['page_num'][0])

    return start, end



if __name__ == '__main__':
    """
    ministy_dict = dict()
    budget_file_list = json.load(open(contents_filepath, 'r'))
    for budget_file in budget_file_list:
        for file_content in budget_file['toc']:
            if file_content.get('ministry') is None:
                continue

            if ministy_dict.get(file_content['ministry']) is None:
                ministy_dict[file_content['ministry']] = dict(
                    pdf_path=budget_file['file_name'],
                    name=file_content['ministry'].strip(),
                    budgetary_units=list()
                )

            ministy_dict[file_content['ministry']]['budgetary_units'].append(
                dict(
                    name=re.sub('^\(\d+\)\s+', '',
                                file_content['title']).strip(),
                    page_range=find_page_range(file_content['contents'])
                )
            )
    ministy_list = list(ministy_dict.values())
    
    with open('ministry_list.json', 'w') as f:
        json.dump(ministy_list, f, indent=4, ensure_ascii=False)
    """

    ministy_list = [
        dict(
            name='งบ',
            pdf_path='../../1703581990_2601.pdf',
            budgetary_units=[
                dict(name='สำนักงานปลัดกระทรวงทรัพยากรธรรมชาติและสิ่งแวดล้อม', page_range=('15', '270'))
            ]
        )
    ]
    

    for ministry in ministy_list:
        logger.info(ministry['name'] + ' ' + str(ministry['pdf_path']))
        pdf_path = os.path.join(root_pdf_dir, ministry['pdf_path'])

        doc = DocumentText(pdf_path, lazy=True)
        ministry_node = BudgetItem(
            budget_type=BudgetType.MINISTRY,
            name=ministry['name'],
            amount=None,
            document=pdf_path,
            page=0,
        )

        for budgetary_unit in ministry['budgetary_units']:

            start, end = budgetary_unit['page_range']

            if start is None or end is None:
                continue
            
            text_lines = doc.get_lines_in_page(start, end)
            entries = get_entries(text_lines)

            if len(entries) == 0:
                logger.error(
                    "{} contains no entry, ({})".format(
                        budgetary_unit['name'], budgetary_unit))
                continue

            logger.info('Total entries: {} {}'.format(
                len(entries), str(budgetary_unit)))

            root = extract_tree_levels(entries)
            root.budget_type = BudgetType.BUDGETARY_UNIT
            root.name = budgetary_unit['name']

            root.parent = ministry_node

        file_name = 'output/{}-{}.json'.format(
            ministry['name'],
            pdf_path.replace('/', '-').replace('.', '-')
        )
        df = pd.DataFrame(ministry_node.to_rows())
        df.to_csv(
            file_name.replace('.json', '.csv'),
            index=False,
            encoding='utf-8-sig'
        )
        
        """

        with open(file_name, 'w') as f:
            json.dump(ministry_node.to_json(), f, indent=4, ensure_ascii=False)

        """
