# -*- coding: utf-8 -*-
##############################################################################
#
#    This module uses OpenERP, Open Source Management Solution Framework.
#    Copyright (C) 2017-Today Sitaram
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

from odoo import models, fields, api, _
from itertools import groupby
from datetime import datetime
from odoo.tools import float_round

MAP_INVOICE_TYPE_PARTNER_TYPE = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
}
# Since invoice amounts are unsigned, this is how we know if money comes in or goes out
MAP_INVOICE_TYPE_PAYMENT_SIGN = {
    'out_invoice': 1,
    'in_refund': -1,
    'in_invoice': -1,
    'out_refund': 1,
}


class AccountPayments(models.Model):
    _inherit = 'account.payment'

    apply_manual_currency_exchange = fields.Boolean(
        string='Apply Manual Currency Exchange')
    manual_currency_exchange_rate = fields.Float(
        string='Manual Currency Exchange Rate', digits=(8, 12))
    # TS
    exchange_rate_inverse = fields.Float(
        string='Exchange Rate', help='Eg, USD to MYR (eg 4.21)', copy=False, digits=(8, 6))
    active_manual_currency_rate = fields.Boolean(
        'active Manual Currency', default=True)

    company_currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id', store=True)
    amount_in_cc = fields.Monetary(string='Amount in CC', compute='_compute_payment_amount_in_cc',
                                   currency_field='company_currency_id', store=True)
    balance_in_cc = fields.Monetary(string='Balance in CC', compute='_get_balance_amount',
                                    help='Balance of Unmatched Payment',
                                    currency_field='company_currency_id', store=True)

    @api.multi
    @api.depends('move_line_ids.reconciled')
    def _get_balance_amount(self):
        for payment in self:
            balance = 0.0
            for aml in payment.move_line_ids.filtered(lambda x: x.account_id.reconcile):
                balance += aml.amount_residual
            payment.balance_in_cc = abs(balance)

    @api.onchange('journal_id')
    def _onchange_journal(self):
        res = super(AccountPayments, self)._onchange_journal()
        # Custom Code by Sitaram Solutions Start
        if self.invoice_ids:
            self.currency_id = self.invoice_ids and self.invoice_ids[0].currency_id.id
        # Custom Code by Sitaram Solutions end
        return res

    @api.onchange('currency_id')
    def onchange_currency_id(self):
        # Custom method by Sitaram Solutions
        if self.currency_id:
            if self.company_id.currency_id != self.currency_id:
                self.active_manual_currency_rate = True
            else:
                self.active_manual_currency_rate = False
        else:
            self.active_manual_currency_rate = False

    @api.onchange('currency_id')
    def _get_current_rate(self):
        if self.company_id or self.currency_id:
            if self.company_id.currency_id != self.currency_id:
                self.apply_manual_currency_exchange = True
                self.active_manual_currency_rate = True
                # fc = self.env['res.currency'].search([('name', '=', self.currency_id.name)], limit=1)
                # for rate_id in fc.rate_ids:
                rate_rec = self.env['res.currency.rate'].search([('currency_id', '=', self.currency_id.id),
                                                                 ('company_id', '=',
                                                                  self.company_id.id),
                                                                 ('name', '<=', datetime.now(
                                                                 ).date()),
                                                                 ('date_to', '>=', datetime.now().date())], limit=1)
                if rate_rec:
                    # print('rate=' + str(rate_rec.rate))
                    self.exchange_rate_inverse = rate_rec.rate
                    # TS - bug # USD3097 * 4.118 (GTL)
                    # self.manual_currency_exchange_rate = 1/self.exchange_rate_inverse
                    # change by knjal - bank exchange issue
                    self.manual_currency_exchange_rate = float(
                        round(1 / self.exchange_rate_inverse, 16))
                    # self.manual_currency_exchange_rate = float(round(1 / self.exchange_rate_inverse, 6))
                    # print('rate=', self.manual_currency_exchange_rate)
                    # print('self.apply_manual_currency_exchange=' + str(
                    #    self.apply_manual_currency_exchange))
            else:
                self.exchange_rate_inverse = 1
                self.manual_currency_exchange_rate = 1
                self.apply_manual_currency_exchange = False
                self.active_manual_currency_rate = False

    @api.onchange('exchange_rate_inverse')
    def _update_exchange_rate(self):
        if self.exchange_rate_inverse:
            # TS - bug # USD3097 * 4.118 (GTL)
            # self.manual_currency_exchange_rate = 1/self.exchange_rate_inverse
            # change by knjal - bank exchange issue
            self.manual_currency_exchange_rate = float(
                round(1 / self.exchange_rate_inverse, 16))
            # self.manual_currency_exchange_rate = float(round(1 / self.exchange_rate_inverse, 6))
            # self.apply_manual_currency_exchange = self.active_manual_currency_rate
            # 'invoice payment _update_exchange_rate manual rate=' + str(self.manual_currency_exchange_rate))
            # print('self.apply_manual_currency_exchange=' + str(
            #   self.apply_manual_currency_exchange))

    @api.model
    def default_get(self, fields):
        rec = super(AccountPayments, self).default_get(fields)
        invoice_defaults = self.resolve_2many_commands(
            'invoice_ids', rec.get('invoice_ids'))
        if invoice_defaults and len(invoice_defaults) == 1:
            invoice = invoice_defaults[0]
            rec['communication'] = invoice['reference'] or invoice['name'] or invoice['number']
            rec['currency_id'] = invoice['currency_id'][0]
            rec['payment_type'] = invoice['type'] in (
                'out_invoice', 'in_refund') and 'inbound' or 'outbound'
            rec['partner_type'] = MAP_INVOICE_TYPE_PARTNER_TYPE[invoice['type']]
            rec['partner_id'] = invoice['partner_id'][0]
            rec['amount'] = invoice['residual']
            # Custom Code by Sitaram Solutions Start
            rec['active_manual_currency_rate'] = invoice['active_manual_currency_rate']
            rec['apply_manual_currency_exchange'] = invoice['apply_manual_currency_exchange']
            rec['manual_currency_exchange_rate'] = invoice['manual_currency_exchange_rate']
            # Custom Code by Sitaram Solutions End
        return rec

    @api.multi
    def _compute_payment_amount(self, invoices=None, currency=None):
        '''Compute the total amount for the payment wizard.

        :param invoices: If not specified, pick all the invoices.
        :param currency: If not specified, search a default currency on wizard/journal.
        :return: The total amount to pay the invoices.
        '''
        # Get the payment invoices
        if not invoices:
            invoices = self.invoice_ids

        # Get the payment currency
        if not currency:
            currency = self.currency_id or self.journal_id.currency_id or self.journal_id.company_id.currency_id or invoices and invoices[
                0].currency_id
        # print('>>>>>>>>> _compute_payment_amount')
        # Avoid currency rounding issues by summing the amounts according to the company_currency_id before
        total = 0.00
        groups = groupby(invoices, lambda i: i.currency_id)
        for payment_currency, payment_invoices in groups:
            amount_total = sum([MAP_INVOICE_TYPE_PAYMENT_SIGN[i.type] * i.residual_signed for i in payment_invoices])
            if payment_currency == currency:
                total += amount_total
                # print('>>>>>>>>>   _compute_payment_amount 1 total:' + total)
            else:
                # Custom code by sitaram solution start
                if self.active_manual_currency_rate and self.apply_manual_currency_exchange:
                    # total += amount_total / self.manual_currency_exchange_rate
                    total += float_round(amount_total * self.exchange_rate_inverse,
                                         3, rounding_method='HALF-UP')
                    # total += round(amount_total * self.exchange_rate_inverse, 3)
                    # print('>>>>>>>>>   _compute_payment_amount 2 total:' + total)
                # Custom code by sitaram solution end
                else:
                    total += payment_currency._convert(
                        amount_total, currency, self.env.user.company_id, self.payment_date or fields.Date.today())
                    # print('>>>>>>>>>   _compute_payment_amount 3 total:' + total)

        return round(total, 2)

    @api.multi
    @api.depends('amount', 'currency_id', 'company_currency_id', 'manual_currency_exchange_rate')
    def _compute_payment_amount_in_cc(self):
        for rec in self:
            aml_obj = self.env['account.move.line'].with_context(
                check_move_validity=False)
            debit, credit, amount_currency, currency_id = \
                aml_obj.with_context(date=rec.payment_date,
                                     manual_rate=rec.manual_currency_exchange_rate,
                                     active_manual_currency=rec.apply_manual_currency_exchange, ).\
                _compute_amount_fields(
                    rec.amount, rec.currency_id, rec.company_id.currency_id)
            rec.amount_in_cc = round(debit, 2) or round(credit, 2) or 0.0
            # print('_compute_payment_amount_in_cc rec.amount_in_cc = ', str(rec.amount_in_cc))

    # @api.depends('amount','currency_id','manual_currency_exchange_rate')
    # def convert_payment_amount_in_cc(self):
    #     for rec in self:
    #         aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
    #         debit, credit, amount_currency, currency_id = \
    #             aml_obj.with_context(date=rec.payment_date,
    #                                 manual_rate=rec.manual_currency_exchange_rate,
    #                                 active_manual_currency=rec.apply_manual_currency_exchange, ).\
    #                 _compute_amount_fields(rec.amount, rec.currency_id, rec.company_id.currency_id)
    #         rec.amount_in_cc = float(round(debit,2)) or float(round(credit,2)) or 0.0
    #         print('_compute_payment_amount_in_cc rec.amount_in_cc = ' + str(rec.amount_in_cc))

    # Code commented by Pycus. It is implemented on another application onepayment_against_multipleinvoice
    # Same method used by different vendors. Now both modules have dependency to each other

    # def _create_payment_entry(self, amount):
    #     """ Create a journal entry corresponding to a payment, if the payment references invoice(s) they are reconciled.
    #         Return the journal entry.
    #     """
    #     aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
    #     #custom code by sitaram solutions start
    #     debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date, manual_rate=self.manual_currency_exchange_rate, active_manual_currency=self.apply_manual_currency_exchange,)._compute_amount_fields(amount, self.currency_id, self.company_id.currency_id)
    #     #custom code by sitaram solutions end
    #     move = self.env['account.move'].create(self._get_move_vals())
    #
    #     #Write line corresponding to invoice payment
    #     counterpart_aml_dict = self._get_shared_move_line_vals(debit, credit, amount_currency, move.id, False)
    #     counterpart_aml_dict.update(self._get_counterpart_move_line_vals(self.invoice_ids))
    #     counterpart_aml_dict.update({'currency_id': currency_id})
    #     counterpart_aml = aml_obj.create(counterpart_aml_dict)
    #     #Reconcile with the invoices
    #     if self.payment_difference_handling == 'reconcile' and self.payment_difference:
    #         writeoff_line = self._get_shared_move_line_vals(0, 0, 0, move.id, False)
    #         debit_wo, credit_wo, amount_currency_wo, currency_id = aml_obj.with_context(date=self.payment_date,  manual_rate=self.invoice_ids[0].manual_currency_exchange_rate, active_manual_currency=self.invoice_ids[0].apply_manual_currency_exchange)._compute_amount_fields(self.payment_difference, self.currency_id, self.company_id.currency_id)
    #         writeoff_line['name'] = self.writeoff_label
    #         writeoff_line['account_id'] = self.writeoff_account_id.id
    #         writeoff_line['debit'] = debit_wo
    #         writeoff_line['credit'] = credit_wo
    #         writeoff_line['amount_currency'] = amount_currency_wo
    #         writeoff_line['currency_id'] = currency_id
    #         writeoff_line = aml_obj.create(writeoff_line)
    #         if counterpart_aml['debit'] or (writeoff_line['credit'] and not counterpart_aml['credit']):
    #             counterpart_aml['debit'] += credit_wo - debit_wo
    #         if counterpart_aml['credit'] or (writeoff_line['debit'] and not counterpart_aml['debit']):
    #             counterpart_aml['credit'] += debit_wo - credit_wo
    #         counterpart_aml['amount_currency'] -= amount_currency_wo
    #
    #     #Write counterpart lines
    #     if not self.currency_id.is_zero(self.amount):
    #         if not self.currency_id != self.company_id.currency_id:
    #             amount_currency = 0
    #         liquidity_aml_dict = self._get_shared_move_line_vals(credit, debit, -amount_currency, move.id, False)
    #         liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amount))
    #         aml_obj.create(liquidity_aml_dict)
    #
    #     #validate the payment
    #     if not self.journal_id.post_at_bank_rec:
    #         move.post()
    #
    #     #reconcile the invoice receivable/payable line(s) with the payment
    #     if self.invoice_ids:
    #         self.invoice_ids.register_payment(counterpart_aml)
    #
    #     return move

    # for transfer payment currency amount changed based on manual rate

    def _create_transfer_entry(self, amount):
        """ Create the journal entry corresponding to the 'incoming money' part of an internal transfer, return the reconcilable move line
        """
        aml_obj = self.env['account.move.line'].with_context(
            check_move_validity=False)
        debit, credit, amount_currency, dummy = aml_obj.with_context(date=self.payment_date, manual_rate=self.manual_currency_exchange_rate,
                                                                     active_manual_currency=self.apply_manual_currency_exchange)._compute_amount_fields(amount, self.currency_id, self.company_id.currency_id)
        amount_currency = self.destination_journal_id.currency_id and self.currency_id._convert(
            amount, self.destination_journal_id.currency_id, self.company_id, self.payment_date or fields.Date.today()) or 0

        dst_move = self.env['account.move'].create(
            self._get_move_vals(self.destination_journal_id))

        dst_liquidity_aml_dict = self._get_shared_move_line_vals(
            debit, credit, amount_currency, dst_move.id)
        if self.currency_id.id != self.destination_journal_id.currency_id.id:
            amount_currency = round(
                amount_currency / self.manual_currency_exchange_rate, 2)
        dst_liquidity_aml_dict.update({
            'name': _('Transfer from %s') % self.journal_id.name,
            'account_id': self.destination_journal_id.default_credit_account_id.id,
            'currency_id': self.destination_journal_id.currency_id.id,
            'journal_id': self.destination_journal_id.id,
            'amount_currency': amount_currency
        })
        aml_obj.create(dst_liquidity_aml_dict)

        transfer_debit_aml_dict = self._get_shared_move_line_vals(
            credit, debit, 0, dst_move.id)
        transfer_debit_aml_dict.update({
            'name': self.name,
            'account_id': self.company_id.transfer_account_id.id,
            'journal_id': self.destination_journal_id.id})
        if self.currency_id != self.company_id.currency_id:
            transfer_debit_aml_dict.update({
                'currency_id': self.currency_id.id,
                'amount_currency': -self.amount,
            })
        transfer_debit_aml = aml_obj.create(transfer_debit_aml_dict)
        if not self.destination_journal_id.post_at_bank_rec:
            dst_move.post()
        return transfer_debit_aml
