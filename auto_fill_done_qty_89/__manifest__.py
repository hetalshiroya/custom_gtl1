# -*- coding: utf-8 -*-

{
    'name': 'Auto Fill Done Qty From Reserved Qty',
    'category': 'Warehouse',
    'summary': 'It will help you to input done qty in stock move lines of stock picking in the easier way.',
    'version': '1.0',
    'description': """""",
    'author': "Nirmay 89",
    'website': "https://apps.odoo.com/apps/modules/browse?author=Nirmay%2089",
    'license': "OPL-1",
    'price': "10",
    'currency': 'EUR',
    'depends': ['stock'],
    'data': [
        'views/stock_view.xml'
    ],
    'images':['static/description/main_screenshot.png'],
    'installable': True,
    'auto_install': True,
}
