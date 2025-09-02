# Thailand Budget PDF to CSV Project


The **Thailand Budget PDF to CSV** project is an open-source initiative designed to transform unstructured Thai government budget data from PDF and XLSX formats into structured, machine-readable CSV and JSON files. Initiated by the Move Forward Party and volunteer developers, this project addresses the critical need for open and accessible government financial data, enabling enhanced transparency and public accountability.

This repository contains the core scripts, documentation, and tools used to extract, parse, validate, and convert the "White-Red Book" (เล่มขาว-แดง) budget documents. The project has evolved to adapt to changing data realities, moving from complex OCR-based PDF processing to a streamlined workflow leveraging government-provided XLSX files.

## Features

*   **Multi-format Ingestion:** Supports both legacy PDF documents (via OCR) and modern XLSX files for budget data extraction.
*   **Hierarchical Parsing:** Extracts and reconstructs the nested hierarchy of budget items (Ministries, Budgetary Units, Plans, Projects, Outputs, Budget Details).
*   **Structured Output:** Generates data in two primary formats:
    *   **JSON:** For a direct, tree-like representation of the budget hierarchy.
    *   **CSV:** For tabular data suitable for analysis, validation, and spreadsheet-based editing.
*   **Collaborative Validation Workflow:** Integrates with Google Sheets and Colab notebooks for interactive, community-driven data validation, including summation checks and structural integrity.
*   **Scalable Processing:** Utilizes parallel processing for efficient handling of multiple budget documents.
*   **Error Reporting:** Provides clear error messages and logging for issues encountered during extraction and validation.

## Getting Started

This section guides you through setting up and running the project locally and leveraging the Google Colab validation workflow.

### Prerequisites

*   Python 3.8+
*   Git
*   (For Google Colab / GDrive integration): A Google Account with access to Google Drive and the ability to authenticate `gspread`.

### Local Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/napatswift/wv-th-bdgt.git
    cd wv-th-bdgt
    git checkout 2567
    ```
2.  **Install dependencies:**
    It is highly recommended to use a virtual environment.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```
3.  **Google Cloud Authentication (for Colab/GSpread):**
    The Colab notebooks (`1-sheet-checker.ipynb`, `1-build-final-budget-items.ipynb`) rely on `google.colab.auth` and `gspread` for Google Drive and Google Sheets API access. When running these notebooks in Colab, you will be prompted to authenticate your Google account. Ensure this account has read/write access to the target Google Spreadsheets.

### Configuration

The Colab notebooks require specific Google Spreadsheet keys and the target fiscal year. Update these variables within the respective `.ipynb` files:

*   `GOOGLE_SPREADSHEET_KEY`: Found in `1-sheet-checker.ipynb`. This key points to the Google Sheet used for intermediate validation. Example: `https://docs.google.com/spreadsheets/d/ABCDEF/edit` implies `ABCDEF` is the key.
*   `BUDGET_YEAR`: Found in `1-build-final-budget-items.ipynb`. Specifies the fiscal year being processed (e.g., `'2569'` for 2569 BE / 2026 CE).
*   `BUDGET_TREE_GSPREADSHEET_KEY`: Found in `1-build-final-budget-items.ipynb`. Points to the Google Sheet containing the validated budget tree data. This is typically the same as `GOOGLE_SPREADSHEET_KEY`.
*   `BUDGET_LIST_GSPREADSHEET_KEY`: Found in `1-build-final-budget-items.ipynb`. Points to the Google Sheet where the final structured budget list will be published.

## Usage

The project workflow consists of two main stages: local automated extraction from XLSX files and collaborative validation/finalization using Google Colab.

### 1. Automated Extraction from XLSX (`convertxlsx.py`)

This script processes raw XLSX budget documents, extracts their hierarchical structure, and generates initial CSV and JSON outputs for each ministry.

1.  **Prepare Input Data:**
    *   Organize the official XLSX budget files into a directory structure where parent folders represent ministries or major administrative units.
    *   Example:
        ```
        ./ฉบับร่างพระราชบัญญัติงบประมาณรายจ่าย (ร่าง พ.ร.บ.) (Excel)/
        ├── กระทรวงการคลัง/
        │   ├── งบประมาณปี69-กรมสรรพากร.xlsx
        │   └── งบประมาณปี69-สำนักงานเศรษฐกิจการคลัง.xlsx
        └── กระทรวงศึกษาธิการ/
            └── งบประมาณปี69-สำนักงานคณะกรรมการการศึกษาขั้นพื้นฐาน.xlsx
        ```
    *   The script expects files to be separated by ministries and budgetary units, as provided by the government. Merging across multiple XLSX files for a single ministry's budget is not a currently supported or encountered scenario.

