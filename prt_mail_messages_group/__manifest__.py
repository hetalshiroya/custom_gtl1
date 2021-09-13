###################################################################################
# 
#    Copyright (C) Cetmix OÜ
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###################################################################################

# -*- coding: utf-8 -*-
{
    'name': 'Mail Messages Group.'
            ' Special Group for "Messages" menu',
    'version': '11.0.1.0',
    'summary': """Optional extension for free 'Mail Messages Easy' app""",
    'author': 'Ivan Sokolov, Cetmix',
    'category': 'Discuss',
    'license': 'LGPL-3',
    'website': 'https://cetmix.com',
    'description': """
Limit access to "Messages" menu. Adds special Group for "Messages" menu
""",
    'depends': ['prt_mail_messages'],
    'images': ['static/description/banner.png'],
    'data': [
        'security/groups.xml',
        'views/prt_mail_group.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False
}
