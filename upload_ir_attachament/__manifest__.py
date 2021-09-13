# -*- coding: utf-8 -*-
# Part of Laxicon Solution. See LICENSE file for full copyright and
# licensing details.

{
    'name': "Attachments Upload From Database",
    'summary': """
        Attachments Upload From Database.
        """,
    'description': """
        Attachments Upload From Database
    """,
    'author': "Laxicon Solution",
    'website': "https://www.laxicon.in",
    'category': 'Generic Modules',
    'version': '12.1',
    "price": 49,
    "currency": 'EUR',
    'license': 'OPL-1',
    # any module necessary for this one to work correctly
    'depends': ['base', 'google_drive_attachment'],
    # always loaded
    'data': [
        'data/scheduler_data.xml'
    ],
    'installable': True,
    'auto_install': False,
}
