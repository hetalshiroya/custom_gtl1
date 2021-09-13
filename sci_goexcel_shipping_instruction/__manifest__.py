# See LICENSE file for full copyright and licensing details.

{
    # Module Info.
    "name": "GoExcel Freight Shipping Instruction",
    "version": "12.0.1",
    "category": "",
    "license": 'OPL-1',
    "summary": """""",
    "description": """""",

    # Author
    "author": "Excelroot Technology Sdn Bhd",
    "website": "https://www.excelroot.com/",

    # Dependencies
    "depends": ['product', 'account', 'sci_goexcel_freight'],

    'css': ['static/src/css/style.css'],

    'sequence': 1,

    # Data
    "data": [
        'reports/si_report_carrier.xml',
        'reports/si_report.xml',
        'data/si_mail_template.xml',
        'views/si_view_inherit.xml',
        'wizard/shipping_instruction_wizard_view.xml'
    ],

    # Odoo App Store Specific
    'images': ['static/description/icon.png'],

    # Technical
    "installable": True,
}
