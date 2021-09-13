from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo import exceptions
import logging
import math

_logger = logging.getLogger(__name__)


class BillOfLading(models.Model):
    _name = 'freight.bol'
    _description = 'Bill Of Lading'
    _order = 'date_of_issue desc, write_date desc'
    _rec_name = 'bol_no'

    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Header
    bol_status = fields.Selection([('01', 'Draft'), ('02', 'Original'), ('03', 'Surrender'), ('04', 'Telex Release')],
                                  string="B/L Status", default="01", copy=False, track_visibility='onchange', store=True)
    service_type = fields.Selection([('ocean', 'Ocean'), ('air', 'Air'), ('land', 'Land')], string="Shipment Mode",
                                    default="ocean", track_visibility='onchange')
    direction = fields.Selection([('import', 'Import'), ('export', 'Export')], string="Direction", default="export",
                                 track_visibility='onchange')
    cargo_type = fields.Selection([('fcl', 'FCL'), ('lcl', 'LCL')], string='Cargo Type', default="fcl",
                                  track_visibility='onchange')
    type_of_movement = fields.Selection([('cy-cy', 'CY/CY'), ('cy-cfs', 'CY/CFS'), ('cfs-cfs', 'CFS/CFS'), ('cfs-cy', 'CFS/CY')],
                                        string='Type Of Movement', track_visibility='onchange')
    booking_ref = fields.Many2one('freight.booking', string='Booking Job Ref', track_visibility='onchange',
                                  copy=False, index=True)
    no_of_original_bl = fields.Selection([('0', '0'), ('1', '1'), ('3', '3')], string="No Of original B/L",
                                         default="0", track_visibility='onchange')
    doc_form_no = fields.Char(string='Doc. Form No.', track_visibility='onchange')
    service_contract_no = fields.Char(string='Service Contract No', track_visibility='onchange')
    bol_no = fields.Char(string='HBL No', copy=False, readonly=True, index=True)
    carrier_booking_no = fields.Char(string='Carrier Booking No', copy=False, readonly=True)
    date_of_issue = fields.Date(string='Shipment Date', copy=False, default=datetime.now().date(),
                                track_visibility='onchange', index=True)
    date_laden_on_board = fields.Date(string='Shipped on Board Date')
    place_of_issue = fields.Char(string='Place of Issue', track_visibility='onchange')
    export_reference = fields.Char(string='Export Reference', track_visibility='onchange')
    fa_reference = fields.Char(string='Forwarding Agent and References', track_visibility='onchange')
    point_country_origin = fields.Text(string='Point and Country of Origin', track_visibility='onchange')
    term = fields.Char(string='Term', track_visibility='onchange', help='eg, CY-CY')
    commodity = fields.Many2one('product.product', string='Commodity', track_visibility='onchange')
    commodity1 = fields.Many2one('freight.commodity1', string='Commodity', track_visibility='onchange')
    shipper_load = fields.Boolean('Shipper Load, Seal and Count')
    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account",
                                          track_visibility='always', copy=False)


    @api.multi
    def _get_default_commodity_category(self):
        commodity_lines = self.env['freight.product.category'].search([('type', '=ilike', 'commodity')])
        for commodity_line in commodity_lines:
            _logger.warning('_get_default_commodity_category=' + str(commodity_line.product_category))
            return commodity_line.product_category

    commodity_category_id = fields.Many2one('product.category', string="Commodity Product Id",
                                            default=_get_default_commodity_category)

    # Invoice Status
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

    # Party Info
    customer_name = fields.Many2one('res.partner', string='Customer Name', track_visibility='onchange')
    contact_name = fields.Many2one('res.partner', string='Contact Name', track_visibility='onchange')
    shipper = fields.Text(string='Shipper', track_visibility='onchange',
                          help="The Party who shipped the freight, eg Exporter")
    notify_party = fields.Text(string='Notify Party',
                               help="The Party who will be notified by Liner when the freight arrived",
                               track_visibility='onchange')
    carrier_c = fields.Many2one('res.partner', string="Carrier")
    consignee = fields.Text(string='Consignee', help="The Party who received the freight", track_visibility='onchange')
    routing_instruction = fields.Text(string='For Delivery Of Goods Please Apply To', track_visibility='onchange')
    delivery_contact = fields.Text(string='Contact for Delivery', help="Contact information for delivery of goods",
                                   track_visibility='onchange')
    unstuff_at = fields.Char(string='Unstuff At', track_visibility='onchange')

    # Shipment Info
    voyage_no = fields.Char(string='Voyage No', track_visibility='onchange')
    vessel = fields.Char(string='Vessel Name', track_visibility='onchange')
    manifest_no = fields.Char(string='Manifest No', track_visibility='onchange')

    port_of_loading_input = fields.Char(string='Port of Loading', track_visibility='onchange')
    port_of_discharge_input = fields.Char(string='Port of Discharge', track_visibility='onchange')
    port_of_discharge_eta = fields.Date(string='Loading ETA', track_visibility='onchange')
    place_of_delivery = fields.Char(string='Final Destination', track_visibility='onchange')
    place_of_receipt = fields.Char(string='Place of Receipt', track_visibility='onchange')
    pre_carriage_by = fields.Char(string='Pre-Carriage By', track_visibility='onchange')

    # Remark
    note = fields.Text(string='Remarks', track_visibility='onchange')

    # System Info
    sales_person = fields.Many2one('res.users', string="Salesperson", track_visibility='onchange')
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, readonly=1,
                                 default=lambda self: self.env.user.company_id.id)
    # analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account",
    #                                       track_visibility='always', copy=False)

    # Line Item
    cargo_line_ids = fields.One2many('freight.bol.cargo', 'cargo_line', string="Cargo Line",
                                     copy=True, auto_join=True, track_visibility='always')
    charge_line_ids = fields.One2many('freight.bol.charge', 'charge_line', string="Charge Line",
                                      copy=True, auto_join=True, track_visibility='always')
    cost_profit_ids = fields.One2many('freight.bol.cost.profit', 'bol_id', string="Cost & Profit",
                                      copy=True, auto_join=True, track_visibility='always')

    # Not Used
    invoice_count = fields.Integer(string='Invoice Count', compute='_get_invoiced_count', copy=False)
    vendor_bill_count = fields.Integer(string='Vendor Bill Count', compute='_get_bill_count', copy=False)

    si_count = fields.Integer(string='SI Count', compute='_get_si_count', copy=False)

    shipper_c = fields.Many2one('res.partner', string='Shipper')
    consignee_c = fields.Many2one('res.partner', string='Consignee Name')
    notify_party_c = fields.Many2one('res.partner', string='Notify Party')

    total_no_of_packages_words = fields.Char(string='Total Packages', track_visibility='onchange',
                                             help='Total no of packages or container in Words')
    lines_description = fields.Integer()
    line_description1 = fields.Text()
    line_description2 = fields.Text()

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

    @api.multi
    def action_send_bl(self):
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = \
                ir_model_data.get_object_reference('sci_goexcel_freight', 'email_template_bol')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False

        ctx = {
            'default_model': 'freight.bol',
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

            'context': dict(bl_id=self.id),
        }

    @api.multi
    def action_create_vendor_bill(self):
        # only lines with vendor
        vendor_po = self.cost_profit_ids.filtered(lambda c: c.vendor_id)
        po_lines = vendor_po.sorted(key=lambda p: p.vendor_id.id)
        vendor_count = False
        vendor_id = False
        if not self.analytic_account_id:
            values = {
                'name': '%s' % self.booking_ref.booking_no,
                'partner_id': self.booking_ref.customer_name.id,
                'code': self.bol_no,
                'company_id': self.booking_ref.company_id.id,
            }

            analytic_account = self.env['account.analytic.account'].sudo().create(values)
            self.booking_ref.write({'analytic_account_id': analytic_account.id})
            self.write({'analytic_account_id': analytic_account.id})
        for line in po_lines:
            if line.vendor_id != vendor_id:
                vb = self.env['account.invoice']
                vendor_count = True
                vendor_id = line.vendor_id
                value = []
                vendor_bill_created = []
                filtered_vb_lines = po_lines.filtered(lambda r: r.vendor_id == vendor_id)
                for vb_line in filtered_vb_lines:
                    if not vb_line.billed:
                        account_id = False
                        price_after_converted = vb_line.cost_price * vb_line.cost_currency_rate
                        if vb_line.product_id.property_account_expense_id:
                            account_id = vb_line.product_id.property_account_expense_id
                        elif vb_line.product_id.categ_id.property_account_expense_categ_id:
                            account_id = vb_line.product_id.categ_id.property_account_expense_categ_id
                        value.append([0, 0, {
                            # 'invoice_id': vendor_bill.id or False,
                            'account_id': account_id.id or False,
                            'name': vb_line.product_id.name or '',
                            'product_id': vb_line.product_id.id or False,
                            'quantity': vb_line.cost_qty or 0.0,
                            'uom_id': vb_line.uom_id.id or False,
                            'price_unit': price_after_converted or 0.0,
                            'account_analytic_id': self.analytic_account_id.id,
                            'bl_line_id': vb_line.id,
                        }])
                        vendor_bill_created.append(vb_line)
                        vb_line.billed = True
                        # print('vendor_id=' + vendor_id.name)
                if value:
                    vendor_bill_id = vb.create({
                        'type': 'in_invoice',
                        'invoice_line_ids': value,
                        'default_currency_id': self.env.user.company_id.currency_id.id,
                        'company_id': self.company_id.id,
                        'date_invoice': fields.Date.context_today(self),
                        'origin': self.bol_no,
                        'partner_id': vendor_id.id,
                        'account_id': vb_line.vendor_id.property_account_payable_id.id or False,
                        'freight_booking': self.booking_ref.id,
                    })
                for new_vendor_bill in vendor_bill_created:
                    new_vendor_bill.vendor_bill_id = vendor_bill_id.id
        if vendor_count is False:
            raise exceptions.ValidationError('No Vendor in Cost & Profit!!!')

    def action_copy_to_booking(self):
        booking = self.env['freight.booking'].search([('id', '=', self.booking_ref.id),])
        booking_val = {
            'cargo_type': self.cargo_type or False,
            'shipper_address_input': self.shipper,
            'consignee_address_input': self.consignee,
            'notify_party_address_input': self.notify_party,
            'carrier_booking_no' : self.carrier_booking_no or False,
            'voyage_no': self.voyage_no,
            'port_of_loading_input': self.port_of_loading_input,
            'port_of_discharge_input': self.port_of_discharge_input,
            'place_of_delivery': self.place_of_delivery,
            'note': self.note,
            'bol_status': self.bol_status,
            'no_of_original_bl': self.no_of_original_bl,
            'carrier': self.carrier_c.id,
        }
        booking.sudo().write(booking_val)
        for booking_line in booking.operation_line_ids:
            booking_line.sudo().unlink()
        for booking_line in booking.operation_line_ids2:
            booking_line.sudo().unlink()

        for line in self.cargo_line_ids:
            if self.cargo_type == 'fcl':
                if line.container_product_name:
                    operation_line_obj = self.env['freight.operations.line']
                    op_line = operation_line_obj.create({
                        'operation_id': booking.id,
                        'container_no': line.container_no or '',
                        'container_product_id': line.container_product_id.id or False,
                        'seal_no': line.seal_no or '',
                        'container_product_name': line.container_product_name or '',
                        'packages_no': line.packages_no_value or '',
                        'packages_no_uom': line.packages_no_uom.id,
                        'exp_net_weight': line.exp_net_weight or '',
                        'exp_gross_weight': line.exp_gross_weight or '',
                        'dim_length': line.dim_length or '',
                        'dim_width': line.dim_width or '',
                        'dim_height': line.dim_height or '',
                        'exp_vol': line.exp_vol or '',
                        'remark': line.marks or '',
                    })
                    booking.operation_line_ids = op_line
            else:
                if line.container_product_name:
                    operation_line_obj = self.env['freight.operations.line2']
                    op_line = operation_line_obj.create({
                        'operation_id2': booking.id,
                        'container_no': line.container_no or '',
                        'container_product_id': line.container_product_id.id or False,
                        'seal_no': line.seal_no or '',
                        'container_product_name': line.container_product_name or '',
                        'packages_no': line.packages_no_value or '',
                        'packages_no_uom': line.packages_no_uom.id,
                        'exp_net_weight': line.exp_net_weight or '',
                        'exp_gross_weight': line.exp_gross_weight or '',
                        'dim_length': line.dim_length or '',
                        'dim_width': line.dim_width or '',
                        'dim_height': line.dim_height or '',
                        'exp_vol': line.exp_vol or '',
                        'shipping_mark': line.marks or '',
                    })
                    booking.operation_line_ids2 = op_line

    def action_copy_from_booking(self):
        booking = self.env['freight.booking'].search([('id', '=', self.booking_ref.id)])
        for line in booking.cost_profit_ids:
            operation_line_obj = self.env['freight.bol.cost.profit']
            op_line = operation_line_obj.create({
                'bol_id': self.id,
                'product_id': line.product_id.id or False,
                'product_name': line.product_name or '',
                'profit_qty': line.profit_qty or 0,
                'list_price': line.list_price or 0,
                'profit_amount': line.profit_amount or 0,
                'profit_currency': line.profit_currency.id or False,
                'profit_currency_rate': line.profit_currency_rate or 0,
                'cost_qty': line.cost_qty or 0,
                'cost_price': line.cost_price or 0,
                'cost_amount': line.cost_amount or 0,
                'vendor_id': line.vendor_id.id or False,
                'cost_currency': line.cost_currency.id or False,
                'cost_currency_rate': line.cost_currency_rate or 0,
            })

    def action_create_si(self):
        si_obj = self.env['freight.website.si']
        si_val = {
            'si_status': '01',
            'carrier': self.carrier_c.id or False,
            'direction': self.direction or False,
            'cargo_type': self.cargo_type or False,
            'service_type': self.service_type or False,
            'customer_name': self.customer_name.id or False,
            'shipper': self.shipper,
            'consignee': self.consignee,
            'notify_party': self.notify_party,
            'carrier_booking_ref': self.carrier_booking_no,
            'voyage_no': self.voyage_no,
            'port_of_loading_input': self.port_of_loading_input,
            'port_of_discharge_input': self.port_of_discharge_input,
            'place_of_delivery': self.place_of_delivery,
            'bl_ref': self.id,
        }
        si = si_obj.create(si_val)
        if self.cargo_type == 'fcl':
            container_line = self.cargo_line_ids
            si_line_obj = self.env['freight.website.si.fcl']
            for line in container_line:
                if line.container_product_id or line.container_no:
                    si_line = si_line_obj.create({
                        'container_product_id': line.container_product_id.id or False,
                        'container_product_name': line.container_product_name or False,
                        'fcl_line': si.id or '',
                        'container_no': line.container_no or '',
                        'packages_no': line.packages_no_value or 0.0,
                        'packages_no_uom': line.packages_no_uom.id,
                        'exp_gross_weight': line.exp_gross_weight or 0.0,
                        'exp_vol': line.exp_vol or 0.0,
                    })
                    si.write({'fcl_line_ids': si_line or False})
        else:
            container_line = self.cargo_line_ids
            si_line_obj = self.env['freight.website.si.lcl']
            for line in container_line:
                if line.container_product_id or line.container_no:
                    si_line = si_line_obj.create({
                        'container_product_name': line.container_product_name or False,
                        #'container_product_id': line.container_commodity_id.id or False,
                        'lcl_line': si.id or '',
                        'container_no': line.container_no or '',
                        'packages_no': line.packages_no_value or 0.0,
                        'packages_no_uom': line.packages_no_uom.id,
                        'exp_gross_weight': line.exp_gross_weight or 0.0,
                        'exp_net_weight': line.exp_net_weight or 0.0,
                        'exp_vol': line.exp_vol or 0.0,
                        # 'remark_line': line.remark or '',
                    })
                    si.write({'lcl_line_ids': si_line or False})

    @api.multi
    def operation_invoices(self):
        """Show Invoice for specific Freight Operation smart Button."""
        for operation in self:
            invoices = self.env['account.invoice'].search([
                ('freight_hbl', '=', operation.id),
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
            # Get from the vendor bill list
            vendor_bill_list = []
            for cost_profit_line in operation.cost_profit_ids:
                for vendor_bill_line in cost_profit_line.vendor_bill_ids:
                    if vendor_bill_line.type in ['in_invoice', 'in_refund']:
                        vendor_bill_list.append(vendor_bill_line.id)

            invoices = self.env['account.invoice'].search([
                ('freight_hbl', '=', operation.id),
                ('type', 'in', ['in_invoice', 'in_refund']),
                ('state', '!=', 'cancel'),
            ])
            invoice_name_list = []
            for x in invoices:
                invoice_name_list.append(x.id)

            unique_list = []
            for y in vendor_bill_list:
                if invoice_name_list and len(invoice_name_list) > 0:
                    if y not in invoice_name_list:
                        unique_list.append(y)
                else:
                    unique_list.append(y)
            for z in invoice_name_list:
                # if z not in vendor_bill_list:
                unique_list.append(z)

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

    @api.multi
    def operation_si(self):
        for operation in self:
            si = self.env['freight.website.si'].search([('bl_ref', '=', operation.id), ])
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

    def _get_invoiced_count(self):
        for operation in self:
            invoices = self.env['account.invoice'].search([
                ('freight_hbl', '=', operation.id),
                ('type', 'in', ['out_invoice','out_refund']),
                ('state', '!=', 'cancel'),
            ])

        self.update({
            'invoice_count': len(invoices),
            #'invoice_ids': invoices,
        })

    def _get_bill_count(self):
        # vendor bill is created from booking job, vendor bill header will have the booking job id
        for operation in self:
            # Get from the vendor bill list
            vendor_bill_list = []
            # vendor_bill_list_temp = []
            for cost_profit_line in operation.cost_profit_ids:
                for vendor_bill_line in cost_profit_line.vendor_bill_ids:
                    if vendor_bill_line.type in ['in_invoice', 'in_refund']:
                        vendor_bill_list.append(vendor_bill_line.id)
                        # vendor_bill_list_temp.append(vendor_bill_line.id)
            # print('vendor_bill_list: ',  len(vendor_bill_list))
            # remove the duplicates in the vendor bill list
            unique_vendor_bill_list = []
            for i in vendor_bill_list:
                if i not in unique_vendor_bill_list:
                    unique_vendor_bill_list.append(i)
            # print('unique_vendor_bill_list: ', len(unique_vendor_bill_list))
            # Get the vendor list (Create the vendor from the job)
            invoices = self.env['account.invoice'].search([
                ('freight_hbl', '=', operation.id),
                ('type', 'in', ['in_invoice', 'in_refund']),
                ('state', '!=', 'cancel'),
            ])
            # print('vendor bills:', len(invoices))
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
                # if z not in vendor_bill_list:
                unique_list.append(z)
            if len(unique_list) > 0:
                self.update({
                    'vendor_bill_count': len(unique_list),
                })

    def _get_si_count(self):
        for operation in self:
            si = self.env['freight.website.si'].search([
                ('bl_ref', '=', operation.id),
            ])

        self.update({
            'si_count': len(si),
        })

    # TS - add for Purchase Receipt
    purchase_receipt_count = fields.Integer(string='Purchase Receipt Count', compute='_get_pr_count', copy=False)

    def _get_pr_count(self):
        # get purchase receipt (Account Voucher) on the lines
        for operation in self:
            # Get PR list
            pr_lines = self.env['account.voucher.line'].search([
                ('freight_hbl', '=', operation.id),
            ])
            pr_list = []
            for pr_line in pr_lines:
                if pr_line.voucher_id.state != 'cancel' and pr_line.voucher_id.voucher_type == 'purchase':
                    pr_list.append(pr_line.voucher_id.id)
            # pr_name_list = []
            # for x in pr_list:
            #     pr_name_list.append(x.id)
            unique_list = []
            for i in pr_list:
                if i not in unique_list:
                    unique_list.append(i)

            if len(unique_list) > 0:
                self.update({
                    'purchase_receipt_count': len(unique_list),
                })

    @api.multi
    def operation_pr(self):
        for operation in self:
            for operation in self:
                # Get PR list
                pr_lines = self.env['account.voucher.line'].search([
                    ('freight_hbl', '=', operation.id),
                ])
                pr_list = []
                for pr_line in pr_lines:
                    if pr_line.voucher_id.state != 'cancel' and pr_line.voucher_id.voucher_type == 'purchase':
                        pr_list.append(pr_line.voucher_id.id)
                # pr_name_list = []
                # for x in pr_list:
                #     pr_name_list.append(x.id)
                unique_list = []
                for i in pr_list:
                    if i not in unique_list:
                        unique_list.append(i)

        if len(unique_list) > 1:
            views = [(self.env.ref('account_voucher.view_voucher_tree').id, 'tree'),
                     (self.env.ref('account_voucher.view_purchase_receipt_form').id, 'form')]
            return {
                'name': 'Purchase Receipt',
                'view_type': 'form',
                'view_mode': 'tree,form',
                # 'view_id': self.env.ref('account.invoice_supplier_tree').id,
                'view_id': False,
                'res_model': 'account.voucher',
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
                'res_model': 'account.voucher',
                'res_id': unique_list[0] or False,  # readonly mode
                #  'domain': [('id', 'in', purchase_order.ids)],
                'type': 'ir.actions.act_window',
                'target': 'popup',  # readonly mode
            }


class CargoLine(models.Model):
    _name = 'freight.bol.cargo'
    _description = 'Cargo Line'

    cargo_line = fields.Many2one('freight.bol', string='Cargo Line', required=True, ondelete='cascade',
                                 index=True, copy=False)
    sequence = fields.Integer(string="sequence")
    marks = fields.Text(string='Marks and Numbers')
    container_no = fields.Char(string="Container No.")
    container_product_id = fields.Many2one('product.product', string='Container', track_visibility='onchange')
    seal_no = fields.Char(string="Seal No.")
    container_product_name = fields.Text(string='Description of Goods')
    packages_no_value = fields.Integer(string="No. of Packages")
    packages_no_uom = fields.Many2one('uom.uom', string="UoM")
    exp_net_weight = fields.Float(string="Net Weight(KG)", help="Expected Weight in kg.", track_visibility='onchange')
    exp_gross_weight = fields.Float(string="Gross Weight(KG)", digits=(12, 4), help="Expected Weight in kg.")

    dim_length = fields.Float(string='Length', help="Length in cm", default="0.00", track_visibility='onchange')
    dim_width = fields.Float(string='Width', default="0.00", help="Width in cm", track_visibility='onchange')
    dim_height = fields.Float(string='Height', default="0.00", help="Height in cm", track_visibility='onchange')
    exp_vol = fields.Float(string="Measurement (M3)", digits=(12, 4),
                           help="Expected Volume in m3 Measure")
    packages_no = fields.Char(string="No. of Packages")

    @api.multi
    def _get_default_container_category(self):
        container_lines = self.env['freight.product.category'].search([('type', '=ilike', 'container')])
        for container_line in container_lines:
            # _logger.warning('_get_default_container_category=' + str(container_line.product_category))
            return container_line.product_category

    container_category_id = fields.Many2one('product.category', string="Container Product Id",
                                            default=_get_default_container_category)


    @api.onchange('container_product_name')
    def _onchange_description(self):
        bl = self.env['freight.bol'].search([('bol_no', '=', self.cargo_line.bol_no)])
        if self.container_product_name:
            lines_description = self.container_product_name.count('\n')/20
            lines_description = math.ceil(lines_description)
            x = self.container_product_name.split('\n')
            count = 0
            line_description1 = ''
            line_description2 = ''
            for line in x:
                if count < 20:
                    line_description1 = line_description1 + line + '\n'
                    count = count + 1
                else:
                    line_description2 = line_description2 + line + '\n'
                    count = count + 1
            bl.write({'lines_description': lines_description,
                      'line_description1': line_description1,
                      'line_description2': line_description2,
                      })

    @api.model
    def create(self, vals):
        # _logger.warning("in create")
        res = super(CargoLine, self).create(vals)
        content = ""
        if vals.get("marks"):
            content = content + "  \u2022 Marks and Numbers: " + str(vals.get("marks")) + "<br/>"
        if vals.get("container_product_name"):
            content = content + "  \u2022 Description of Goods: " + str(vals.get("container_product_name")) + "<br/>"
        if vals.get("packages_no"):
            content = content + "  \u2022 No. of Packages: " + str(vals.get("packages_no")) + "<br/>"
        if vals.get("seal_no"):
            content = content + "  \u2022 Seal no: " + str(vals.get("seal_no")) + "<br/>"
        if vals.get("container_no"):
            content = content + "  \u2022 Container No.: " + str(vals.get("container_no")) + "<br/>"
        if vals.get("exp_gross_weight"):
            content = content + "  \u2022 Gross Weight(KG): " + str(vals.get("exp_gross_weight")) + "<br/>"
        if vals.get("exp_vol"):
            content = content + "  \u2022 Measurement (M3): " + str(vals.get("exp_vol")) + "<br/>"
        res.cargo_line.message_post(body=content)

        return res

    @api.multi
    def write(self, vals):
        # _logger.warning("in write")
        res = super(CargoLine, self).write(vals)
        # _logger.warning("after super write")
        content = ""
        if vals.get("marks"):
            content = content + "  \u2022 Marks and Numbers: " + str(vals.get("marks")) + "<br/>"
        if vals.get("container_product_name"):
            content = content + "  \u2022 Description of Goods: " + str(vals.get("container_product_name")) + "<br/>"
        if vals.get("packages_no"):
            content = content + "  \u2022 No. of Packages: " + str(vals.get("packages_no")) + "<br/>"
        if vals.get("seal_no"):
            content = content + "  \u2022 Seal no: " + str(vals.get("seal_no")) + "<br/>"
        if vals.get("container_no"):
            content = content + "  \u2022 Container No.: " + str(vals.get("container_no")) + "<br/>"
        if vals.get("exp_gross_weight"):
            content = content + "  \u2022 Gross Weight(KG): " + str(vals.get("exp_gross_weight")) + "<br/>"
        if vals.get("exp_vol"):
            content = content + "  \u2022 Measurement (M3): " + str(vals.get("exp_vol")) + "<br/>"
        self.cargo_line.message_post(body=content)

        return res


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
    # fcl_container_qty = fields.Float(string="Qty", digits=(8, 0), track_visibility='onchange')

    revenue_tons = fields.Char(string='Revenue Tons')

    @api.model
    def create(self, vals):
        # _logger.warning("in create")
        res = super(ChargeLine, self).create(vals)
        content = ""
        if vals.get("freight_charges"):
            content = content + "  \u2022 Freight & Charges: " + str(vals.get("freight_charges")) + "<br/>"
        if vals.get("revenue_tons"):
            content = content + "  \u2022 Revenue Tons: " + str(vals.get("revenue_tons")) + "<br/>"
        if vals.get("rate"):
            content = content + "  \u2022 Rate: " + str(vals.get("rate")) + "<br/>"
        if vals.get("per"):
            content = content + "  \u2022 Per: " + str(vals.get("per")) + "<br/>"
        if vals.get("amount"):
            content = content + "  \u2022 Amount: " + str(vals.get("amount")) + "<br/>"
        if vals.get("prepaid"):
            content = content + "  \u2022 Prepaid: " + str(vals.get("prepaid")) + "<br/>"
        if vals.get("collect"):
            content = content + "  \u2022 Collect: " + str(vals.get("collect")) + "<br/>"
        if vals.get("payable_at_by"):
            content = content + "  \u2022 Payable at/by: " + str(vals.get("payable_at_by")) + "<br/>"
        res.charge_line.message_post(body=content)

        return res

    @api.multi
    def write(self, vals):
        # _logger.warning("in write")
        res = super(ChargeLine, self).write(vals)
        # _logger.warning("after super write")
        content = ""
        if vals.get("freight_charges"):
            content = content + "  \u2022 Freight & Charges: " + str(vals.get("freight_charges")) + "<br/>"
        if vals.get("revenue_tons"):
            content = content + "  \u2022 Revenue Tons: " + str(vals.get("revenue_tons")) + "<br/>"
        if vals.get("rate"):
            content = content + "  \u2022 Rate: " + str(vals.get("rate")) + "<br/>"
        if vals.get("per"):
            content = content + "  \u2022 Per: " + str(vals.get("per")) + "<br/>"
        if vals.get("amount"):
            content = content + "  \u2022 Amount: " + str(vals.get("amount")) + "<br/>"
        if vals.get("prepaid"):
            content = content + "  \u2022 Prepaid: " + str(vals.get("prepaid")) + "<br/>"
        if vals.get("collect"):
            content = content + "  \u2022 Collect: " + str(vals.get("collect")) + "<br/>"
        if vals.get("payable_at_by"):
            content = content + "  \u2022 Payable at/by: " + str(vals.get("payable_at_by")) + "<br/>"
        self.charge_line.message_post(body=content)

        return res


class CostProfit(models.Model):
    _name = 'freight.bol.cost.profit'
    _description = "BOL Cost & Profit"

    sequence = fields.Integer(string="sequence")
    bol_id = fields.Many2one('freight.bol', string='BOL ID', required=True, ondelete='cascade',
                                 index=True, copy=False)
    product_id = fields.Many2one('product.product', string="Product")
    product_name = fields.Text(string="Description")

    #Profit
    #profit_qty = fields.Integer(string='Qty', default="1")
    #profit_qty = fields.Float(string='Qty', default="1", digits=(12, 2))
    list_price = fields.Float(string="Unit Price")
    uom_id = fields.Many2one('uom.uom', string="UoM")
    profit_gst = fields.Selection([('zer', 'ZER')], string="GST", default="zer", track_visibility='onchange')
    tax_id = fields.Many2many('account.tax', string='Taxes', domain=['|', ('active', '=', False), ('active', '=', True)])
    profit_currency = fields.Many2one('res.currency', 'Currency',
                    default=lambda self: self.env.user.company_id.currency_id.id, track_visibility='onchange')
    profit_currency_rate = fields.Float(string='Rate', default="1.00", track_visibility='onchange')
    profit_amount = fields.Float(string="Amt", compute="_compute_profit_amount", store=True, track_visibility='onchange')
    sale_total = fields.Float(string="Total Sales", compute="_compute_sale_total", store=True, track_visibility='onchange')

    #Cost
    #cost_qty = fields.Integer(string='Qty', default="1", track_visibility='onchange')
    profit_qty = fields.Float(string='Qty', default="1.000", digit=(12, 3))
    cost_qty = fields.Float(string='Qty', default="1.000", digit=(12, 3))
    cost_price = fields.Float(string="Unit Price", track_visibility='onchange')
    cost_gst = fields.Selection([('zer', 'ZER')], string="Tax", default="zer", track_visibility='onchange')
    vendor_id = fields.Many2one('res.partner', string="Vendor", track_visibility='onchange')
    vendor_bill_id = fields.Many2one('account.invoice', string="Vendor Bill")
    cost_currency = fields.Many2one('res.currency', string="Curr", required=True,
                    default=lambda self: self.env.user.company_id.currency_id.id, track_visibility='onchange')
    cost_currency_rate = fields.Float(string='Rate', default="1.00", track_visibility='onchange')
    cost_amount = fields.Float(string="Amt",
                               compute="_compute_cost_amount", store=True, track_visibility='onchange')
    cost_total = fields.Float(string="Total Cost",
                              compute="_compute_cost_total", store=True, track_visibility='onchange')

    # Invoice & Bill
    billed = fields.Boolean(string='Billed', copy=False)
    is_billed = fields.Char('Is Biiled?', compute='_compute_is_billed', store=True)

    added_to_invoice = fields.Boolean(string='Invoiced', copy=False)
    invoice_paid = fields.Boolean(string='Invoice Paid', copy=False)

    paid = fields.Boolean(string='Paid', copy=False)
    is_paid = fields.Char('Is Paid?', compute='_compute_is_paid', store=True)

    invoice_id = fields.Many2one('account.invoice', string="Invoice")
    inv_line_id = fields.Many2one('account.invoice.line', string="Invoice Line")

    bill_id = fields.Many2one('account.invoice', string="Bill")
    bill_line_id = fields.Many2one('account.invoice.line', string="Bill Line")

    route_service = fields.Boolean(string='Is Route Service', default=False)

    profit_total = fields.Float(string="Total Profit", compute="_compute_profit_total", store=True)
    margin_total = fields.Float(string="Margin %", compute="_compute_margin_total", digits=(8,2), store=True, group_operator="avg")
    vendor_id_ids = fields.Many2many('res.partner', string="Vendor List", copy=False)
    vendor_bill_ids = fields.Many2many('account.invoice', string="Vendor Bill List", copy=False)


    @api.one
    def _set_access_for_invoiced(self):
        if self.env['res.users'].has_group('account.group_account_manager'):
            self.invoiced_readonly = False
        else:
            self.invoiced_readonly = True

    invoiced_readonly = fields.Boolean(compute="_set_access_for_invoiced",
                                       string='Is user able to modify invoiced?')


    @api.depends('profit_qty', 'list_price')
    def _compute_profit_amount(self):
        for service in self:
            if service.product_id:
                service.profit_amount = service.profit_qty * service.list_price or 0.0

    @api.depends('cost_qty', 'cost_price')
    def _compute_cost_amount(self):
        for service in self:
            if service.product_id:
                service.cost_amount = service.cost_qty * service.cost_price or 0.0

    @api.depends('profit_amount', 'profit_currency_rate')
    def _compute_sale_total(self):
        for service in self:
            if service.product_id:
                service.sale_total = service.profit_amount * service.profit_currency_rate or 0.0

    @api.onchange('profit_currency_rate')
    def _onchange_profit_currency_rate(self):
        for service in self:
            if service.product_id:
                service.sale_total = service.profit_amount * service.profit_currency_rate or 0.0

    @api.onchange('profit_amount')
    def _onchange_profit_amount(self):
        for service in self:
            if service.product_id:
                service.sale_total = service.profit_amount * service.profit_currency_rate or 0.0
                service.profit_total = service.sale_total - service.cost_total or 0.0

    @api.depends('cost_amount', 'cost_currency_rate')
    def _compute_cost_total(self):
        for service in self:
            if service.product_id:
                service.cost_total = service.cost_amount * service.cost_currency_rate or 0.0
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
                    service.margin_total = service.profit_total / service.sale_total * 100

    @api.onchange('cost_amount')
    def _onchange_cost_amount(self):
        for service in self:
            if service.product_id:
                service.cost_total = service.cost_amount * service.cost_currency_rate or 0.0
                service.profit_total = service.sale_total - service.cost_total or 0.0

    @api.onchange('cost_currency_rate')
    def _onchange_cost_currency_rate(self):
        for service in self:
            if service.product_id:
                service.cost_total = service.cost_amount * service.cost_currency_rate or 0.0
                service.profit_total = service.sale_total - service.cost_total or 0.0

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
            if not self.billed:
                self.billed = False
                print('Invoiced False')


    @api.multi
    @api.depends('billed')
    def _compute_is_billed(self):
        for cost_profit_line in self:
            if cost_profit_line.vendor_id:
                if cost_profit_line.billed:
                    cost_profit_line.is_billed = 'Y'
                elif not cost_profit_line.billed:
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
