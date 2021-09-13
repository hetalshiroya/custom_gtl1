from odoo import models, fields, api
from odoo import tools


class BookingReport(models.Model):
    _name = 'freight.booking.pivot.report'
    _description = 'Freight Job Analysis Report'
    _auto = False

    direction = fields.Selection(
        [('import', 'Import'), ('export', 'Export')], string="Direction", readonly=True)
    cargo_type = fields.Selection(
        [('fcl', 'FCL'), ('lcl', 'LCL')], string='Cargo Type', readonly=True)
    booking_no = fields.Char(string='Booking No', readonly=True)
    obl_no = fields.Char(string='OBL No', readonly=True)
    booking_date_time = fields.Date(string='ETA/ETD Date', readonly=True)
    carrier_booking_no = fields.Char(
        string='Carrier Booking No', readonly=True)
    customer_name = fields.Many2one(
        'res.partner', string='Customer Name', readonly=True)
    billing_address = fields.Many2one(
        'res.partner', string='Billing Address', eadonly=True)
    shipper = fields.Many2one('res.partner', string='Shipper', readonly=True)
    consignee = fields.Many2one(
        'res.partner', string='Consignee Name', help="The Party who received the freight")
    port_of_loading = fields.Many2one(
        'freight.ports', string='Port of Loading', readonly=True)
    port_of_discharge = fields.Many2one(
        'freight.ports', string='Port of Discharge', readonly=True)
    owner = fields.Many2one('res.users', string="Owner", readonly=True)
    sales_person = fields.Many2one(
        'res.users', string="Salesperson", readonly=True)
    container_product_id = fields.Many2one(
        'product.product', string='Container Type', readonly=True)
    container_qty = fields.Float(
        string="Ctnr Qty", digits=(8, 0), readonly=True)
    job_no = fields.Char(
        string='Job No', track_visibility='onchange', readonly=True)
    type = fields.Char(string='Type', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    sale_total = fields.Float(string='Total Sale', readonly=True)
    cost_total = fields.Float(string='Total Cost', readonly=True)
    profit_total = fields.Float(string='Total Profit', readonly=True)

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        with_ = ("WITH %s" % with_clause) if with_clause else ""

        select_ = """
                   min(b.id) as id,
                   b.direction as direction,
                   book.job_no as job_no,
                   b.container_qty as container_qty,
                   b.booking_no as booking_no,
                   b.container_product_id as container_product_id,
                   b.carrier_booking_no as carrier_booking_no,
                   b.cargo_type as cargo_type,
                   b.booking_date_time as booking_date_time,
                   b.booking_type as booking_type,
                   b.customer_name as customer_name,
                   b.shipper as shipper,
                   b.consignee as consignee,
                   b.port_of_loading as port_of_loading,
                   b.port_of_discharge as port_of_discharge,
                   b.owner as owner,
                   b.sales_person as sales_person,
                   b.billing_address as billing_address,
                   b.obl_no as obl_no,
                   b.company_id as company_id,
                   book.type as type,
                   book.total_sale as sale_total,
                   book.total_cost as cost_total,
                   book.total_sale - book.total_cost as profit_total
                   """
        for field in fields.values():
            select_ += field

        from_ = """
                booking_invoice_line book
                    join freight_booking b on (book.booking_id=b.id)
                %s
        """ % from_clause

        groupby_ = """
            b.shipment_booking_status,
            b.customer_name,
            b.create_date,
            b.booking_no,
            b.direction,
            b.cargo_type,
            b.booking_date_time,
            b.shipper,
            book.job_no,
            b.container_product_id,
            book.type,
            b.consignee,
            b.carrier,
            book.type,
            b.container_qty,
            book.total_sale,
            book.total_cost,
            b.id %s
        """ % (groupby)

        return '%s (SELECT %s FROM %s GROUP BY %s)' % (with_, select_, from_, groupby_)

    @api.model_cr
    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (
            self._table, self._query()))
