# -*- coding: utf-8 -*-
{
    'name': 'Invoice, Bill, Customer, Vendor Credit Note Approval Workflow',
    'summary': """Invoice, Bill,  Customer, Vendor Credit Note Approval Workflow""",
    'description': 'Invoice, Bill,  Customer, Vendor Credit Note Approval Workflow',

    'author': 'iPredict IT Solutions Pvt. Ltd.',
    'website': 'http://ipredictitsolutions.com',
    "support": "ipredictitsolutions@gmail.com",

    'category': 'Accounting',
    'version': '12.0.0.1.1',
    'depends': ['account'],

    'data': [
        'data/validate_invoice_bill_email_template.xml',
        'views/res_config_settings_view.xml',
        'views/account_invoice_view.xml',
    ],

    'license': "OPL-1",
    'price': 35,
    'currency': "EUR",

    "auto_install": False,
    "installable": True,

    'images': ['static/description/banner.png'],
}
