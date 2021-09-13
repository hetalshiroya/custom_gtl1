# -*- coding: utf-8 -*-
{
    'name' : 'Bulk Debit./Credit note v12',
    'version' : '12.0.1',
    'summary': "Bulk creation of Debit/Credit note against invoices",
    'sequence': 15,
    'description': """
                    Bulk creation of Debit/Credit note against invoices
                    """,
    'category': 'Accounting/Accounting',
    "price": 0,
    'author': 'Pycus',
    'maintainer': 'Pycus Technologies',
    'website': '',
    #'images': ['static/description/banner.gif'],
    'depends': ['account','account_debitnote'],
    'data': [
             'wizard/bulk_refund_wizard_view.xml',
             'views/account_customer_debit_note.xml'
             ],
    'demo': [],
    'license': 'OPL-1',
    #'qweb': ['static/src/xml/view.xml',],
    'installable': True,
    'application': True,
    'auto_install': False,
}
