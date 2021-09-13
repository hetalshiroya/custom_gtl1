# -*- coding: utf-8 -*-
{
    'name': 'Dynamic Sales Terms and Condition',
    'version': '0.1',
    'category': 'Facility',
    'license': 'OPL-1',
    'price': 25.00,
    'images': ['static/description/sale002.png'],
    'author': 'oranga',
    'currency': 'EUR',
    'summary': 'Sales Terms, Conditions, Agreements, Contracts in Quotation and Sale order',
    'description': """
    Warranty List
    Sales Warranty Cards
    Warranty Template
    Design Sales agreements
    Agreements sales
""",
    'depends': ['base', 'mail', 'sale', 'account','stock', 'purchase'],
    'data': [
        'security/ir.model.access.csv',
        #'report/letter_print.xml',
        'views/sale_letter_pad.xml',
        'views/term_view.xml',
    ],
    'installable': True,
    'application': True,
}