from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)
from odoo import exceptions
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError, UserError

class InvoiceWizard(models.TransientModel):
    _name = 'invoice.wizard'

    customer_name = fields.Many2one('res.partner', string='Customer Name')
    booking_no = fields.Char(string='Booking Job No', index=True)
    bl_no = fields.Char(string='HBL No', index=True)
    cost_profit_ids = fields.One2many('invoice.wizard.line', 'booking_id', string="Cost & Profit")
    cost_profit_bl_ids = fields.One2many('invoice.wizard.bl.line', 'bl_id', string="Cost & Profit")

    select_add = fields.Selection([('all', 'Select All'), ('deselect', 'DeSelect All')],
                                  string='Select/DeSelect All to Add to Invoice'
                                  , default='all')
    container_product_name = fields.Text(string='Description of Goods')

    @api.onchange('select_add')
    def onchange_select_add(self):
        if self.select_add == 'all':
            for cost_profit_line in self.cost_profit_ids:
                cost_profit_line.add_to_invoice = True
            for cost_profit_line in self.cost_profit_bl_ids:
                cost_profit_line.add_to_invoice = True
        elif self.select_add == 'deselect':
            for cost_profit_line in self.cost_profit_ids:
                cost_profit_line.add_to_invoice = False
            for cost_profit_line in self.cost_profit_bl_ids:
                cost_profit_line.add_to_invoice = False

    def _saleorder_create_analytic_account_prepare_values(self):
        """
         Prepare values to create analytic account
        :return: list of values
        """
        return {
            'name': '%s' % self.booking_no,
            'partner_id': self.customer_name.id,
            'company_id': self.company_id.id,
        }

    @api.model
    def default_get(self, fields):
        print('in default_get')
        result = super(InvoiceWizard, self).default_get(fields)
        booking_id = self.env.context.get('booking_id')
        bl_id = self.env.context.get('bl_id')
        if booking_id:
            booking = self.env['freight.booking'].browse(booking_id)
            if not booking.analytic_account_id:
                values = {
                    'partner_id': booking.customer_name.id,
                    'name': '%s' % booking.booking_no,
                    'code': booking.booking_no,
                    'company_id': self.env.user.company_id.id,
                }
                analytic_account = self.env['account.analytic.account'].sudo().create(values)
                booking.write({'analytic_account_id': analytic_account.id,
                               })

            # for rec in self:
            result.update({'customer_name': booking.customer_name.id,
                           'booking_no': booking.booking_no,
                           })
            booking_list = []
            for booking_line in booking.cost_profit_ids:
                if not booking_line.added_to_invoice:
                    booking_list.append({
                        'booking_line_id': booking_line.id,
                        'product_id': booking_line.product_id,
                        'list_price': booking_line.list_price,
                        'profit_qty': booking_line.profit_qty,
                        'sale_total': booking_line.sale_total,
                        'cost_profit_line' : booking_line,
                        'analytic_account_id': booking.analytic_account_id,
                    })

            if booking.cargo_type == 'fcl':
                if booking.operation_line_ids:
                    result.update({'container_product_name': booking.operation_line_ids[0].container_product_name})

            if booking.cargo_type == 'lcl':
                if booking.operation_line_ids2:
                    result.update({'container_product_name': booking.operation_line_ids2[0].container_product_name})

            result['cost_profit_ids'] = booking_list
            result = self._convert_to_write(result)

        elif bl_id:
            bl = self.env['freight.bol'].browse(bl_id)
            print('in default_get BL=', bl)
            if not bl.analytic_account_id:
                values = {
                    #'partner_id': bl.customer_name.id,
                    #'name': '%s' % bl.booking_ref.booking_no,
                    'code': bl.booking_ref.booking_no,
                    #'company_id': self.env.user.company_id.id,
                    'name': '%s' % bl.bol_no,
                    'partner_id': bl.customer_name.id,
                    # 'partner_id': self.customer_name.id,
                    'company_id': bl.booking_ref.company_id.id,
                }
                if not bl.booking_ref.analytic_account_id:
                    analytic_account = self.env['account.analytic.account'].sudo().create(values)
                    #bl.booking_ref.write({'analytic_account_id': analytic_account.id})
                    bl.write({'analytic_account_id': analytic_account.id,
                              })
                else:
                    bl.write({'analytic_account_id': bl.analytic_account_id.id,
                              })

            # for rec in self:
            result.update({'customer_name': bl.customer_name.id,
                           'bl_no': bl.bol_no,
                           })
            bl_list = []
            for bl_line in bl.cost_profit_ids:
                if not bl_line.added_to_invoice:
                    bl_list.append({
                        'bl_line_id': bl_line.id,
                        'product_id': bl_line.product_id,
                        'list_price': bl_line.list_price,
                        'profit_qty': bl_line.profit_qty,
                        'sale_total': bl_line.sale_total,
                        'cost_profit_bl_line': bl_line,
                        'analytic_account_id': bl.analytic_account_id.id,
                    })

            if bl.cargo_line_ids:
                result.update({'container_product_name': bl.cargo_line_ids[0].container_product_name})

            result['cost_profit_bl_ids'] = bl_list
            result = self._convert_to_write(result)
        #print(result)
        return result


    @api.multi
    def action_create_invoice(self):
        if self.booking_no:
            booking = self.env['freight.booking'].search([('booking_no', '=', self.booking_no)])
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
                        #print(booking.booking_no)
                        if account_id:
                            if sale_unit_price_converted > 0:
                                inv_line = inv_line_obj.create({
                                    'booking_line_id': line_item.id or False,
                                    'invoice_id': invoice.id or False,
                                    'account_id': account_id.id or False,
                                    'name': line_item.product_name or '',
                                    'product_id': line_item.product_id.id or False,
                                    'quantity': line_item.profit_qty or 0.0,
                                    'uom_id': line_item.uom_id.id or False,
                                    'price_unit': sale_unit_price_converted or 0.0,
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

        if self.bl_no:
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
                                'uom_id': line_item.uom_id.id or False,
                                'price_unit': sale_unit_price_converted or 0.0,
                                'freight_hbl': bl.id,
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

    @api.multi
    def action_select_all(self):
        for booking_line in self.cost_profit_ids:
            booking_line.write({'add_to_invoice': True})
        for booking_line in self.cost_profit_bl_ids:
            booking_line.write({'add_to_invoice': True})



    @api.multi
    def action_deselect_all(self):
        for booking_line in self.cost_profit_ids:
            booking_line.add_to_invoice = False
        for booking_line in self.cost_profit_bl_ids:
            booking_line.add_to_invoice = False


class InvoiceWizardLine(models.TransientModel):
    _name = "invoice.wizard.line"

    booking_id = fields.Many2one('invoice.wizard', string='Booking Reference', required=True, ondelete='cascade',
                                 index=True,copy=False)
    cost_profit_line = fields.Many2one('freight.cost_profit', string='Booking Reference', required=True, ondelete='cascade',
                                 index=True,copy=False)
    product_id = fields.Many2one('product.product', string="Product")
    add_to_invoice = fields.Boolean(string='Add to Invoice')
    list_price = fields.Float(string="Unit Price")
    #profit_qty = fields.Integer(string='Qty')
    profit_qty = fields.Float(string='Qty', digits=(12, 2))
    sale_total = fields.Float(string="Total Sales")
    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account",
                                          track_visibility='always')
    booking_line_id = fields.Many2one('freight.cost_profit')

class InvoiceWizardLine(models.TransientModel):
    _name = "invoice.wizard.bl.line"

    bl_id = fields.Many2one('invoice.wizard', string='BL Reference', required=True, ondelete='cascade',
                                 index=True, copy=False)
    cost_profit_bl_line = fields.Many2one('freight.bol.cost.profit', string='Booking Reference', required=True,
                                       ondelete='cascade', index=True, copy=False)
    product_id = fields.Many2one('product.product', string="Product")
    add_to_invoice = fields.Boolean(string='Add to Invoice')
    list_price = fields.Float(string="Unit Price")
    #profit_qty = fields.Integer(string='Qty')
    profit_qty = fields.Float(string='Qty', digits=(12, 2))
    sale_total = fields.Float(string="Total Sales")
    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account",
                                          track_visibility='always')
    bl_line_id = fields.Many2one('freight.bol.cost.profit')