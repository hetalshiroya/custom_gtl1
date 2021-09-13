from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)
from odoo import exceptions


class FreightBookingJobCost(models.TransientModel):
    _name = 'job.cost.wizard'

    booking_job_no = fields.Char(string='Booking Job No', help='Enter Booking Job No to search for Job Cost')
    carrier_job_no = fields.Char(string='Carrier Job No', help='Enter Carrier Booking No to search for Job Cost')
    vendor_id = fields.Many2one('res.partner', string='Vendor', domain="[('supplier','=',True)]")
    vendor_bill_id = fields.Many2one('account.invoice', string='Vendor Bill')
    customer_name = fields.Many2one('res.partner', string='Customer')
    job_cost_lines = fields.One2many('job.cost.wizard.line', 'job_cost_id')

    product_id = fields.Many2one('product.product', string='Product')


    @api.model
    def default_get(self, fields):
        rec = super().default_get(fields)
        rec.update({
            'vendor_id': self.env.context.get('partner_id'),
            'vendor_bill_id': self.env.context.get('vendor_bill_id'),
        })
        return rec

    @api.multi
    def action_assign_job_cost(self):
        for job_cost in self.job_cost_lines:
            if job_cost.add_to_vendor_bill:
                bookings = self.env['freight.booking'].search([('booking_no', '=', self.booking_job_no),])
                for booking in bookings:
                    if not booking.analytic_account_id:
                        values = {
                            'partner_id': booking.customer_name.id,
                            'name': '%s' % booking.booking_no,
                            'company_id': self.env.user.company_id.id,
                        }
                        analytic_account = self.env['account.analytic.account'].sudo().create(values)
                        booking.write({'analytic_account_id': analytic_account.id,
                                       })

                    # update the invoice_line_ids
                    invoice_lines = self.env['account.invoice.line'].browse(self.env.context.get('invoice_line_id'))
                    voucher_lines = self.env['account.voucher.line'].browse(self.env.context.get('invoice_line_id'))
                    if invoice_lines:
                        for invoice_line in invoice_lines:
                            invoices = self.env['account.invoice'].browse(self.env.context.get('vendor_bill_id'))
                            for invoice in invoices:
                                inv_value = {
                                    'freight_booking': booking.id,
                                    'origin': booking.booking_no,
                                    'account_analytic_id': booking.analytic_account_id.id,
                                    'booking_line_id': job_cost.id,
                                }
                                print(job_cost.id)
                                invoice_line.write(inv_value)
                                value = {
                                    'invoiced': True,
                                    'vendor_id': self.vendor_id.id,
                                    'cost_amount': invoice_line.price_subtotal,
                                    'cost_price': invoice_line.price_unit,
                                    'cost_qty': invoice_line.quantity,
                                    'vendor_bill_id': invoice.id,
                                }
                                print(invoice.id)
                    if voucher_lines:
                        for invoice_line in voucher_lines:
                            invoices = self.env['account.voucher'].browse(self.env.context.get('voucher_id'))
                            for invoice in invoices:
                                inv_value = {
                                    'freight_booking': booking.id,
                                    'origin': booking.booking_no,
                                    'account_analytic_id': booking.analytic_account_id.id,
                                }
                                invoice.write({
                                    'line_ids': [
                                        (1, invoice_line.id, inv_value),
                                    ]
                                })
                                value = {
                                    'invoiced': True,
                                    'vendor_id': self.vendor_id.id,
                                    'cost_amount': invoice_line.price_subtotal,
                                    'cost_price': invoice_line.price_unit,
                                    'cost_qty': invoice_line.quantity,
                                }

                    booking.write({
                        'cost_profit_ids': [
                            (1, job_cost.id, value),
                        ]
                    })

    @api.onchange('booking_job_no')
    def onchange_booking_job_no(self):
        for job_cost in self:
            if job_cost.booking_job_no:
                bookings = self.env['freight.booking'].search([('booking_no', '=', job_cost.booking_job_no)], limit=1)
                for booking in bookings:
                    booking_list = []
                    job_cost.customer_name = booking.customer_name.id
                    for booking_line in booking.cost_profit_ids:
                        booking_list.append({
                            'booking_line_id': booking_line.id,
                            'product_id': booking_line.product_id,
                            'product_name': booking_line.product_name,
                            'list_price': booking_line.list_price,
                            'profit_amount': booking_line.profit_amount,
                            'sale_total': booking_line.sale_total,
                            'cost_qty': booking_line.cost_qty,
                            'cost_price': booking_line.cost_price,
                            'cost_amount': booking_line.cost_amount,
                            'cost_total': booking_line.cost_total,
                            'profit_total': booking_line.profit_total,
                            'cost_profit_line': booking_line,
                        })
                    print(booking_list)
                    job_cost
                    #job_cost.job_cost_lines.append() = booking_list

    @api.multi
    def action_match_job_cost(self):
        vendor_bill = self.env['account.invoice'].search([('id', '=', self.vendor_bill_id.id), ])
        for booking_line in self.job_cost_lines:
            for vendor_line in vendor_bill.invoice_line_ids:
                if booking_line.product_id == vendor_line.product_id:
                    print(booking_line.product_id)
                    print(vendor_line.product_id)
                    #vendor_line.matched = True





class FreightBookingJobCostLine(models.TransientModel):
    _name = 'job.cost.wizard.line'

    job_cost_id = fields.Many2one('job.cost.wizard', 'Job Cost')
    add_to_vendor_bill = fields.Boolean(string='Add')
    matched = fields.Boolean(string='Matched')
    cost_profit_line = fields.Many2one('freight.cost_profit', string='Booking Reference', required=True,
                                       ondelete='cascade', index=True)
    booking_line_id = fields.Many2one('freight.cost_profit')

    product_id = fields.Many2one('product.product', string="Product")
    product_name = fields.Text(string="Description")
    profit_qty = fields.Float(string='Qty', digits=(12, 2))
    list_price = fields.Float(string="Unit Price")
    profit_amount = fields.Float(string="Amt")
    sale_total = fields.Float(string="Total Sales")
    cost_qty = fields.Integer(string='Qty')
    cost_price = fields.Float(string="Unit Price")
    cost_amount = fields.Float(string="Amt")
    cost_total = fields.Float(string="Total Cost")
    profit_total = fields.Float(string="Total Profit")

