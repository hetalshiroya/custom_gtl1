# -*- coding: utf-8 -*-
{
    "name": "GoExcel Logistics Invoice",
    "version": "12.0.1.0.0",
    "category": "Transport",
    "license": 'LGPL-3',
    "summary": """Invoice/Vendor Bill Enhancement""",
    'description': 'Invoice/Vendor Bill Enhancement',
    "author": "Excelroot Technology Sdn Bhd",
    "depends": ['account','sci_goexcel_freight','sci_goexcel_transport'],
    'sequence': 2,
    'application': True,
    "data": [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/account_invoice_view.xml',
        'views/booking_view_inherit.xml',
        'views/job_cost_view.xml',
        'views/res_config_settings_view.xml',
        'views/res_user_views.xml',
        #'reports/report_invoice_inherit.xml',
        'views/document_attachment_view.xml',
        'views/account_voucher_view.xml',
        'wizards/job_cost_view.xml'
        #'reports/report_invoice.xml'


    ]
}
