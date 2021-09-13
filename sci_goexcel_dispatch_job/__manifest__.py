# See LICENSE file for full copyright and licensing details.

{
    # Module Info.
    "name": "GoExcel Dispatch Job",
    "version": "12.0.2.0.0",
    "category": "Sales",
    "license": 'OPL-1',
    "summary": "Freight Dispatch Job",
    "description": """Freight Dispatch Job""",

    # Author
    "author": "Excelroot Technology Sdn Bhd",
    "website": "https://www.excelroot.com/",

    # Dependencies
    "depends": ['mail', 'sci_goexcel_freight'],

    # Data
    "data": [
        'security/dispatch_job_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/dispatch_job_view.xml',
        'views/freight_booking_view.xml',
        'report/dispatch.xml',
    ],

    # Odoo App Store Specific
    'images': ['static/description/icon.png'],

    # Technical
    "application": True,
    "installable": True,
    'currency': 'EUR',
}
