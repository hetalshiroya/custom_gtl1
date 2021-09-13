from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo import exceptions
from odoo.tools import float_round
import logging

_logger = logging.getLogger(__name__)
from odoo.exceptions import UserError


class FreightBooking(models.Model):
    _name = 'freight.booking'
    _description = 'Booking'
    _order = 'booking_date_time desc, write_date desc'

    _inherit = ['mail.thread', 'mail.activity.mixin']
    color = fields.Integer('Color Index', default=0, store=False)

    ##General
    shipment_booking_status = fields.Selection([('01', 'Booking Draft'),
                                                ('02', 'Booking Confirmed'),
                                                ('03', 'SI Received'),
                                                ('04', 'BL Confirmed'),
                                                ('05', 'OBL confirmed'),
                                                ('06', 'AWB Confirmed'),
                                                ('07', 'Shipment Arrived'),
                                                ('10', 'Invoiced'),
                                                ('11', 'Paid'),
                                                ('08', 'Done'),
                                                ('09', 'Cancelled')],
                                               string="Booking Status", default="01", copy=False,
                                               track_visibility='onchange')
    status_import = fields.Selection(related='shipment_booking_status', copy=False, string="Import Status")
    status_export = fields.Selection(related='shipment_booking_status', copy=False, string="Export Status")
    air_status_import = fields.Selection(related='shipment_booking_status', copy=False, string="Air Import Status")
    air_status_export = fields.Selection(related='shipment_booking_status', copy=False, string="Air Export Status")
    # .Many2one('freight.status.shipment', string="Shipment Booking Status")
    # liner_booking_status = fields.Many2one('freight.status.liner', string="Liner Booking Status")
    status_date_time = fields.Datetime(string='Status Date', track_visibility='onchange', index=True)
    notification_sent = fields.Boolean(string='Invoice Notification Sent')
    direction = fields.Selection([('import', 'Import'), ('export', 'Export'), ('transhipment', 'Transhipment')],
                                 string="Direction", default="import", track_visibility='onchange')
    service_type = fields.Selection([('ocean', 'Ocean'), ('air', 'Air'), ('land', 'Land')], string="Shipment Mode",
                                    default="ocean", track_visibility='onchange')
    cargo_type = fields.Selection([('fcl', 'FCL'), ('lcl', 'LCL')], string='Cargo Type', default="fcl",
                                  track_visibility='onchange')
    origin = fields.Char(string='Source Document',
                         help="Reference of the document that generated this.", copy=False)
    booking_no = fields.Char(string='Job No', copy=False, readonly=True, index=True)

    booking_date_time = fields.Date(string='ETA/ETD Date', copy=False, default=datetime.now().date(),
                                    track_visibility='onchange', index=True)
    carrier_booking_no = fields.Char(string='Carrier Booking No', track_visibility='onchange', copy=False)
    invoice_count = fields.Integer(string='Invoice Count', compute='_get_invoiced_count', copy=False)
    invoice_ids = fields.One2many('account.invoice', 'freight_booking', string='Invoice')
    sq_reference = fields.Many2one('sale.order', string='S.Q Reference', track_visibility='onchange', copy=False,
                                   index=True)
    vendor_bill_count = fields.Integer(string='Vendor Bill Count', compute='_get_bill_count', copy=False)
    booking_type = fields.Selection([('master', 'Master'), ('sub', 'Sub')], string='Job Type',
                                    track_visibility='onchange', copy=False)
    master_booking = fields.Many2one('freight.booking', string='Master Job', track_visibility='onchange', copy=False)
    # master_booking_id = fields.Integer(string='Master Job Count', compute='_get_masterbooking_id', readonly=True)
    job_category = fields.Selection([('freight', 'Freight Job'), ('local', 'Local Job')],
                                    string="Job Category", default='freight', track_visibility='onchange')
    # po_count = fields.Integer(string='Purchase Order Count', compute='_get_po_count', readonly=True, copy=False)
    # TODO delete po_count
    # po_count = fields.Integer(string='Purchase Order Count', readonly=True, copy=False)
    subbooking_count = fields.Integer(string='Sub Job Count', compute='_get_subbooking_count', copy=False)
    master_booking_count = fields.Integer(string='Master Job Count', compute='_get_masterbooking_count', copy=False)
    si_count = fields.Integer(string='SI Count', compute='_get_si_count', copy=False)
    bol_count = fields.Integer(string='BL Count', compute='_get_bol_count', copy=False)
    ##Party
    customer_name = fields.Many2one('res.partner', string='Customer Name', track_visibility='onchange')
    contact_name = fields.Many2one('res.partner', string='Contact Name', track_visibility='onchange')
    # phone = fields.Char(string='Phone', readonly=True)
    # fax = fields.Char(string='Fax', readonly=True)
    # email = fields.Char(string='E-Mail', readonly=True)
    # billing_address = fields.Char(string='Billing Address')
    billing_address = fields.Many2one('res.partner', string='Billing Address', track_visibility='onchange')
    payment_term = fields.Many2one('account.payment.term', string='Payment Term', track_visibility='onchange')
    incoterm = fields.Many2one('freight.incoterm', string='Incoterm', track_visibility='onchange')
    shipper = fields.Many2one('res.partner', string='Shipper', help="The Party who shipped the freight, eg Exporter",
                              track_visibility='onchange')
    shipper_address_input = fields.Text(string='Shipper Address', track_visibility='onchange')
    # shipper_address = fields.Char(string='Shipper Address')
    consignee = fields.Many2one('res.partner', string='Consignee Name', help="The Party who received the freight",
                                track_visibility='onchange')
    consignee_address_input = fields.Text(string='Consignee Address', track_visibility='onchange')
    # consignee_address = fields.Char(string='Consignee Address')
    commodity = fields.Many2one('product.product', string='Commodity', track_visibility='onchange')
    commodity1 = fields.Many2one('freight.commodity1', string='Commodity', track_visibility='onchange')
    commodity_type = fields.Many2one('freight.commodity', string="Commodity Type",
                                     help="Dangerous Goods or General Goods", track_visibility='onchange')
    commodity_dg = fields.Many2one('freight.dangerous.goods', string="DG UN Class/Div",
                                   help="Dangerous Goods UN Class/Division and Classification",
                                   track_visibility='onchange')
    hide_commodity_dg = fields.Boolean(string='Hide DG', default=True)
    # hs_code = fields.Char(string='HS Code', track_visibility='onchange')
    hs_code = fields.Many2one('freight.hscode', string='HS Code', track_visibility='onchange')
    notify_party = fields.Many2one('res.partner', string='Notify Party',
                                   help="The Party who will be notified by Liner when the freight arrived",
                                   track_visibility='onchange')
    notify_party_address_input = fields.Text(string='Notify Party Address', track_visibility='onchange')
    oversea_agent = fields.Many2one('res.partner', string='Oversea Agent',
                                    help="The Party who will be help to ship import cargo from oversea",
                                    track_visibility='onchange')
    lcl_pcs = fields.Integer(string='LCL Pcs', store=True, track_visibility='onchange')
    lcl_weight = fields.Float(string='LCL Weight', store=True, track_visibility='onchange')
    lcl_volume = fields.Float(string='LCL Volume', store=True, track_visibility='onchange')

    note = fields.Text(string='Remarks', track_visibility='onchange')
    changed_consignee = fields.Text(string='Changed Consignee')
    changed_shipper = fields.Text(string='Changed Shipper')
    original_shipper = fields.Text(string='Original Shipper')
    original_consignee = fields.Text(string='Original Consignee')
    changed_description = fields.Char(string='DESCRIPTION')
    changed_gross_weight = fields.Char(string='GROSS WEIGHT')
    changed_measurement = fields.Char(string='MEASUREMENT')
    changed_date = fields.Date(string='Date')

    changed_to = fields.Char(string='TO')
    changed_tel = fields.Char(string='TEL')
    # changed_fax = fields.Char(string='FAX')
    changed_attn = fields.Char(string='ATTN')
    changed_from = fields.Char(string='FROM')

    # job_no = fields.Char(string='Job No', track_visibility='onchange')
    # origin = fields.Many2one('freight.ports', string="Origin")
    # destination = fields.Many2one('freight.ports', string="Destination", track_visibility='onchange')
    # master_job_no = fields.Char(string='Master Job No', track_visibility='onchange')

    ##Shipment Info (Ocean Freight)
    hbl_no = fields.Char(string='HBL No', copy=False, track_visibility='onchange', store=True)
    obl_no = fields.Char(string='OBL No', copy=False, track_visibility='onchange')
    hbl_status = fields.Selection(
        [('original', 'Original'), ('surrender', 'Surrender'), ('telex_release', 'Telex Release')]
        , string='B/L Status', track_visibility='onchange')
    manifest_no = fields.Char(string='Manifest No', track_visibility='onchange')
    unstuff_at = fields.Char(string='Unstuff At', track_visibility='onchange')

    shipment_type = fields.Selection([('house', 'House'), ('direct', 'Direct')], string='Shipment Type',
                                     track_visibility='onchange', default='house')
    priority = fields.Selection([('0', 'Low'), ('1', 'Low'), ('2', 'Normal'), ('3', 'High'), ('4', 'Very High')],
                                string='Priority', select=True, default='2', track_visibility='onchange')
    place_of_receipt = fields.Char(string='Place of Receipt', track_visibility='onchange')
    place_of_receipt_ata = fields.Date(string='Receipt ATA', track_visibility='onchange', copy=False)
    port_of_loading = fields.Many2one('freight.ports', string='Port of Loading', track_visibility='onchange')
    port_of_loading_input = fields.Text(string='POL Input', track_visibility='onchange')
    port_of_loading_eta = fields.Date(string='Loading ETA', track_visibility='onchange')
    port_of_tranship = fields.Many2one('freight.ports', string='Port of Tranship', track_visibility='onchange')
    port_of_tranship_input = fields.Text(string='POT Input', track_visibility='onchange')
    port_of_tranship_eta = fields.Date(string='Tranship ETA', track_visibility='onchange', copy=False)
    port_of_discharge = fields.Many2one('freight.ports', string='Port of Discharge', track_visibility='onchange')
    port_of_discharge_input = fields.Text(string='POD Input', track_visibility='onchange')
    port_of_discharge_eta = fields.Date(string='Discharge ETA', track_visibility='onchange', copy=False)
    place_of_delivery = fields.Char(string='Place of Delivery', track_visibility='onchange')
    shipment_close_date_time = fields.Datetime(string='Closing Date Time', track_visibility='onchange', copy=False)

    carrier = fields.Many2one('res.partner', string="Carrier", track_visibility='onchange')
    coloader = fields.Many2one('res.partner', string="Co-loader", track_visibility='onchange')

    vessel_name = fields.Many2one('freight.vessels', string='Vessel Name', track_visibility='onchange')
    feeder_vessel_name = fields.Char(string='Feeder Vessel', track_visibility='onchange')
    feeder_voyage_no = fields.Char(string='Feeder Voyage No', track_visibility='onchange')
    vessel_id = fields.Char(string='Vessel ID', track_visibility='onchange')
    voyage_no = fields.Char(string='Voyage No', track_visibility='onchange')
    psa_code = fields.Char(string='PSA Code', track_visibility='onchange')
    scn_code = fields.Char(string='SCN Code', track_visibility='onchange')
    # terminal = fields.Char(string='Terminal', track_visibility='onchange')
    terminal = fields.Many2one('freight.terminal', string='Terminal', track_visibility='onchange')

    freight_type = fields.Selection([('prepaid', 'Prepaid'), ('collect', 'Collect')], string='Freight Type',
                                    track_visibility='onchange')
    other_charges = fields.Selection([('prepaid', 'Prepaid'), ('collect', 'Collect')], string='Other Charges',
                                     track_visibility='onchange')

    ##Vessel Details
    principal_agent_code = fields.Many2one('res.partner', string='Principal Agent Code', track_visibility='onchange')
    principal_agent_smk_code = fields.Char(string='Principal SMK Code', track_visibility='onchange')
    # shipping_agent_code = fields.Many2one('res.partner', string='Shipping Agent Code', track_visibility='onchange')
    shipping_agent_code = fields.Char(string='Shipping Agent Code', track_visibility='onchange')
    shipping_agent_smk_code = fields.Char(string='SA SMK Code', track_visibility='onchange')
    # vessel_close_date_time = fields.Datetime(string='Closing Date Time')

    shipping_instruction_remark = fields.Text(string='Shipping Instruction Remark', track_visibility='onchange')

    haulage = fields.Boolean(string='Include Haulage?', track_visibility='onchange')
    transporter_company = fields.Many2one('res.partner', string='Transporter Company',
                                          help="The Party who transport the goods from one place to another",
                                          track_visibility='onchange')

    haulage_address = fields.Char(string='Haulage Address', track_visibility='onchange')
    custom_clearance = fields.Boolean(string='Include Custom Clearance?', track_visibility='onchange')
    custom_registration_no = fields.Char(string='Custom Registration No', track_visibility='onchange')
    insurance = fields.Boolean(string='Include Insurance', track_visibility='onchange')
    fumigation = fields.Boolean(string='Fumigation', track_visibility='onchange')
    cpc = fields.Boolean(string='Container Packing Certificate', track_visibility='onchange')
    coo = fields.Boolean(string='COO', track_visibility='onchange')
    warehouse_hours = fields.Many2one('transport.accept.hour', track_visibility='onchange', copy=False)
    forwarding_agent_code = fields.Many2one('res.partner', string='Forwarding Agent',
                                            help="The Party who help to do custom clearance",
                                            track_visibility='onchange')
    custom_approved_date = fields.Date(string="Custom Approved Date", track_visibility='onchange')
    unstuff_discharge_date = fields.Date(string="Unstaff Discharge Date", track_visibility='onchange')
    gate_in_date = fields.Date(string="Gate In Date", track_visibility='onchange')

    # delivery_date = fields.Date(string="Delivery Date", track_visibility='onchange')
    # shipment_date = fields.Date(string='Shipment Date', track_visibility='onchange')

    # shipment_term = fields.Char(string='Shipment Term', track_visibility='onchange')
    # pre_carriage = fields.Char(string='Contact Info', track_visibility='onchange')

    ##Air Cargo
    awb_no = fields.Char(string='HAWB No', track_visibility='onchange')
    mawb_no = fields.Char(string='MAWB No', track_visibility='onchange')
    airport_departure = fields.Many2one("freight.airport", string='Airport Departure', track_visibility='onchange')
    airport_destination = fields.Many2one("freight.airport", string='Airport Destination', track_visibility='onchange')
    first_carrier_to = fields.Many2one("freight.airport", string='First Carrier To', track_visibility='onchange')
    first_carrier_flight_no = fields.Many2one("airline.flight", string='1st Flight No', track_visibility='onchange')
    first_carrier_etd = fields.Datetime(string='F. Carrier ETD', track_visibility='onchange', copy=False)
    first_carrier_eta = fields.Datetime(string='F. Carrier ETA', track_visibility='onchange', copy=False)
    second_carrier_to = fields.Many2one("freight.airport", string='Second Carrier To', track_visibility='onchange')
    second_carrier_flight_no = fields.Many2one("airline.flight", string='2nd Flight No', track_visibility='onchange')
    second_carrier_etd = fields.Datetime(string='S.Carrier ETD', track_visibility='onchange', copy=False)
    second_carrier_eta = fields.Datetime(string='S. Carrier ETA', track_visibility='onchange', copy=False)
    third_carrier_to = fields.Many2one("freight.airport", string='Third Carrier To', track_visibility='onchange')
    third_carrier_flight_no = fields.Many2one("airline.flight", string='3rd Flight No', track_visibility='onchange')
    third_carrier_etd = fields.Datetime(string='T. Carrier ETD', track_visibility='onchange', copy=False)
    third_carrier_eta = fields.Datetime(string='T. Carrier ETA', track_visibility='onchange', copy=False)
    air_agent = fields.Many2one('res.partner', string='Air Agent',
                                help="The Party who will be help to ship import cargo", track_visibility='onchange')

    airlines_ids = fields.Many2many('freight.airlines', string='Airlines')
    weight_ids = fields.Many2many('freight.airlines.weight', string='Weight', limit=3)

    airlines_weight_ids = fields.Many2many('freight.airlines.info', string='Airlines Info')

    warehouse_location = fields.Char(string='Warehouse Location', track_visibility='onchange')
    depot_name = fields.Many2one('res.partner', string='Depot Name', track_visibility='onchange')

    @api.onchange('airlines_ids', 'weight_ids')
    def onchange_airlines(self):
        info_ids = []
        for airline in self.airlines_ids:
            for weight in self.weight_ids:
                info = self.env['freight.airlines.info'].search(
                    [('airline.id', '=', airline.id), ('weight.id', '=', weight.id)])
                if info:
                    info_ids.append(info.id)
        info1 = self.env['freight.airlines.info'].browse(info_ids)
        # self.airlines_weight_ids = info1
        self.airlines_weight_ids = [(6, 0, info_ids)]

    # Land Freight
    land_cargo_type = fields.Selection([('ftl', 'FTL'), ('ltl', 'LTL')], string='Cargo Type', default="ftl",
                                       track_visibility='onchange')
    land_type = fields.Selection([('truck', 'Truck'), ('train', 'Train')], string='Land Type',
                                 track_visibility='onchange')
    trip_type = fields.Selection([('round', 'Round Trip'), ('single', 'Single Trip')], string='Trip',
                                 track_visibility='onchange')
    customer_seal = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Customer Seal',
                                     track_visibility='onchange')
    delivery_type = fields.Selection([('direct', 'Direct Delivery'), ('normal', 'Normal Delivery')],
                                     string='Delivery Type',
                                     track_visibility='onchange')
    direct_loading = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Direct Loading',
                                      track_visibility='onchange')
    pickup_from = fields.Many2one('res.partner', string='Pick-Up From', track_visibility='onchange')
    pickup_from_address_input = fields.Text(string='Pick-Up Address', track_visibility='onchange')
    # pickup_from_contact_name = fields.Many2one('res.partner', string='Contact Person', track_visibility='onchange')
    delivery_to = fields.Many2one('res.partner', string='Delivery To', track_visibility='onchange')
    delivery_to_address_input = fields.Text(string='Delivery To Address', track_visibility='onchange')
    # delivery_to_contact_name = fields.Many2one('res.partner', string='Contact Person', track_visibility='onchange')
    accept_hour = fields.Many2one('accept.hour', string="Accept Hour", help="Customer Working Hours",
                                  track_visibility='onchange')
    land_port = fields.Many2one('freight.ports', string='Port', track_visibility='onchange')
    land_status = fields.Selection(related='shipment_booking_status', copy=False)

    # Haulage service for ocean/air freight
    pickup_date_time = fields.Datetime(string='Pickup Date Time', track_visibility='onchange', copy=False)
    transport_company = fields.Many2one('res.partner', string='Transport Company', track_visibility='onchange')
    transport_address = fields.Char(string='Transport address', track_visibility='onchange')
    customer_collection_from = fields.Many2one('res.partner', string='Customer Collection From',
                                               track_visibility='onchange')
    delivery_to_address = fields.Many2one('res.partner', string='Delivery To Addr.', track_visibility='onchange')
    delivery_instruction = fields.Text(string='Delivery Instruction', track_visibility='onchange')

    income_acc_id = fields.Many2one("account.account",
                                    string="Income Account", track_visibility='onchange')
    expence_acc_id = fields.Many2one("account.account",
                                     string="Expense Account", track_visibility='onchange')

    owner = fields.Many2one('res.users', string="Owner", default=lambda self: self.env.user.id,
                            track_visibility='onchange')
    sales_person = fields.Many2one('res.users', string="Salesperson", track_visibility='onchange')
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, readonly=1,
                                 default=lambda self: self.env.user.company_id.id)

    elapsed_day_booking = fields.Char(string='Elapsed Days', copy=False, store=True, index=True)

    pl_to_receive_date = fields.Date(string='Receive Date', track_visibility='onchange', copy=False)
    pl_file_name = fields.Char(string="File name", track_visibility='onchange', copy=False)
    pl_attachment = fields.Binary(string="CI/PL Documents", track_visibility='onchange', copy=False)

    # shipping_instruction = fields.Boolean(track_visibility='onchange')
    si_to_receive_date = fields.Date(string='Receive Date', track_visibility='onchange', copy=False)
    si_file_name = fields.Char(string="File name", track_visibility='onchange', copy=False)
    si_attachment = fields.Binary(string="NOA Documents", track_visibility='onchange', copy=False)

    # commercial_invoice = fields.Boolean(track_visibility='onchange')
    ci_to_receive_date = fields.Date(string='Receive Date', track_visibility='onchange', copy=False)
    ci_file_name = fields.Char(string="File name", track_visibility='onchange')
    ci_attachment = fields.Binary(string="Permit Documents", track_visibility='onchange', copy=False)

    # obl = fields.Boolean(track_visibility='onchange')
    obl_to_receive_date = fields.Date(string='Receive Date', track_visibility='onchange', copy=False)
    obl_file_name = fields.Char(string="OBL File name", track_visibility='onchange', copy=False)
    obl_attachment = fields.Binary(string="Others Documents", track_visibility='onchange', copy=False)

    # cc = fields.Boolean(track_visibility='onchange')
    cc_to_receive_date = fields.Date(string='Custom Docs To Receive Date', track_visibility='onchange', copy=False)
    cc_file_name = fields.Char(string="CC File name", track_visibility='onchange', copy=False)
    cc_attachment = fields.Binary(string="Custom Docs Attachment", track_visibility='onchange', copy=False)

    # TODO to delete this
    # packing_list = fields.Boolean(string='Packing List', track_visibility='onchange')
    # pl_received_date_time = fields.Datetime(string='PL Received Date Time', track_visibility='onchange', copy=False)
    # shipping_instruction = fields.Boolean(string='Shipping Instruction', track_visibility='onchange')
    # si_received_date_time = fields.Datetime(string='SI Received Date Time', track_visibility='onchange', copy=False)
    # commercial_invoice = fields.Boolean(string='Commercial Invoice', track_visibility='onchange')
    # ci_received_date_time = fields.Datetime(string='CI Received Date Time', track_visibility='onchange', copy=False)
    # obl = fields.Boolean(string='OBL Received', track_visibility='onchange')
    # obl_received_date_time = fields.Datetime(string='OBL Received Date Time', track_visibility='onchange', copy=False)

    # activity_ids = fields.One2many('mail.activity', string='Schedule Reminder')

    operation_line_ids = fields.One2many('freight.operations.line', 'operation_id', string="FCL Order",
                                         copy=True, auto_join=True, track_visibility='always')
    operation_line_ids2 = fields.One2many('freight.operations.line2', 'operation_id2', string="LCL Order",
                                          copy=True, auto_join=True, track_visibility='always')
    # booking_id is corresponding to freight.cost_profit
    cost_profit_ids = fields.One2many('freight.cost_profit', 'booking_id', string="Cost & Profit",
                                      copy=True, auto_join=True, track_visibility='always')
    # subbooking_ids = fields.One2many('freight.subbooking.line', 'subbooking_line', string="Subbooking",
    #                                   copy=True, auto_join=True, track_visibility='always')

    pivot_sale_total = fields.Float(string='Total Sales', compute="_compute_pivot_sale_total", store=True)
    pivot_cost_total = fields.Float(string='Total Cost', compute="_compute_pivot_cost_total", store=True)
    pivot_profit_total = fields.Float(string='Total Profit', compute="_compute_pivot_profit_total", store=True)
    pivot_margin_total = fields.Float(string='Margin %', compute="_compute_pivot_margin_total", digit=(8, 2),
                                      store=True,
                                      group_operator="avg")

    sale_order_template_id = fields.Many2one('sale.order.template', string='Quotation Template')

    empty_pick_up_location = fields.Char(string='Empty Pick Up Location', track_visibility='onchange')
    empty_pick_up_address = fields.Text(string='Empty Pick Up Address', track_visibility='onchange')
    empty_pick_up_telephone = fields.Char(string='Empty Pick Up Telephone', track_visibility='onchange')

    full_return_location = fields.Char(string='Full Return Location', track_visibility='onchange')
    full_return_address = fields.Text(string='Full Return Address', track_visibility='onchange')
    full_return_telephone = fields.Char(string='Full Return Telephone', track_visibility='onchange')

    laden_back_terminal = fields.Many2one('freight.terminal', string='Laden-back Terminal', related='terminal')

    cargo_nature = fields.Char(string='Cargo Nature', track_visibility='onchange')
    required_document = fields.Char(string='Note', track_visibility='onchange')
    due_date = fields.Datetime(string='Pick Up Empty Date', track_visibility='onchange')
    responsible_parties = fields.Char(string='Responsible Parties', track_visibility='onchange')
    intended_vgm_cut_off = fields.Datetime(string='Intended VGM Cut Off', track_visibility='onchange')
    intended_cy_cut_off = fields.Datetime(string='Intended CY Cut Off', track_visibility='onchange')
    # intended_si_cut_off = fields.Datetime(string='Intended SI Cut Off', track_visibility='onchange')
    # intended_bl_cut_off = fields.Datetime(string='Intended BL Cut Off', track_visibility='onchange')

    intended_si_cut_off = fields.Many2one('freight.cutoff', string='Intended SI Cut Off', track_visibility='onchange')
    intended_bl_cut_off = fields.Many2one('freight.cutoff', string='Intended BL Cut Off', track_visibility='onchange')

    # invoice
    invoice_status = fields.Selection([('01', 'New'),
                                       ('02', 'Partially Invoiced'),
                                       ('03', 'Fully Invoiced')],
                                      string="Invoice Status", default="01", copy=False,
                                      track_visibility='onchange')
    invoice_paid_status = fields.Selection([('01', 'New'),
                                            ('02', 'Partially Paid'),
                                            ('03', 'Fully Paid')],
                                           string="Invoice Paid Status", default="01", copy=False,
                                           track_visibility='onchange')
    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account",
                                          track_visibility='always', copy=False)

    bol_status = fields.Selection([('01', 'Draft'), ('02', 'Original'), ('03', 'Surrender')], string="BOL Status",
                                  default="01")
    no_of_original_bl = fields.Selection([('0', '0'), ('1', '1'), ('3', '3')], string="No Of original B/L",
                                         default="0")

    @api.multi
    def _get_default_commodity_category(self):
        commodity_lines = self.env['freight.product.category'].search([('type', '=ilike', 'commodity')])
        for commodity_line in commodity_lines:
            _logger.warning('_get_default_commodity_category=' + str(commodity_line.product_category))
            return commodity_line.product_category

    commodity_category_id = fields.Many2one('product.category', string="Commodity Product Id",
                                            default=_get_default_commodity_category)

    @api.model
    def _set_department(self):
        employee_rec = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)])
        department = employee_rec.department_id
        return department

    sales_team = fields.Many2one('crm.team', string="Sales Team")
    department = fields.Many2one('hr.department', string="Department", default=_set_department)

    @api.model
    def create(self, vals):
        service_type = vals.get('service_type')
        if service_type == 'ocean' or service_type == 'air' or service_type == 'land':
            vals['booking_no'] = self.env['ir.sequence'].next_by_code('fb')
        res = super(FreightBooking, self).create(vals)
        return res

    #TS bug - in case job no is not created
    @api.multi
    def write(self, vals):
        for record in self:
            if not record.booking_no:
                if record.service_type == 'ocean' or record.service_type == 'air' or record.service_type == 'land':
                    vals['booking_no'] = self.env['ir.sequence'].next_by_code('fb')

        res = super(FreightBooking, self).write(vals)
        return res


    @api.model
    def fields_get(self, fields=None):
        fields_to_hide = ['si_file_name', 'note', 'accept_hour']
        res = super(FreightBooking, self).fields_get()
        for field in fields_to_hide:
            res[field]['selectable'] = False
        return res

    @api.model
    def _cron_elapsed_day(self):
        yesterday_date = datetime.now().date() - timedelta(days=1)
        # bookings = self.env['freight.booking'].search([
        #     ('booking_date_time', '>=', yesterday_date),
        # ])
        bookings = self.env['freight.booking'].search([
            ('elapsed_day_booking', '!=', '0'),
        ])
        # _logger.warning('len bookings=' + str(len(bookings)))
        for booking in bookings:
            if booking.booking_date_time:
                elapsed_days = (booking.booking_date_time - datetime.now().date()).days
                # _logger.warning('elapsed_days=' + str(elapsed_days))
                if elapsed_days <= 0:
                    booking.elapsed_day_booking = 0
                else:
                    booking.elapsed_day_booking = elapsed_days

        # send notification if the booking status Done is more than 24 hours
        current_date = datetime.now()
        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
        date_format = datetime.strptime(str(current_date), DATETIME_FORMAT)
        plan_invoice_date = date_format + timedelta(days=-1)
        # start_date_time = datetime.strftime(d, "%Y-%m-%d %H:%M:%S")
        # end_date_time = datetime.strftime(d, "%Y-%m-%d 23:59:59")
        done_bookings = self.env['freight.booking'].search([
            ('shipment_booking_status', '=', '08'),
            ('status_date_time', '>', plan_invoice_date),
            ('notification_sent', '!=', True),
        ])
        for booking in done_bookings:
            self.env['mail.message'].create({'message_type': "notification",
                                             "subtype": self.env.ref("mail.mt_comment").id,
                                             'body': "Kindly take action on the job %s" % booking.booking_no,
                                             'subject': "Booking Job to Invoice",
                                             'needaction_partner_ids': [(4, booking.owner.partner_id.id)],
                                             'model': booking._name,
                                             'res_id': booking.id,
                                             })
            booking.notification_sent = True

    @api.multi
    def name_get(self):
        result = []
        for booking in self:
            # print('service_type=', booking.service_type)
            # print('direction=', booking.direction)
            # print('cargo_type=', booking.direction)
            # print('booking_no=', booking.booking_no)
            name = ''
            if booking.service_type == 'ocean':
                #if booking.booking_no:
                name = booking.direction + '-' + booking.service_type + "-" + booking.cargo_type + "-" + str(
                        booking.booking_no)
                # else:
                #     name = booking.direction + '-' + booking.service_type + "-" + booking.cargo_type
            elif booking.service_type == 'land':
                name = booking.direction + '-' + booking.service_type + "-" + booking.land_cargo_type + "-" + str(
                    booking.booking_no)
            elif booking.service_type == 'air':
                name = booking.direction + '-' + booking.service_type + "-" + booking.cargo_type + "-" + str(
                    booking.booking_no)
           
            result.append((booking.id, name))
        return result

    @api.one
    @api.depends('cost_profit_ids.sale_total')
    def _compute_pivot_sale_total(self):
        # _logger.warning('onchange_pivot_sale_total')
        for service in self.cost_profit_ids:
            if service.product_id:
                self.pivot_sale_total = service.sale_total + self.pivot_sale_total

    @api.one
    @api.depends('cost_profit_ids.cost_total')
    def _compute_pivot_cost_total(self):
        for service in self.cost_profit_ids:
            if service.product_id:
                self.pivot_cost_total = service.cost_total + self.pivot_cost_total

    @api.one
    @api.depends('cost_profit_ids.profit_total')
    def _compute_pivot_profit_total(self):
        for service in self.cost_profit_ids:
            if service.product_id:
                self.pivot_profit_total = service.profit_total + self.pivot_profit_total

    @api.one
    @api.depends('pivot_profit_total')
    def _compute_pivot_margin_total(self):
        for service in self:
            if service.pivot_sale_total > 0:
                service.pivot_margin_total = (service.pivot_profit_total / service.pivot_sale_total) * 100

    def _get_invoiced_count(self):
        for operation in self:
            invoices = self.env['account.invoice'].search([
                ('freight_booking', '=', operation.id),
                ('type', 'in', ['out_invoice', 'out_refund']),
                ('state', '!=', 'cancel'),
            ])

        self.update({
            'invoice_count': len(invoices),
            'invoice_ids': invoices,
        })


    def _get_bill_count(self):
        # vendor bill is created from booking job, vendor bill header will have the booking job id
        for operation in self:
            # Get from the vendor bill list
            vendor_bill_list = []
            #vendor_bill_list_temp = []
            for cost_profit_line in operation.cost_profit_ids:
                for vendor_bill_line in cost_profit_line.vendor_bill_ids:
                    if vendor_bill_line.type in ['in_invoice', 'in_refund']:
                        vendor_bill_list.append(vendor_bill_line.id)
                        #vendor_bill_list_temp.append(vendor_bill_line.id)
            #print('vendor_bill_list: ',  len(vendor_bill_list))
            # remove the duplicates in the vendor bill list
            unique_vendor_bill_list = []
            for i in vendor_bill_list:
                if i not in unique_vendor_bill_list:
                    unique_vendor_bill_list.append(i)
            #print('unique_vendor_bill_list: ', len(unique_vendor_bill_list))
            # Get the vendor list (Create the vendor from the job)
            invoices = self.env['account.invoice'].search([
                ('freight_booking', '=', operation.id),
                ('type', 'in', ['in_invoice', 'in_refund']),
                ('state', '!=', 'cancel'),
            ])
            #print('vendor bills:', len(invoices))
            invoice_name_list = []
            for x in invoices:
                invoice_name_list.append(x.id)
            unique_list = []
            # for x in invoices:
            #     invoice_name_list.append(x.vendor_bill_id.id)
            # unique_list = []
            for y in unique_vendor_bill_list:
                if invoice_name_list and len(invoice_name_list) > 0:
                    if y not in invoice_name_list:
                        unique_list.append(y)
                else:
                    unique_list.append(y)
            for z in invoice_name_list:
                #if z not in vendor_bill_list:
                unique_list.append(z)
            if len(unique_list) > 0:
                self.update({
                    'vendor_bill_count': len(unique_list),
                })

    def _get_si_count(self):
        for operation in self:
            si = self.env['freight.website.si'].search([
                ('booking_ref', '=', operation.id),
            ])

        self.update({
            'si_count': len(si),
        })

    def _get_bol_count(self):
        for operation in self:
            bol = self.env['freight.bol'].search([
                ('booking_ref', '=', operation.id),
            ])

        self.update({
            'bol_count': len(bol),
        })

    def _get_masterbooking_count(self):
        for operation in self:
            if operation.master_booking:
                master_booking = self.env['freight.booking'].search([
                    ('id', '=', operation.master_booking.id),
                ])

                self.update({
                    'master_booking_count': len(master_booking),
                })

    def _get_subbooking_count(self):
        for operation in self:
            subbookings = self.env['freight.booking'].search([
                ('master_booking', '=', operation.id),
            ])

        self.update({
            'subbooking_count': len(subbookings),
        })

    @api.multi
    def action_set_to_quotation_confirmed(self):
        self.shipment_booking_status = '02'

    @api.multi
    def action_cancel_booking(self):
        self.shipment_booking_status = '09'

    @api.multi
    def action_schedule_reminder(self, context=None):
        summary = context.get('summary')
        action = context.get('action')
        if action == 'pl':
            date_deadline = self.pl_to_receive_date
        elif action == 'si':
            date_deadline = self.si_to_receive_date
        elif action == 'ci':
            date_deadline = self.ci_to_receive_date
        elif action == 'obl':
            date_deadline = self.obl_to_receive_date
        elif action == 'cc':
            date_deadline = self.cc_to_receive_date
        if date_deadline:
            self.env['mail.activity'].create({
                'summary': summary,
                'note': 'Please follow up!',
                'res_id': self.id,
                # 'res_model_id': self.id,
                'res_model_id': self.env.ref('sci_goexcel_freight.model_freight_booking').id,
                'user_id': self.env.user.id,
                'date_deadline': date_deadline,
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                # 'activity_type_id': 2,
            })
        else:
            raise exceptions.ValidationError('Please select a Date to schedule!!!')

    @api.multi
    def action_create_invoice(self):
        """Create Invoice for the freight."""
        inv_obj = self.env['account.invoice']
        inv_line_obj = self.env['account.invoice.line']
        # account_id = self.income_acc_id
        inv_val = {
            'type': 'out_invoice',
            #     'transaction_ids': self.ids,
            'state': 'draft',
            'partner_id': self.customer_name.id or False,
            'date_invoice': fields.Date.context_today(self),
            'origin': self.booking_no,
            'freight_booking': self.id,
            'account_id': self.customer_name.property_account_receivable_id.id or False,
            'company_id': self.company_id.id,
            'user_id': self.sales_person.id,
        }

        invoice = inv_obj.create(inv_val)
        for line in self.cost_profit_ids:
            sale_unit_price_converted = line.list_price * line.profit_currency_rate
            account_id = False
            if line.product_id.property_account_income_id:
                account_id = line.product_id.property_account_income_id
            elif line.product_id.categ_id.property_account_income_categ_id:
                account_id = line.product_id.categ_id.property_account_income_categ_id
            if sale_unit_price_converted > 0:
                inv_line = inv_line_obj.create({
                    'invoice_id': invoice.id or False,
                    'account_id': account_id.id or False,
                    'name': line.product_id.name or '',
                    'product_id': line.product_id.id or False,
                    'quantity': line.profit_qty or 0.0,
                    'uom_id': line.uom_id.id or False,
                    'price_unit': sale_unit_price_converted or 0.0
                })
                line.write({'invoice_id': invoice.id or False,
                            'inv_line_id': inv_line.id or False})

        self.shipment_booking_status = '10'

    @api.multi
    def action_invoice(self):
        self.ensure_one()
        view = self.env.ref('sci_goexcel_freight.invoice_view_form')
        return {
            'name': 'Create Invoice',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'invoice.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',

            'context': dict(booking_id=self.id),
        }

    @api.multi
    def action_create_vendor_bill(self):
        # only lines with vendor
        vendor_po = self.cost_profit_ids.filtered(lambda c: c.vendor_id)
        # print('vendor_po=' + str(len(vendor_po)))
        po_lines = vendor_po.sorted(key=lambda p: p.vendor_id.id)
        # print('po_lines=' + str(len(po_lines)))
        vendor_count = False
        vendor_id = False
        if not self.analytic_account_id:
            values = {
                'partner_id': self.customer_name.id,
                'name': '%s' % self.booking_no,
                # 'partner_id': self.customer_name.id,
                'company_id': self.company_id.id,
            }

            analytic_account = self.env['account.analytic.account'].sudo().create(values)
            self.write({'analytic_account_id': analytic_account.id})
        for line in po_lines:
            print(line.vendor_bill_id)
            # print('line.vendor_id=' + line.vendor_id.name)
            if line.vendor_id != vendor_id:
                print('not same partner')
                vb = self.env['account.invoice']
                # vb_line_obj = self.env['account.invoice.line']
                # if line.vendor_id:
                vendor_count = True
                vendor_id = line.vendor_id
                # print('vendor_id=' + vendor_id.name)
                # combine multiple cost lines from same vendor
                value = []
                vendor_bill_created = []
                filtered_vb_lines = po_lines.filtered(lambda r: r.vendor_id == vendor_id)
                for vb_line in filtered_vb_lines:
                    # print('combine lines')
                    if not vb_line.invoiced:
                        account_id = False
                        price_after_converted = vb_line.cost_price * vb_line.cost_currency_rate
                        if vb_line.product_id.property_account_expense_id:
                            account_id = vb_line.product_id.property_account_expense_id
                        elif vb_line.product_id.categ_id.property_account_expense_categ_id:
                            account_id = vb_line.product_id.categ_id.property_account_expense_categ_id
                        print(vb_line)
                        value.append([0, 0, {
                            # 'invoice_id': vendor_bill.id or False,
                            'account_id': account_id.id or False,
                            'name': vb_line.product_id.name or '',
                            'product_id': vb_line.product_id.id or False,
                            'quantity': vb_line.cost_qty or 0.0,
                            'uom_id': vb_line.uom_id.id or False,
                            'price_unit': price_after_converted or 0.0,
                            'account_analytic_id': self.analytic_account_id.id,
                            'freight_booking': self.id,
                            'booking_line_id': vb_line.id,
                        }])
                        vendor_bill_created.append(vb_line)
                        vb_line.invoiced = True
                        # print('vendor_id=' + vendor_id.name)
                if value:
                    vendor_bill_id = vb.create({
                        'type': 'in_invoice',
                        'invoice_line_ids': value,
                        #  'default_purchase_id': self.booking_no,
                        'default_currency_id': self.env.user.company_id.currency_id.id,
                        'company_id': self.company_id.id,
                        'date_invoice': fields.Date.context_today(self),
                        'origin': self.booking_no,
                        'partner_id': vendor_id.id,
                        'account_id': vb_line.vendor_id.property_account_payable_id.id or False,
                        'freight_booking': self.id,
                    })
                for new_vendor_bill in vendor_bill_created:
                    new_vendor_bill.vendor_bill_id = vendor_bill_id.id
        if vendor_count is False:
            raise exceptions.ValidationError('No Vendor in Cost & Profit!!!')

    def action_create_bl(self):
        # _logger.warning('action_create_si')
        if self.service_type == 'ocean':
            # _logger.warning('export and ocean')
            # _logger.warning('si id=' + str(si.id))
            if self.cargo_type == 'fcl':
                # _logger.warning('si fcl')
                container_line = self.operation_line_ids
                bol_line_obj = self.env['freight.bol.cargo']
                for line in container_line:
                    if line.container_product_name and not line.created_bl:
                        bol_obj = self.env['freight.bol']
                        bol_val = {
                            'bol_status': self.bol_status or '01',
                            'no_of_original_bl': self.no_of_original_bl or '0',
                            'direction': self.direction or False,
                            'cargo_type': self.cargo_type or False,
                            'service_type': self.service_type or False,
                            'booking_date': self.booking_date_time,
                            'customer_name': self.customer_name.id or False,
                            'contact_name': self.contact_name.id or False,
                            'shipper': self.shipper_address_input,
                            'consignee': self.consignee_address_input,
                            'notify_party': self.notify_party_address_input,
                            'booking_ref': self.id,
                            'carrier_booking_no': self.carrier_booking_no,
                            'voyage_no': self.voyage_no,
                            'vessel': self.vessel_name.name,
                            'port_of_loading_input': self.port_of_loading.name,
                            'port_of_discharge_input': self.port_of_discharge.name,
                            'port_of_discharge_eta': self.port_of_discharge_eta,
                            'place_of_delivery': self.place_of_delivery,
                            'term': self.payment_term.name,
                            'analytic_account_id': self.analytic_account_id.id or False,
                            'sales_person': self.sales_person.id or False,
                            'shipping_agent_code': self.shipping_agent_code or False,
                            'shipper_c': self.shipper.id or False,
                            'consignee_c': self.consignee.id or False,
                            'notify_party_c': self.notify_party.id or False,
                            'carrier_c': self.carrier.id or False,
                            'commodity1': self.commodity1.id or False,
                        }
                        bol = bol_obj.create(bol_val)
                        print(bol)
                        bol_line = bol_line_obj.create({
                            'marks': line.remark or '',
                            'container_product_name': line.container_product_name or False,
                            'cargo_line': bol.id or '',
                            'container_no': line.container_no or '',
                            'container_product_id': line.container_product_id.id or False,
                            'seal_no': line.seal_no or '',
                            'packages_no': str(line.packages_no) + ' ' + str(line.packages_no_uom.name),
                            'packages_no_value': line.packages_no or '',
                            'packages_no_uom': line.packages_no_uom.id or '',
                            'exp_gross_weight': str(line.exp_gross_weight) or 0.0,
                            'exp_vol': str(line.exp_vol) or 0.0,

                        })
                        bol.write({'cargo_line_ids': bol_line or False})
                        line.created_bl = True
            else:
                # _logger.warning('action_copy_to_booking operation_line_ids2')
                container_line = self.operation_line_ids2
                bol_line_obj = self.env['freight.bol.cargo']
                for line in container_line:
                    if line.container_product_name and not line.created_bl:
                        bol_obj = self.env['freight.bol']
                        bol_val = {
                            'bol_status': self.bol_status or '01',
                            'no_of_original_bl': self.no_of_original_bl or '0',
                            'direction': self.direction or False,
                            'cargo_type': self.cargo_type or False,
                            'service_type': self.service_type or False,
                            'booking_date': self.booking_date_time,
                            'customer_name': self.customer_name.id or False,
                            'contact_name': self.contact_name.id or False,
                            'shipper': self.shipper_address_input,
                            'consignee': self.consignee_address_input,
                            'notify_party': self.notify_party_address_input,
                            'booking_ref': self.id,
                            'carrier_booking_no': self.carrier_booking_no,
                            'voyage_no': self.voyage_no,
                            'vessel': self.vessel_name.name,
                            'port_of_loading_input': self.port_of_loading.name,
                            'port_of_discharge_input': self.port_of_discharge.name,
                            'place_of_delivery': self.place_of_delivery,
                            'term': self.payment_term.name,
                            'analytic_account_id': self.analytic_account_id.id or False,
                            'sales_person': self.sales_person.id or False,
                            'shipping_agent_code': self.shipping_agent_code or False,
                            'shipper_c': self.shipper.id or False,
                            'consignee_c': self.consignee.id or False,
                            'notify_party_c': self.notify_party.id or False,
                            'carrier_c': self.carrier.id or False,
                            'commodity1': self.commodity1.id or False,
                        }
                        bol = bol_obj.create(bol_val)
                        print(bol)
                        bol_line = bol_line_obj.create({
                            'marks': line.shipping_mark or '',
                            'container_product_name': line.container_product_name or False,
                            'cargo_line': bol.id or '',
                            'container_no': line.container_no or '',
                            # 'seal_no': line.seal_no or '',
                            # 'container_product_name': line.freight_currency.id,
                            'packages_no': str(line.packages_no) + ' ' + str(line.packages_no_uom.name),
                            'exp_gross_weight': str(line.exp_gross_weight) or 0.0,
                            'exp_vol': str(line.exp_vol) or 0.0,
                            # 'remark_line': line.remark or '',
                        })
                        bol.write({'cargo_line_ids': bol_line or False})
                        line.created_bl = True

        else:
            raise exceptions.ValidationError('BL Creation is only for Ocean Export Freight Booking Job!!!')

    def action_create_si(self):
        si_obj = self.env['freight.website.si']
        if self.shipment_type == 'house':
            air_freight_type = '2'
        if self.shipment_type == 'direct':
            air_freight_type = '1'
        si_val = {
            'si_status': '01',
            'carrier': self.carrier.id or False,
            'direction': self.direction or False,
            'cargo_type': self.cargo_type or False,
            'service_type': self.service_type or False,
            'booking_date': self.booking_date_time,
            'customer_name': self.customer_name.id or False,
            'shipper': self.shipper_address_input,
            'consignee': self.consignee_address_input,
            'notify_party': self.notify_party_address_input,
            # 'billing_address': self.customer_name.id or False,
            'booking_ref': self.id,
            'carrier_booking_ref': self.carrier_booking_no,
            'voyage_no': self.voyage_no,
            'vessel': self.vessel_name.name,
            'port_of_loading_input': self.port_of_loading.name,
            'port_of_discharge_input': self.port_of_discharge.name,
            'place_of_delivery': self.place_of_delivery,
            'freight_type': self.freight_type,
            'air_freight_type': air_freight_type or False,
        }
        si = si_obj.create(si_val)
        # _logger.warning('si id=' + str(si.id))
        if self.cargo_type == 'fcl':
            # _logger.warning('si fcl')
            container_line = self.operation_line_ids
            si_line_obj = self.env['freight.website.si.fcl']
            for line in container_line:
                if line.container_product_id or line.container_no:
                    si_line = si_line_obj.create({
                        'container_product_id': line.container_product_id.id or False,
                        'container_product_name': line.container_product_name or False,
                        'container_commodity_id': line.container_commodity_id.id or False,
                        'fcl_line': si.id or '',
                        'container_no': line.container_no or '',
                        'seal_no': line.seal_no or '',
                        'fcl_container_qty': line.fcl_container_qty,
                        'packages_no': line.packages_no or 0.0,
                        'packages_no_uom': line.packages_no_uom.id,
                        'exp_gross_weight': line.exp_gross_weight or 0.0,
                        'exp_net_weight': line.exp_net_weight or 0.0,
                        'exp_vol': line.exp_vol or 0.0,
                        'remark': line.remark or '',
                    })
                    si.write({'fcl_line_ids': si_line or False})
        else:
            # _logger.warning('action_copy_to_booking operation_line_ids2')
            container_line = self.operation_line_ids2
            si_line_obj = self.env['freight.website.si.lcl']
            for line in container_line:
                if line.container_product_id or line.container_no:
                    si_line = si_line_obj.create({
                        # 'container_id': line.container_product_id.id or False,
                        'container_product_name': line.container_product_name or False,
                        'container_product_id': line.container_commodity_id.id or False,
                        'lcl_line': si.id or '',
                        'container_no': line.container_no or '',
                        # 'container_product_name': line.freight_currency.id,
                        'packages_no': line.packages_no or 0.0,
                        'packages_no_uom': line.packages_no_uom.id,
                        'exp_gross_weight': line.exp_gross_weight or 0.0,
                        'exp_net_weight': line.exp_net_weight or 0.0,
                        'exp_vol': line.exp_vol or 0.0,
                        # 'remark_line': line.remark or '',
                    })
                    si.write({'lcl_line_ids': si_line or False})
        self.shipment_booking_status = '02'

    def action_create_subbooking(self):
        self.ensure_one()
        view = self.env.ref('sci_goexcel_freight.subjob_view_form')
        return {
            'name': 'Add or Create Sub Job',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'freight.booking.subjob',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',  # readonly mode
            'context': dict(master_booking_id=self.id),
            # 'res_id': self.id,

        }

    @api.multi
    def operation_invoices(self):
        """Show Invoice for specific Freight Operation smart Button."""
        for operation in self:
            invoices = self.env['account.invoice'].search([
                ('freight_booking', '=', operation.id),
                ('type', 'in', ['out_invoice', 'out_refund']),
                ('state', '!=', 'cancel'),
            ])
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            action['views'] = [(self.env.ref('account.invoice_form').id, 'form')]
            action['res_id'] = invoices.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action


    @api.multi
    def operation_bill(self):
        for operation in self:
            """
            invoices = self.env['account.invoice'].search([
                ('origin', '=', self.booking_no),
                ('type', '=', 'in_invoice'),
            ])
            """
            invoices = self.env['freight.cost_profit'].search([
                ('booking_id', '=', operation.id),
                ('vendor_bill_id', '!=', False)
            ])
            invoice_name_list = []
            for x in invoices:
                invoice_name_list.append(x.vendor_bill_id.id)
            unique_list = []
            for y in invoice_name_list:
                if y not in unique_list:
                    unique_list.append(y)

        if len(unique_list) > 1:
            views = [(self.env.ref('account.invoice_supplier_tree').id, 'tree'),
                     (self.env.ref('account.invoice_supplier_form').id, 'form')]
            return {
                'name': 'Vendor bills',
                'view_type': 'form',
                'view_mode': 'tree,form',
                # 'view_id': self.env.ref('account.invoice_supplier_tree').id,
                'view_id': False,
                'res_model': 'account.invoice',
                'views': views,
                # 'context': "{'type':'in_invoice'}",
                'domain': [('id', 'in', unique_list)],
                'type': 'ir.actions.act_window',
                # 'target': 'new',
            }
        elif len(unique_list) == 1:
            # print('in vendor bill length =1')
            return {
                # 'name': self.booking_no,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'account.invoice',
                'res_id': unique_list[0] or False,  # readonly mode
                #  'domain': [('id', 'in', purchase_order.ids)],
                'type': 'ir.actions.act_window',
                'target': 'popup',  # readonly mode
            }
        else:
            print('operation_bill no VB on header')
            vbs_to_view = self.env['account.invoice']
            # vendor bill is created manually and assigned the cost by the invoice line
            billed_vbs = operation.cost_profit_ids.filtered(lambda r: r.invoiced is True)
            print('operation_bill billed_vbs=' + str(len(billed_vbs)))
            if billed_vbs:
                for billed_vb in billed_vbs:
                    invoice_lines = self.env['account.invoice.line'].search([
                        ('id', '=', billed_vb.bill_line_id.id),
                    ])
                    for invoice_line in invoice_lines:
                        vbs_to_view |= invoice_line.invoice_id

                if vbs_to_view and len(vbs_to_view) > 0:
                    views = [(self.env.ref('account.invoice_supplier_tree').id, 'tree'),
                             (self.env.ref('account.invoice_supplier_form').id, 'form')]
                    return {
                        'name': 'Vendor bills',
                        'view_type': 'form',
                        'view_mode': 'tree,form',
                        # 'view_id': self.env.ref('account.invoice_supplier_tree').id,
                        'view_id': False,
                        'res_model': 'account.invoice',
                        'views': views,
                        # 'context': "{'type':'in_invoice'}",
                        'domain': [('id', 'in', vbs_to_view.ids)],
                        'type': 'ir.actions.act_window',
                        # 'target': 'new',
                    }
                else:
                    # TS - bugs vendor bill not shown in the smart button
                    invoices = self.env['account.invoice'].search([
                        ('origin', '=', self.booking_no),
                        ('type', '=', 'in_invoice'),
                        ('state', '!=', 'cancel'),
                    ])
                    if len(invoices) > 1:
                        views = [(self.env.ref('account.invoice_supplier_tree').id, 'tree'),
                                 (self.env.ref('account.invoice_supplier_form').id, 'form')]
                        return {
                            'name': 'Vendor bills',
                            'view_type': 'form',
                            'view_mode': 'tree,form',
                            # 'view_id': self.env.ref('account.invoice_supplier_tree').id,
                            'view_id': False,
                            'res_model': 'account.invoice',
                            'views': views,
                            # 'context': "{'type':'in_invoice'}",
                            'domain': [('id', 'in', invoices.ids)],
                            'type': 'ir.actions.act_window',
                            # 'target': 'new',
                        }
                    else:
                        # print('in vendor bill length =1')
                        return {
                            # 'name': self.booking_no,
                            'view_type': 'form',
                            'view_mode': 'form',
                            'res_model': 'account.invoice',
                            'res_id': invoices.id or False,  # readonly mode
                            #  'domain': [('id', 'in', purchase_order.ids)],
                            'type': 'ir.actions.act_window',
                            'target': 'popup',  # readonly mode
                        }

    # @api.multi
    # def operation_bill(self):
    #     for operation in self:
    #         # Get from the vendor bill list
    #         vendor_bill_list = []
    #         for cost_profit_line in operation.cost_profit_ids:
    #             for vendor_bill_line in cost_profit_line.vendor_bill_ids:
    #                 if vendor_bill_line.type in ['in_invoice', 'in_refund']:
    #                     vendor_bill_list.append(vendor_bill_line.id)
    #
    #         invoices = self.env['account.invoice'].search([
    #             ('freight_booking', '=', operation.id),
    #             ('type', 'in', ['in_invoice', 'in_refund']),
    #             ('state', '!=', 'cancel'),
    #         ])
    #
    #         invoice_name_list = []
    #         for x in invoices:
    #             invoice_name_list.append(x.id)
    #
    #         unique_list = []
    #         for y in vendor_bill_list:
    #             if invoice_name_list and len(invoice_name_list) > 0:
    #                 if y not in invoice_name_list:
    #                     unique_list.append(y)
    #             else:
    #                 unique_list.append(y)
    #         for z in invoice_name_list:
    #             # if z not in vendor_bill_list:
    #             unique_list.append(z)
    #
    #     if len(unique_list) > 1:
    #         views = [(self.env.ref('account.invoice_supplier_tree').id, 'tree'),
    #                  (self.env.ref('account.invoice_supplier_form').id, 'form')]
    #         return {
    #             'name': 'Vendor bills',
    #             'view_type': 'form',
    #             'view_mode': 'tree,form',
    #             # 'view_id': self.env.ref('account.invoice_supplier_tree').id,
    #             'view_id': False,
    #             'res_model': 'account.invoice',
    #             'views': views,
    #             # 'context': "{'type':'in_invoice'}",
    #             'domain': [('id', 'in', unique_list)],
    #             'type': 'ir.actions.act_window',
    #             # 'target': 'new',
    #         }
    #     elif len(unique_list) == 1:
    #         # print('in vendor bill length =1')
    #         return {
    #             # 'name': self.booking_no,
    #             'view_type': 'form',
    #             'view_mode': 'form',
    #             'res_model': 'account.invoice',
    #             'res_id': unique_list[0] or False,  # readonly mode
    #             #  'domain': [('id', 'in', purchase_order.ids)],
    #             'type': 'ir.actions.act_window',
    #             'target': 'popup',  # readonly mode
    #         }


    @api.multi
    def operation_si(self):
        for operation in self:
            si = self.env['freight.website.si'].search([('booking_ref', '=', operation.id), ])
        if len(si) > 1:
            views = [(self.env.ref('sci_goexcel_freight.view_tree_si').id, 'tree'),
                     (self.env.ref('sci_goexcel_freight.view_form_si').id, 'form')]
            return {
                'name': 'Shipping Instruction',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'view_id': False,
                'res_model': 'freight.website.si',
                'views': views,
                'domain': [('id', 'in', si.ids)],
                'type': 'ir.actions.act_window',
            }
        elif len(si) == 1:
            return {
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'freight.website.si',
                'res_id': si.id or False,
                'type': 'ir.actions.act_window',
                'target': 'popup',  # readonly mode
            }
        else:
            action = {'type': 'ir.actions.act_window_close'}
            return action

    @api.multi
    def operation_bol(self):
        for operation in self:
            bol = self.env['freight.bol'].search([('booking_ref', '=', operation.id)])

        if len(bol) > 1:
            views = [(self.env.ref('sci_goexcel_freight.view_tree_bol').id, 'tree'),
                     (self.env.ref('sci_goexcel_freight.view_form_bol').id, 'form')]
            return {
                'name': 'Bill Of Lading',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'view_id': False,
                'res_model': 'freight.bol',
                'views': views,
                'domain': [('id', 'in', bol.ids)],
                'type': 'ir.actions.act_window',
            }
        elif len(bol) == 1:
            return {
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'freight.bol',
                'res_id': bol.id or False,
                'type': 'ir.actions.act_window',
                'target': 'popup',  # readonly mode
            }
        else:
            action = {'type': 'ir.actions.act_window_close'}
            return action

    @api.multi
    def operation_master_booking(self):
        for operation in self:
            master_booking = self.env['freight.booking'].search([
                ('id', '=', operation.master_booking.id),
            ])
            # action = self.env.ref('sci_goexcel_freight.view_tree_ocean_booking').read()[0]
            # action['views'] = [(self.env.ref('sci_goexcel_freight.view_form_booking').id, 'form')]
            # action['res_id'] = master_booking.ids[0]
            return {
                # 'name': self.booking_no,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'freight.booking',
                'res_id': master_booking.ids[0],  # readonly mode
                'domain': [('id', 'in', master_booking.ids)],
                'type': 'ir.actions.act_window',
                'target': 'popup',  # readonly mode
            }
        # return action

    @api.multi
    def action_print_job_sheet(self):

        data = {
            'model': self._name,
            'ids': self.ids,
            'form': self.ids,
        }

        return self.env.ref('sci_goexcel_freight.report_job_sheet_action').report_action(self, data=data)

    @api.multi
    def action_send_booking_confirmation(self):
        '''
        This function opens a window to compose an email, with the template message loaded by default
        '''
        self.ensure_one()
        if self.carrier_booking_no:
            ir_model_data = self.env['ir.model.data']
            try:
                template_id = \
                ir_model_data.get_object_reference('sci_goexcel_freight', 'email_template_edi_booking_confirmation')[1]
            except ValueError:
                template_id = False
            try:
                compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
            except ValueError:
                compose_form_id = False

            ctx = {
                'default_model': 'freight.booking',
                'default_res_id': self.ids[0],
                'default_use_template': bool(template_id),
                'default_template_id': template_id,
                'default_composition_mode': 'comment',
                'mark_so_as_sent': True,
                'custom_layout': "mail.mail_notification_light",
                # 'proforma': self.env.context.get('proforma', False),
                'force_email': True
            }
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            ctx['action_url'] = "{}/web?db={}".format(base_url, self.env.cr.dbname)
            return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'mail.compose.message',
                'views': [(compose_form_id, 'form')],
                'view_id': compose_form_id,
                'target': 'new',
                'context': ctx,
            }
            self.shipment_booking_status = '02'
        else:
            raise exceptions.ValidationError('Carrier Booking No must not be empty!!!')

    @api.multi
    def action_send_bl(self):
        '''
        This function opens a window to compose an email, with the template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = \
                ir_model_data.get_object_reference('sci_goexcel_freight', 'email_template_edi_bl')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False

        ctx = {
            'default_model': 'freight.booking',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'custom_layout': "mail.mail_notification_light",
            # 'proforma': self.env.context.get('proforma', False),
            'force_email': True
        }
        # base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        # ctx['action_url'] = "{}/web?db={}".format(base_url, self.env.cr.dbname)
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }
        self.shipment_booking_status = '04'

    @api.multi
    def action_send_do(self):
        '''
        This function opens a window to compose an email, with the template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = \
                ir_model_data.get_object_reference('sci_goexcel_freight', 'email_template_edi_do')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False

        ctx = {
            'default_model': 'freight.booking',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'custom_layout': "mail.mail_notification_light",
            # 'proforma': self.env.context.get('proforma', False),
            'force_email': True
        }
        # base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        # ctx['action_url'] = "{}/web?db={}".format(base_url, self.env.cr.dbname)
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    @api.onchange('status_import')
    def onchange_status_import(self):
        self.shipment_booking_status = self.status_import

    @api.onchange('status_export')
    def onchange_status_export(self):
        self.shipment_booking_status = self.status_export

    @api.onchange('commodity_type')
    def onchange_commodity_type(self):
        if self.commodity_type:
            if self.commodity_type.code == 'DG':
                self.hide_commodity_dg = False

    @api.onchange('carrier')
    def onchange_carrier(self):
        if self.carrier:
            partner = self.env['res.partner'].search([('id', '=', self.carrier.id), ])
            self.shipping_agent_code = partner.shipping_agent_code

    @api.onchange('air_status_import')
    def onchange_air_status_import(self):
        self.shipment_booking_status = self.air_status_import

    @api.onchange('air_status_export')
    def onchange_air_status_export(self):
        # _logger.warning('export=', self.status_export)
        self.shipment_booking_status = self.air_status_export

    @api.onchange('land_status')
    def onchange_land_status(self):
        self.shipment_booking_status = self.land_status

    @api.onchange('shipment_booking_status')
    def onchange_shipment_booking_status(self):
        if self.shipment_booking_status == '08':
            self.status_date_time = datetime.now()

    @api.onchange('shipment_type')
    def onchange_shipment_type(self):
        if self.shipment_type == 'direct' and self.service_type == 'ocean':
            self.hbl_no = ''
        elif self.shipment_type == 'direct' and self.service_type == 'air':
            self.awb_no = ''

    @api.onchange('service_type')
    def onchange_service_type(self):
        if self.service_type == 'air':
            self.cargo_type = 'lcl'
            self.land_cargo_type = ''
        if self.service_type == 'land':
            self.cargo_type = ''
            self.land_cargo_type = 'ftl'
        if self.service_type == 'ocean':
            self.land_cargo_type = ''
            self.cargo_type = 'fcl'

    @api.onchange('cargo_type')
    def onchange_cargo_type(self):
        if self.service_type == 'ocean':
            if self.cargo_type == 'lcl':
                self.land_cargo_type = ''

    @api.multi
    @api.onchange('customer_name')
    def onchange_customer_name(self):
        if not self.customer_name:
            self.update({
                'billing_address': False,
                'payment_term': False,
                'contact_name': False,
            })
            return
        # ['default', 'invoice', 'delivery', 'contact'])
        addr = self.customer_name.address_get(['invoice'])
        if self.direction == 'export':
            self.shipper = self.customer_name
        # self.pickup_from = self.customer_name
        if self.direction == 'import':
            self.notify_party = self.customer_name
            self.consignee = self.customer_name
        # phone = self.customer_name.address_get(['default']).phone
        values = {
            'billing_address': addr['invoice'],
            'payment_term': self.customer_name.property_payment_term_id and self.customer_name.property_payment_term_id.id or False
            # 'contact_name':

        }
        self.update(values)

    @api.onchange('vessel_name')
    def onchange_state(self):
        self.vessel_id = self.vessel_name.code

    @api.onchange('delivery_to')
    def onchange_delivery_to(self):

        adr = ''
        if self.delivery_to:
            # if self.delivery_to_address_input is False or '':
            adr += self.delivery_to.name + "\n"
            if self.delivery_to.street:
                adr += self.delivery_to.street
            if self.delivery_to.street2:
                adr += ' ' + self.delivery_to.street2
            if self.delivery_to.zip:
                adr += ' ' + self.delivery_to.zip
            if self.delivery_to.city:
                adr += ' ' + self.delivery_to.city
            if self.delivery_to.state_id:
                adr += ', ' + self.delivery_to.state_id.name
            if self.delivery_to.country_id:
                adr += ', ' + self.delivery_to.country_id.name + "\n"
            if not self.delivery_to.country_id:
                adr += "\n"
            if self.delivery_to.phone:
                adr += 'Phone: ' + self.delivery_to.phone
            elif self.delivery_to.mobile:
                adr += '. Mobile: ' + self.delivery_to.mobile
            # if self.delivery_to.country_id:
            #     adr += ', ' + self.delivery_to.country_id.name
            # _logger.warning("adr" + adr)
            self.delivery_to_address_input = adr

    @api.onchange('pickup_from')
    def onchange_pickup_from(self):
        adr = ''
        if self.pickup_from:
            # if self.pickup_from_address_input is False or '':
            adr += self.pickup_from.name + "\n"
            if self.pickup_from.street:
                adr += self.pickup_from.street
            if self.pickup_from.street2:
                adr += ' ' + self.pickup_from.street2
            if self.pickup_from.zip:
                adr += ' ' + self.pickup_from.zip
            if self.pickup_from.city:
                adr += ' ' + self.pickup_from.city
            if self.pickup_from.state_id:
                adr += ', ' + self.pickup_from.state_id.name
            if self.pickup_from.country_id:
                adr += ', ' + self.pickup_from.country_id.name + "\n"
            if not self.pickup_from.country_id:
                adr += "\n"
            if self.pickup_from.phone:
                adr += 'Phone: ' + self.pickup_from.phone
            elif self.pickup_from.mobile:
                adr += '. Mobile: ' + self.pickup_from.mobile
            # if self.pickup_from.country_id:
            #     adr += ', ' + self.pickup_from.country_id.name
            # _logger.warning("adr" + adr)
            self.pickup_from_address_input = adr

    @api.onchange('shipper')
    def onchange_shipper(self):
        adr = ''
        if self.shipper:
            # if self.shipper_address_input is False or '':
            adr += self.shipper.name + "\n"
            if self.shipper.street:
                adr += self.shipper.street
            if self.shipper.street2:
                adr += ' ' + self.shipper.street2
            if self.shipper.zip:
                adr += ' ' + self.shipper.zip
            if self.shipper.city:
                adr += ' ' + self.shipper.city
            if self.shipper.state_id:
                adr += ', ' + self.shipper.state_id.name
            if self.shipper.country_id:
                adr += ', ' + self.shipper.country_id.name + "\n"
            if not self.shipper.country_id:
                adr += "\n"
            if self.shipper.phone:
                adr += 'Phone: ' + self.shipper.phone
            elif self.shipper.mobile:
                adr += '. Mobile: ' + self.shipper.mobile
            # if self.shipper.country_id:
            #     adr += ', ' + self.shipper.country_id.name
            # _logger.warning("adr" + adr)
            self.shipper_address_input = adr

    @api.onchange('consignee')
    def onchange_consignee(self):
        adr = ''
        if self.consignee:
            # if self.consignee_address_input is False or '':
            adr += self.consignee.name + "\n"
            if self.consignee.street:
                adr += self.consignee.street
            if self.consignee.street2:
                adr += ' ' + self.consignee.street2
            if self.consignee.zip:
                adr += ' ' + self.consignee.zip
            if self.consignee.city:
                adr += ' ' + self.consignee.city
            if self.consignee.state_id:
                adr += ', ' + self.consignee.state_id.name
            if self.consignee.country_id:
                adr += ', ' + self.consignee.country_id.name + "\n"
            if not self.consignee.country_id:
                adr += "\n"
            if self.consignee.phone:
                adr += 'Phone: ' + self.consignee.phone
            elif self.consignee.mobile:
                adr += '. Mobile: ' + self.consignee.mobile
            # if self.consignee.country_id:
            #     adr += ', ' + self.consignee.country_id.name
            # _logger.warning("adr" + adr)
            self.consignee_address_input = adr
        if self.direction:
            if self.direction == 'export':
                self.notify_party = self.consignee.id

    @api.onchange('notify_party')
    def onchange_notify_party(self):
        adr = ''
        if self.notify_party:
            # if self.notify_party_address_input is False or '':
            adr = self.notify_party.name + "\n"
            if self.notify_party.street:
                adr += self.notify_party.street
            if self.notify_party.street2:
                adr += ' ' + self.notify_party.street2
            if self.notify_party.zip:
                adr += ' ' + self.notify_party.zip
            if self.notify_party.city:
                adr += ' ' + self.notify_party.city
            if self.notify_party.state_id:
                adr += ', ' + self.notify_party.state_id.name
            if self.notify_party.country_id:
                adr += ', ' + self.notify_party.country_id.name + "\n"
            if not self.notify_party.country_id:
                adr += "\n"
            if self.notify_party.phone:
                adr += 'Phone: ' + self.notify_party.phone
            elif self.notify_party.mobile:
                adr += '. Mobile: ' + self.notify_party.mobile

            # if self.notify_party.country_id:
            #     adr += ', ' + self.notify_party.country_id.name
            # _logger.warning("adr" + adr)
            self.notify_party_address_input = adr

    @api.onchange('port_of_loading')
    def onchange_port_of_loading(self):
        if self.port_of_loading:
            self.port_of_loading_input = self.port_of_loading.name

    @api.onchange('port_of_tranship')
    def onchange_port_of_tranship(self):
        if self.port_of_tranship:
            self.port_of_tranship_input = self.port_of_tranship.name

    @api.onchange('port_of_discharge')
    def onchange_port_of_discharge(self):
        if self.port_of_discharge:
            self.port_of_discharge_input = self.port_of_discharge.name

    @api.onchange('lcl_pcs')
    def onchange_lcl_pcs(self):
        if self.lcl_pcs:
            if self.lcl_volume > 0.0 and self.lcl_weight > 0.0:
                # manifest = self.env['freight.operations.line2'].search([
                #     ('operation_id2', '=', self.operation_line_ids2.id),
                # ])
                # _logger.warning('len:' + str(len(manifest)))
                # if len(manifest) == 0:
                # booking_obj = self.env['freight.booking']
                operation_line_obj = self.env['freight.operations.line2']
                op_line = operation_line_obj.create({
                    'packages_no': self.lcl_pcs or '',
                    'exp_vol': self.lcl_volume or '',
                    'exp_gross_weight': self.lcl_weight or '',
                    'container_commodity_id': self.commodity.id or '',
                    'container_product_name': self.commodity.name or '',
                    'operation_id2': self._origin.id,
                })
                self.operation_line_ids2 = op_line
                # self.write({'operation_line_ids2': op_line or False})

    @api.onchange('lcl_volume')
    def onchange_lcl_volume(self):
        if self.lcl_pcs:
            if self.lcl_volume > 0.0 and self.lcl_weight > 0.0:
                # manifest = self.env['freight.operations.line2'].search([
                #     ('operation_id2', '=', self.operation_line_ids2.id),
                # ])
                # _logger.warning('len:' + str(len(manifest)))
                # if len(manifest) == 0:
                operation_line_obj = self.env['freight.operations.line2']
                op_line = operation_line_obj.create({
                    'packages_no': self.lcl_pcs or '',
                    'exp_vol': self.lcl_volume or '',
                    'exp_gross_weight': self.lcl_weight or '',
                    'container_commodity_id': self.commodity.id or '',
                    'container_product_name': self.commodity.name or '',
                    'operation_id2': self._origin.id,
                })
                self.operation_line_ids2 = op_line
                # self.write({'operation_line_ids2': op_line or False})

    @api.onchange('lcl_weight')
    def onchange_lcl_weight(self):
        if self.lcl_pcs:
            if self.lcl_volume > 0.0 and self.lcl_weight > 0.0:
                # manifest = self.env['freight.operations.line2'].search([
                #     ('operation_id2', '=', self.operation_line_ids2.id),
                # ])
                # _logger.warning('len:' + str(len(manifest)))
                # if len(manifest) == 0:
                operation_line_obj = self.env['freight.operations.line2']
                op_line = operation_line_obj.create({
                    'packages_no': self.lcl_pcs or '',
                    'exp_vol': self.lcl_volume or '',
                    'exp_gross_weight': self.lcl_weight or '',
                    'container_commodity_id': self.commodity.id or '',
                    'container_product_name': self.commodity.name or '',
                    'operation_id2': self._origin.id,
                })
                self.operation_line_ids2 = op_line
                # self.write({'operation_line_ids2': op_line or False})

    @api.onchange('booking_date_time')
    def _onchange_booking_date_time(self):
        if self.booking_date_time:
            # days = self.booking_date_time - datetime.now().date()
            elapsed_days = (self.booking_date_time - datetime.now().date()).days
            # _logger.warning('elapsed days:' + str(elapsed_days))
            if elapsed_days <= 0:
                self.elapsed_day_booking = '0'
            else:
                self.elapsed_day_booking = elapsed_days
            # self.sudo().write({'elapsed_day_booking': elapsed_days})

    # TODO
    @api.multi
    @api.onchange('sale_order_template_id')
    def onchange_sale_order_template_id(self):
        cost_profit_obj = self.env['freight.cost_profit']
        # _logger.warning('booking_no=' + str(self.booking_no))
        booking = self.env['freight.booking'].search([('booking_no', '=', self.booking_no), ])
        if not self.sale_order_template_id:
            return
        # order_lines = [(5, 0, 0)]    #remove all the existing lines
        # data = []
        for line in self.sale_order_template_id.sale_order_template_line_ids:
            if line.product_id:
                # _logger.warning('line.product_id=' + str(line.product_id))
                # _logger.warning('self.id=' + str(self.id))
                # _logger.warning('self.ids=' + str(self.ids))
                # _logger.warning('booking id=' + str(self.env.context.get('active_ids')))
                cost_profit_ids = booking.cost_profit_ids.ids
                cost_profit_line = cost_profit_obj.create({
                    'list_price': line.price_unit or 0.0,
                    'profit_qty': line.product_uom_qty or 1,
                    'product_id': line.product_id.id,
                    'booking_id': booking.id,
                    'product_name': line.name,
                    # 'uom_id': line.product_uom_id.id,
                })
                cost_profit_ids.append(cost_profit_line.id)
                booking.cost_profit_ids = [(6, 0, cost_profit_ids)]
        message = 'Click Save to refresh the Cost & Profit!'
        warning_mess = {'title': ('Refresh'), 'message': message}

        return {'warning': warning_mess}
        # raise exceptions.ValidationError('Click Save to refresh the Cost & Profit!!!')

    @api.onchange('sq_reference')
    def onchange_sq_reference(self):
        if self.sq_reference:
            sq = self.env['sale.order'].search([('id', '=', self.sq_reference.id)])
            booking = self.env['freight.booking'].search([('booking_no', '=', self.booking_no)])

            self.billing_address = sq.partner_id.id or False,
            self.sales_person = sq.user_id.id,
            self.incoterm = sq.incoterm.id or False,
            self.port_of_loading = sq.POL.id or False,
            self.port_of_discharge = sq.POD.id or False,
            self.commodity = sq.commodity.id or False,
            self.payment_term = sq.payment_term_id.id or False,
            if sq.carrier_booking_no:
                self.carrier_booking_no = sq.carrier_booking_no
            self.contact_name = sq.contact_name.id or False,
            self.forwarding_agent_code = sq.forwarding_agent_code.id or False,
            self.hs_code = sq.hs_code.id or False,
            if sq.coo:
                self.coo = True
            else:
                self.coo = False
            if sq.fumigation:
                self.fumigation = True
            else:
                self.fumigation = False
            if sq.insurance:
                self.insurance = True
            else:
                self.insurance = False
            if sq.cpc:
                self.cpc = True
            else:
                self.cpc = False
            self.warehouse_hours = sq.warehouse_hours.id or False,
            self.airport_departure = sq.airport_departure.id or False,
            self.airport_destination = sq.airport_destination.id or False,
            self.transporter_company = sq.transporter_company.id or False,
            shipper_adr = ''
            consignee_adr = ''
            notify_party_adr = ''
            if sq.shipper:
                shipper_adr += sq.shipper.name + "\n"
                if sq.shipper.street:
                    shipper_adr += sq.shipper.street
                if sq.shipper.street2:
                    shipper_adr += ' ' + sq.shipper.street2
                if sq.shipper.zip:
                    shipper_adr += ' ' + sq.shipper.zip
                if sq.shipper.city:
                    shipper_adr += ' ' + sq.shipper.city
                if sq.shipper.state_id:
                    shipper_adr += ', ' + sq.shipper.state_id.name
                if sq.shipper.country_id:
                    shipper_adr += ', ' + sq.shipper.country_id.name + "\n"
                if not sq.shipper.country_id:
                    shipper_adr += "\n"
                if sq.shipper.phone:
                    shipper_adr += 'Phone: ' + sq.shipper.phone
                elif sq.shipper.mobile:
                    shipper_adr += '. Mobile: ' + sq.shipper.mobile
            if sq.consignee:
                consignee_adr += sq.consignee.name + "\n"
                if sq.consignee.street:
                    consignee_adr += sq.consignee.street
                if sq.consignee.street2:
                    consignee_adr += ' ' + sq.consignee.street2
                if sq.consignee.zip:
                    consignee_adr += ' ' + sq.consignee.zip
                if sq.consignee.city:
                    consignee_adr += ' ' + sq.consignee.city
                if sq.consignee.state_id:
                    consignee_adr += ', ' + sq.consignee.state_id.name
                if sq.consignee.country_id:
                    consignee_adr += ', ' + sq.consignee.country_id.name + "\n"
                if not sq.consignee.country_id:
                    consignee_adr += "\n"
                if sq.consignee.phone:
                    consignee_adr += 'Phone: ' + sq.consignee.phone
                elif sq.consignee.mobile:
                    consignee_adr += '. Mobile: ' + sq.consignee.mobile
            if sq.partner_id:
                notify_party_adr = sq.partner_id.name + "\n"
                if sq.partner_id.street:
                    notify_party_adr += sq.partner_id.street
                if sq.partner_id.street2:
                    notify_party_adr += ' ' + sq.partner_id.street2
                if sq.partner_id.zip:
                    notify_party_adr += ' ' + sq.partner_id.zip
                if sq.partner_id.city:
                    notify_party_adr += ' ' + sq.partner_id.city
                if sq.partner_id.state_id:
                    notify_party_adr += ', ' + sq.partner_id.state_id.name
                if sq.partner_id.country_id:
                    notify_party_adr += ', ' + sq.partner_id.country_id.name + "\n"
                if not sq.partner_id.country_id:
                    notify_party_adr += "\n"
                if sq.partner_id.phone:
                    notify_party_adr += 'Phone: ' + sq.partner_id.phone
                elif sq.partner_id.mobile:
                    notify_party_adr += '. Mobile: ' + sq.partner_id.mobile
            booking.write({'direction': sq.mode or False,
                           'customer_name': sq.partner_id.id or False,
                           'cargo_type': sq.type or False,
                           'service_type': sq.service_type,
                           'shipper': sq.shipper.id or False,
                           'consignee': sq.consignee.id or False,
                           'notify_party': sq.partner_id.id or False,
                           'notify_party_address_input': notify_party_adr,
                           'consignee_address_input': consignee_adr,
                           'shipper_address_input': shipper_adr,
                           })
            for line in booking.cost_profit_ids:
                line.unlink()
            cost_profit_obj = self.env['freight.cost_profit']
            for line in sq.order_line:
                if line.product_id:
                    if line.freight_foreign_price > 0.0:
                        price_unit = line.freight_foreign_price
                    else:
                        price_unit = line.price_unit
                    cost_profit_line = cost_profit_obj.create({
                        'product_id': line.product_id.id or False,
                        'product_name': line.name or False,
                        'booking_id': booking.id or '',
                        'profit_qty': line.product_uom_qty or 0,
                        'profit_currency': line.freight_currency.id,
                        'profit_currency_rate': line.freight_currency_rate or 1.0,
                        'list_price': price_unit or 0.0,
                    })
                    booking.write({'cost_profit_ids': cost_profit_line or False})


