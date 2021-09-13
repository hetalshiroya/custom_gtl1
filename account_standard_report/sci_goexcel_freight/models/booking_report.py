from odoo import models, fields, api
from odoo import tools
from odoo.exceptions import Warning


class BookingReport(models.Model):
    _name = 'freight.booking.report'
    _description = 'Freight Job Analysis Report'
    _auto = False

    direction = fields.Selection([('import', 'Import'), ('export', 'Export')], string="Direction", readonly=True)
    service_type = fields.Selection([('ocean', 'Ocean'), ('air', 'Air')], string="Shipment Mode", readonly=True)
    cargo_type = fields.Selection([('fcl', 'FCL'), ('lcl', 'LCL')], string='Cargo Type', readonly=True)
    shipment_booking_status = fields.Selection([('01', 'Booking Draft'),
                                                ('02', 'Booking Confirmed'),
                                                ('03', 'SI Received'),
                                                ('04', 'BL Confirmed'),
                                                ('05', 'OBL confirmed'),
                                                ('06', 'AWB Confirmed'),
                                                ('07', 'Shipment Arrived'), ('08', 'Done'), ('09', 'Cancelled'), ('10', 'Invoiced')], string="Booking Status", readonly=True)
    booking_no = fields.Char(string='Booking No', readonly=True)
    #hbl_no = fields.Char(string='HBL No', readonly=True)
    #obl_no = fields.Char(string='OBL No', readonly=True)
    booking_date_time = fields.Date(string='Booking Date', readonly=True)
    carrier_booking_no = fields.Char(string='Carrier Booking No', readonly=True)
    #invoice_count = fields.Integer(string='Invoice Count', readonly=True)
    #vendor_bill_count = fields.Integer(string='Vendor Bill Count', readonly=True)
    #bol_count = fields.Integer(string='BL Count', readonly=True)
    booking_type = fields.Selection([('master', 'Master'), ('sub', 'Sub')], string='Master or Sub', readonly=True)
    ##Party
    customer_name = fields.Many2one('res.partner', string='Customer Name', readonly=True)
    contact_name = fields.Many2one('res.partner', string='Contact Name', readonly=True)
    # billing_address = fields.Many2one('res.partner', string='Billing Address', eadonly=True)
    payment_term = fields.Many2one('account.payment.term', string='Payment Term', readonly=True)
    incoterm = fields.Many2one('freight.incoterm', string='Incoterm', readonly=True)
    shipper = fields.Many2one('res.partner', string='Shipper', readonly=True)
    consignee = fields.Many2one('res.partner', string='Consignee Name', help="The Party who received the freight")
    commodity = fields.Many2one('product.product', readonly=True)
    commodity_type = fields.Many2one('freight.commodity', string="Commodity Type", readonly=True)
    notify_party = fields.Many2one('res.partner', string='Notify Party', readonly=True)
    lcl_pcs = fields.Integer(string='LCL Pcs', readonly=True)
    lcl_weight = fields.Integer(string='LCL Weight', readonly=True)
    lcl_volume = fields.Integer(string='LCL Volume', readonly=True)
    # destination = fields.Many2one('freight.ports', string="Destination", readonly=True)
    ##Shipment Info
    shipment_type = fields.Selection([('house', 'House'), ('direct', 'Direct')], string='Shipment Type', readonly=True)
    priority = fields.Selection([('0', 'Low'), ('1', 'Low'), ('2', 'Normal'), ('3', 'High'), ('4', 'Very High')],
                                string='Priority', readonly=True)
    place_of_receipt = fields.Char(string='Place of Receipt', readonly=True)
    place_of_receipt_ata = fields.Date(string='Receipt ATA', readonly=True)
    port_of_loading = fields.Many2one('freight.ports', string='Port of Loading', readonly=True)
    port_of_loading_eta = fields.Date(string='Loading ETA', readonly=True)
    port_of_discharge = fields.Many2one('freight.ports', string='Port of Discharge', readonly=True)
    port_of_discharge_eta = fields.Date(string='Discharge ETA', readonly=True)
    place_of_delivery = fields.Char(string='Place of Delivery', readonly=True)
    shipment_close_date_time = fields.Datetime(string='Closing Date Time', readonly=True)

    carrier = fields.Many2one('res.partner', string="Carrier", readonly=True)
    ##Vessel Details
    vessel_name = fields.Many2one('freight.vessels', string='Vessel Name', readonly=True)
    vessel_id = fields.Char(string='Vessel ID', readonly=True)
    #psa_code = fields.Char(string='PSA Code', readonly=True)
    #scn_code = fields.Char(string='SCN Code', readonly=True)
    terminal = fields.Char(string='Terminal', readonly=True)
    freight_type = fields.Selection([('prepaid', 'Prepaid'), ('collect', 'Collect')], string='Freight Type',
                                    readonly=True)
    #other_charges = fields.Selection([('prepaid', 'Prepaid'), ('collect', 'Collect')], readonly=True)
    #principal_agent_code = fields.Many2one('res.partner', string='Principal Agent Code', readonly=True)
    #principal_agent_smk_code = fields.Char(string='Principal SMK Code', readonly=True)
    #shipping_agent_code = fields.Many2one('res.partner', string='Shipping Agent Code', readonly=True)
    #shipping_agent_smk_code = fields.Char(string='SA SMK Code', readonly=True)

    owner = fields.Many2one('res.users', string="Owner", readonly=True)
    sales_person = fields.Many2one('res.users', string="Salesperson", readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    transporter_company = fields.Many2one('res.partner', string='Transporter Company',
                                          help="The Party who transport the goods from one place to another",
                                          track_visibility='onchange')
    forwarding_agent_code = fields.Many2one('res.partner', string='Forwarding Agent',
                                            help="The Party who help to do custom clearance",
                                            track_visibility='onchange')
    product_id = fields.Many2one('product.product', string="Product", readonly=True)
    product_name = fields.Text(string="Prod. Description")
    profit_qty = fields.Integer(string='Sales Qty', readonly=True)
    list_price = fields.Float(string="Sales Unit Rate", readonly=True)
    uom_id = fields.Many2one('uom.uom', string="UoM", readonly=True)
    #profit_gst = fields.Selection([('zer', 'ZER')], string="GST", readonly=True)
    #profit_currency = fields.Many2one('res.currency', 'Currency', readonly=True)

    #profit_currency_rate = fields.Float(string='Rate', readonly=True)
    #profit_amount = fields.Float(string="Amt", readonly=True)
    sale_total = fields.Float(string="Total Sales", readonly=True)
    cost_qty = fields.Integer(string='Cost Qty', readonly=True)
    #cost_price = fields.Float(string="Cost Unit Price", readonly=True)
    #cost_gst = fields.Selection([('zer', 'ZER')], string="Tax", readonly=True)
    vendor_id = fields.Many2one('res.partner', string="Vendor", readonly=True)
    #cost_currency = fields.Many2one('res.currency', string="Curr", readonly=True)
    #cost_currency_rate = fields.Float(string='Rate', readonly=True)
    #cost_amount = fields.Float(string="Amt", readonly=True)
    cost_total = fields.Float(string="Total Cost", readonly=True)
    #invoiced = fields.Boolean(string='Invoiced', readonly=True)
    is_billed = fields.Char(String='Is Billed', readonly=True)
    # route_service = fields.Boolean(string='Is Route Service', readonly=True)
    profit_total = fields.Float(string="Total Profit", readonly=True)
    margin_total = fields.Float(string="Margin %", readonly=True, group_operator="avg")
    # container line
    container_product_id = fields.Many2one('product.product', string='Container Type', readonly=True)
    packages_no = fields.Integer(string="No. of Packages", readonly=True)
    #packages_no_uom = fields.Many2one('uom.uom', string="Pckg UoM", readonly=True)
    exp_net_weight = fields.Float(string="Net Weight(KG)", readonly=True)
    #exp_net_weight_uom = fields.Many2one('uom.uom', string="N.Weight UoM", readonly=True)
    exp_gross_weight = fields.Float(string="Gross Weight(KG)", readonly=True)
    #exp_gross_weight_uom = fields.Many2one('uom.uom', string="G.Weight UoM", readonly=True)
    exp_vol = fields.Float(string="Measurement Vol", readonly=True)
    #exp_vol_uom = fields.Many2one('uom.uom', string="Vol UoM", readonly=True)

    #pivot_sale_total = fields.Float(string='Total Sales', compute="_compute_pivot_sale_total", store=True)
    #pivot_cost_total = fields.Float(string='Total Cost', compute="_compute_pivot_cost_total", store=True)
    #pivot_profit_total = fields.Float(string='Total Profit', compute="_compute_pivot_profit_total", store=True)

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        with_ = ("WITH %s" % with_clause) if with_clause else ""

        select_ = """
            min(b.id) as id,
            b.shipment_booking_status as shipment_booking_status,
            b.direction as direction,
            b.booking_no as booking_no,
            b.carrier_booking_no as carrier_booking_no,
            b.service_type as service_type,
            b.cargo_type as cargo_type,
            b.booking_date_time as booking_date_time,
            b.customer_name as customer_name,
            b.contact_name as contact_name,
            b.incoterm as incoterm,
            b.booking_type as booking_type,
            b.shipper as shipper,
            b.consignee as consignee,
            b.commodity as commodity,
            b.commodity_type as commodity_type,
            b.notify_party as  notify_party,
            b.carrier as carrier, 
            b.shipment_type as shipment_type,
            b.priority as priority,
            b.place_of_receipt as place_of_receipt,
            b.port_of_loading as port_of_loading,
            b.port_of_discharge as port_of_discharge,	
            b.place_of_receipt_ata as place_of_receipt_ata,
            b.port_of_loading_eta as port_of_loading_eta,
            b.port_of_discharge_eta as port_of_discharge_eta,
            b.place_of_delivery as place_of_delivery,
            b.shipment_close_date_time as shipment_close_date_time,
            b.vessel_name as vessel_name,
            b.owner as owner,
            b.sales_person as sales_person,
            b.company_id as company_id,
            b.transporter_company as transporter_company,
            b.forwarding_agent_code as forwarding_agent_code,
            c.product_id as product_id, 
            c.product_name as product_name,
            c.vendor_id as vendor_id,
            c.uom_id as uom_id,
            c.cost_qty as cost_qty,
            c.profit_qty as profit_qty,
            c.list_price as list_price,
            c.is_billed as is_billed,
            f.container_product_id as container_product_id,
            f.packages_no as packages_no,
            f.packages_no_uom as packages_no_uom,
            f.exp_net_weight as exp_net_weight,
            f.exp_gross_weight as exp_gross_weight,
            f.exp_vol as exp_vol,
            sum(c.sale_total) as sale_total,
            sum(c.cost_total) as cost_total,
            sum(c.profit_total) as profit_total,
            avg(c.margin_total) as margin_total
        """

        #count(c.profit_qty) as profit_qty,
        #count(c.cost_qty) as cost_qty,

        for field in fields.values():
            select_ += field

        from_ = """
                freight_cost_profit c
                      join freight_booking b on (c.booking_id=b.id)
                      join freight_operations_line f on b.id = f.operation_id
                      join res_partner partner on b.customer_name = partner.id
                        left join product_product p on (c.product_id=p.id)
                            left join product_template t on (p.product_tmpl_id=t.id)
                    left join uom_uom u on (u.id=c.uom_id)
                    left join uom_uom u2 on (u2.id=t.uom_id)
                %s
        """ % from_clause

        groupby_ = """
            c.product_id,
            c.product_name,
            c.uom_id,
            c.vendor_id,
            c.cost_qty,
            c.profit_qty,
            c.list_price,
            c.is_billed,
            f.container_product_id,
            f.packages_no,
            f.packages_no_uom,
            f.exp_net_weight,
            f.exp_gross_weight,
            f.exp_vol,
            b.shipment_booking_status,
            b.customer_name,
            b.create_date,
            b.direction,
            b.service_type,
            b.cargo_type,
            b.booking_date_time,
            b.shipper,
            b.consignee,
            b.carrier,
            b.vessel_name,
            b.id %s
        """ % (groupby)

        return '%s (SELECT %s FROM %s WHERE c.product_id IS NOT NULL GROUP BY %s)' % (with_, select_, from_, groupby_)

    @api.model_cr
    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, self._query()))
