from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)
from odoo import exceptions
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError, UserError

class InvoiceWizard(models.TransientModel):
    _name = 'invoice.wizard.tallysheet'

    customer = fields.Many2one('res.partner', string='Customer')
    job_no = fields.Char(string='Job No', index=True)
    cost_profit_ids = fields.One2many('invoice.wizard.line.tallysheet', 'tallysheet_id', string="Cost & Profit")
    select_add = fields.Selection([('all', 'Select All'), ('deselect', 'DeSelect All')],
                                  string='Select/DeSelect All to Add to Invoice'
                                  , default='all')
    product_name = fields.Text(string='Description of Goods')

    @api.onchange('select_add')
    def onchange_select_add(self):
        if self.select_add == 'all':
            for cost_profit_line in self.cost_profit_ids:
                cost_profit_line.add_to_invoice = True
        elif self.select_add == 'deselect':
            for cost_profit_line in self.cost_profit_ids:
                cost_profit_line.add_to_invoice = False


    def _saleorder_create_analytic_account_prepare_values(self):
        """
         Prepare values to create analytic account
        :return: list of values
        """
        return {
            'name': '%s' % self.job_no,
            'partner_id': self.customer.id,
            'company_id': self.company_id.id,
        }



    @api.model
    def default_get(self, fields):
        # _logger.warning('in default_get')
        result = super(InvoiceWizard, self).default_get(fields)
        tallysheet_id = self.env.context.get('tallysheet_id')
        if tallysheet_id:
            tallysheet = self.env['warehouse.tally.sheet'].browse(tallysheet_id)
            if not tallysheet.analytic_account_id:
                values = {
                    'name': '%s' % tallysheet.job_no,
                    #'partner_id': tallysheet.customer_name.id,
                    'company_id': self.env.user.company_id.id,
                }
                analytic_account = self.env['account.analytic.account'].sudo().create(values)
                tallysheet.write({'analytic_account_id': analytic_account.id,
                               })

            # for rec in self:
            result.update({'customer': tallysheet.customer.id,
                           'job_no': tallysheet.job_no,
                           })
            tallysheet_list = []
            for tallysheet_line in tallysheet.cost_profit_ids:
                if not tallysheet_line.added_to_invoice:
                    tallysheet_list.append({
                        'product_id': tallysheet_line.product_id,
                        'list_price': tallysheet_line.list_price,
                        'profit_qty': tallysheet_line.profit_qty,
                        'sale_total': tallysheet_line.sale_total,
                        'cost_profit_line' : tallysheet_line,
                        'analytic_account_id': tallysheet.analytic_account_id,
                    })


                    #result.update({'product_name': tallysheet.operation_line_ids2[0].container_product_name})

            result['cost_profit_ids'] = tallysheet_list
            result = self._convert_to_write(result)

        return result


    @api.multi
    def action_create_invoice(self):
        print("test")
        if self.job_no:
            tallysheet = self.env['warehouse.tally.sheet'].search([('job_no', '=', self.job_no)])
            create_invoice = False
            for tallysheet_line in self.cost_profit_ids:
                if tallysheet_line.add_to_invoice:
                    create_invoice = True

            if create_invoice:
                """Create Invoice for the tally sheet."""
                inv_obj = self.env['account.invoice']
                inv_line_obj = self.env['account.invoice.line']
                # account_id = self.income_acc_id
                # if tallysheet.service_type == "land":
                #     invoice_type = "lorry"
                # else:
                #     invoice_type = "without_lorry"
                inv_val = {
                    'type': 'out_invoice',
                    #     'transaction_ids': self.ids,
                    'state': 'draft',
                    'partner_id': tallysheet.customer.id or False,
                    'date_invoice': fields.Date.context_today(self),
                    'origin': tallysheet.job_no,
                    'tally_sheet': tallysheet.id,
                    'account_id': tallysheet.customer.property_account_receivable_id.id or False,
                    'company_id': tallysheet.company_id.id,
                    'user_id': tallysheet.sales_person.id,
                    #'invoice_type': invoice_type,
                    #'invoice_description': self.container_product_name,
                }
                invoice = inv_obj.create(inv_val)
                for tallysheet_line in self.cost_profit_ids:
                    if tallysheet_line.add_to_invoice:
                        line_item = tallysheet_line.cost_profit_line
                        line_item.added_to_invoice = True
                        sale_unit_price_converted = line_item.list_price * line_item.profit_currency_rate
                        if line_item.product_id.property_account_income_id:
                            account_id = line_item.product_id.property_account_income_id
                        elif line_item.product_id.categ_id.property_account_income_categ_id:
                            account_id = line_item.product_id.categ_id.property_account_income_categ_id
                        if sale_unit_price_converted > 0:
                            inv_line = inv_line_obj.create({
                                'invoice_id': invoice.id or False,
                                'account_id': account_id.id or False,
                                'name': line_item.product_name or '',
                                'product_id': line_item.product_id.id or False,
                                'quantity': line_item.profit_qty or 0.0,
                                'uom_id': line_item.uom_id.id or False,
                                'price_unit': sale_unit_price_converted or 0.0,
                                'account_analytic_id': tallysheet.analytic_account_id.id or False,
                                'invoice_line_tax_ids': [(6, 0, line_item.tax_id.ids)],
                            })
                            line_item.write({'invoice_id': invoice.id or False,
                                        'inv_line_id': inv_line.id or False})

            for check_line in tallysheet.cost_profit_ids:
                if check_line.added_to_invoice:
                    tallysheet.invoice_status = '03'
                else:
                    tallysheet.invoice_status = '02'


    @api.multi
    def action_select_all(self):
        for tallysheet_line in self.cost_profit_ids:
            tallysheet_line.write({'add_to_invoice': True})



    @api.multi
    def action_deselect_all(self):
        for tallysheet_line in self.cost_profit_ids:
            tallysheet_line.add_to_invoice = False



class InvoiceWizardLine(models.TransientModel):
    _name = "invoice.wizard.line.tallysheet"

    tallysheet_id = fields.Many2one('invoice.wizard.tallysheet', string='TallySheet Reference', required=True, ondelete='cascade',
                                 index=True,copy=False)
    cost_profit_line = fields.Many2one('warehouse.cost.profit', string='Cost Profit Reference', required=True, ondelete='cascade',
                                 index=True,copy=False)
    product_id = fields.Many2one('product.product', string="Product")
    add_to_invoice = fields.Boolean(string='Add to Invoice')
    list_price = fields.Float(string="Unit Price")
    profit_qty = fields.Integer(string='Qty')
    sale_total = fields.Float(string="Total Sales")
    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account",
                                          track_visibility='always')
