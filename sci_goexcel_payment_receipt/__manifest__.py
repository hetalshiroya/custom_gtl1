# See LICENSE file for full copyright and licensing details.

{
    # Module Info.
    "name": "GoExcel Payment Receipt",
    "version": "12.0.2.0.5",
    "category": "Account",
    "license": 'OPL-1',
    "summary": "Payment Receipt Print Out",
    "description": """Payment Receipt Print Out for Account Voucher""",

    # Author
    "author": "Excelroot Technology Sdn Bhd",
    "website": "https://www.excelroot.com/",

    # Dependencies
    "depends": ['mail', 'account', 'account_cancel', 'account_voucher', 'onepayment_against_multipleinvoices_mdpmdp89'],

    # Data
    "data": [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/account_voucher_view.xml',
        'views/payment_receipt_view.xml',
        'views/account_move_line_view.xml',
        'views/account_view.xml',
        'views/account_payment_view.xml',
        'report/account_voucher_report.xml',
        'report/purchase_receipt_report.xml',
        'report/account_voucher_report_menu.xml',
        'report/payment_receipt_report.xml',
        'report/official_receipt_report.xml',
        'report/payment_receipt_report_menu.xml',
    ],

    # Odoo App Store Specific
    'images': ['static/description/icon.png'],

    # Technical
    "installable": True,

}
