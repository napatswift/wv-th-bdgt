from thbud.model import BudgetItem, FiscalYearBudget, BudgetType
from thbud import build_csv


def test_build_csv_2_levels():
    root = BudgetItem(
        'MINISTRY',
        'กระทรวงการคลัง',
        0,
        '2563.3.1',
        0,
        children=[
            BudgetItem(
                'BUDGETARY_UNIT',
                'หน่วยรับงบ',
                0,
                '2563.3.1',
                10,
                children=[
                    BudgetItem(
                        'BUDGET_PLAN',
                        'แผนงาน',
                        0,
                        '2563.3.1',
                        11,
                        children=[
                            BudgetItem(
                                'BUDGET_DETAIL',
                                'รายการงบ 1',
                                300,
                                '2563.3.1',
                                12,
                                children=[
                                    BudgetItem(
                                        'BUDGET_DETAIL',
                                        'รายการงบ 2',
                                        100,
                                        '2563.3.1',
                                        12,
                                    ),
                                    BudgetItem(
                                        'BUDGET_DETAIL',
                                        'รายการงบ 3',
                                        200,
                                        '2563.3.1',
                                        12,
                                    )
                                ]
                            )
                        ]
                    )
                ]
            )
        ]
    )

    expected = [
        {
            'REF_DOC': '2563.3.1',
            'REF_PAGE_NO': 12,
            'MINISTRY': 'กระทรวงการคลัง',
            'BUDGETARY_UNIT': 'หน่วยรับงบ',
            'CROSS_FUNC?': False,
            'BUDGET_PLAN': 'แผนงาน',
            'OUTPUT': '',
            'PROJECT': '',
            'CATEGORY_LV1': 'รายการงบ 1',
            'ITEM_DESCRIPTION': 'รายการงบ 2',
            'FISCAL_YEAR': None,
            'AMOUNT': 100,
            'OBLIGED?': False
        },
        {
            'REF_DOC': '2563.3.1',
            'REF_PAGE_NO': 12,
            'MINISTRY': 'กระทรวงการคลัง',
            'BUDGETARY_UNIT': 'หน่วยรับงบ',
            'CROSS_FUNC?': False,
            'BUDGET_PLAN': 'แผนงาน',
            'OUTPUT': '',
            'PROJECT': '',
            'CATEGORY_LV1': 'รายการงบ 1',
            'ITEM_DESCRIPTION': 'รายการงบ 3',
            'FISCAL_YEAR': None,
            'AMOUNT': 200,
            'OBLIGED?': False
        },
    ]

    assert build_csv(root) == expected


def test_build_csv_3_levels():
    root = BudgetItem(
        'MINISTRY',
        'กระทรวงการคลัง',
        0,
        '2563.3.1',
        0,
        children=[
            BudgetItem(
                'BUDGETARY_UNIT',
                'หน่วยรับงบ',
                0,
                '2563.3.1',
                10,
                children=[
                    BudgetItem(
                        'BUDGET_PLAN',
                        'แผนงาน',
                        0,
                        '2563.3.1',
                        11,
                        children=[
                            BudgetItem(
                                'BUDGET_DETAIL',
                                'รายการงบ 1',
                                300,
                                '2563.3.1',
                                12,
                                children=[
                                    BudgetItem(
                                        'BUDGET_DETAIL',
                                        'รายการงบ 2',
                                        100,
                                        '2563.3.1',
                                        12,
                                        children=[
                                            BudgetItem(
                                                'BUDGET_DETAIL',
                                                'รายการงบ 3',
                                                50,
                                                '2563.3.1',
                                                12,
                                            ),
                                            BudgetItem(
                                                'BUDGET_DETAIL',
                                                'รายการงบ 4',
                                                50,
                                                '2563.3.1',
                                                12,
                                            )
                                        ]
                                    )
                                ]
                            )
                        ]
                    )
                ]
            )
        ]
    )

    expected = [
        {
            'REF_DOC': '2563.3.1',
            'REF_PAGE_NO': 12,
            'MINISTRY': 'กระทรวงการคลัง',
            'BUDGETARY_UNIT': 'หน่วยรับงบ',
            'CROSS_FUNC?': False,
            'BUDGET_PLAN': 'แผนงาน',
            'OUTPUT': '',
            'PROJECT': '',
            'CATEGORY_LV1': 'รายการงบ 1',
            'CATEGORY_LV2': 'รายการงบ 2',
            'ITEM_DESCRIPTION': 'รายการงบ 3',
            'FISCAL_YEAR': None,
            'AMOUNT': 50,
            'OBLIGED?': False
        },
        {
            'REF_DOC': '2563.3.1',
            'REF_PAGE_NO': 12,
            'MINISTRY': 'กระทรวงการคลัง',
            'BUDGETARY_UNIT': 'หน่วยรับงบ',
            'CROSS_FUNC?': False,
            'BUDGET_PLAN': 'แผนงาน',
            'OUTPUT': '',
            'PROJECT': '',
            'CATEGORY_LV1': 'รายการงบ 1',
            'CATEGORY_LV2': 'รายการงบ 2',
            'ITEM_DESCRIPTION': 'รายการงบ 4',
            'FISCAL_YEAR': None,
            'AMOUNT': 50,
            'OBLIGED?': False
        }
    ]

    assert build_csv(root) == expected


