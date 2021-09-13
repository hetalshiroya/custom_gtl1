# See LICENSE file for full copyright and licensing details.

{
    # Module Info.
    "name": "GoExcel Statement of Account",
    "version": "12.0.1.0.0",
    "category": "Generic Modules/Accounting",
    "license": 'OPL-1',
    "summary": """	Print & Send Statement of Account by invoice date/due date""",
    "description": """Print Statement of Account with invoice date/due date and Aging.
                      Send Email with the Statement of Account as attachment""",

    # Author
    "author": "Excelroot Technology Sdn Bhd",
    "website": "https://www.excelroot.com/",

    # Dependencies
    'depends': ['mail', 'base', 'account'],

    # Data
    "data": [
        'views/res_config_settings_view.xml',
        'report/report_menu.xml',
        'data/customer_statement_mail_template.xml',
        'report/customer_statement_template.xml',
        'wizard/customer_statement_views.xml',

    ],

    # Odoo App Store Specific
    'images': ['static/description/goexcel.jpg'],

    # Technical
    "application": True,
    "installable": True,
    'price': 89,
    'currency': 'EUR',
}
