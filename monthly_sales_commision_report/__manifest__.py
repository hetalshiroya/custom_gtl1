# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    "name": "Monthly Sales Commission Report",
    "version": "1.0.4",
    "author": "Laxicon Solution",
    "website": "https://laxicon.in",
    "category": "",
    "description": """
        Monthly Sales Commission Report
    """,
    "depends": ["account"],
    "data": [
        'wizard/sales_commission_report_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
