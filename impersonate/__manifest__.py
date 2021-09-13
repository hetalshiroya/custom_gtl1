# -*- coding: UTF-8 -*-

{
    'name': 'Impersonate',
    'version': '1.0.0',
    'author': "Advanced Accountancy OÜ",
    'website': "https://www.advancedaccountancy.org",
    'license': 'OPL-1',
    'category': 'Extra Tools',
    'description': """
Allows to impersonate other users.
    """,
    'depends': [
        'web',
    ],
    'data': [
        'security/security.xml',
        'views/res_users_view.xml',
        'views/impersonate_assets.xml',
        'wizard/impersonate_view.xml',
    ],
    'qweb': [
        'static/src/xml/templates.xml',
    ],
    'images': [
        'static/description/icon.png',
        'static/description/full_screenshot.png',
    ],
    'installable': True,
    'price': 30.0,
    'currency': 'EUR',
    
}
