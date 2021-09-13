from odoo import api, fields, models,exceptions
import logging
_logger = logging.getLogger(__name__)


class SaleQuotation(models.Model):
    _inherit = "sale.order"

    sq_rft_count = fields.Integer(compute='_compute_sq_rft_count')
    #sq_description = fields.Char(string='SQ Description', track_visibility='onchange')


    @api.multi
    def _compute_sq_rft_count(self):
        for sq in self:
            rfts = self.env['transport.rft'].search([
                ('sq_reference', '=', sq.id),
            ])
            sq.sq_rft_count = len(rfts)


    @api.multi
    def action_copy_to_rft(self):
        rft_obj = self.env['transport.rft']
        cost_profit_obj = self.env['rft.cost.profit']
        #_logger.warning('action_copy_to_booking 1')
        rft_val = {
            'rft_status': '01',
            'shipper': self.partner_id.id or False,
            'billing_address': self.partner_id.id or False,
            'sq_reference': self.id,
            'company_id': self.company_id.id,
            'sales_person': self.user_id.id
        }
        rft = rft_obj.create(rft_val)
        for line in self.order_line:
            #_logger.warning('action_copy_to_booking 1')
            if line.product_id:
                #_logger.warning('action_copy_to_booking 2')
                price_unit = line.price_unit
                cost_profit_line = cost_profit_obj.create({
                    'product_id': line.product_id.id or False,
                    'product_name': line.name or False,
                    'rft_transport_id': rft.id or '',
                    'sales_qty': line.product_uom_qty or 0,
                    'sales_currency': line.freight_currency.id,
                    'sales_currency_rate': line.freight_currency_rate or 1.0,
                    'unit_price': price_unit or 0.0,
                   # 'sale_total': line.price_unit or 0.0,

                })
                # booking.write({'booking_id': booking.id or False,
                #             'cost_profit_ids': cost_profit_line.id or False})
                rft.write({'cost_profit_ids_rft': cost_profit_line or False})