# Full Container Cargo
class FreightOperationLine(models.Model):
    """Freight Operation Line Model."""

    _name = 'freight.operations.line'
    _description = 'Order Line'
    _rec_name = 'container_id'
    # _inherit = ['mail.thread', 'mail.activity.mixin']

    created_bl = fields.Boolean('Created BL')

    operation_id = fields.Many2one('freight.booking', string='Operation FCL', required=True, ondelete='cascade',
                                   index=True,
                                   copy=False)
    # not used anymore
    container_id = fields.Many2one('freight.containers', string="Obs Container", track_visibility='onchange')
    sequence = fields.Integer(string="sequence")
    # used this as container
    container_product_id = fields.Many2one('product.product', string='Container Size', track_visibility='onchange')
    container_commodity_id = fields.Many2one('product.product', string='Commodity', track_visibility='onchange')
    container_product_name = fields.Text(string='Description', track_visibility='onchange')
    container_no = fields.Char(string="Container No.", track_visibility='onchange')
    seal_no = fields.Char(string="Seal No.", track_visibility='onchange')
    packages_no = fields.Integer(string="No. of Packages", track_visibility='onchange')
    packages_no_uom = fields.Many2one('uom.uom', string="UoM", track_visibility='onchange')
    exp_net_weight = fields.Float(string="Net Weight(KG)", help="Expected Weight in kg.", track_visibility='onchange')
    exp_net_weight_uom = fields.Many2one('uom.uom', string="UoM", track_visibility='onchange')
    exp_gross_weight = fields.Float(string="Gross Weight(KG)", digits=(12, 4),
                                    help="Expected Weight in kg.", track_visibility='onchange')
    exp_gross_weight_uom = fields.Many2one('uom.uom', string="UoM", track_visibility='onchange')
    exp_vol = fields.Float(string="Measurement Vol", digits=(12, 4),
                           help="Expected Volume in M3 or CM3", track_visibility='onchange')
    exp_vol_uom = fields.Many2one('uom.uom', string="UoM", track_visibility='onchange')
    remark = fields.Text(string="Marking")
    dim_length = fields.Float(string='Length', help="Length in cm", default="0.00", track_visibility='onchange')
    dim_width = fields.Float(string='Width', default="0.00", help="Width in cm", track_visibility='onchange')
    dim_height = fields.Float(string='Height', default="0.00", help="Height in cm", track_visibility='onchange')

    # total_packages = fields.Float(string="Total Cartons")
    # exp_net_weight = fields.Float(string="Net Weight",
    #                               help="Expected Weight in kg.")
    # exp_gross_weight = fields.Float(string="Gross Weight",
    #                                 help="Expected Weight in kg.")

    shipping_mark = fields.Char(string="Shipping Mark", track_visibility='onchange')

    fcl_container_qty = fields.Float(string="Qty", digits=(8, 0), default=1, track_visibility='onchange')
    billing_on = fields.Selection([('weight', 'Weight'),
                                   ('volume', 'Volume')], string="Billing On",
                                  default='weight', track_visibility='onchange')
    # sale_price = fields.Float(string='Sale Price',
    #                           compute="_compute_calculate_sale_price",
    #                           store=True)
    # price = fields.Float(string='Price')
    invoice_id = fields.Many2one('account.invoice', string="Invoice", track_visibility='onchange')
    inv_line_id = fields.Many2one('account.invoice.line',
                                  string="Invoice Line", track_visibility='onchange')

    # @api.onchange('container_id')
    # def _onchange_container_id(self):
    #     vals = {}
    #     vals['container_product_id'] = self.operation_id.commodity
    #     self.update(vals)

    @api.onchange('container_product_id')
    def _onchange_container_product_id(self):
        vals = {}
        if not self.container_commodity_id:
            if self.operation_id.commodity:
                vals['container_commodity_id'] = self.operation_id.commodity.id
                self.update(vals)

    @api.onchange('container_commodity_id')
    def _onchange_container_commodity_id(self):
        vals = {}
        if self.container_commodity_id:
            vals['container_product_name'] = self.container_commodity_id.name
            self.update(vals)

    @api.multi
    def _get_default_container_category(self):
        container_lines = self.env['freight.product.category'].search([('type', '=ilike', 'container')])
        for container_line in container_lines:
            # _logger.warning('_get_default_container_category=' + str(container_line.product_category))
            return container_line.product_category

    container_category_id = fields.Many2one('product.category', string="Container Product Id",
                                            default=_get_default_container_category)

    @api.multi
    def _get_default_commodity_category(self):
        commodity_lines = self.env['freight.product.category'].search([('type', '=ilike', 'commodity')])
        for commodity_line in commodity_lines:
            # _logger.warning('_get_default_commodity_category=' + str(commodity_line.product_category))
            return commodity_line.product_category

    commodity_category_id = fields.Many2one('product.category', string="Commodity Product Id",
                                            default=_get_default_commodity_category)

    @api.model
    def create(self, vals):
        # _logger.warning("in create")
        res = super(FreightOperationLine, self).create(vals)
        content = ""
        if vals.get("container_no"):
            content = content + "  \u2022 Container No: " + str(vals.get("container_no")) + "<br/>"
        if vals.get("container_product_id"):
            content = content + "  \u2022 Container: " + str(vals.get("container_product_id")) + "<br/>"
        if vals.get("container_commodity_id"):
            content = content + "  \u2022 Commodity: " + str(vals.get("container_commodity_id")) + "<br/>"
        if vals.get("seal_no"):
            content = content + "  \u2022 Seal No.: " + str(vals.get("seal_no")) + "<br/>"
        if vals.get("container_product_name"):
            content = content + "  \u2022 Description: " + str(vals.get("container_product_name")) + "<br/>"
        if vals.get("packages_no"):
            content = content + "  \u2022 No. of Packages: " + str(vals.get("packages_no")) + "<br/>"
        if vals.get("packages_no_uom"):
            content = content + "  \u2022 UoM: " + str(vals.get("packages_no_uom")) + "<br/>"
        if vals.get("exp_net_weight"):
            content = content + "  \u2022 Net Weight(KG): " + str(vals.get("exp_net_weight")) + "<br/>"
        if vals.get("exp_gross_weight"):
            content = content + "  \u2022 Gross Weight(KG): " + str(vals.get("exp_gross_weight")) + "<br/>"
        if vals.get("dim_length"):
            content = content + "  \u2022 Length: " + str(vals.get("dim_length")) + "<br/>"
        if vals.get("dim_width"):
            content = content + "  \u2022 Width: " + str(vals.get("dim_width")) + "<br/>"
        if vals.get("dim_height"):
            content = content + "  \u2022 Height: " + str(vals.get("dim_height")) + "<br/>"
        if vals.get("exp_vol"):
            content = content + "  \u2022 Measurement (M3): " + str(vals.get("exp_vol")) + "<br/>"
        if vals.get("remark"):
            content = content + "  \u2022 Remark: " + str(vals.get("remark")) + "<br/>"
        res.operation_id.message_post(body=content)
        return res

    @api.multi
    def write(self, vals):
        res = super(FreightOperationLine, self).write(vals)
        content = ""
        if vals.get("container_no"):
            content = content + "  \u2022 Container No: " + str(vals.get("container_no")) + "<br/>"
        if vals.get("container_product_id"):
            content = content + "  \u2022 Container: " + str(vals.get("container_product_id")) + "<br/>"
        if vals.get("container_commodity_id"):
            content = content + "  \u2022 Commodity: " + str(vals.get("container_commodity_id")) + "<br/>"
        if vals.get("seal_no"):
            content = content + "  \u2022 Seal No.: " + str(vals.get("seal_no")) + "<br/>"
        if vals.get("container_product_name"):
            content = content + "  \u2022 Description: " + str(vals.get("container_product_name")) + "<br/>"
        if vals.get("packages_no"):
            content = content + "  \u2022 No. of Packages: " + str(vals.get("packages_no")) + "<br/>"
        if vals.get("packages_no_uom"):
            content = content + "  \u2022 UoM: " + str(vals.get("packages_no_uom")) + "<br/>"
        if vals.get("exp_net_weight"):
            content = content + "  \u2022 Net Weight(KG): " + str(vals.get("exp_net_weight")) + "<br/>"
        if vals.get("exp_gross_weight"):
            content = content + "  \u2022 Gross Weight(KG): " + str(vals.get("exp_gross_weight")) + "<br/>"
        if vals.get("dim_length"):
            content = content + "  \u2022 Length: " + str(vals.get("dim_length")) + "<br/>"
        if vals.get("dim_width"):
            content = content + "  \u2022 Width: " + str(vals.get("dim_width")) + "<br/>"
        if vals.get("dim_height"):
            content = content + "  \u2022 Height: " + str(vals.get("dim_height")) + "<br/>"
        if vals.get("exp_vol"):
            content = content + "  \u2022 Measurement (M3): " + str(vals.get("exp_vol")) + "<br/>"
        if vals.get("remark"):
            content = content + "  \u2022 Remark: " + str(vals.get("remark")) + "<br/>"
        for line in self:
            line.operation_id.message_post(body=content)
        return res


