from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round

class InvoiceWizard1(models.TransientModel):
    _inherit = "invoice.wizard"

    @api.multi
    def action_create_invoice(self):
        if self.booking_no:
            booking = self.env['freight.booking'].search([('booking_no', '=', self.booking_no)], limit=1)
            create_invoice = False
            for booking_line in self.cost_profit_ids:
                if booking_line.add_to_invoice:
                    create_invoice = True

            if create_invoice:
                """Create Invoice for the freight."""
                inv_obj = self.env['account.invoice']
                inv_line_obj = self.env['account.invoice.line']
                # account_id = self.income_acc_id
                if booking.service_type == "land":
                    invoice_type = "lorry"
                else:
                    invoice_type = "without_lorry"
                inv_val = {
                    'type': 'out_invoice',
                    #     'transaction_ids': self.ids,
                    'state': 'draft',
                    'partner_id': booking.customer_name.id or False,
                    'date_invoice': fields.Date.context_today(self),
                    'origin': booking.booking_no,
                    'freight_booking': booking.id,
                    'account_id': booking.customer_name.property_account_receivable_id.id or False,
                    'company_id': booking.company_id.id,
                    'user_id': booking.sales_person.id,
                    'invoice_type': invoice_type,
                    'invoice_description': self.container_product_name,
                }
                invoice = inv_obj.create(inv_val)
                for booking_line in self.cost_profit_ids:
                    if booking_line.add_to_invoice:
                        line_item = booking_line.cost_profit_line
                        line_item.added_to_invoice = True
                        sale_unit_price_converted = line_item.list_price * line_item.profit_currency_rate
                        if line_item.product_id.property_account_income_id:
                            account_id = line_item.product_id.property_account_income_id
                        elif line_item.product_id.categ_id.property_account_income_categ_id:
                            account_id = line_item.product_id.categ_id.property_account_income_categ_id
                        print('before sales_unit_price_converted:', sale_unit_price_converted)
                        print('after sales_unit_price_converted:', round(sale_unit_price_converted, 2))
                        if account_id:
                            if sale_unit_price_converted > 0:
                                inv_line = inv_line_obj.create({
                                    'booking_line_id': line_item.id or False,
                                    'invoice_id': invoice.id or False,
                                    'account_id': account_id.id or False,
                                    'name': line_item.product_name or '',
                                    'product_id': line_item.product_id.id or False,
                                    'quantity': line_item.profit_qty or 0.0,
                                    'freight_currency': line_item.profit_currency.id or False,
                                    'freight_foreign_price': line_item.list_price or 0.00,
                                    'freight_currency_rate': round(line_item.profit_currency_rate, 6) or 1.000000,
                                    'uom_id': line_item.uom_id.id or False,
                                    'price_unit': float_round(sale_unit_price_converted, 2, rounding_method='HALF-UP') or 0.00,
                                    'account_analytic_id': booking.analytic_account_id.id or False,
                                    'invoice_line_tax_ids': [(6, 0, line_item.tax_id.ids)],
                                    'origin': booking.booking_no,
                                })
                                line_item.write({'invoice_id': invoice.id or False,
                                                 'inv_line_id': inv_line.id or False})

                        else:
                            raise ValidationError(_('Please Check Your Product Income/Expense Account!'))
                invoice.compute_taxes()
            for check_line in booking.cost_profit_ids:
                if check_line.added_to_invoice:
                    booking.invoice_status = '03'
                else:
                    booking.invoice_status = '02'

        elif self.bl_no:
            bl = self.env['freight.bol'].search([('bol_no', '=', self.bl_no)])
            create_invoice = False
            for bl_line in self.cost_profit_bl_ids:
                if bl_line.add_to_invoice:
                    create_invoice = True

            if create_invoice:
                """Create Invoice for the freight."""
                inv_obj = self.env['account.invoice']
                inv_line_obj = self.env['account.invoice.line']
                # account_id = self.income_acc_id
                if bl.service_type == "land":
                    invoice_type = "lorry"
                else:
                    invoice_type = "without_lorry"
                inv_val = {
                    'type': 'out_invoice',
                    #     'transaction_ids': self.ids,
                    'state': 'draft',
                    'partner_id': bl.customer_name.id or False,
                    'date_invoice': fields.Date.context_today(self),
                    'origin': bl.bol_no,
                    'freight_hbl': bl.id,
                    'account_id': bl.customer_name.property_account_receivable_id.id or False,
                    'company_id': bl.company_id.id,
                    'user_id': bl.sales_person.id,
                    'invoice_type': invoice_type,
                    'invoice_description': self.container_product_name,
                }
                invoice = inv_obj.create(inv_val)
                for bl_line in self.cost_profit_bl_ids:
                    if bl_line.add_to_invoice:
                        line_item = bl_line.cost_profit_bl_line
                        line_item.added_to_invoice = True
                        sale_unit_price_converted = line_item.list_price * line_item.profit_currency_rate
                        if line_item.product_id.property_account_income_id:
                            account_id = line_item.product_id.property_account_income_id
                        elif line_item.product_id.categ_id.property_account_income_categ_id:
                            account_id = line_item.product_id.categ_id.property_account_income_categ_id
                        if sale_unit_price_converted > 0:
                            inv_line = inv_line_obj.create({
                                'bl_line_id': line_item.id or False,
                                'invoice_id': invoice.id or False,
                                'account_id': account_id.id or False,
                                'name': line_item.product_name or '',
                                'product_id': line_item.product_id.id or False,
                                'quantity': line_item.profit_qty or 0.0,
                                'freight_currency': line_item.profit_currency.id or False,
                                'freight_foreign_price': line_item.list_price or 0.00,
                                'freight_currency_rate': float_round(line_item.profit_currency_rate, 6,
                                                                     rounding_method='HALF-UP') or 1.000000,
                                'uom_id': line_item.uom_id.id or False,
                                'price_unit': float_round(sale_unit_price_converted, 2, rounding_method='HALF-UP') or 0.00,
                                'account_analytic_id': bl.analytic_account_id.id or False,
                                'invoice_line_tax_ids': [(6, 0, line_item.tax_id.ids)],
                                'origin': bl.bol_no,
                            })
                            line_item.write({'invoice_id': invoice.id or False,
                                             'inv_line_id': inv_line.id or False})
                invoice.compute_taxes()
            for check_line in bl.cost_profit_ids:
                if check_line.added_to_invoice:
                    bl.invoice_status = '03'
                else:
                    bl.invoice_status = '02'


