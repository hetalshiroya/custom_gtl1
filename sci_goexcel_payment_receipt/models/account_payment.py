# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class AccountPayment(models.Model):
    _inherit = "account.payment"

    journal_type = fields.Selection(related='journal_id.type', string="Type")
    check_no = fields.Char(string='Check No.')
    cheque_no = fields.Char(string='Cheque No.')
    bank_date = fields.Date(string='Cheque Date')
    reference = fields.Char(string='Payment Ref')
    add_to_receipt = fields.Boolean(string='Add to Receipt', default=False)
    # payment_id = fields.Many2one('payment.receipt', 'Payment')

    def get_amount(self, amount):
        amt_en = self.currency_id.amount_to_text(amount)
        return amt_en

    def action_print_receipt(self):
        self.ensure_one()
        #print('action_print_receipt')
        data = {
            'model': self._name,
            'ids': self.ids,
            'form': self.ids,
        }
        if self.payment_type == 'inbound':
            #print('action_print inbound')
            return self.env.ref('sci_goexcel_payment_receipt.report_official_receipt_action').report_action(self, data=data)
        else:
            #print('action_print outbound')
            return self.env.ref('sci_goexcel_payment_receipt.report_payment_receipt_action').report_action(self,
                                                                                                           data=data)
        # self.ensure_one()
        # view = self.env.ref('sci_goexcel_payment_receipt.payment_receipt_view_form')
        # return {
        #     'name': 'Print Payment Receipt',
        #     'type': 'ir.actions.act_window',
        #     'view_type': 'form',
        #     'view_mode': 'form',
        #     'res_model': 'payment.receipt',
        #     'views': [(view.id, 'form')],
        #     'view_id': view.id,
        #     'target': 'new',  # readonly mode
        #     'context': dict(account_payment_id=self.id),
        # }

    # Done by Laxicon Solution - Shivam
    @api.model
    def create(self, vals):
        if not vals.get('name') and vals.get('payment_type') == 'inbound':
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('so.payment.receipts') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('so.payment.receipts') or _('New')
        if not vals.get('name') and vals.get('payment_type') == 'outbound':
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('po.payment.receipts') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('po.payment.receipts') or _('New')
        return super(AccountPayment, self).create(vals)



class AccountPaymentInvoices(models.Model):
    _inherit = 'account.payment.invoice'

    description = fields.Char(string='Description')
