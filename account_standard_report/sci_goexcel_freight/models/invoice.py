from odoo import models, fields, api


class FreightInvoice(models.Model):

    _inherit = 'account.invoice'

    freight_booking = fields.Many2one('freight.booking', string='Freight Booking', readonly=True)

    @api.onchange('amount_total')
    def onchange_amount_total(self):
        if self.freight_booking:
            #for invoice only, changes will update back to the job's cost & profit
            if self.type == 'out_invoice':
                #print("out_invoice")
                for line in self.invoice_line_ids:
                    freight_cost_profit_lines = self.env['freight.cost_profit'].search([
                        ('inv_line_id', '=', line.id),
                    ])
                    if freight_cost_profit_lines:
                        #print('freight_cost_profit_lines len:' + str(len(freight_cost_profit_lines)))
                        for cost_line in freight_cost_profit_lines:
                            if line.price_subtotal != cost_line.sale_total:
                                #print('change sale total')
                                #print('line.price_subtotal=' + str(line.price_subtotal))
                                #print('sale_total=' + str(cost_line.sale_total))
                                #cost_line.sale_total = line.price_subtotal
                                #cost_line.profit_qty = line.quantity
                                value = {
                                    'sale_total': line.price_subtotal,
                                    'list_price': line.price_unit,
                                    'profit_qty': line.quantity,
                                }
                                #update to the existing line
                                # freight_cost_profit_lines.operation_id.write({
                                #     'cost_profit_ids': [
                                #         (1, cost_line.id, value),
                                #     ]
                                # })
                                if self.freight_booking:
                                    self.freight_booking.write({
                                        'cost_profit_ids': [
                                            (1, cost_line.id, value),
                                        ]
                                    })





