from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)
from odoo import exceptions
from datetime import datetime, timedelta


class PaymentReceipt(models.Model):
    _name = 'payment.receipt'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'payment_receipt_date desc, write_date desc'

    payment_lines = fields.One2many('account.payment.receipt.line', 'payment_id', string="payment lines", copy=False, auto_join=True)
    payment_receipt_no = fields.Char(string='Payment Receipt No', copy=False, readonly=True, index=True)
    payment_receipt_date = fields.Date(string='Payment Receipt Date', copy=False, default=datetime.now().date(), index=True)
    payment_type = fields.Selection([('or', 'Official Receipt'),('pv', 'Payment Voucher'),], string='Type', track_visibility='onchange', store=True)
    payment_receipt_status = fields.Selection([('new', 'New'),('done', 'Done'),('cancelled', 'Cancelled'),],
                                              string="Status", default="new", copy=False,track_visibility='onchange', store=True)
    partner_id = fields.Many2one('res.partner', string='Partner', track_visibility='onchange', store=True)
    approved_by = fields.Many2one('res.users', string="Approved By", track_visibility='onchange', store=True)
    received_by = fields.Many2one('res.users', string="Received By", track_visibility='onchange', store=True)
    amount = fields.Monetary(string='Amount', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.user.company_id.currency_id)


    @api.model
    def default_get(self, fields):
        # _logger.warning('in default_get')
        result = super(PaymentReceipt, self).default_get(fields)
        account_payment_id = self.env.context.get('account_payment_id')
        account_payment = self.env['account.payment'].browse(account_payment_id)
        payment_lines = self.env['account.payment'].search([('state', '!=', 'draft'),
                                                     ('payment_type', '=', account_payment.payment_type),
                                                       ('partner_id', '=', account_payment.partner_id.id)])
        #for rec in self:
        result.update({'partner_id': account_payment.partner_id.id, })
        if account_payment.payment_type == 'inbound':
                payment_type = 'or'

        result.update({'partner_id': account_payment.partner_id.id,
                       'payment_type': payment_type,
                       })

        #for rec in self:

        #rec.payment_receipt_status = 'new'
        # for ap in self:
        #     self.pa = account_payment.payment_type
        payment_list = []
        for payment_line in payment_lines:
            add_to_receipt = False
            if account_payment.id == payment_line.id:
                add_to_receipt = True
            payment_list.append({
                'payment_id': self.id,
                'payment_date': payment_line.payment_date,
                'add_to_receipt': add_to_receipt,
                'name': payment_line.name,
                'journal_id': payment_line.journal_id,
                'payment_method_id': payment_line.payment_method_id,
                'payment_reference': payment_line.reference,
                'partner_id': payment_line.partner_id,
                'amount': payment_line.amount,
                'state': payment_line.state,
            })

        result['payment_lines'] = payment_list
        result = self._convert_to_write(result)
        return result
    # @api.multi
    # def _get_default_payment_list(self):
    #     #_logger.warning('_get_default_payment_list')
    #     account_payment_id = self.env.context.get('account_payment_id')
    #     #_logger.warning('account_payment_id=' + str(account_payment_id))
    #     account_payment = self.env['account.payment'].search([('id', '=', account_payment_id)])
    #     payment_lines = self.env['account.payment'].search([('state', '!=', 'draft'),
    #                                                         ('payment_type', '=', account_payment.payment_type),
    #                                                         ('partner_id', '=', account_payment.partner_id.id)])
    #     for payment in payment_lines:
    #         _logger.warning('account_payment.id=' + str(account_payment.id) + ' , payment.id=' + str(payment.id))
    #         if account_payment.id == payment.id:
    #             #payment.add_to_payment = True
    #             payment.write({'add_to_payment': True})
    #             _logger.warning('MATCHED')
    #
    #     #_logger.warning('payment_lines=' + str(len(payment_lines)))
    #     return payment_lines
    #
    # payment_lines = fields.One2many('account.payment', 'payment_id', default=_get_default_payment_list)


    @api.multi
    def action_print_payment_receipt(self):
        #_logger.warning('action_print_payment_receipt')
        account_payment_id = self.env.context.get('account_payment_id')
        #account_payment = self.env['account.payment'].search([('id', '=', account_payment_id)])
        #_logger.warning('account_payment_id=' + str(account_payment_id))
        for payment_line in self.payment_lines:
            if not payment_line.add_to_receipt:
                payment_line.unlink()
            else:
                self.amount += payment_line.amount
        self.payment_receipt_status = 'done'

        data = {
            'model': self._name,
            'ids': self.ids,
            'form': self.ids,
        }
        # datas = {
        #       'form': payment_ids.ids,
        #        'ids': payment_ids.ids,
        #    'doc_ids': payment_ids.ids,
        #     'model':  'accout.payment',
        # }
        #_logger.warning('payment_ids=' + str(payment_ids) + " , payment_ids.ids=" + str(payment_ids.ids))
        # datas = {
        #      'form': account_payment.ids
        # }
        # will call _get_report_value
        return self.env.ref('sci_goexcel_payment_receipt.report_payment_receipt_action').report_action(self, data=data)
        #return self.env.ref('account_voucher_report.report_payment_receipt_action').report_action([], data=data)

    @api.model
    def create(self, vals):
        if not self.payment_type:
            account_payment_id = self.env.context.get('account_payment_id')
            account_payment = self.env['account.payment'].search([('id', '=', account_payment_id)])
            #_logger.warning("payment_type=" + account_payment.payment_type)
            #self[0].payment_type = account_payment.payment_type
        if account_payment.payment_type == 'inbound':
            vals['payment_receipt_no'] = self.env['ir.sequence'].next_by_code('pr')
            vals['partner_id'] = account_payment.partner_id.id
            vals['payment_type'] = 'or'
        elif account_payment.payment_type == 'outbound':
            vals['payment_receipt_no'] = self.env['ir.sequence'].next_by_code('pv')
            vals['partner_id'] = account_payment.partner_id.id
            #print('account_payment.partner_id.id=' + account_payment.partner_id.id)
            vals['payment_type'] = 'pv'
                #print('payment_type=' + account_payment.payment_type)
            #_logger.warning("payment_type supplier")

        res = super(PaymentReceipt, self).create(vals)

        return res

    @api.multi
    def action_print_receipt(self):
        data = {
            'model': self._name,
            'ids': self.ids,
            'form': self.ids,
        }

        return self.env.ref('sci_goexcel_payment_receipt.report_payment_receipt_action').report_action(self, data=data)


class AccountPaymentReceiptLine(models.Model):
    _name = "account.payment.receipt.line"

    payment_id = fields.Many2one('payment.receipt', string='Payment Receipt Line', ondelete='cascade',
                                 index=True, copy=False)
    name = fields.Char(copy=False, store=True) # The name is attributed upon post()
    payment_date = fields.Date(string='Payment Date', store=True)
    journal_id = fields.Many2one('account.journal', string='Payment Journal', store=True)
    account_id = fields.Many2one('account.account', string='Account', store=True)
    partner_id = fields.Many2one('res.partner', string='Partner', store=True)
    payment_reference = fields.Char(string='Payment Reference', store=True)
    payment_method_id = fields.Many2one('account.payment.method', string='Payment Method Type', store=True)
    amount = fields.Monetary(string='Amount', currency_field='currency_id', store=True)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.user.company_id.currency_id, store=True)
    state = fields.Selection([('draft', 'Draft'), ('posted', 'Posted'), ('sent', 'Sent'), ('reconciled', 'Reconciled'), ('cancelled', 'Cancelled')], string="Status"
                             , store=True)
    add_to_receipt = fields.Boolean(string='Add to Receipt', default=False)
    #company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Company Currency")
