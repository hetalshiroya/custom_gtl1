# Copyright 2018 Apruzzese Francesco <f.apruzzese@apuliasoftware.it>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Partner fax',
    'category': 'Extra Tools',
    'summary': 'Add fax number on partner',
    'version': '12.0.1.0.0',
    'license': 'AGPL-3',
    'author':  'Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/partner-contact',
    'depends': [
        'base_setup'
        ],
    'data': [
        'views/res_partner.xml',
        'views/res_company_views.xml',
        ],
    'installable': True,
}
