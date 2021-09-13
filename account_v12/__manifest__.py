# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

{
    'name' : 'Account Report',
    'summary': '''Balance Sheet
Profit and Loss
Trial Balance
Partner Ledger
Partner Aeging report
Customer and Supplier Aeging report
Tax Report
Journal Audit Report with pdf and excel formats with multiple filters
Journal Audit Report
Aged Partner Balance Report   
Partner Ledger Report
General Ledger Report 
Trial Balance Report
Account Tax Report    
Balance Sheet Report
Profit & Loss Report  
Due Payments Report
Payment Receipt Report    
Monthly Balance Report
Quarterly Balance Report''',
    'version': '12.0.1.0.1',
    'description': '''Balance Sheet
Profit and Loss
Trial Balance
Partner Ledger
Partner Aeging report
Customer and Supplier Aeging report
Tax Report
Journal Audit Report with pdf and excel formats with multiple filters
Journal Audit Report
Aged Partner Balance Report   
Partner Ledger Report
General Ledger Report 
Trial Balance Report
Account Tax Report    
Balance Sheet Report
Profit & Loss Report  
Due Payments Report
Payment Receipt Report    
Monthly Balance Report
Quarterly Balance Report''',
    'category': 'Accounting',
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'maintainer': 'Serpent Consulting Services Pvt. Ltd.',
    'website': 'http://www.serpentcs.com',
    'depends' : ['account'],
    'data': [
            'security/security.xml',
            'security/ir.model.access.csv',
            #'views/web_layout.xml',
            # 'views/account_menuitem.xml',
            'views/account_view.xml',
            'views/report_journal.xml',
            'wizard/account_report_print_journal_view.xml',
            'views/account_report.xml',
            'views/report_overdue.xml',
            'wizard/account_report_aged_partner_balance_view.xml',
            'views/report_agedpartnerbalance.xml',
            'wizard/account_report_partner_ledger_view.xml',
            'views/report_partnerledger.xml',
            'wizard/account_report_general_ledger_view.xml',
            'views/report_generalledger.xml',
            'wizard/account_report_trial_balance_view.xml',
            'views/report_trialbalance.xml',
            'data/account_financial_report_data.xml',
            'wizard/account_financial_report_view.xml',
            'views/report_financial.xml',
            'views/account_report_payment_receipt_templates.xml',
            'views/report_tax.xml',
            'wizard/account_report_tax_view.xml',
            'wizard/account_report_template_wizard.xml',
            'views/account_balance_full_temp.xml',
            'views/account_financial_report_view.xml',
            'views/account_full_qtr_cols.xml',
            'views/account_full_13_cols.xml',

    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'license': 'AGPL-3',
    'auto_install': False,
    'application': False,
    'price': 49,
    'currency': 'EUR',
}
