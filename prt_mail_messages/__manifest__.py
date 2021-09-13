# -*- coding: utf-8 -*-
{
    'name': 'Mail Messages Easy.'
            ' Show all messages, Show sent messages, Reply to message, Forward message, Quote message, Move message'
            ' Email client style for messages views and more',
    'version': '12.0.5.1',
    'summary': """Read and manage all Odoo messages in one place!""",
    'author': 'Ivan Sokolov, Cetmix',
    'category': 'Discuss',
    'license': 'LGPL-3',
    'website': 'https://cetmix.com',
    'description': """
 Show all messages, Show sent message, Reply to messages, Forward messages, Move messages, Quote messages
""",
    'depends': ['base', 'mail'],
    'live_test_url': 'https://demo.cetmix.com',
    'images': ['static/description/banner.png'],

    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'security/rules.xml',
        'views/prt_mail.xml',
        'views/mail_assign.xml',
        'views/conversation.xml',
        'views/partner.xml',
        'views/actions.xml',
        'views/res_config_settings.xml',
        'data/data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False
}
