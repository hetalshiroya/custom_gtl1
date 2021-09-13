# See LICENSE file for full copyright and licensing details.

{
    # Module Info.
    "name": "Custom GTL",
    "version": "12.0.1.0.2",
    "category": "",
    "license": 'OPL-1',
    "summary": """""",
    "description": """""",

    # Author
    "author": "Excelroot Technology Sdn Bhd",
    "website": "https://www.excelroot.com/",

    # Dependencies
    "depends": ['product', 'account', 'sci_goexcel_freight', 'sci_goexcel_transport', 'sci_goexcel_invoice',
                'sci_goexcel_shipping_instruction', 'sci_goexcel_dispatch_job', 'sci_goexcel_sq',
                'sci_goexcel_payment_receipt', 'sale_term', 'sci_goexcel_warehouse'],

    'css': ['static/src/css/style.css'],

    # Data
    "data": [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'reports/report_external_layout_inherit.xml',
        'reports/report_account_invoice.xml',
        #'reports/rft_pcl.xml',
        #'reports/rft_synhee.xml',
        'reports/letter_of_demand_report.xml',
        'reports/report_sq_inherit.xml',
        # 'reports/si_report_carrier_inherit.xml',
        'reports/report_booking_confirmation_inherit.xml',
        'reports/report_door_to_door_delivery_order.xml',
        'reports/si_report_carrier_gtl.xml',
        'reports/report_noa_inherit.xml',
        'reports/report_transport.xml',
        'reports/report_bl_sn.xml',
        'views/transport_rft_view.xml',
        'views/res_config_settings_view.xml',
        'views/account_invoice_view.xml',
        'views/res_company.xml',
        'views/res_partner_view.xml',
        'views/booking_view.xml',
        'views/payment_view.xml',
        'views/account_voucher_view.xml',
        'views/sales_quotation_view.xml',
        'views/bol_view.xml',
        'views/shipping_instruction_view.xml',
        #'views/booking_invoice_report.xml',
        "data/mail_template_pcl.xml",
        "data/mail_template_synhee.xml",
        'views/cron.xml',
        'reports/official_receipt_report.xml',
        'reports/payment_receipt_report.xml',
        'views/sale_term.xml',
    ],

    # Odoo App Store Specific
    'images': ['static/description/icon.png'],

    # Technical
    "application": True,
    "installable": True,

}
