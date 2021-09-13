# -*- coding: utf-8 -*-
# Copyright (c) 2015 ACSONE SA/NV (<http://acsone.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
{
    'name': "Show DB Name",

    'summary': """
       Show the database name on the top right of web page without needing to debug mode.""",

    'description': """
        By Installing this module, you will be able To see the database name on the top right of web page without needing to debug mode.
    """,
    'author': 'CorTex IT Solutions Ltd.',
    'website': 'https://cortexsolutions.net',
    'license': 'OPL-1',
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Tools',
    'version': '12.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['web'],

    # always loaded
    'data': [
        'views/show_db_name_views.xml',
    ],
    'installable': True,
    'auto_install': False,
 
}