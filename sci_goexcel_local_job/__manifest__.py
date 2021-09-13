# See LICENSE file for full copyright and licensing details.

{
    # Module Info.
    "name": "GoExcel Local Job",
    "version": "12.0.2.0.0",
    "category": "Sales",
    "license": 'OPL-1',
    "summary": "Freight Local Job",
    "description": """Freight Local Job""",

    # Author
    "author": "Excelroot Technology Sdn Bhd",
    "website": "https://www.excelroot.com/",

    # Dependencies
    "depends": ['mail', 'sci_goexcel_freight'],

    # Data
    "data": [
        'data/ir_sequence_data.xml',
        'views/freight_local_job_view.xml',

    ],

    # Odoo App Store Specific
    'images': ['static/description/icon.png'],

    # Technical
    "application": True,
    "installable": True,

}
