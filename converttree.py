from thbud.textextract import read_lines, get_entries, extract_tree_levels
import logging
import json

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    lines = read_lines('test/data/budget-1page-5nodes.pdf')
    entries = get_entries(lines)
    logger.info('Total entries: {}'.format(len(entries)))

    root = extract_tree_levels(entries)

    with open('budget-1page-5nodes.json', 'w') as f:
        json.dump(root.to_json(), f, indent=4, ensure_ascii=False)

    for ent in entries:
        logger.info(
            f'ENTRY::level={ent.level}, type={ent.itemtype}, text={ent}')