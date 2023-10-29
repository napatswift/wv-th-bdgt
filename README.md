## Data structure

### 1. JSON

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

### 2. CSV For Validating And Editing

| column          | description                                                                                             |
| --------------- | ------------------------------------------------------------------------------------------------------- |
| error_message   | error message if the budget is invalid                                                                  |
| budget_type     | `MINISTRY`, `BUDGETARY_UNIT`, `BUDGET_PLAN`, `PROJECT`, `OUTPUT`, `BUDGET_DETAIL`, `FISCAL_YEAR_BUDGET` |
| name_1          | name of the budgetary unit at level 1                                                                   |
| name_2          | name of the budgetary unit at level 2                                                                   |
| ...             | ...                                                                                                     |
| name_n          | name of the budgetary unit at level `n` when `n` is the number of levels of the budgetary hierarchy     |
| amount          | amount of the budget                                                                                    |
| document        | path to the document (if budget_type is `FISCAL_YEAR_BUDGET` then this field is null)                   |
| page            | page number of the document (if budget_type is `FISCAL_YEAR_BUDGET` then this field is null)            |
| fiscal_year     | fiscal year of the budget (if budget_type is not `FISCAL_YEAR_BUDGET` then this field is null)          |
| fiscal_year_end | fiscal year end of the budget (if budget_type is not `FISCAL_YEAR_BUDGET` then this field is null)      |

#### Example

From the JSON above, the CSV file will be:

```
error_message,budget_type,name_1,name_2,amount,document,page,fiscal_year,fiscal_year_end
,PROJECT,Example Project,,1000000.0,path/to/Example Document,1,,
,FISCAL_YEAR_BUDGET,,,500000.0,,,2022,
,FISCAL_YEAR_BUDGET,,,500000.0,,,2023,
,BUDGET_DETAIL,,Example Output 1,500000.0,path/to/Example Document,2,,
,FISCAL_YEAR_BUDGET,,,250000.0,,,2022,
,FISCAL_YEAR_BUDGET,,,250000.0,,,2023,
```
