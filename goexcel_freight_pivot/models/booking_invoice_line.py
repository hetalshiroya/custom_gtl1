from odoo import fields, models, api


class BookingInvoiceLines(models.Model):
    _inherit = "booking.invoice.line"

    total_sale = fields.Float(compute='_get_total_sale_cost', store=True)
    total_cost = fields.Float(compute='_get_total_sale_cost', store=True)

    @api.multi
    def _get_total_sale_cost(self):
        for rec in self:
            rec.total_sale = 0.0
            rec.total_cost = 0.0
            if rec.type in ('in_invoice', 'in_refund', 'purchase_receipt'):
                rec.total_cost += rec.invoice_amount
            if rec.type in ('out_invoice', 'out_refund'):
                rec.total_sale += rec.invoice_amount
