from thbud.model.budget import BudgetItem, BudgetType
from thbud.textextract import XLSXDocumentText
from thbud.textextract.pdf_to_tree import extract_tree_levels, get_entries
import json
import os
import re
import concurrent.futures
import traceback
import pandas as pd
import logging


OUTPUT_DIR = os.path.join('.', 'output-i', '2568_local-administration')
xlsx_dir = './ฉบับร่างพระราชบัญญัติงบประมาณรายจ่าย (ร่าง พ.ร.บ.) (Excel)/'
logger = logging.getLogger(__name__)
logging.basicConfig(
    filename='convertxlsx__.log',
    level=logging.INFO)


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


def extract_dataframe_columns(dataframe):
    name_cols = [col for col in dataframe.columns if col.startswith('name_')]

    name_cols.sort(key=lambda c: int(c.split('_')[1]))

    cols = ['error_message', 'budget_type', *name_cols,]

    cols += ['amount', 'document', 'page']

    for col in dataframe.columns:
        if col not in cols:
            cols.append(col)

    return cols


def check_page(page, required_text):
    norm_required_text = re.sub(r'\s', '', required_text)
    norm_page_text = re.sub(r'\s', '', str(page))

    return norm_required_text in norm_page_text


def is_start_page(page):
    required_text = [
        "7. รายละเอียดงบประมาณจำแนกตามแผนงาน และ ผลผลิต/โครงการ",
        "1. รายละเอียดงบประมาณจำแนกตามแผนงาน และ ผลผลิต/โครงการ",
        "รายละเอียดงบประมาณจำแนกตามงบรายจ่าย",
        "รายละเอียดงบประมาณจำแนกตามงบรายจ่าย",
        '7. รายละเอียดงบประมาณรายจ่ายจำแนกตามแผนงาน - งบรายจ่าย',
        '3. รายละเอียดงบประมาณ'
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

    file_name = os.path.basename(file_path)
    file_name = os.path.splitext(file_name)[0]
    output_file_path = os.path.join(
        OUTPUT_DIR, '###'+file_name + '.csv'
    )

    """
    if os.path.exists(output_file_path):
        print('Skip already processed', file_path)
        return
    """

    try:
        tree = build_tree_from_xlsx(file_path)
        tree.name = file_name
        tree.budget_type = BudgetType.BUDGETARY_UNIT

        ministry_df = pd.DataFrame(tree.to_rows())
        for i in range(1, 12):
            if 'name_'+str(i) not in ministry_df.columns:
                ministry_df['name_'+str(i)] = ''
                print('name_'+str(i), 'not in columns')
        cols = extract_dataframe_columns(ministry_df)
        ministry_df = ministry_df[cols]
        ministry_df.to_csv(output_file_path, index=False)
        logger.info('Saved CSV to ' + output_file_path)

        """
        print('Done', file_path)

        with open(output_file_path, 'w') as fp:
            json.dump(
                tree.to_json(),
                fp,
                ensure_ascii=False,
                indent=4
            )
        """

    except CannotFindStartPageError as e:
        logger.error(str(e) + ' in', '"'+file_path+'"')
    except NoEntriesFoundError as e:
        logger.error(str(e) + ' in', '"'+file_path+'"')
    except Exception as e:
        # print the error and traceback
        logger.error(str(e) + ' in', '"'+file_path+'"')
        traceback.print_exc()
        return


def build_tree_for_ministry(ministry_name, file_paths):
    common_prefix = os.path.commonprefix(file_paths)

    root = BudgetItem(
        budget_type=BudgetType.MINISTRY,
        name=ministry_name,
        amount=None,
        document=common_prefix,
        page=0,
    )

    tree_list = []
    for file_path in file_paths:
        file_name = os.path.basename(file_path)
        budget_unit_logger = logging.getLogger(re.sub(r'\s+', '_', file_name))
        budget_unit_logger.info('Processing "{}"'.format(file_path))
        try:
            tree = build_tree_from_xlsx(file_path)
            tree.name = os.path.basename(file_path)
            tree.budget_type = BudgetType.BUDGETARY_UNIT
            tree.parent = root
        except CannotFindStartPageError as e:
            budget_unit_logger.error('{} in "{}"'.format(str(e), file_path))
        except NoEntriesFoundError as e:
            budget_unit_logger.error('{} in "{}"'.format(str(e), file_path))
        except Exception as e:
            budget_unit_logger.error('{} in "{}"'.format(str(e), file_path))
            traceback.print_exc()
            return

    output_file_path = os.path.join(
        OUTPUT_DIR, ministry_name + '.json'
    )

    csv_file_path = os.path.join(
        OUTPUT_DIR, ministry_name + '.csv'
    )

    with open(output_file_path, 'w') as fp:
        json.dump(
            root.to_json(),
            fp,
            ensure_ascii=False,
            indent=4
        )
    
    logger.info('Saved JSON to ' + output_file_path)

    ministry_df = pd.DataFrame(root.to_rows())
    for i in range(1, 12):
        if 'name_'+str(i) not in ministry_df.columns:
            print('name_'+str(i), 'not in columns')
            ministry_df['name_'+str(i)] = ''
    cols = extract_dataframe_columns(ministry_df)
    ministry_df = ministry_df[cols]
    ministry_df.to_csv(csv_file_path, index=False)

    logger.info('Saved CSV to ' + csv_file_path)

    return tree_list


def group_files_by_directory(file_paths):
    file_paths_by_directory = {}
    for file_path in file_paths:
        # head_dir, directory = os.path.split(file_path)
        directory = os.path.dirname(file_path)
        prefix, directory = os.path.split(directory)
        if directory not in file_paths_by_directory:
            file_paths_by_directory[directory] = []
        file_paths_by_directory[directory].append(file_path)
    return file_paths_by_directory


def main():
    logger.setLevel(0)
    logger.info('*'*80)
    logger.info('Start processing ' + xlsx_dir)
    logger.info('Output to ' + OUTPUT_DIR)
    logger.info('*'*80)
    # process_file(
    #     'ฉบับร่างพระราชบัญญัติงบประมาณรายจ่าย (ร่าง พ.ร.บ.) (Excel)/เล่ม 5/กระทรวงคมนาคม/AO_08006 กรมทางหลวง 08.05.67.xlsx'
    # )
    # return
    file_paths = list_all_document_in_directory()
    file_paths.sort()

    grouped_file_paths = group_files_by_directory(file_paths)

    output_dir = os.path.join(OUTPUT_DIR)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    ministry_list = []
    ministry_file_list = []
    for ministry_name, file_paths in grouped_file_paths.items():
        # if ministry_name == 'องค์กรปกครองส่วนท้องถิ่น':
        #     continue
        # if 'กระทรวงการอุดมศึกษา' not in ministry_name:
        # if 'ท้องถิ่น' not in ministry_name:
        #     continue

        interested_bud_units = [
            # 'เทคโนโลยีปทุมวัน',
            # 'ราชภัฏยะลา',
            # 'ราชภัฏสุรินทร์',
            # 'สำนักงานคณะกรรมการส่งเสริมวิทยาศาสตร์'

            # 'เด็กและเยาวชน',

            # 'AO_23012_ส.ปทุมวัน',
            # '23043_มรภ.ยะลา_68',
            # '23030_มรภ.สุรินทร์_68',
            # 'AO_23086_Kmutt',
            # 'AO_27073 สกสว',

            # 'AO_07011_กรมส่งเสริมการเกษตร',

            # 'งบกลาง

            # "เทศบาลตำบลบ้านค่าหมื่นแผ้ว",
            # "เทศบาลตำบลชีลอง",
            # "เทศบาลตำบลลาดใหญ่",
            # "เทศบาลตำบลโคกสูง",
            # "เทศบาลตำบลทุ่งทอง",
            # "เทศบาลตำบลบ้านเขว้า",
            # "เทศบาลตำบลตลาดแร้ง",
            # "เทศบาลตำบลลุ่มลำชี",
            # "เทศบาลตำบลคอนสวรรค์",
            # "เทศบาลตำบลเกษตรสมบูรณ์",
            # "เทศบาลตำบลบ้านเดื่อ",
            # "เทศบาลตำบลบ้านเป้า",
            # "เทศบาลตำบลหนองบัวแดง",
            # "เทศบาลตำบลหลวงศิริ",
            # "เทศบาลตำบลจัตุรัส",
            # "เทศบาลตำบลหนองบัวใหญ่",
            # "เทศบาลตำบลหนองบัวโคก",
            # "เทศบาลตำบลบำเหน็จณรงค์",
            # "เทศบาลตำบลบ้านเพชร",
            # "เทศบาลตำบลหนองบัวระเหว",
            # "เทศบาลตำบลห้วยแย้",
            # "เทศบาลตำบลโคกสะอาด",
            # "เทศบาลตำบลเทพสถิต",
            # "เทศบาลตำบลภูเขียว",
            # "เทศบาลตำบลบ้านแก้ง",
            # "เทศบาลตำบลบ้านเพชรภูเขียว",
            # "เทศบาลตำบลธาตุทอง",
            # "เทศบาลตำบลบ้านแท่น",
            # "เทศบาลตำบลบ้านเต่า",
            # "เทศบาลตำบลแก้งคร้อ",
            # "เทศบาลตำบลนาหนองทุ่ม",
            # "เทศบาลตำบลหนองสังข์",
            # "เทศบาลตำบลคอนสาร",
            # "เทศบาลตำบลห้วยยาง",
            # "เทศบาลตำบลทุ่งลุยลาย",

            "AO_757AG_เทศบาลตำบลบ้านตาด.xlsx",
            "AO_7526K_เทศบาลตำบลบ้านหลวง.xlsx",
            "AO_7526N_เทศบาลตำบลบ้านแปะ.xlsx",
        ]

        # file_paths = [
        #     f for f in file_paths
        #     if any(i in f for i in interested_bud_units)
        # ]

        # assert len(file_paths) == len(interested_bud_units), \
        #     'Not all interested budgetary units found {} != {}'.format(
        #         file_paths, interested_bud_units
        #     )

        logger.info('Processing {} files for {}'.format(
            len(file_paths), ministry_name
        ))

        # file_paths = [f for f in file_paths if '11012' in f]

        logger.info(f'Processing {ministry_name}')

        ministry_list.append(ministry_name)
        ministry_file_list.append(file_paths)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(
            build_tree_for_ministry,
            ministry_list,
            ministry_file_list
        )


if __name__ == '__main__':
    main()