2.  **Run the Extraction Script:**
    Navigate to the project root and execute `convertxlsx.py`:
    ```bash
    python wv-th-bdgt/convertxlsx.py
    ```
    *   The script will scan the configured input directory (default: `./ฉบับร่างพระราชบัญญัติงบประมาณรายจ่าย (ร่าง พ.ร.บ.) (Excel)/`).
    *   It will process each XLSX file, identify budget sections, and build `BudgetItem` trees.
    *   Output CSV and JSON files for each ministry will be generated in the `OUTPUT_DIR` (default: `./output/`)

    **Key Technical Aspects of `convertxlsx.py`:**
    *   `XLSXDocumentText` Class: Reads Excel file content page-by-page.
    *   `is_start_page()` / `is_end_page()`: Utility functions to locate budget data boundaries using specific Thai text patterns.
    *   `get_entries()` / `extract_tree_levels()`: Functions to parse text lines and infer hierarchy based on cell indentation.
    *   `ThreadPoolExecutor`: Enables parallel processing of ministries for efficiency.
    *   **Output Schema:** CSV output flattens the hierarchy using `name_1` to `name_N` columns, while JSON maintains the nested structure.

### 2. Collaborative Validation and Finalization (Google Colab)

This stage involves uploading the locally generated CSVs to Google Sheets for validation and then using Colab notebooks to apply checks and produce the final, clean dataset.

1.  **Prepare for Validation:**
    *   Create a new folder in Google Shared Drive for the current fiscal year (e.g., "2599").
    *   Copy the `1-validation` and `2-build-csv` subdirectories (from this repository) into this new shared drive folder.
    *   Upload the CSV files generated by `convertxlsx.py` into the "1-validation" folder. Rename/replace the placeholder `Budget Tree For Validation.xlsx` if it exists, ensuring the uploaded CSVs are organized as individual worksheets within a single Google Spreadsheet.
    *   Update the `GOOGLE_SPREADSHEET_KEY` in `1-sheet-checker.ipynb` to point to this new validation spreadsheet.

2.  **Run Validation Checks (**`1-sheet-checker.ipynb`**):**
    *   Open `1-sheet-checker.ipynb` in Google Colab (File > Open in playground mode).
    *   Run all cells (`Runtime > Run all`).
    *   The script will connect to the specified Google Sheet and iterate through its worksheets.
    *   `validateChildrenAmountSum(worksheet, curr_fiscal_year)` function performs:
        *   **Hierarchical Summation Validation:** Checks if `amount` for parent items matches the sum of their direct children.
        *   **Metadata Presence:** Verifies required fields like `page`, `document`, `budget_type`.
        *   **Budget Type Hierarchy:** Validates that parent-child `budget_type` relationships are consistent (e.g., `BUDGETARY_UNIT` -> `BUDGET_PLAN`).
        *   **Category Level 1 Check:** Ensures `OUTPUT` or `PROJECT` items have appropriate `CATEGORY_LV1` values.
    *   Any validation errors will be written directly into the `error_message` column of the corresponding row in the Google Sheet. These errors are **non-blocking** for subsequent steps, allowing for human review and manual correction.

3.  **Manual Correction and Review:**
    *   Volunteers review the Google Sheet, particularly the `error_message` column.
    *   Corrections are made directly in the Google Sheet. In cases of summation errors where the source document itself is ambiguous, issues can be commented on in the sheet and ignored by the final converter. Publicly reported issues are tracked on GitHub.

4.  **Build Final Budget Items (**`1-build-final-budget-items.ipynb`**):**
    *   Once validation is complete (or sufficiently reviewed), open `1-build-final-budget-items.ipynb` in Google Colab.
    *   Verify `BUDGET_YEAR`, `BUDGET_TREE_GSPREADSHEET_KEY`, and `BUDGET_LIST_GSPREADSHEET_KEY` are correctly set.
    *   Run all cells.
    *   This script reads the (validated) data from the `BUDGET_TREE_GSPREADSHEET_KEY`, reconstructs the `BudgetItem` tree, and flattens it into a standardized Pandas DataFrame.
    *   The DataFrame is then published as a new worksheet (named `YYYY-MM-DD#`) in the Google Sheet specified by `BUDGET_LIST_GSPREADSHEET_KEY`. This sheet serves as the project's final, clean, and structured budget data output.

## Data Structure

### 1. JSON (Hierarchical Representation)

The JSON output provides a direct, nested representation of the budget hierarchy, preserving the parent-child relationships between budget items.

