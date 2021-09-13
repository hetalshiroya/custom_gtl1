{
    "name": "GoExcel Freight Pivot",
    "version": "12.0.1.0.0",
    "category": "Transport",
    "license": 'LGPL-3',
    "summary": """GoExcel Freight Pivot.""",
    "author": "Excelroot Technology Sdn Bhd",
    "depends": ['custom_gtl', 'sci_goexcel_freight'],
    'sequence': 1,
    'application': True,
    "data": [
        'security/ir.model.access.csv',
        'report/goexcel_freight_pivot_view.xml'
    ],
    "application": True,
    "installable": True,
}
