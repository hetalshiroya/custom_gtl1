# -*- coding: utf-8 -*-
import time
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class BulkRefund(models.TransientModel):
    _name = "account.bulk.refund"
    _description = "Bulk Credit Note/Debit note from invoice"

    partner_id = fields.Many2one('res.partner', string='Partner', required=True,
                                 domain=['|',('customer','=',True),('supplier','=',True)])
    date = fields.Date(string='Accounting Date', required=True, default=fields.Date.today())
    type = fields.Selection([
        ('Debit Note','Debit Note'),
        ('Credit Note','Credit Note')],
        default='Credit Note', required=True)
    description = fields.Char(string='Extra notes if any')
    account_id = fields.Many2one('account.account', string='Account',
                required=True, domain=[('user_type_id.type','not in',['receivable','payable','liquidity'])])

    refund_line_ids = fields.One2many('account.bulk.refund.line', 'bulk_refund_id')

    @api.onchange('partner_id','date','type')
    def onchange_partner_id(self):
        op_list = []
        self.refund_line_ids = False

        date_from = fields.Date.to_string(fields.Date.from_string(self.date) - relativedelta(days=365))

        if self.partner_id and self.date:
            search_domain = [
                ('partner_id', '=', self.partner_id.id),
                ('date_invoice', '<=', self.date),
                ('date_invoice', '>=', date_from),
                ('state','not in',['draft','cancel'])
            ]
            if self.type == 'Credit Note':
                search_domain.append(('type', '=', 'out_invoice'))
            else:
                search_domain.append(('type', '=', 'in_invoice'))

            for invoice in self.env['account.invoice'].search(search_domain):
                op_list.append((0,0,{
                    'invoice_id': invoice.id,
                    #'reconcile_amount': invoice.residual
                }))
        if op_list:
            self.refund_line_ids = op_list
        else:
            self.refund_line_ids = False

    @api.multi
    def create_debit_credit_note(self):
        for line in self.refund_line_ids:
            if line.reconcile_amount > line.residual and line.residual:
                raise UserError(_('You cannot create debit/credit note for more than the '
                                  'balance amount in invoice - %s')%(line.invoice_id.number))
            if line.reconcile_amount:
                # Prepare invoice lines
                invoice_lines = []
                name = 'Credit Note - %s'%(line.invoice_id.number) if self.type == 'Credit Note' else \
                    'Debit Note - %s'%(line.invoice_id.number)
                invoice_lines.append((0,0,{
                    'name': (name or '') + ' - ' + (self.description or ''),
                    'account_id': line.account_id and line.account_id.id or self.account_id.id,
                    'price_unit': line.reconcile_amount,
                    'invoice_line_tax_ids': [(6, 0, line.tax_ids.ids)],
                    'quantity': 1.0
                }))
                # Prepare Invoice
                invoice_dict = {
                    'partner_id': self.partner_id and self.partner_id.id,
                    'journal_id': self.refund_line_ids[0].invoice_id.journal_id.id,
                    'invoice_line_ids': invoice_lines,
                    'type': 'out_refund' if self.type == 'Credit Note' else 'in_refund',
                    'date_invoice': self.date
                }
                refund_invoice_id = self.env['account.invoice'].create(invoice_dict)
                refund_invoice_id.action_invoice_open()
                refund_move_line = refund_invoice_id.move_id.line_ids.filtered(
                    lambda a: a.account_id.user_type_id.type in ['receivable', 'payable'])
                invoice_move_line = line.invoice_id.move_id.line_ids.filtered(
                    lambda a: a.account_id.user_type_id.type in ['receivable', 'payable'])

                if line.residual:
                    (refund_move_line + invoice_move_line).reconcile()


class BulkRefundLine(models.TransientModel):
    _name = "account.bulk.refund.line"
    _description = "Bulk Credit Note/Debit note line"

    bulk_refund_id = fields.Many2one('account.bulk.refund', string='Bulk Refund')

    invoice_id = fields.Many2one('account.invoice', string='Invoice', required=True)
    date = fields.Date(string='Invoice Date', related='invoice_id.date_invoice')
    partner_id = fields.Many2one('res.partner', string='Partner', related='invoice_id.partner_id')
    date_due = fields.Date(string='Due Date', related='invoice_id.date_due')
    move_id = fields.Many2one('account.move', string='Journal Entry', related='invoice_id.move_id')
    reconcile_amount = fields.Monetary(string='Reconcile Amount', currency_field='company_currency_id')
    amount_total = fields.Monetary(related="invoice_id.amount_total", currency_field='company_currency_id')
    residual = fields.Monetary(related="invoice_id.residual", currency_field='company_currency_id')
    company_currency_id = fields.Many2one('res.currency', related="invoice_id.company_currency_id")
    tax_ids = fields.Many2many('account.tax', string='Tax/VAT')
    account_id = fields.Many2one('account.account', string='Account',
                                 required=False,
                                 domain=[('user_type_id.type', 'not in', ['receivable', 'payable', 'liquidity'])])

