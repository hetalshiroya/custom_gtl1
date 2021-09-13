# See LICENSE file for full copyright and licensing details.

{
    # Module Info.
    "name": "GoExcel Freight Notice Of Arrival",
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
        'reports/notice_of_arrival_bl.xml',
        'reports/notice_of_arrival_booking.xml',
        'data/noa_mail_template_bl.xml',
        'data/noa_mail_template_booking.xml',
        'views/bol_view_inherit.xml',
        'views/booking_view_inherit.xml',
    ],

    # Odoo App Store Specific
    'images': ['static/description/icon.png'],

    # Technical
    "installable": True,

}
