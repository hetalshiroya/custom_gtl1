# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Bank Reconciliation',
    'price': 129.0,
    'currency': 'USD',
    'version': '12.0.0.0.0',
    'category': 'Account',
    'license': 'Other proprietary',
    'sequence': 3,
    'summary': 'Bank Statement Reconciliation made simple.'
,
    'description': """
            This module allows you to reconcile bank statements with payments as like as tally
            """,
    'author': 'FOSS INFOTECH PVT LTD',
    'website': 'https://www.fossinfotech.com',
    'depends': ['base', 'account','account_cancel'],
    'data': [
            'wizard/bank_reconcile_view.xml',
            'views/account_payment_view.xml',
            'views/account_views.xml',
    ],
    'images': [
    'static/description/banner.png',
    'static/description/icon.png',
    'static/description/index.html'
    ],

    'installable': True,
    'auto_install': True,
    'application': True,
}
