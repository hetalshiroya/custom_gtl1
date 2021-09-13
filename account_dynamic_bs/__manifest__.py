# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

{
    'name': 'Dynamic Balance Sheet Report',
    'version': '12.0.0.1',
    'category': 'Accounting',
    'author': 'Pycus',
    'summary': 'Dynamic Balance Sheet Report with interactive drill down view and extra filters',
    'description': """
                This module support for viewing Balance Sheet report on the screen with 
                drilldown option. Option to download report into Pdf and Xlsx

                    """,
    "price": 45,
    "currency": 'EUR',
    'depends': ['account','accounting_pdf_reports','report_xlsx'],
    'data': [
             "views/assets.xml",
             "views/views.xml",
    ],
    'demo': [],
    'qweb':['static/src/xml/dynamic_bs_report.xml'],
    "images":['static/description/Dynamic_BS.gif'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
