# See LICENSE file for full copyright and licensing details.

{
    # Module Info.
    "name": "GoExcel Visit",
    "version": "12.0.2.0.0",
    "category": "Sales",
    "license": 'OPL-1',
    "summary": """Customer Visit and Planning for the salesperson""",
    "description": """Customer Visit Management""",

    # Author
    "author": "Excelroot Technology Sdn Bhd",
    "website": "https://www.excelroot.com/",

    # Dependencies
    "depends": ['mail', 'web', 'base_geolocalize','web_view_google_map'],

    # Data
    "data": [
        'static/src/xml/assets.xml',
        'views/visit_view.xml',
        'views/res_partner_view.xml',
        'views/configure_view.xml',
        'security/visit_security.xml',
        'security/ir.model.access.csv',
    ],

    # Odoo App Store Specific
    'images': ['static/description/goexcel.jpg'],

    # Technical
    "application": True,
    "installable": True,
    'price': 289,
    'currency': 'EUR',
}