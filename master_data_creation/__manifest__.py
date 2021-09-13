# See LICENSE file for full copyright and licensing details.

{
    # Module Info.
    "name": "GoExcel Master Data Creation",
    "version": "12.0.1",
    "category": "",
    "license": 'OPL-1',
    "summary": """""",
    "description": """""",

    # Author
    "author": "Excelroot Technology Sdn Bhd",
    "website": "https://www.excelroot.com/",

    # Dependencies
    "depends": ['product', 'account', 'sci_goexcel_freight', 'sci_goexcel_sq'],

    'css': ['static/src/css/style.css'],

    'sequence': 1,

    # Data
    "data": [
        'views/sales_quotation_view.xml',
        'views/booking_view.xml',
        'views/transport_view.xml',
        'views/master_data_edit.xml',
        'wizards/master_data.xml',
    ],

    # Odoo App Store Specific
    'images': ['static/description/icon.png'],

    # Technical
    "installable": True,

}
