from odoo import api, fields, models,exceptions
import logging
_logger = logging.getLogger(__name__)


class SaleQuotation(models.Model):
    _inherit = "sale.order"

    service_type = fields.Selection([('ocean', 'Ocean'), ('air', 'Air'), ('land', 'Land'), ('others', 'Others')], string="Shipment Mode",
                                    default="ocean", track_visibility='onchange')
    sq_type = fields.Selection([('freight', 'Freight'), ('warehouse', 'Warehouse')], default="freight",string="SQ Type")

    instruction = fields.Text('Instruction')

    @api.onchange('sq_type')
    def onchange_sq_type(self):
        #print('onchange_sq_type')
        if self.sq_type:
            sale_term = self.env['sale.letter.template'].search([('sq_type', '=', self.sq_type)], limit=1)
            #print(sale_term)
            self.sale_term = sale_term.template

    @api.multi
    def action_copy_to_booking(self):
        booking_obj = self.env['freight.booking']
        cost_profit_obj = self.env['freight.cost_profit']
        # fcl_operation_obj = self.env['freight.operations.line']
        # _logger.warning('action_copy_to_booking 1')
        freight_booking_val = {
            'shipment_booking_status': '01',
            'customer_name': self.partner_id.id or False,
            'billing_address': self.partner_id.id or False,
            'sq_reference': self.id,
            'company_id': self.company_id.id,
            'sales_person': self.user_id.id,
            'incoterm': self.incoterm.id or False,
            'direction': self.mode or False,
            'port_of_loading': self.POL.id or False,
            'port_of_discharge': self.POD.id or False,
            'commodity': self.commodity.id or False,
            'payment_term': self.payment_term_id.id or False,
            'cargo_type': self.type or False,
            'carrier_booking_no': self.carrier_booking_no,
            'contact_name': self.contact_name.id or False,
            'shipper': self.shipper.id or False,
            'forwarding_agent_code': self.forwarding_agent_code.id or False,
            'consignee': self.consignee.id or False,
            'hs_code': self.hs_code.id or False,
            'coo': self.coo,
            'fumigation': self.fumigation,
            'insurance': self.insurance,
            'cpc': self.cpc,
            'warehouse_hours': self.warehouse_hours.id or False,
            'service_type': self.service_type,
            'airport_departure': self.airport_departure.id or False,
            'airport_destination': self.airport_destination.id or False,
            'instruction': self.instruction or False,
        }
        if self.mode == 'import':
            freight_booking_val = {
                'shipment_booking_status': '01',
                'customer_name': self.partner_id.id or False,
                'billing_address': self.partner_id.id or False,
                'sq_reference': self.id,
                'company_id': self.company_id.id,
                'sales_person': self.user_id.id,
                'incoterm': self.incoterm.id or False,
                'direction': self.mode or False,
                'port_of_loading': self.POL.id or False,
                'port_of_discharge': self.POD.id or False,
                'commodity': self.commodity.id or False,
                'payment_term': self.payment_term_id.id or False,
                'cargo_type': self.type or False,
                'carrier_booking_no': self.carrier_booking_no,
                'contact_name': self.contact_name.id or False,
                'shipper': self.shipper.id or False,
                'forwarding_agent_code': self.forwarding_agent_code.id or False,
                'hs_code': self.hs_code.id or False,
                'coo': self.coo,
                'fumigation': self.fumigation,
                'insurance': self.insurance,
                'cpc': self.cpc,
                'warehouse_hours': self.warehouse_hours.id or False,
                'consignee': self.partner_id.id or False,
                'notify_party': self.partner_id.id or False,
                'service_type': self.service_type,
                'airport_departure': self.airport_departure.id or False,
                'airport_destination': self.airport_destination.id or False,
                'instruction': self.instruction or False,
            }

        booking = booking_obj.create(freight_booking_val)
        if booking.service_type == 'air':
            booking.cargo_type = 'lcl'
            booking.land_cargo_type = 'ltl'
        for line in self.order_line:
            # _logger.warning('action_copy_to_booking 1')
            if line.product_id:
                # _logger.warning('action_copy_to_booking 2')

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
                    # 'sale_total': line.price_unit or 0.0,

                })
                # booking.write({'booking_id': booking.id or False,
                #             'cost_profit_ids': cost_profit_line.id or False})
                booking.write({'cost_profit_ids': cost_profit_line or False})
        # if container_product_id:

        self.state = 'sale'