# Less Container Cargo
class FreightOperationLine2(models.Model):
    """Freight Operation Line Model."""

    _name = 'freight.operations.line2'
    _description = 'Order Line'
    _rec_name = 'container_id'
    # _inherit = ['mail.thread', 'mail.activity.mixin']

    created_bl = fields.Boolean('Created BL')

    operation_id2 = fields.Many2one('freight.booking', string='Operation LCL', required=True, ondelete='cascade',
                                    index=True,
                                    copy=False)
    # not used anymore
    container_id = fields.Many2one('freight.containers', string="Obs Container", track_visibility='onchange')
    container_lcl_id = fields.Many2one('product.product', string='Container', track_visibility='onchange')
    sequence = fields.Integer(string="sequence")
    # subjob_no = fields.Char(string='Sub Job', copy=False)
    subjob = fields.Many2one('freight.booking', string='Sub Job', copy=False)
    container_product_id = fields.Many2one('product.product', string='Container Size', track_visibility='onchange')
    container_commodity_id = fields.Many2one('product.product', string='Commodity', track_visibility='onchange')
    container_product_name = fields.Text(string='Description', track_visibility='onchange')
    container_no = fields.Char(string="Container No.", track_visibility='onchange')
    seal_no = fields.Char(string="Seal No.", track_visibility='onchange')

    """
    lcl_pcs = fields.Integer(string='LCL Pcs', store=True, track_visibility='onchange')
    lcl_weight = fields.Float(string='LCL Weight', store=True, track_visibility='onchange')
    lcl_volume = fields.Float(string='LCL Volume', store=True, track_visibility='onchange')

    @api.multi
    def _get_default_packages_no(self):
        print(self.operation_id2)
        packages_no = False
        if self.operation_id2.lcl_pcs:
            print(self.operation_id2)
            print(self.operation_id2.lcl_pcs)
            packages_no = self.operation_id2.lcl_pcs
            return packages_no
            """

    packages_no = fields.Integer(string="No. of Packages", help="Eg, Carton", track_visibility='onchange')
    packages_no_uom = fields.Many2one('uom.uom', string="UoM", track_visibility='onchange')
    exp_gross_weight = fields.Float(string="Gross Weight(KG)", digits=(12, 4),
                                    help="Expected Weight in kg.", track_visibility='onchange')
    exp_gross_weight_uom = fields.Many2one('uom.uom', string="UoM", track_visibility='onchange')
    exp_net_weight = fields.Float(string="Net Weight(KG)",
                                  help="Expected Net Weight in kg.", track_visibility='onchange')
    exp_net_weight_uom = fields.Many2one('uom.uom', string="UoM", track_visibility='onchange')
    dim_length = fields.Float(string='Length', help="Length in cm", default="0.00", track_visibility='onchange')
    dim_width = fields.Float(string='Width', default="0.00", help="Width in cm", track_visibility='onchange')
    dim_height = fields.Float(string='Height', default="0.00", help="Height in cm", track_visibility='onchange')
    exp_vol = fields.Float(string="Measurement Vol", digits=(12, 4),
                           help="Expected Volume in M3 or CM3 Measure", compute="_compute_vol")
    exp_vol_uom = fields.Many2one('uom.uom', string="UoM", track_visibility='onchange')
    volumetric_weight = fields.Float(string='Vol. Weight', compute="_compute_vol_weight", store=True)
    chargeable_weight = fields.Float(string='Chargeable Weight', compute="_compute_chargeable_weight", store=True)
    remark = fields.Text(string="Remark")
    # goods_desc = fields.Text(string="Description of Goods")
    # total_packages = fields.Float(string="Total Packages")

    # exp_gross_weight = fields.Float(string="Gross Weight",
    #                                help="Expected Weight in kg.")

    shipping_mark = fields.Char(string="Shipping Mark", track_visibility='onchange')
    fcl_container_qty = fields.Float(string="Qty", track_visibility='onchange')
    billing_on = fields.Selection([('weight', 'Weight'),
                                   ('volume', 'Volume')], string="Billing On",
                                  default='weight', track_visibility='onchange')
    # sale_price = fields.Float(string='Sale Price',
    #                           compute="_compute_calculate_sale_price",
    #                           store=True)
    # price = fields.Float(string='Price')
    invoice_id = fields.Many2one('account.invoice', vol_weightstring="Invoice", track_visibility='onchange')
    inv_line_id = fields.Many2one('account.invoice.line',
                                  string="Invoice Line", track_visibility='onchange')

    # @api.onchange('container_product_id')
    # def _onchange_container_product_id(self):
    #     vals = {}
    #     vals['container_product_name'] = self.container_product_id.name
    #     self.update(vals)

    @api.onchange('container_no')
    def _onchange_container_no(self):
        vals = {}
        if self.operation_id2.commodity:
            vals['container_commodity_id'] = self.operation_id2.commodity.id
            self.update(vals)

    @api.onchange('container_commodity_id')
    def _onchange_container_commodity_id(self):
        vals = {}
        if self.container_commodity_id:
            vals['container_product_name'] = self.container_commodity_id.name
            self.update(vals)

    @api.depends('dim_length', 'dim_width', 'dim_height', 'packages_no')
    def _compute_vol(self):
        for line in self:
            if line.dim_length or line.dim_width or line.dim_height or line.packages_no:
                line.exp_vol = line.packages_no * line.dim_length * line.dim_width * line.dim_height

    @api.depends('dim_length', 'dim_width', 'dim_height', 'packages_no')
    def _compute_vol_weight(self):
        for line in self:
            if line.dim_length or line.dim_width or line.dim_height or line.packages_no:
                line.volumetric_weight = (line.packages_no * line.dim_length * line.dim_width * line.dim_height) / 6000

    @api.depends('exp_gross_weight', 'volumetric_weight')
    def _compute_chargeable_weight(self):
        for line in self:
            if line.exp_gross_weight > line.volumetric_weight:
                line.chargeable_weight = line.exp_gross_weight
            else:
                line.chargeable_weight = line.volumetric_weight

    @api.multi
    def _get_default_container_category(self):
        container_lines = self.env['freight.product.category'].search([('type', '=ilike', 'container')])
        for container_line in container_lines:
            # _logger.warning('_get_default_container_category=' + str(container_line.product_category))
            return container_line.product_category

    container_category_id = fields.Many2one('product.category', string="Container Product Id",
                                            default=_get_default_container_category)

    @api.multi
    def _get_default_commodity_category(self):
        commodity_lines = self.env['freight.product.category'].search([('type', '=ilike', 'commodity')])
        for commodity_line in commodity_lines:
            # _logger.warning('_get_default_commodity_category=' + str(commodity_line.product_category))
            return commodity_line.product_category

    commodity_category_id = fields.Many2one('product.category', string="Commodity Product Id",
                                            default=_get_default_commodity_category)

    @api.model
    def create(self, vals):
        # _logger.warning("in create")
        res = super(FreightOperationLine2, self).create(vals)
        content = ""
        if vals.get("container_no"):
            content = content + "  \u2022 Container No.: " + str(vals.get("container_no")) + "<br/>"
        if vals.get("container_commodity_id"):
            content = content + "  \u2022 Commodity: " + str(vals.get("container_commodity_id")) + "<br/>"
        if vals.get("container_product_name"):
            content = content + "  \u2022 Description: " + str(vals.get("container_product_name")) + "<br/>"
        if vals.get("subjob"):
            content = content + "  \u2022 Sub Job: " + str(vals.get("subjob")) + "<br/>"
        if vals.get("packages_no"):
            content = content + "  \u2022 No. of Packages: " + str(vals.get("packages_no")) + "<br/>"
        if vals.get("packages_no_uom"):
            content = content + "  \u2022 UoM: " + str(vals.get("packages_no_uom")) + "<br/>"
        if vals.get("exp_gross_weight"):
            content = content + "  \u2022 Gross Weight(KG): " + str(vals.get("exp_gross_weight")) + "<br/>"
        if vals.get("exp_net_weight"):
            content = content + "  \u2022 Net Weight(KG): " + str(vals.get("exp_net_weight")) + "<br/>"
        if vals.get("dim_length"):
            content = content + "  \u2022 Length: " + str(vals.get("dim_length")) + "<br/>"
        if vals.get("dim_width"):
            content = content + "  \u2022 Width: " + str(vals.get("dim_width")) + "<br/>"
        if vals.get("dim_height"):
            content = content + "  \u2022 Height: " + str(vals.get("dim_height")) + "<br/>"
        if vals.get("exp_vol"):
            content = content + "  \u2022 Measurement Vol: " + str(vals.get("exp_vol")) + "<br/>"
        if vals.get("volumetric_weight"):
            content = content + "  \u2022 Vol. Weight: " + str(vals.get("volumetric_weight")) + "<br/>"
        if vals.get("chargeable_weight"):
            content = content + "  \u2022 Chargeable Weight: " + str(vals.get("chargeable_weight")) + "<br/>"
        if vals.get("shipping_mark"):
            content = content + "  \u2022 Shipping Mark: " + str(vals.get("shipping_mark")) + "<br/>"
        # _logger.warning("create content:" + content)
        res.operation_id2.message_post(body=content)

        return res

    @api.multi
    def write(self, vals):
        # _logger.warning("in write")
        res = super(FreightOperationLine2, self).write(vals)
        # _logger.warning("after super write")
        content = ""
        if vals.get("container_no"):
            content = content + "  \u2022 Container No.: " + str(vals.get("container_no")) + "<br/>"
        if vals.get("container_commodity_id"):
            content = content + "  \u2022 Commodity: " + str(vals.get("container_commodity_id")) + "<br/>"
        if vals.get("container_product_name"):
            content = content + "  \u2022 Description: " + str(vals.get("container_product_name")) + "<br/>"
        if vals.get("subjob"):
            content = content + "  \u2022 Sub Job: " + str(vals.get("subjob")) + "<br/>"
        if vals.get("packages_no"):
            content = content + "  \u2022 No. of Packages: " + str(vals.get("packages_no")) + "<br/>"
        if vals.get("packages_no_uom"):
            content = content + "  \u2022 UoM: " + str(vals.get("packages_no_uom")) + "<br/>"
        if vals.get("exp_gross_weight"):
            content = content + "  \u2022 Gross Weight(KG): " + str(vals.get("exp_gross_weight")) + "<br/>"
        if vals.get("exp_net_weight"):
            content = content + "  \u2022 Net Weight(KG): " + str(vals.get("exp_net_weight")) + "<br/>"
        if vals.get("dim_length"):
            content = content + "  \u2022 Length: " + str(vals.get("dim_length")) + "<br/>"
        if vals.get("dim_width"):
            content = content + "  \u2022 Width: " + str(vals.get("dim_width")) + "<br/>"
        if vals.get("dim_height"):
            content = content + "  \u2022 Height: " + str(vals.get("dim_height")) + "<br/>"
        if vals.get("exp_vol"):
            content = content + "  \u2022 Measurement Vol: " + str(vals.get("exp_vol")) + "<br/>"
        if vals.get("volumetric_weight"):
            content = content + "  \u2022 Vol. Weight: " + str(vals.get("volumetric_weight")) + "<br/>"
        if vals.get("chargeable_weight"):
            content = content + "  \u2022 Chargeable Weight: " + str(vals.get("chargeable_weight")) + "<br/>"
        if vals.get("shipping_mark"):
            content = content + "  \u2022 Shipping Mark: " + str(vals.get("shipping_mark")) + "<br/>"
        # _logger.warning("write content:" + content)
        self.operation_id2.message_post(body=content)

        return res


