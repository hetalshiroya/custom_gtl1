# -*- coding: utf-8 -*-
{
    "name": "GoExcel Logistics SQ",
    "version": "12.0.1.0.0",
    "category": "Transport",
    "license": 'LGPL-3',
    "summary": """Sales Quotation Enhancement""",
    'description': 'Sales Quotation Enhancement',
    "author": "Excelroot Technology Sdn Bhd",
    "depends": ['sale_management','sci_goexcel_freight'],
    'sequence': 2,
    'application': True,
    "data": [
        'reports/report_sq_inherit.xml',
        'views/sales_quotation_view.xml',
        'views/res_config_settings_view.xml',
        'views/sale_order_template.xml',
        'data/sq_mail_template_bl.xml',
    ],
}
