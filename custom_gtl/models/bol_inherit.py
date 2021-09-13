from odoo import api, fields, models,exceptions
import logging
_logger = logging.getLogger(__name__)
from odoo.tools import float_round

class BillOfLading(models.Model):
    _inherit = "freight.bol"

    hbl_no = fields.Char(string='OBL No', copy=False, readonly=False)
    bl_status = fields.Selection([('original', 'Original'),
                                  ('seaway', 'Seaway'),
                                  ('telex', 'Telex')],
                                 string="BL Status", track_visibility='onchange')
    freight_type = fields.Selection([('prepaid', 'Prepaid'), ('collect', 'Collect')],
                                    string='Freight Type', track_visibility='onchange')

    sn_no = fields.Char(string='SN No', copy=False, readonly=True, index=True)
    unstuff_date = fields.Date(string='Unstuff Date')

    @api.model
    def create(self, vals):
        vals['sn_no'] = self.env['ir.sequence'].next_by_code('sn')
        res = super(BillOfLading, self).create(vals)
        return res


    def write(self, value):
        if self.direction == 'export' and self.bol_no:
            if not self.hbl_no:
                value['hbl_no'] = self.bol_no
        res = super(BillOfLading, self).write(value)
        return res


    @api.model
    def _get_default_term(self):
        comment = self.env.user.company_id.invoice_note
        return comment

    invoice_term = fields.Text('Term', default=_get_default_term)

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
                        price_after_converted = float_round(vb_line.cost_price * vb_line.cost_currency_rate, 2,
                                                            rounding_method='HALF-UP')
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
                            'freight_hbl': self.id,
                            'freight_currency': vb_line.cost_currency.id or False,
                            'freight_foreign_price': vb_line.cost_price or 0.0,
                            'freight_currency_rate': float_round(vb_line.cost_currency_rate, 6,
                                                                 rounding_method='HALF-UP') or 1.000000,
                        }])
                        vendor_bill_created.append(vb_line)
                        vb_line.billed = True
                        # print('vendor_id=' + vendor_id.name)

                vendor_bill_list = []
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
                        'freight_hbl': self.id,
                    })
                    vendor_bill_list.append(vendor_bill_id.id)
                for vb_line in filtered_vb_lines:
                    if vb_line.billed:
                        vendor_bill_ids_list = []
                        if vendor_bill_list:
                            vendor_bill_ids_list.append(vendor_bill_list[0])
                            vb_line.write({
                                # 'vendor_id_ids': [(6, 0, vendor_ids_list)],
                                'vendor_bill_ids': [(6, 0, vendor_bill_ids_list)],
                            })
                # for new_vendor_bill in vendor_bill_created:
                #     new_vendor_bill.vendor_bill_id = vendor_bill_id.id
        if vendor_count is False:
            raise exceptions.ValidationError('No Vendor in Cost & Profit!!!')

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
            'shipper_load': self.shipper_load,
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