# CLAUDE.md

## Project Overview

Thailand Budget PDF/XLSX to CSV project. Extracts Thai government budget data (เล่มขาว-แดง / White-Red Book) from PDF and XLSX into structured CSV and JSON. Currently on branch `2567`.

## Quick Reference

```bash
# Install
uv sync

# Run all commands with uv
uv run python <script.py>

# Run tests
uv run pytest
```

## Architecture

### Core Library: `thbud/`

- `thbud/model/budget.py` — `BudgetItem` (tree node using `anytree.NodeMixin`) and `BudgetType` enum (MINISTRY > BUDGETARY_UNIT > BUDGET_PLAN > PROJECT/OUTPUT > BUDGET_DETAIL)
- `thbud/textextract/documenttext.py` — `DocumentText` (PDF) and `XLSXDocumentText` (Excel) readers. **Page ranges use exclusive end** (`range(start, end)` semantics)
- `thbud/textextract/pdf_to_tree.py` — `get_entries()` parses text lines, `extract_tree_levels()` builds the hierarchy
- `thbud/textextract/text.py` — `WordText`, `LineText`, `PageText` data classes
- `thbud/tableparser/` — table detection in PDF page images
- `thbud/build_csv.py` — converts `BudgetItem` tree to CSV rows

### Extraction Scripts

| Script | Purpose |
|--------|---------|
| `extract_budget_units.py` | Parse PDF TOC (สารบัญ) to create `budget_units.csv` index |
| `run_budget_extraction.py` | Extract budget details from PDFs using page ranges in `budget_units.csv` |
| `convertxlsx.py` | Extract from XLSX files (primary workflow for newer budgets) |
| `1_sheet_checker.py` | Local validation script (Colab equivalent: `1-sheet-checker.ipynb`) |

### Key Data Files

- `budget_units.csv` — Index of all budget units with columns: `ministry,budget_unit,start,end,doc`
- `output/` — Generated CSV and JSON files per ministry
- `pdfs/` — Source PDF files (not in git)
- `ministry_list.json` — Reference list of all ministries

## Important Conventions

### Page Ranges in `budget_units.csv`

- `start` = page label of first page of "7. รายละเอียดงบประมาณรายจ่ายจำแนกตามแผนงาน" (Budget details by expenditure)
- `end` = page label of first page to **exclude** (typically "8. รายงานสถานะฯ เงินนอกงบประมาณ")
- `DocumentText.get_lines_in_page()` uses `range(start_index, end_index)` — **end is exclusive**
- Page labels (strings) are mapped to page indices via `page_label_to_index` dict

### Budget Hierarchy

```
MINISTRY (กระทรวง)
  └── BUDGETARY_UNIT (หน่วยรับงบประมาณ)
       └── BUDGET_PLAN (แผนงาน)
            ├── PROJECT (โครงการ)
            │    └── BUDGET_DETAIL (รายการงบ)
            └── OUTPUT (ผลผลิต)
                 └── BUDGET_DETAIL (รายการงบ)
```

### CSV Output Format

- Hierarchy flattened using `name_1` through `name_11` columns ("staircase" pattern)
- `error_message` column for validation errors
- `budget_type` column identifies the level
- `amount`, `document`, `page` for each item

## Workflow

1. **PDF path**: `extract_budget_units.py` (TOC -> index) -> `run_budget_extraction.py` (pages -> CSV/JSON)
2. **XLSX path**: `convertxlsx.py` (XLSX -> CSV/JSON)
3. **Validation**: Upload CSVs to Google Sheets -> run `1-sheet-checker.ipynb` in Colab
4. **Final output**: Run `1-build-final-budget-items.ipynb` in Colab -> publishes structured dataset

## Dependencies

Python 3.10+, pymupdf (fitz), pillow, anytree, pandas, openpyxl, opencv-python