def test_build_csv_with_fiscal_year_budget():
    root = BudgetItem(
        'MINISTRY',
        'กระทรวงการคลัง',
        0,
        '2563.3.1',
        0,
        children=[
            BudgetItem(
                'BUDGETARY_UNIT',
                'หน่วยรับงบ',
                0,
                '2563.3.1',
                10,
                children=[
                    BudgetItem(
                        'BUDGET_PLAN',
                        'แผนงาน',
                        0,
                        '2563.3.1',
                        11,
                        children=[
                            BudgetItem(
                                'BUDGET_DETAIL',
                                'รายการงบ 1',
                                300,
                                '2563.3.1',
                                12,
                                children=[
                                    BudgetItem(
                                        'BUDGET_DETAIL',
                                        'รายการงบ 2',
                                        100,
                                        '2563.3.1',
                                        12,
                                        children=[
                                            BudgetItem(
                                                'BUDGET_DETAIL',
                                                'รายการงบ 3',
                                                50,
                                                '2563.3.1',
                                                12,
                                                fiscal_year_budget=[
                                                    FiscalYearBudget(
                                                        'ปี 2563 50 บาท',
                                                        2563,
                                                        50,
                                                    ),
                                                    FiscalYearBudget(
                                                        'ปี 2564 20 บาท',
                                                        2564,
                                                        20,
                                                    ),
                                                ]
                                            ),
                                            BudgetItem(
                                                'BUDGET_DETAIL',
                                                'รายการงบ 4',
                                                50,
                                                '2563.3.1',
                                                12,
                                            )
                                        ]
                                    )
                                ]
                            )
                        ]
                    )
                ]
            )
        ]
    )

    expected = [
        {
            'REF_DOC': '2563.3.1',
            'REF_PAGE_NO': 12,
            'MINISTRY': 'กระทรวงการคลัง',
            'BUDGETARY_UNIT': 'หน่วยรับงบ',
            'CROSS_FUNC?': False,
            'BUDGET_PLAN': 'แผนงาน',
            'OUTPUT': '',
            'PROJECT': '',
            'CATEGORY_LV1': 'รายการงบ 1',
            'CATEGORY_LV2': 'รายการงบ 2',
            'ITEM_DESCRIPTION': 'รายการงบ 3',
            'FISCAL_YEAR': 2563,
            'AMOUNT': 50,
            'OBLIGED?': True
        },
        {
            'REF_DOC': '2563.3.1',
            'REF_PAGE_NO': 12,
            'MINISTRY': 'กระทรวงการคลัง',
            'BUDGETARY_UNIT': 'หน่วยรับงบ',
            'CROSS_FUNC?': False,
            'BUDGET_PLAN': 'แผนงาน',
            'OUTPUT': '',
            'PROJECT': '',
            'CATEGORY_LV1': 'รายการงบ 1',
            'CATEGORY_LV2': 'รายการงบ 2',
            'ITEM_DESCRIPTION': 'รายการงบ 3',
            'FISCAL_YEAR': 2564,
            'AMOUNT': 20,
            'OBLIGED?': True
        },
        {
            'REF_DOC': '2563.3.1',
            'REF_PAGE_NO': 12,
            'MINISTRY': 'กระทรวงการคลัง',
            'BUDGETARY_UNIT': 'หน่วยรับงบ',
            'CROSS_FUNC?': False,
            'BUDGET_PLAN': 'แผนงาน',
            'OUTPUT': '',
            'PROJECT': '',
            'CATEGORY_LV1': 'รายการงบ 1',
            'CATEGORY_LV2': 'รายการงบ 2',
            'ITEM_DESCRIPTION': 'รายการงบ 4',
            'FISCAL_YEAR': None,
            'AMOUNT': 50,
            'OBLIGED?': False
        }
    ]

    assert build_csv(root) == expected


