# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details

from odoo import api, exceptions, fields, models, _
from odoo.exceptions import UserError


class BankReconcile(models.TransientModel):
    _name = "bank.reconcile"
    _description = 'Bank Reconciliation Wizard'

    def compute_starting_balance(self):
        context = dict(self._context or {})
        payment_ids = context.get('active_ids')
        ABS = self.env['account.bank.statement']
        AccountPayment = self.env['account.payment']
        for payment_id in payment_ids:
            payment_br = AccountPayment.browse(payment_id)
        starting_bal = ABS._get_opening_balance(payment_br.journal_id.id)
        return starting_bal

    starting_bal = fields.Float(string='Starting Balance', default=compute_starting_balance)

    @api.multi
    def button_reconcile(self):
        context = dict(self._context or {})
        payment_ids = context.get('active_ids')
        self.env['account.payment'].action_reconcile(self.starting_bal, payment_ids)
        return True
