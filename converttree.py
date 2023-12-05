from thbud.textextract import DocumentText, get_entries, extract_tree_levels
import logging
import json
import pandas as pd

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    doc = DocumentText('test/data/budget-1page-15nodes-fiscalyear.pdf')
    entries = get_entries(doc.get_lines_in_page())
    logger.info('Total entries: {}'.format(len(entries)))

    root = extract_tree_levels(entries)

    with open('budget-1page-15nodes-fiscalyear.json', 'w') as f:
        json.dump(root.to_json(), f, indent=4, ensure_ascii=False)

    for ent in entries:
        logger.info(
            f'ENTRY::level={ent.level}, type={ent.itemtype}, text={ent}')
