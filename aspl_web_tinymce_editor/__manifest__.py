# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################

{
    'name': 'TinyMCE Widget',
    'summary': 'Provides a widget for editing HTML fields using tinymce',
    'version': '1.2.0',
    'description': """Provides a widget for editing HTML fields using tinymce.""",
    'author': 'Acespritech Solutions Pvt. Ltd.',
    'category': 'Tools',
    'website': "http://www.acespritech.com",
    'price': 15.00,
    'currency': 'EUR',
    'depends': ['base', 'base_setup', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/template.xml',
        'views/res_config_view.xml',
    ],
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
