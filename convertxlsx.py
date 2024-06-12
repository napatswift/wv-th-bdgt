from thbud.textextract import XLSXDocumentText
from thbud.textextract.pdf_to_tree import extract_tree_levels, get_entries
import json
import os
import re
import concurrent.futures
import traceback


xlsx_dir = './ฉบับร่างพระราชบัญญัติงบประมาณรายจ่าย (ร่าง พ.ร.บ.) (Excel)/'


class CannotFindStartPageError(Exception):
    """
    Exception when cannot find the start page
    """


class NoEntriesFoundError(Exception):
    """
    Exception when no entries found in the document
    """


def list_all_document_in_directory():
    file_paths = []
    for root, dirs, files in os.walk(xlsx_dir):
        for file in files:
            if (file.endswith('.xlsx')
                    and not file.startswith('~$')):
                file_paths.append(os.path.join(root, file))
    return file_paths


def check_page(page, required_text):
    norm_required_text = re.sub(r'\s', '', required_text)
    norm_page_text = re.sub(r'\s', '', str(page))

    return norm_required_text in norm_page_text


def is_start_page(page):
    required_text = [
        "7. รายละเอียดงบประมาณจำแนกตามแผนงาน และ ผลผลิต/โครงการ",
        "1. รายละเอียดงบประมาณจำแนกตามแผนงาน และ ผลผลิต/โครงการ",
        "รายละเอียดงบประมาณจำแนกตามงบรายจ่าย",
    ]

    return any(check_page(page, t) for t in required_text)


def is_end_page(page):
    required_text = [
        '8. รายงานสถานะและแผนการใช้จ่ายเงินนอกงบประมาณ',
        '8. รายละเอียดงบประมาณจำแนกตามหมวดรายจ่าย'
    ]
    return any(check_page(page, t) for t in required_text)


def build_tree_from_xlsx(file_path):
    doc = XLSXDocumentText(file_path)

    start_page_idx = None
    end_page_idx = None
    for i, page in enumerate(doc.pages):
        if is_start_page(page) and start_page_idx is None:
            start_page_idx = i
        if is_end_page(page):
            end_page_idx = i

    if start_page_idx is None:
        raise CannotFindStartPageError('Cannot find start page')

    lines = doc.get_lines_in_page(
        start=start_page_idx, end=end_page_idx)

    # print('\n'.join([str(p) for p in lines if str(p).strip()]))

    entries = get_entries(lines)

    if not entries:
        raise NoEntriesFoundError('No entries found')

    return extract_tree_levels(entries)

    # tree_s = json.dumps(root.to_json(), ensure_ascii=False, indent=4)

    # tree_s = re.sub(r'"children": \[\s+\]', '"children": []', tree_s)

    # print(json.dumps(root.to_json(), ensure_ascii=False, indent=4))


def process_file(file_path):
    # TODO: remove this
    if 'องค์กรปกครองส่วนท้องถิ่น' in file_path:
        print('Skip not supported yet', file_path)
        return

    file_name = os.path.basename(file_path)
    file_name = os.path.splitext(file_name)[0]
    output_file_path = os.path.join(
        '.', 'output', '2568', file_name + '.json'
    )

    if os.path.exists(output_file_path):
        print('Skip already processed', file_path)
        return

    try:
        tree = build_tree_from_xlsx(file_path)
        print('Done', file_path)

        with open(output_file_path, 'w') as fp:
            json.dump(
                tree.to_json(),
                fp,
                ensure_ascii=False,
                indent=4
            )

    except CannotFindStartPageError as e:
        print(e, 'in', '"'+file_path+'"')
    except NoEntriesFoundError as e:
        print(e, 'in', '"'+file_path+'"')
    except Exception as e:
        # print the error and traceback
        print(e, 'in', '"'+file_path+'"')
        traceback.print_exc()
        return


def main():
    file_paths = list_all_document_in_directory()
    file_paths.sort()

    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(process_file, file_paths)


if __name__ == '__main__':
    main()