def test_build_csv_with_output():
    root = BudgetItem(
        'MINISTRY',
        'กระทรวงการคลัง',
        0,
        '2563.3.1',
        0,
        children=[
            BudgetItem(
                'BUDGETARY_UNIT',
                'หน่วยรับงบ',
                0,
                '2563.3.1',
                10,
                children=[
                    BudgetItem(
                        'BUDGET_PLAN',
                        'แผนงาน',
                        0,
                        '2563.3.1',
                        11,
                        children=[
                            BudgetItem(
                                'OUTPUT',
                                'ผลผลิต',
                                0,
                                '2563.3.1',
                                11,
                                children=[
                                    BudgetItem(
                                        'BUDGET_DETAIL',
                                        'รายการงบ 1',
                                        300,
                                        '2563.3.1',
                                        12,
                                        children=[
                                            BudgetItem(
                                                'BUDGET_DETAIL',
                                                'รายการงบ 2',
                                                100,
                                                '2563.3.1',
                                                12,
                                                children=[
                                                    BudgetItem(
                                                        'BUDGET_DETAIL',
                                                        'รายการงบ 3',
                                                        50,
                                                        '2563.3.1',
                                                        12,
                                                    ),
                                                    BudgetItem(
                                                        'BUDGET_DETAIL',
                                                        'รายการงบ 4',
                                                        50,
                                                        '2563.3.1',
                                                        12,
                                                    )
                                                ]
                                            )
                                        ]
                                    )
                                ]
                            )
                        ]
                    )
                ]
            )
        ]
    )

    expected = [
        {
            'REF_DOC': '2563.3.1',
            'REF_PAGE_NO': 12,
            'MINISTRY': 'กระทรวงการคลัง',
            'BUDGETARY_UNIT': 'หน่วยรับงบ',
            'CROSS_FUNC?': False,
            'BUDGET_PLAN': 'แผนงาน',
            'OUTPUT': 'ผลผลิต',
            'PROJECT': '',
            'CATEGORY_LV1': 'รายการงบ 1',
            'CATEGORY_LV2': 'รายการงบ 2',
            'ITEM_DESCRIPTION': 'รายการงบ 3',
            'FISCAL_YEAR': None,
            'AMOUNT': 50,
            'OBLIGED?': False
        },
        {
            'REF_DOC': '2563.3.1',
            'REF_PAGE_NO': 12,
            'MINISTRY': 'กระทรวงการคลัง',
            'BUDGETARY_UNIT': 'หน่วยรับงบ',
            'CROSS_FUNC?': False,
            'BUDGET_PLAN': 'แผนงาน',
            'OUTPUT': 'ผลผลิต',
            'PROJECT': '',
            'CATEGORY_LV1': 'รายการงบ 1',
            'CATEGORY_LV2': 'รายการงบ 2',
            'ITEM_DESCRIPTION': 'รายการงบ 4',
            'FISCAL_YEAR': None,
            'AMOUNT': 50,
            'OBLIGED?': False
        }
    ]

    assert build_csv(root) == expected