class CostProfit(models.Model):
    _name = 'freight.cost_profit'
    _description = "Cost & Profit"
    # _order = 'booking_id, sequence, id'
    # _inherit = ['mail.thread', 'mail.activity.mixin']

    sequence = fields.Integer(string="sequence")
    operation_id = fields.Many2one('freight.booking', string='Operation')
    product_id = fields.Many2one('product.product', string="Product")
    product_name = fields.Text(string="Description")
    # qty for sales
    # profit_qty = fields.Integer(string='Qty', default="1")
    #profit_qty = fields.Float(string='Qty', default="1", digits=(12, 2))
    list_price = fields.Float(string="Unit Price")
    uom_id = fields.Many2one('uom.uom', string="UoM")
    profit_gst = fields.Selection([('zer', 'ZER')], string="GST", default="zer", track_visibility='onchange')
    tax_id = fields.Many2many('account.tax', string='Taxes',
                              domain=['|', ('active', '=', False), ('active', '=', True)])
    booking_id = fields.Many2one('freight.booking', string='Booking Reference', required=True, ondelete='cascade',
                                 index=True,
                                 copy=False)

    # company_id = fields.Many2one('res.company', 'Company', required=True, index=True, readonly=1,
    #                             default=lambda self: self.env.user.company_id.id)
    # profit_currency = fields.Many2one(related='company_id.currency_id', string="Curr")
    profit_currency = fields.Many2one('res.currency', 'Currency',
                                      default=lambda self: self.env.user.company_id.currency_id.id,
                                      track_visibility='onchange')
    # profit_currency = fields.Many2one('res.currency', string="Curr")
    profit_currency_rate = fields.Float(string='Rate', default="1.000000", digits=(12, 6), track_visibility='onchange')
    # sale amount
    profit_amount = fields.Float(string="Amt",
                                 compute="_compute_profit_amount", store=True, track_visibility='onchange')
    sale_total = fields.Float(string="Total Sales",
                              compute="_compute_sale_total", store=True, track_visibility='onchange')
    profit_qty = fields.Float(string='Qty', default="1.000", digit=(12, 3))
    cost_qty = fields.Float(string='Qty', default="1.000", digit=(12, 3))
    #cost_qty = fields.Integer(string='Qty', default="1", track_visibility='onchange')
    cost_price = fields.Float(string="Unit Price", track_visibility='onchange')
    cost_gst = fields.Selection([('zer', 'ZER')], string="Tax", default="zer", track_visibility='onchange')
    vendor_id = fields.Many2one('res.partner', string="Vendor", track_visibility='onchange')
    vendor_bill_id = fields.Many2one('account.invoice', string="Vendor Bill")

    cost_currency = fields.Many2one('res.currency', string="Curr", required=True,
                                    default=lambda self: self.env.user.company_id.currency_id.id,
                                    track_visibility='onchange')
    cost_currency_rate = fields.Float(string='Rate', default="1.000000", digits=(12, 6), track_visibility='onchange')
    cost_amount = fields.Float(string="Amt",
                               compute="_compute_cost_amount", store=True, track_visibility='onchange')
    cost_total = fields.Float(string="Total Cost",
                              compute="_compute_cost_total", store=True, track_visibility='onchange')

    #   po_created = fields.Boolean(string="PO created", default=False)
    invoiced = fields.Boolean(string='Billed', copy=False)
    is_billed = fields.Char('Is Biiled?', compute='_compute_is_billed', store=True)

    added_to_invoice = fields.Boolean(string='Invoiced', copy=False)
    invoice_paid = fields.Boolean(string='Invoice Paid', copy=False)

    @api.one
    def _set_access_for_invoiced(self):
        if self.env['res.users'].has_group('account.group_account_manager'):
            self.invoiced_readonly = False
        else:
            self.invoiced_readonly = True

    invoiced_readonly = fields.Boolean(compute="_set_access_for_invoiced",
                                       string='Is user able to modify invoiced?')
    paid = fields.Boolean(string='Paid', copy=False)
    is_paid = fields.Char('Is Paid?', compute='_compute_is_paid', store=True)

    invoice_id = fields.Many2one('account.invoice', string="Invoice")
    inv_line_id = fields.Many2one('account.invoice.line',
                                  string="Invoice Line")
    bill_id = fields.Many2one('account.invoice', string="Bill")
    bill_line_id = fields.Many2one('account.invoice.line', string="Bill Line")
    route_service = fields.Boolean(string='Is Route Service', default=False)
    profit_total = fields.Float(string="Total Profit",
                                compute="_compute_profit_total", store=True)
    margin_total = fields.Float(string="Margin %",
                                compute="_compute_margin_total", digits=(8, 2), store=True, group_operator="avg")

    @api.depends('profit_qty', 'list_price')
    def _compute_profit_amount(self):
        for service in self:
            if service.product_id:
                amount = service.profit_qty * service.list_price
                service.profit_amount = float_round(amount, 2,
                                                    rounding_method='HALF-UP') or 0.0
                # service.profit_amount = float_round(service.profit_qty * service.list_price, 2,
                #                                     rounding_method='HALF-UP') or 0.0

    @api.depends('cost_qty', 'cost_price')
    def _compute_cost_amount(self):
        for service in self:
            if service.product_id:
                amount = service.cost_qty * service.cost_price
                service.cost_amount = float_round(amount, 2,
                                                  rounding_method='HALF-UP') or 0.0
                # service.cost_amount = float_round(service.cost_qty * service.cost_price, 2,
                #                                   rounding_method='HALF-UP') or 0.0

    @api.depends('profit_amount', 'profit_currency_rate')
    def _compute_sale_total(self):
        for service in self:
            if service.product_id:
                amount = service.profit_amount * service.profit_currency_rate
                service.sale_total = float_round(amount, 2, rounding_method='HALF-UP') or 0.0
                # service.sale_total = float_round(service.profit_amount * service.profit_currency_rate, 2,
                #                                  rounding_method='HALF-UP') or 0.0

    @api.onchange('profit_currency_rate')
    def _onchange_profit_currency_rate(self):
        for service in self:
            if service.product_id:
                amount = service.profit_amount * service.profit_currency_rate
                service.sale_total = float_round(amount, 2,
                                                 rounding_method='HALF-UP') or 0.0
                # service.sale_total = float_round(service.profit_amount * service.profit_currency_rate, 2,
                #                                  rounding_method='HALF-UP') or 0.0

    @api.onchange('profit_amount')
    def _onchange_profit_amount(self):
        for service in self:
            if service.product_id:
                amount = service.profit_amount * service.profit_currency_rate
                service.sale_total = float_round(amount, 2,
                                                 rounding_method='HALF-UP') or 0.0
                service.profit_total = service.sale_total - service.cost_total or 0.0

    @api.depends('cost_amount', 'cost_currency_rate')
    def _compute_cost_total(self):
        for service in self:
            if service.product_id:
                amount = service.cost_amount * service.cost_currency_rate
                service.cost_total = float_round(amount, 2,
                                                 rounding_method='HALF-UP') or 0.0
                service.profit_total = service.sale_total - service.cost_total or 0.0

    @api.onchange('cost_amount')
    def _onchange_cost_amount(self):
        for service in self:
            if service.product_id:
                amount = service.cost_amount * service.cost_currency_rate
                service.cost_total = float_round(amount, 2,
                                                 rounding_method='HALF-UP') or 0.0
                service.profit_total = service.sale_total - service.cost_total or 0.0

    @api.onchange('cost_currency_rate')
    def _onchange_cost_currency_rate(self):
        for service in self:
            if service.product_id:
                amount = service.cost_amount * service.cost_currency_rate
                service.cost_total = float_round(amount, 2,
                                                 rounding_method='HALF-UP') or 0.0
                service.profit_total = service.sale_total - service.cost_total or 0.0

    @api.depends('cost_total', 'sale_total')
    def _compute_profit_total(self):
        for service in self:
            if service.product_id:
                service.profit_total = service.sale_total - service.cost_total or 0.0

    @api.depends('profit_total', 'sale_total')
    def _compute_margin_total(self):
        for service in self:
            if service.product_id:
                if service.sale_total > 0:
                    service.margin_total = float_round(service.profit_total / service.sale_total * 100, 2,
                                                       rounding_method='HALF-UP')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if not self.product_id:
            return {'domain': {'uom_id': []}}

        vals = {}
        domain = {'uom_id': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        if not self.uom_id or (self.product_id.uom_id.id != self.uom_id.id):
            vals['uom_id'] = self.product_id.uom_id
            vals['product_name'] = self.product_id.name

        self.update(vals)

        if self.product_id:
            self.update({
                'list_price': self.product_id.list_price or 0.0,
                'cost_price': self.product_id.standard_price or 0.0
            })

    @api.onchange('vendor_id')
    def _onchange_vendor_id(self):
        print('OnChange Vendor_ID')
        if self.vendor_id:
            if not self.invoiced:
                self.invoiced = False
                print('Invoiced False')

    @api.multi
    @api.depends('invoiced')
    def _compute_is_billed(self):
        for cost_profit_line in self:
            if cost_profit_line.vendor_id:
                if cost_profit_line.invoiced:
                    cost_profit_line.is_billed = 'Y'
                elif not cost_profit_line.invoiced:
                    cost_profit_line.is_billed = 'N'

    @api.multi
    @api.depends('paid')
    def _compute_is_paid(self):
        for cost_profit_line in self:
            if cost_profit_line.vendor_id:
                if cost_profit_line.paid:
                    cost_profit_line.is_paid = 'Y'
                elif not cost_profit_line.paid:
                    cost_profit_line.is_paid = 'N'

    @api.model
    def create(self, vals):
        # _logger.warning("in create")
        res = super(CostProfit, self).create(vals)

        # currency = self.env.user.company_id.currency_id.id
        content = ""
        if vals.get("product_name"):
            content = content + "  \u2022 Description: " + str(vals.get("product_name")) + "<br/>"
        if vals.get("profit_qty"):
            content = content + "  \u2022 Profit Qty: " + str(vals.get("profit_qty")) + "<br/>"
        if vals.get("list_price"):
            content = content + "  \u2022 list price: " + str(vals.get("list_price")) + "<br/>"
        if vals.get("profit_amount"):
            content = content + "  \u2022 Profit Amt: " + str(vals.get("profit_amount")) + "<br/>"
        if vals.get("profit_currency"):
            currency = self.env['res.currency'].search([('id', '=', vals.get("profit_currency"))])
            content = content + "  \u2022 Profit Currency: " + str(currency.name) + "<br/>"
        if vals.get("profit_currency_rate"):
            content = content + "  \u2022 Profit Currency Rate: " + str(vals.get("profit_currency_rate")) + "<br/>"
        if vals.get("sale_total"):
            content = content + "  \u2022 Total Sales: " + str(vals.get("sale_total")) + "<br/>"
        if vals.get("cost_qty"):
            content = content + "  \u2022 Cost Qty: " + str(vals.get("cost_qty")) + "<br/>"
        if vals.get("cost_price"):
            content = content + "  \u2022 Cost Unit Price: " + str(vals.get("cost_price")) + "<br/>"
        if vals.get("cost_amount"):
            content = content + "  \u2022 Cost Amt: " + str(vals.get("cost_amount")) + "<br/>"
        if vals.get("vendor_id"):
            content = content + "  \u2022 Vendor: " + str(vals.get("vendor_id.name")) + "<br/>"
        if vals.get("cost_currency"):
            currency = self.env['res.currency'].search([('id', '=', vals.get("cost_currency"))])
            content = content + "  \u2022 Cost Currency: " + str(currency.name) + "<br/>"
        if vals.get("cost_currency_rate"):
            content = content + "  \u2022 Cost Currency Rate: " + str(vals.get("cost_currency_rate")) + "<br/>"
        if vals.get("cost_total"):
            content = content + "  \u2022 Total Cost: " + str(vals.get("cost_total")) + "<br/>"
        if vals.get("profit_total"):
            content = content + "  \u2022 Total Profit: " + str(vals.get("profit_total")) + "<br/>"

        # _logger.warning("create content:" + content)
        res.booking_id.message_post(body=content)
        print(self.cost_currency)
        print(self.profit_currency)
        return res

    @api.multi
    def write(self, vals):
        # _logger.warning("in write")
        res = super(CostProfit, self).write(vals)
        # _logger.warning("after super write")
        content = ""
        if vals.get("product_name"):
            content = content + "  \u2022 Description: " + str(vals.get("product_name")) + "<br/>"
        if vals.get("profit_qty"):
            content = content + "  \u2022 Profit Qty: " + str(vals.get("profit_qty")) + "<br/>"
        if vals.get("list_price"):
            content = content + "  \u2022 Profit Unit Rate: " + str(vals.get("list_price")) + "<br/>"
        if vals.get("profit_amount"):
            content = content + "  \u2022 Profit Amt: " + str(vals.get("profit_amount")) + "<br/>"
        if vals.get("profit_currency"):
            content = content + "  \u2022 Profit Currency: " + str(self.profit_currency.name) + "<br/>"
        if vals.get("profit_currency_rate"):
            content = content + "  \u2022 Profit Currency Rate: " + str(vals.get("profit_currency_rate")) + "<br/>"
        if vals.get("sale_total"):
            content = content + "  \u2022 Total Sales: " + str(vals.get("sale_total")) + "<br/>"
        if vals.get("cost_qty"):
            content = content + "  \u2022 Cost Qty: " + str(vals.get("cost_qty")) + "<br/>"
        if vals.get("cost_price"):
            content = content + "  \u2022 Cost Unit Price: " + str(vals.get("cost_price")) + "<br/>"
        if vals.get("cost_amount"):
            content = content + "  \u2022 Cost Amt: " + str(vals.get("cost_amount")) + "<br/>"
        if vals.get("vendor_id"):
            content = content + "  \u2022 Vendor: " + str(vals.get("vendor_id.name")) + "<br/>"
        if vals.get("cost_currency"):
            content = content + "  \u2022 Cost Currency: " + str(self.cost_currency.name) + "<br/>"
        if vals.get("cost_currency_rate"):
            content = content + "  \u2022 Cost Currency Rate: " + str(vals.get("cost_currency_rate")) + "<br/>"
        if vals.get("cost_total"):
            content = content + "  \u2022 Total Cost: " + str(vals.get("cost_total")) + "<br/>"
        if vals.get("profit_total"):
            content = content + "  \u2022 Total Profit: " + str(vals.get("profit_total")) + "<br/>"

        # _logger.warning("write content:" + content)
        self.booking_id.message_post(body=content)

        return res


#
# class SubBookingLine(models.Model):
#     _name = 'freight.subbooking.line'
#     _description = 'Subbooking Line'
#     _inherit = ['mail.thread', 'mail.activity.mixin']
#
#     #rec_name = 'container_line_id'
#     sequence = fields.Integer(string="sequence")
#     subbooking_line = fields.Many2one('freight.booking', string='Subbooking Line', required=True, ondelete='cascade',
#                                     index=True, copy=False)
#     subbooking_id = fields.Many2one('freight.booking', string='Booking Job', track_visibility='onchange')
#     cargo_type = fields.Char(string='Cargo Type', copy=False, track_visibility='onchange')
#     customer_name = fields.Many2one('res.partner', string='Customer Name', track_visibility='onchange')

class FreightAirlineLine(models.Model):
    """Freight Operation Line Model."""

    _name = 'freight.airline.line'
    _description = 'Airlines'

    booking_id = fields.Many2one('freight.booking', string='Operation LCL', ondelete='cascade', index=True,
                                 copy=False)
    sq_id = fields.Many2one('sale.order', string='Operation LCL', ondelete='cascade', index=True, copy=False)
    airline = fields.Many2one('freight.airlines', string='Airline')
    price1 = fields.Float(string="Price/kg", default=0)
    price1_weight = fields.Integer(string="Weight", default=0)
    price2 = fields.Float(string="Price/kg", default=0)
    price2_weight = fields.Integer(string="Weight", default=0)
    price3 = fields.Float(string="Price/kg", default=0)
    price3_weight = fields.Integer(string="Weight", default=0)
    fsc = fields.Float(string="FSC/kg", default=0)
    ssc = fields.Float(string="SSC/kg", default=0)
    validity = fields.Selection([('ufn', 'UFN')], string='Validity')
    routing_frequency = fields.Text(string='Routing & Frequency')
    dimension_weight = fields.Text(string='Maximum dimension & weight per piece acceptable')