```json
{
  "budget_type": "PROJECT",
  "name": "Example Project",
  "amount": 1000000.0,
  "document": "path/to/Example Document",
  "page": 1,
  "fiscal_year_budget": [
    {
      "year": 2022,
      "year_end": null,
      "amount": 500000.0
    },
    {
      "year": 2023,
      "year_end": null,
      "amount": 500000.0
    }
  ],
  "children": [
    {
      "budget_type": "BUDGET_DETAIL",
      "name": "Example Output 1",
      "amount": 500000.0,
      "document": "path/to/Example Document",
      "page": 2,
      "fiscal_year_budget": [
        {
          "year": 2022,
          "year_end": null,
          "amount": 250000.0
        },
        {
          "year": 2023,
          "year_end": null,
          "amount": 250000.0
        }
      ],
      "children": []
    }
  ]
}
```

The `budget_type` field can be one of the following enumerations, representing a level in the budget hierarchy:

*   `MINISTRY`
*   `BUDGETARY_UNIT`
*   `BUDGET_PLAN`
*   `PROJECT`
*   `OUTPUT`
*   `BUDGET_DETAIL`
*   `FISCAL_YEAR_BUDGET` (used for yearly budget breakdowns within a parent item)

### 2. CSV For Validating And Editing (Tabular Representation)

The CSV format provides a flattened, tabular view of the budget data, suitable for spreadsheet-based validation, editing, and simplified data analysis. The hierarchical structure is represented using `name_N` columns, creating a "staircase" effect.

| Column            | Description                                                                                                                                              |
| :---------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `error_message`   | Contains validation error messages if the budget item is invalid (generated by `1-sheet-checker.ipynb`).                                                 |
| `budget_type`     | The type of budget item: `MINISTRY`, `BUDGETARY_UNIT`, `BUDGET_PLAN`, `PROJECT`, `OUTPUT`, `BUDGET_DETAIL`, `FISCAL_YEAR_BUDGET`.                      |
| `name_1`          | Name of the budgetary unit at level 1 (e.g., Ministry name).                                                                                             |
| `name_2`          | Name of the budgetary unit at level 2 (e.g., Department name).                                                                                           |
| ...               | ... (Continues up to `name_N` where `N` is the maximum number of hierarchy levels identified).                                                           |
| `amount`          | The total allocated amount for this budget item.                                                                                                         |
| `document`        | Path or reference to the source document (e.g., `path/to/Example Document`). Null for `FISCAL_YEAR_BUDGET` entries.                                        |
| `page`            | Page number within the source document where this item is found. Null for `FISCAL_YEAR_BUDGET` entries.                                                  |
| `fiscal_year`     | The specific fiscal year for a `FISCAL_YEAR_BUDGET` entry. Null for other `budget_type`s.                                                                |
| `fiscal_year_end` | The end fiscal year for a `FISCAL_YEAR_BUDGET` entry (e.g., for multi-year obligations). Null for other `budget_type`s or single-year budgets.           |
| `REF_DOC`         | (Final CSV only) Reference document identifier.                                                                                                          |
| `REF_PAGE_NO`     | (Final CSV only) Reference page number.                                                                                                                  |
| `MINISTRY`        | (Final CSV only) Top-level Ministry name.                                                                                                                |
| `BUDGETARY_UNIT`  | (Final CSV only) Specific Budgetary Unit.                                                                                                                |
| `BUDGET_PLAN`     | (Final CSV only) The overall Budget Plan.                                                                                                                |
| `CROSS_FUNC?`     | (Final CSV only) Indicates if it's a cross-functional budget.                                                                                            |
| `OUTPUT`          | (Final CSV only) Program Output description.                                                                                                             |
| `PROJECT`         | (Final CSV only) Project description.                                                                                                                    |
| `CATEGORY_LVX`    | (Final CSV only) Standardized budget categorization levels (e.g., `CATEGORY_LV1` for "งบลงทุน").                                                         |
| `ITEM_DESCRIPTION`| (Final CSV only) Detailed description of the budget item.                                                                                                |
| `OBLIGED?`        | (Final CSV only) Indicates if the budget is an obligation (e.g., multi-year commitment).                                                                 |

#### Example (CSV for Validation/Editing)

Derived from the JSON example above, a simplified CSV representation for validation might look like this:

```csv
error_message,budget_type,name_1,name_2,amount,document,page,fiscal_year,fiscal_year_end
,PROJECT,"Example Project",,1000000.0,"path/to/Example Document",1,,
,FISCAL_YEAR_BUDGET,,,,,2022,500000.0
,FISCAL_YEAR_BUDGET,,,,,2023,500000.0
,BUDGET_DETAIL,,"Example Output 1",500000.0,"path/to/Example Document",2,,
,FISCAL_YEAR_BUDGET,,,,,2022,250000.0
,FISCAL_YEAR_BUDGET,,,,,2023,250000.0
```

*Note: The actual CSV output from `1-build-final-budget-items.ipynb` will have a more extensive set of columns as listed in the table above, including explicit Ministry, Budgetary Unit, and Category levels.*
