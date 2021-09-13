from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo import exceptions
import logging
_logger = logging.getLogger(__name__)

class BillOfLading(models.Model):

    _name = 'freight.bol'
    _description = 'BOL'
    _order = 'date_of_issue desc, write_date desc'

    _inherit = ['mail.thread', 'mail.activity.mixin']

    bol_status = fields.Selection([('01', 'Draft'), ('02', 'Original'), ('03', 'Surrender')], string="BOL Status", default="01",
                                      copy=False, track_visibility='onchange', store=True)
    bol_no = fields.Char(string='HBL No', copy=False, readonly=True, index=True)
    carrier_booking_no = fields.Char(string='Carrier Booking No', copy=False, readonly=True)
    booking_ref = fields.Many2one('freight.booking', string='Booking Job Ref', track_visibility='onchange',
                                        copy=False, index=True)
    cargo_type = fields.Selection([('fcl', 'FCL'), ('lcl', 'LCL')], string='Cargo Type', default="fcl", track_visibility='onchange')
    direction = fields.Selection([('import', 'Import'), ('export', 'Export')], string="Direction", default="export",
                                 track_visibility='onchange')
    service_type = fields.Selection([('ocean', 'Ocean'), ('air', 'Air'), ('land', 'Land')], string="Shipment Mode",
                                    default="ocean", track_visibility='onchange')
    export_reference = fields.Char(string='Export Reference', track_visibility='onchange')
    fa_reference = fields.Char(string='Forwarding Agent and References', track_visibility='onchange')
    routing_instruction = fields.Text(string='Notify Party Routing and Instruction', track_visibility='onchange')
    point_country_origin = fields.Text(string='Point and Country of Origin', track_visibility='onchange')
    service_contract_no = fields.Char(string='Service Contract No', track_visibility='onchange')
    doc_form_no = fields.Char(string='Doc. Form No.', track_visibility='onchange')

    customer_name = fields.Many2one('res.partner', string='Customer Name', track_visibility='onchange')
    shipper = fields.Text(string='Shipper', track_visibility='onchange', help="The Party who shipped the freight, eg Exporter")
    consignee = fields.Text(string='Consignee', help="The Party who received the freight", track_visibility='onchange')
    notify_party = fields.Text(string='Notify Party', help="The Party who will be notified by Liner when the freight arrived", track_visibility='onchange')

    shipper_c = fields.Many2one('res.partner', string='Shipper')
    consignee_c = fields.Many2one('res.partner', string='Consignee Name')
    notify_party_c = fields.Many2one('res.partner', string='Notify Party')
    carrier_c = fields.Many2one('res.partner', string="Carrier")

    delivery_contact = fields.Text(string='Contact for Delivery', help="Contact information for delivery of goods", track_visibility='onchange')
    no_of_original_bl = fields.Selection([('0', '0'), ('3', '3')], string="No Of original B/L",
                     default="0", track_visibility='onchange')
    #payable_at = fields.Char(string='Payable At', default='Destination', track_visibility='onchange')
    pre_carriage_by = fields.Char(string='Pre-Carriage By', track_visibility='onchange')
    vessel = fields.Char( string='Vessel Name', track_visibility='onchange')
    voyage_no = fields.Char(string='Vessel Voyage No', track_visibility='onchange')
    date_of_issue = fields.Date(string='Shipment Date', copy=False, default=datetime.now().date(), track_visibility='onchange', index=True)
    place_of_issue = fields.Char( string='Place of Issue', track_visibility='onchange')
    # port_of_loading = fields.Many2one('freight.ports', string='Port of Loading', track_visibility='onchange')
    # port_of_discharge = fields.Many2one('freight.ports', string='Place of Discharge', track_visibility='onchange')
    port_of_loading_input = fields.Char(string='Port of Loading', track_visibility='onchange')
    port_of_discharge_input = fields.Char(string='Port of Discharge', track_visibility='onchange')
    place_of_delivery = fields.Char(string='Place of Delivery', track_visibility='onchange')
    place_of_receipt = fields.Char(string='Place of Receipt', track_visibility='onchange')

    #type_of_movement = fields.Char(string='Type of Movement', track_visibility='onchange', help='FCL or LCL')
    term = fields.Char(string='Term', track_visibility='onchange', help='eg, CY-CY')
    #freight_type = fields.Char(string='Freight Type', track_visibility='onchange', help='Prepaid or Collection')
    total_no_of_packages_words = fields.Char(string='Freight Type', track_visibility='onchange',
                                             help='Total no of packages or container in Words')
    cargo_line_ids = fields.One2many('freight.bol.cargo', 'cargo_line', string="Cargo Line",
                                         copy=True, auto_join=True, track_visibility='always')
    charge_line_ids = fields.One2many('freight.bol.charge', 'charge_line', string="Charge Line",
                                         copy=True, auto_join=True, track_visibility='always')
    # lcl_line_ids = fields.One2many('freight.website.si.lcl', 'lcl_line', string="LCL Line",
    #                                       copy=True, auto_join=True, track_visibility='always')

    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, readonly=1,
                                 default=lambda self: self.env.user.company_id.id)

    date_laden_on_board = fields.Date(string='Date Laden on Board')

    @api.model
    def create(self, vals):
        vals['bol_no'] = self.env['ir.sequence'].next_by_code('hbl')
        res = super(BillOfLading, self).create(vals)
        return res


    @api.multi
    def name_get(self):
        result = []
        for bol in self:
            name = str(bol.bol_no)
        result.append((bol.id, name))
        return result

    # @api.multi
    # def action_cancel_si(self):
    #     self.si_status = '04'



class CargoLine(models.Model):

    _name = 'freight.bol.cargo'
    _description = 'Cargo Line'

    cargo_line = fields.Many2one('freight.bol', string='Cargo Line', required=True, ondelete='cascade',
                                   index=True, copy=False)
    marks = fields.Text(string='Marks and Numbers')
    sequence = fields.Integer(string="sequence")
    container_product_name = fields.Text(string='Description of Goods')
    packages_no = fields.Char(string="No. of Packages")
    seal_no = fields.Char(string="Seal No.")
    container_no = fields.Char(string="Container No.")
    #fcl_container_qty = fields.Float(string="Qty", digits=(8, 0), track_visibility='onchange')

    exp_gross_weight = fields.Float(string="Gross Weight(KG)",
                                    help="Expected Weight in kg.")
    exp_vol = fields.Float(string="Measurement (M3)",
                           help="Expected Volume in m3 Measure")


class ChargeLine(models.Model):

    _name = 'freight.bol.charge'
    _description = 'Charge Line'

    charge_line = fields.Many2one('freight.bol', string='Charge Line', required=True, ondelete='cascade',
                                   index=True, copy=False)
    sequence = fields.Integer(string="sequence")
    freight_charges = fields.Text(string='Freight & Charges')
    rate = fields.Char(string='Rate')
    per = fields.Char(string="Per")
    amount = fields.Char(string="Amount")
    prepaid = fields.Char(string="Prepaid")
    collect = fields.Char(string="Collect")
    payable_at_by = fields.Char(string="Payable at/by")
    #fcl_container_qty = fields.Float(string="Qty", digits=(8, 0), track_visibility='onchange')

    revenue_tons = fields.Char(string='Revenue Tons')




