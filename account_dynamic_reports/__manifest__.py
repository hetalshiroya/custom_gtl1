# -*- coding: utf-8 -*-
{
    'name' : 'All in one Dynamic Financial Reports v12',
    'version' : '12.0.5',
    'summary': "General Ledger Trial Balance Ageing Balance Sheet Profit and Loss Cash Flow Dynamic",
    'sequence': 15,
    'description': """
                    Odoo 12 Full Accouning, Odoo 12 All in one Accouning, PDF Reports, XLSX Reports,
                    Dynamic View, Drill down, Clickable, Pdf and Xlsx package, Odoo 12 Accounting,
                    Full Account Reports, Complete Accounting Reports, Financial Report for Odoo 12,
                    Financial Reports, Excel reports, Financial Reports in Excel, Ageing Report,
                    General Ledger, Partner Ledger, Trial Balance, Balance Sheet, Profit and Loss,
                    Financial Report Kit, Cash Flow Statements, Cash Flow Report, Cash flow
                    """,
    'category': 'Accounting/Accounting',
    "price": 100,
    'author': 'Pycus',
    'maintainer': 'Pycus Technologies',
    'website': '',
    'images': ['static/description/banner.gif'],
    'depends': ['account', 'account_fiscal_year', 'sci_goexcel_payment_receipt'],
    'data': [
             'security/ir.model.access.csv',
             'data/data_financial_report.xml',

             'views/views.xml',
             'views/res_company_view.xml',

             'views/general_ledger_view.xml',
             'views/partner_ledger_view.xml',
             'views/trial_balance_view.xml',
             'views/partner_ageing_view.xml',
             'views/financial_report_view.xml',
             'views/partner_payment_view.xml',
             'views/partner_invoice_view.xml',
             'views/analytic_report_view.xml',

             'wizard/general_ledger_view.xml',
             'wizard/partner_ledger_view.xml',
             'wizard/trial_balance_view.xml',
             'wizard/partner_ageing_view.xml',
             'wizard/financial_report_view.xml',
             'wizard/partner_payment_view.xml',
             'wizard/partner_invoice_view.xml',
             'wizard/analytic_report_view.xml'
             ],
    'demo': [],
    'license': 'OPL-1',
    'qweb': ['static/src/xml/view.xml',],
    'installable': True,
    'application': True,
    'auto_install': False,
}
