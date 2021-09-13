# See LICENSE file for full copyright and licensing details.

{
    # Module Info.
    "name": "GoExcel Freight Job Sheet",
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
        'reports/job_sheet.xml',
    ],

    # Odoo App Store Specific
    'images': ['static/description/icon.png'],

    # Technical
    "installable": True,

}
