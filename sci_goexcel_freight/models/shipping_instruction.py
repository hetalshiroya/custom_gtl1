from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo import exceptions
from num2words import num2words
import logging
_logger = logging.getLogger(__name__)

class ShippingInstruction(models.Model):

    _name = 'freight.website.si'
    _description = 'SI'
    _order = 'booking_date desc, write_date desc'

    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Booking Information
    si_status = fields.Selection([('01', 'SI Draft'), ('02', 'SI Confirmed'), ('03', 'Done'), ('04', 'Cancelled')], string="Packing Status", default="01",
                                      copy=False, track_visibility='onchange', store=True)
    service_type = fields.Selection([('ocean', 'Ocean'), ('air', 'Air'), ('land', 'Land')], string="Shipment Mode",
                                    default="ocean", track_visibility='onchange')
    direction = fields.Selection([('import', 'Import'), ('export', 'Export')], string="Direction", default="export",
                                 track_visibility='onchange')

    cargo_type = fields.Selection([('fcl', 'FCL'), ('lcl', 'LCL')], string='Cargo Type', default="fcl", track_visibility='onchange')
    booking_ref = fields.Many2one('freight.booking', string='Booking Job Ref', track_visibility='onchange',
                                  copy=False, index=True)
    bl_ref = fields.Many2one('freight.bol', string='BL Ref', track_visibility='onchange',
                                  copy=False, index=True)
    si_no = fields.Char(string='SI No', copy=False, readonly=True, index=True)

    booking_date = fields.Date(string='Shipment Date', copy=False, default=datetime.now().date(), track_visibility='onchange', index=True)
    carrier = fields.Many2one('res.partner', string="Carrier")
    carrier_contact = fields.Many2one('res.partner', string='Carrier Contact')
    carrier_booking_ref = fields.Char(string='Carrier Booking Ref.', track_visibility='onchange', copy=False)
    customer_ref = fields.Char(string='Customer Ref.', track_visibility='onchange', copy=False)

    air_freight_type = fields.Selection([('1', 'MAWB'), ('2', 'HAWB')], string='Type')

    # Customer Information
    customer_name = fields.Many2one('res.partner', string='Customer Name', track_visibility='onchange')
    contact_name = fields.Many2one('res.partner', string='Contact Name', track_visibility='onchange')
    notify_party = fields.Text(string='Notify Party', help="The Party who will be notified by Liner when the freight arrived", track_visibility='onchange')
    shipper = fields.Text(string='Shipper', track_visibility='onchange', help="The Party who shipped the freight, eg Exporter")
    consignee = fields.Text(string='Consignee', help="The Party who received the freight", track_visibility='onchange')

    shipper_c = fields.Many2one('res.partner', string='Shipper')
    consignee_c = fields.Many2one('res.partner', string='Consignee Name')
    notify_party_c = fields.Many2one('res.partner', string='Notify Party')

    # Shipment Information
    voyage_no = fields.Char(string='Voyage No', track_visibility='onchange')
    vessel = fields.Char( string='Vessel Name', track_visibility='onchange')
    vessel_name = fields.Many2one('freight.vessels', string='Vessel Name', track_visibility='onchange')
    #vessel_id = fields.Char(string='Vessel ID', track_visibility='onchange')
    freight_type = fields.Selection([('prepaid', 'Prepaid'), ('collect', 'Collect')], string='Freight Type',
                                    track_visibility='onchange')
    bill_of_lading_type = fields.Selection([('original', 'Original'), ('telex', 'Telex'), ('seaway', 'Seaway')],
                                           string='Bill of Lading Type', track_visibility='onchange')
    bol_status = fields.Selection([('01', 'Draft'), ('02', 'Original'), ('03', 'Surrender')], string="BOL Status",
                                  default="01")
    no_of_original_bl = fields.Selection([('0', '0'), ('1', '1'), ('3', '3')], string="No Of original B/L",
                                         default="0")
    note = fields.Text(string='Remarks', track_visibility='onchange')

    port_of_loading_input = fields.Char(string='Port of Loading', track_visibility='onchange')
    port_of_discharge_input = fields.Char(string='Place of Discharge', track_visibility='onchange')
    place_of_delivery = fields.Char(string='Place of Delivery', track_visibility='onchange')
    shipping_agent = fields.Char(string='Oversea Shipping Agent', track_visibility='onchange')

    fcl_line_ids = fields.One2many('freight.website.si.fcl', 'fcl_line', string="FCL Line",
                                         copy=True, auto_join=True, track_visibility='always')
    lcl_line_ids = fields.One2many('freight.website.si.lcl', 'lcl_line', string="LCL Line",
                                          copy=True, auto_join=True, track_visibility='always')

    si_file_name = fields.Char(string="SI File name", track_visibility='onchange', copy=False)
    si_attachment = fields.Binary(string="SI Attachment", track_visibility='onchange', copy=False)
    owner = fields.Many2one('res.users', string="Owner", default=lambda self: self.env.user.id, track_visibility='onchange')
    processor = fields.Many2one('res.users', string="Processor", track_visibility='onchange')
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, readonly=1,
                                 default=lambda self: self.env.user.company_id.id)
    packages_no_input = fields.Char(string="Packages Words")

    @api.model
    def create(self, vals):
        vals['si_no'] = self.env['ir.sequence'].next_by_code('si')
        res = super(ShippingInstruction, self).create(vals)
        return res


    @api.multi
    def name_get(self):
        result = []
        for si in self:
            name = str(si.si_no)
        result.append((si.id, name))
        return result

    @api.multi
    def action_cancel_si(self):
        self.si_status = '04'


    def action_copy_to_booking(self):
        _logger.warning('action_copy_to_booking')
        if self.direction == 'export' and self.service_type == 'ocean':
            #_logger.warning('export and ocean')
            booking = self.env['freight.booking'].search([('id', '=', self.booking_ref.id),])
            booking_val = {
                #'direction': self.direction or False,
                'cargo_type': self.cargo_type or False,
                #'service_type': self.service_type or False,
                'booking_date_time': self.booking_date or '',
                #'customer_name': self.customer_name.id or False,
                'shipper_address_input': self.shipper,
                'consignee_address_input': self.consignee,
                'notify_party_address_input': self.notify_party,
                #'billing_address': self.customer_name.id or False,
                #'booking_ref': self.id,
                #'carrier_booking_ref': self.carrier_booking_no,
                'carrier_booking_no' : self.carrier_booking_ref or False,
                'voyage_no': self.voyage_no,
                #'vessel_name': self.vessel_name.name,
                'port_of_loading_input': self.port_of_loading_input,
                'port_of_discharge_input': self.port_of_discharge_input,
                'place_of_delivery': self.place_of_delivery,
                'freight_type': self.freight_type,
                'note': self.note,
                'shipment_booking_status': '03',
                'bol_status': self.bol_status,
                'no_of_original_bl': self.no_of_original_bl,
                'carrier': self.carrier.id,
                #Oversea Agent - todo
            }
            booking.sudo().write(booking_val)
            if self.cargo_type == 'fcl':
                #remove all existing booking fcl lines
                for booking_line in booking.operation_line_ids:
                   booking_line.sudo().unlink()
                _logger.warning('si fcl')
                container_line = self.fcl_line_ids
                #si_line_obj = self.env['freight.website.si.fcl']
                for line in container_line:
                    if line.container_product_name:
                        _logger.warning('line.container_product_name=' + line.container_product_name)
                        operation_line_obj = self.env['freight.operations.line']
                        op_line = operation_line_obj.create({
                            'operation_id': booking.id,
                            'container_product_id': line.container_product_id.id or False,
                            'container_commodity_id': line.container_commodity_id.id or False,
                            'container_product_name': line.container_product_name or '',
                            'fcl_container_qty': line.fcl_container_qty or 0,
                            'container_no': line.container_no or '',
                            'packages_no': line.packages_no or '',
                            'packages_no_uom': line.packages_no_uom.id,
                            'exp_vol': line.exp_vol or '',
                            'exp_gross_weight': line.exp_gross_weight or '',
                            'remark': line.remark or '',
                        })
                        _logger.warning('before assign')
                        booking.operation_line_ids = op_line
                        _logger.warning('after assign')
                        #booking.write({'operation_line_ids': op_line or False})
            else:
                #_logger.warning('action_copy_to_booking operation_line_ids2')
                for booking_line in booking.operation_line_ids2:
                    booking_line.sudo().unlink()
                container_line = self.lcl_line_ids
                for line in container_line:
                    if line.container_product_name:
                        operation_line_obj = self.env['freight.operations.line2']
                        op_line = operation_line_obj.create({
                            'operation_id2': booking.id,
                            'container_product_id': line.container_product_id.id or False,
                            'container_commodity_id': line.container_product_id.id or False,
                            'container_product_name': line.container_product_name or '',
                            'container_no': line.container_no or '',
                            'packages_no': line.packages_no or '',
                            'packages_no_uom': line.packages_no_uom.id,
                            'exp_vol': line.exp_vol or '',
                            'dim_length': line.dim_length or '',
                            'dim_width': line.dim_width or '',
                            'dim_height': line.dim_height or '',
                            'exp_net_weight': line.exp_net_weight or '',
                            'exp_gross_weight': line.exp_gross_weight or '',
                            'shipping_mark': line.shipping_mark or '',

                        })
                        booking.operation_line_ids2 = op_line

                        #booking.write({'operation_line_ids2': op_line or False})
            self.si_status = '03'

           # raise exceptions.ValidationError('Kindly make sure Master Data for Notify Party, Consignee, Oversea Agent, '
           #                                  'etc, are Correct!!')

    @api.multi
    def action_send_si(self):
        '''
        This function opens a window to compose an email, with the template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = \
                ir_model_data.get_object_reference('sci_goexcel_freight', 'email_template_si')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False

        ctx = {
            'default_model': 'freight.website.si',
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

    @api.multi
    def action_send_si_xlsx(self):
        return self.env.ref('sci_goexcel_freight.action_si_report_xlsx').report_action(self)


class FCLLine(models.Model):

    _name = 'freight.website.si.fcl'
    _description = 'FCL Line'

    fcl_line = fields.Many2one('freight.website.si', string='FCL Line', required=True, ondelete='cascade',
                                   index=True, copy=False)
    container_no = fields.Char(string="Container No.", track_visibility='onchange')
    container_product_id = fields.Many2one('product.product', string='Container', track_visibility='onchange')
    seal_no = fields.Char(string="Seal No.", track_visibility='onchange')
    container_product_name = fields.Text(string='Description', track_visibility='onchange')
    packages_no = fields.Integer(string="No. of Packages", track_visibility='onchange')
    packages_no_uom = fields.Many2one('uom.uom', string="UoM", track_visibility='onchange')
    exp_net_weight = fields.Float(string="Net Weight(KG)", help="Expected Weight in kg.", track_visibility='onchange')
    exp_gross_weight = fields.Float(string="Gross Weight(KG)", digits=(12, 4),
                                    help="Expected Weight in kg.", track_visibility='onchange')
    dim_length = fields.Float(string='Length', help="Length in cm", default="0.00")
    dim_width = fields.Float(string='Width', default="0.00", help="Width in cm")
    dim_height = fields.Float(string='Height', default="0.00", help="Height in cm")
    exp_vol = fields.Float(string="Measurement (M3)", digits=(12, 4),
                           help="Expected Volume in m3 Measure", track_visibility='onchange')
    remark = fields.Text(string='Marking', track_visibility='onchange')

    container_commodity_id = fields.Many2one('product.product', string='Commodity', track_visibility='onchange')
    fcl_container_qty = fields.Float(string="Qty", digits=(8, 0), track_visibility='onchange')





    @api.model
    def create(self, vals):
        #_logger.warning("in create")
        res = super(FCLLine, self).create(vals)
        content = ""
        if vals.get("container_product_id"):
            content = content + "  \u2022 Container: " + str(vals.get("container_product_id")) + "<br/>"
        if vals.get("container_product_name"):
            content = content + "  \u2022 Description: " + str(vals.get("container_product_name")) + "<br/>"
        if vals.get("container_no"):
            content = content + "  \u2022 Container No: " + str(vals.get("container_no")) + "<br/>"
        if vals.get("seal_no"):
            content = content + "  \u2022 Seal no: " + str(vals.get("seal_no")) + "<br/>"
        if vals.get("fcl_container_qty"):
            content = content + "  \u2022 Qty: " + str(vals.get("fcl_container_qty")) + "<br/>"
        if vals.get("packages_no"):
            content = content + "  \u2022 Pckg No: " + str(vals.get("packages_no")) + "<br/>"
        if vals.get("packages_no_uom"):
            content = content + "  \u2022 Pckg No UoM: " + str(vals.get("packages_no_uom")) + "<br/>"
        if vals.get("exp_net_weight"):
            content = content + "  \u2022 Net Weight: " + str(vals.get("exp_net_weight")) + "<br/>"
        if vals.get("exp_gross_weight"):
            content = content + "  \u2022 G. Weight " + str(vals.get("exp_gross_weight")) + "<br/>"
        if vals.get("exp_vol"):
            content = content + "  \u2022 Vol: " + str(vals.get("exp_vol")) + "<br/>"
        if vals.get("remark"):
            content = content + "  \u2022 Remark: " + str(vals.get("remark")) + "<br/>"
        #_logger.warning("create content:" + content)
        res.fcl_line.message_post(body=content)

        return res


    @api.multi
    def write(self, vals):
        #_logger.warning("in write")
        res = super(FCLLine, self).write(vals)
        #_logger.warning("after super write")
        content = ""
        if vals.get("container_product_id"):
            content = content + "  \u2022 Container: " + str(vals.get("container_product_id")) + "<br/>"
        if vals.get("container_product_name"):
            content = content + "  \u2022 Description: " + str(vals.get("container_product_name")) + "<br/>"
        if vals.get("container_no"):
            content = content + "  \u2022 Container No: " + str(vals.get("container_no")) + "<br/>"
        if vals.get("seal_no"):
            content = content + "  \u2022 Seal no: " + str(vals.get("seal_no")) + "<br/>"
        if vals.get("fcl_container_qty"):
            content = content + "  \u2022 Qty: " + str(vals.get("fcl_container_qty")) + "<br/>"
        if vals.get("packages_no"):
            content = content + "  \u2022 Pckg No: " + str(vals.get("packages_no")) + "<br/>"
        if vals.get("packages_no_uom"):
            content = content + "  \u2022 Pckg No UoM: " + str(vals.get("packages_no_uom")) + "<br/>"
        if vals.get("exp_net_weight"):
            content = content + "  \u2022 Net Weight: " + str(vals.get("exp_net_weight")) + "<br/>"
        if vals.get("exp_gross_weight"):
            content = content + "  \u2022 G. Weight " + str(vals.get("exp_gross_weight")) + "<br/>"
        if vals.get("exp_vol"):
            content = content + "  \u2022 Vol: " + str(vals.get("exp_vol")) + "<br/>"
        if vals.get("remark"):
            content = content + "  \u2022 Remark: " + str(vals.get("remark")) + "<br/>"
        #_logger.warning("write content:" + content)
        self.fcl_line.message_post(body=content)

        return res

    @api.multi
    def _get_default_container_category(self):
        container_lines = self.env['freight.product.category'].search([('type', '=ilike', 'container')])
        for container_line in container_lines:
            return container_line.product_category

    container_category_id = fields.Many2one('product.category', string="Container Product Id",
                                            default=_get_default_container_category)

    @api.multi
    def _get_default_commodity_category(self):
        commodity_lines = self.env['freight.product.category'].search([('type', '=ilike', 'commodity')])
        for commodity_line in commodity_lines:
            return commodity_line.product_category

    commodity_category_id = fields.Many2one('product.category', string="Commodity Product Id",
                                            default=_get_default_commodity_category)

    @api.onchange('packages_no')
    def _onchange_packages_no(self):
        si = self.env['freight.website.si'].search([('si_no', '=', self.fcl_line.si_no)])
        packages_no_input = num2words(self.packages_no, lang='en_IN').upper()
        si.write({'packages_no_input': packages_no_input})

class LCLLine(models.Model):

    _name = 'freight.website.si.lcl'
    _description = 'LCL Line'

    lcl_line = fields.Many2one('freight.website.si', string='LCL Line', required=True, ondelete='cascade',
                                    index=True, copy=False)
    #container_id = fields.Many2one('freight.containers', string="Container", track_visibility='onchange')
    # subjob_no = fields.Char(string='Sub Job', copy=False)
    container_product_id = fields.Many2one('product.product', string='Commodity', track_visibility='onchange')
    container_product_name = fields.Text(string='Description')
    container_no = fields.Char(string="Container No.")
    seal_no = fields.Char(string="Seal No.")
    packages_no = fields.Integer(string="No. of Packages", help="Eg, Carton")
    packages_no_uom = fields.Many2one('uom.uom', string="UoM", track_visibility='onchange')
    dim_length = fields.Float(string='Length', help="Length in cm", default="0.00")
    dim_width = fields.Float(string='Width', default="0.00", help="Width in cm")
    dim_height = fields.Float(string='Height', default="0.00", help="Height in cm")
    exp_gross_weight = fields.Float(string="Gross Weight(KG)", digits=(12,4),
                                    help="Expected Weight in kg.", track_visibility='onchange')
    exp_net_weight = fields.Float(string="Net Weight(KG)",
                                  help="Expected Net Weight in kg.", track_visibility='onchange')
    exp_vol = fields.Float(string="Measurement (M3)", digits=(12,4),
                           help="Expected Volume in m3 Measure", track_visibility='onchange')
    shipping_mark = fields.Char(string="Shipping Mark", track_visibility='onchange')
    remark = fields.Text(string='Remarks', track_visibility='onchange')

    @api.multi
    def _get_default_container_category(self):
        container_lines = self.env['freight.product.category'].search([('type', '=ilike', 'container')])
        for container_line in container_lines:
            return container_line.product_category

    container_category_id = fields.Many2one('product.category', string="Container Product Id",
                                            default=_get_default_container_category)

    @api.multi
    def _get_default_commodity_category(self):
        commodity_lines = self.env['freight.product.category'].search([('type', '=ilike', 'commodity')])
        for commodity_line in commodity_lines:
            return commodity_line.product_category

    commodity_category_id = fields.Many2one('product.category', string="Commodity Product Id",
                                            default=_get_default_commodity_category)

    @api.onchange('packages_no')
    def _onchange_packages_no(self):
        si = self.env['freight.website.si'].search([('si_no', '=', self.lcl_line.si_no)])
        packages_no_input = num2words(self.packages_no, lang='en_IN').upper()
        si.write({'packages_no_input': packages_no_input})

