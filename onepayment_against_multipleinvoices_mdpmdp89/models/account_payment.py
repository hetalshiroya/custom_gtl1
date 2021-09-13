# coding: utf-8
from decimal import Decimal, ROUND_HALF_UP
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountPaymentInvoices(models.Model):
    _name = 'account.payment.invoice'

    invoice_id = fields.Many2one('account.invoice', string='Invoice')
    payment_id = fields.Many2one('account.payment', string='Payment')
    currency_id = fields.Many2one(related='invoice_id.currency_id')
    origin = fields.Char(related='invoice_id.origin')
    date_invoice = fields.Date(related='invoice_id.date_invoice')
    date_due = fields.Date(related='invoice_id.date_due')
    payment_state = fields.Selection(related='payment_id.state', store=True)
    reconcile_amount = fields.Monetary(
        string='Reconcile Amount', default=0.000, digits=(16, 3))
    amount_total = fields.Monetary(related="invoice_id.amount_total")
    residual = fields.Monetary(related="invoice_id.residual")
    # TS add
    reference = fields.Char(related='invoice_id.reference')
    fully_reconcile = fields.Boolean('Fully Reconciled?')

    @api.onchange('fully_reconcile')
    def onchange_fully_reconcile(self):
        if self.fully_reconcile:
            # cents = Decimal('.001')
            # residual = self.residual.quantize(cents, ROUND_HALF_UP)
            self.reconcile_amount = self.residual
        if not self.fully_reconcile:
            self.reconcile_amount = 0.00
    # TS add


class AccountPaymentMoveLine(models.Model):
    _name = 'account.payment.move.line'

    date = fields.Date(string='Date')
    move_id = fields.Many2one('account.move', string='journal Entry')
    journal_id = fields.Many2one('account.journal', string='Journal')
    name = fields.Char(string='Label')
    ref = fields.Char(string='Reference')
    partner_id = fields.Many2one('res.partner', string='Partner')
    account_id = fields.Many2one('account.account', string='Account')
    analytic_account_id = fields.Many2one(
        'account.analytic.account', string='Analytic Account')
    # analytic_tag_ids = fields.Manymany(related="invoice_id.amount_total")
    debit = fields.Float(string="Debit")
    credit = fields.Float(string="Credit")
    amount_currency = fields.Monetary(string="Amount Currency")
    date_maturity = fields.Date(string='Due Date')
    currency_id = fields.Many2one('res.currency')

    payment_id = fields.Many2one('account.payment', string='Payment')


class AccountPayment(models.Model):
    _inherit = 'account.payment'
    bank_charge_amount = fields.Monetary('Extra Bank Charges Amount')

    @api.onchange('journal_id')
    def _get_default_bank_charge_account(self):
        journal = self.env['account.journal'].search(
            [('id', '=', self.journal_id.id)], limit=1)
        self.bank_charge_account_id = journal.bank_charge_account_id.id

    bank_charge_account_id = fields.Many2one('account.account', string='Bank Charge Account',
                                             domain=[('user_type_id.name', '=', 'Expenses')])

    @api.onchange('partner_id', 'state', 'partner_type', 'payment_type')
    def _get_open_journal_entries(self):
        for rec in self:
            if rec.partner_id and not rec.move_line_ids:
                account_id = rec.partner_id.property_account_receivable_id.id if rec.partner_type == 'customer' \
                    else rec.partner_id.property_account_payable_id.id
                entries = self.env['account.move.line'].search([
                    ('move_id.state', '=', 'posted'),
                    ('amount_residual', '!=', 0),
                    ('partner_id', '=', rec.partner_id.id),
                    ('account_id', '=', account_id),
                    ('journal_id.type', 'not in', ['bank', 'cash'])
                ])
                op = []
                for e in entries:
                    op.append((0, 0, {
                        'date': e.date,
                        'move_id': e.move_id.id,
                        'journal_id': e.journal_id.id,
                        'name': e.name,
                        'ref': e.ref,
                        'partner_id': e.partner_id.id,
                        'account_id': e.account_id.id,
                        'analytic_account_id': e.analytic_account_id and e.analytic_account_id.id,
                        'debit': e.debit,
                        'credit': e.credit,
                        'amount_currency': e.amount_currency,
                        'date_maturity': e.date_maturity,
                        'currency_id': e.currency_id and e.currency_id.id
                    }))
                rec.open_move_line_ids = op
            else:
                rec.open_move_line_ids = False

    payment_invoice_ids = fields.One2many(
        'account.payment.invoice', 'payment_id', string="Customer Invoices")
    open_move_line_ids = fields.One2many(
        'account.payment.move.line', 'payment_id', string='Open Journal Entries')

    @api.onchange('payment_type', 'partner_type', 'partner_id', 'currency_id')
    def _onchange_to_get_vendor_invoices(self):
        if self.payment_type in ['inbound', 'outbound'] and self.partner_type and self.partner_id and self.currency_id:
            if self.payment_type == 'inbound' and self.partner_type == 'customer':
                invoice_type = 'out_invoice'
            elif self.payment_type == 'outbound' and self.partner_type == 'customer':
                invoice_type = 'out_refund'
            elif self.payment_type == 'outbound' and self.partner_type == 'supplier':
                invoice_type = 'in_invoice'
            else:
                invoice_type = 'in_refund'
            invoice_recs = self.env['account.invoice'].search([('partner_id', 'child_of', self.partner_id.id), (
                'type', '=', invoice_type), ('state', '=', 'open'), ('currency_id', '=', self.currency_id.id)])
            payment_invoice_values = [(5, 0, 0)]
            for invoice_rec in invoice_recs:
                payment_invoice_values.append(
                    [0, 0, {'invoice_id': invoice_rec.id}])
            self.payment_invoice_ids = payment_invoice_values

    @api.multi
    def post(self):
        if self.payment_invoice_ids:
            amount = 0.00
            for payment_invoice_id in self.payment_invoice_ids:
                if (payment_invoice_id.reconcile_amount):
                    amount += float(round(payment_invoice_id.reconcile_amount, 5))
                    print('post reconcile amount=' +
                          str(payment_invoice_id.reconcile_amount))

                    print('amount=' + str(amount))
            #     print('sum=' + str(sum(self.payment_invoice_ids.mapped('reconcile_amount'))))
            # cents = Decimal('.001')
            # recon_amount = amount.quantize(cents, ROUND_HALF_UP)
            # recon_amount = round(amount, 3)
            # amount = sum(self.payment_invoice_ids.mapped('reconcile_amount'))

            # print('recon_amount=' + str(recon_amount))
            # if amount > 0:
            #    print('self amount=' + str(self.amount))
            #    if self.amount != float(round(amount,2)):
            #        raise UserError(_("The sum of the reconcile amount of listed invoices are not equivalent to the payment's amount."))
        res = super(AccountPayment, self).post()
        return res

    # TS
    @api.onchange('reference')
    def _onchange_reference(self):
        if self.reference:
            self.communication = self.reference

    # this is the actual code by the owner. But need to copy paste below due to same method override by one of its dependancy
    # module. So added both concept together just below this method. and dependant to each other.

    # def _create_payment_entry(self, amount):
    #     """ Create a journal entry corresponding to a payment, if the payment references invoice(s) they are reconciled.
    #         Return the journal entry.
    #     """
    #     aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
    #     debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(amount, self.currency_id, self.company_id.currency_id)
    #
    #     move = self.env['account.move'].create(self._get_move_vals())
    #
    #     counterpart_aml_list = {}
    #     # Write line corresponding to invoice payment
    #     if self.payment_invoice_ids and self.payment_type == 'inbound':
    #         total_reconcile_amount = 0.00
    #         total_separate_amount_currency = 0.00
    #         for payment_invoice_id in self.payment_invoice_ids:
    #             if payment_invoice_id.reconcile_amount > 0:
    #                 separate_amount_currency = amount_currency
    #                 reconcile_amount = payment_invoice_id.reconcile_amount
    #                 if amount_currency and credit:
    #                     reconcile_amount = (payment_invoice_id.reconcile_amount * credit) / amount_currency
    #                     separate_amount_currency = -payment_invoice_id.reconcile_amount
    #                     reconcile_amount = -reconcile_amount
    #                 total_reconcile_amount += reconcile_amount
    #                 total_separate_amount_currency += separate_amount_currency
    #                 counterpart_aml_dict = self._get_shared_move_line_vals(debit, reconcile_amount, separate_amount_currency, move.id, False)
    #                 counterpart_aml_dict.update(self._get_counterpart_move_line_vals([payment_invoice_id.invoice_id]))
    #                 counterpart_aml_dict.update({'currency_id': currency_id})
    #                 counterpart_aml = aml_obj.create(counterpart_aml_dict)
    #                 counterpart_aml_list[payment_invoice_id.invoice_id.id] = counterpart_aml
    #         if credit > total_reconcile_amount:
    #             remaining_reconcile_amount = credit - total_reconcile_amount
    #             separate_amount_currency = amount_currency
    #             if amount_currency and credit:
    #                 separate_amount_currency = amount_currency - total_separate_amount_currency
    #             counterpart_aml_dict = self._get_shared_move_line_vals(debit, remaining_reconcile_amount, separate_amount_currency, move.id, False)
    #             counterpart_aml_dict.update(self._get_counterpart_move_line_vals(self.invoice_ids))
    #             counterpart_aml_dict.update({'currency_id': currency_id})
    #             counterpart_aml = aml_obj.create(counterpart_aml_dict)
    #     elif self.payment_invoice_ids and self.payment_type == 'outbound':
    #         total_reconcile_amount = 0.00
    #         total_separate_amount_currency = 0.00
    #         for payment_invoice_id in self.payment_invoice_ids:
    #             if payment_invoice_id.reconcile_amount > 0:
    #                 separate_amount_currency = amount_currency
    #                 reconcile_amount = payment_invoice_id.reconcile_amount
    #                 if amount_currency and debit:
    #                     reconcile_amount = (payment_invoice_id.reconcile_amount * debit) / amount_currency
    #                     separate_amount_currency = payment_invoice_id.reconcile_amount
    #                 total_reconcile_amount += reconcile_amount
    #                 total_separate_amount_currency += separate_amount_currency
    #                 counterpart_aml_dict = self._get_shared_move_line_vals(reconcile_amount, credit, separate_amount_currency, move.id, False)
    #                 counterpart_aml_dict.update(self._get_counterpart_move_line_vals([payment_invoice_id.invoice_id]))
    #                 counterpart_aml_dict.update({'currency_id': currency_id})
    #                 counterpart_aml = aml_obj.create(counterpart_aml_dict)
    #                 counterpart_aml_list[payment_invoice_id.invoice_id.id] = counterpart_aml
    #         if debit > total_reconcile_amount:
    #             remaining_reconcile_amount = debit - total_reconcile_amount
    #             separate_amount_currency = amount_currency
    #             if amount_currency and debit:
    #                 separate_amount_currency = amount_currency - total_separate_amount_currency
    #             counterpart_aml_dict = self._get_shared_move_line_vals(remaining_reconcile_amount, credit, separate_amount_currency, move.id, False)
    #             counterpart_aml_dict.update(self._get_counterpart_move_line_vals(self.invoice_ids))
    #             counterpart_aml_dict.update({'currency_id': currency_id})
    #             counterpart_aml = aml_obj.create(counterpart_aml_dict)
    #     else:
    #         counterpart_aml_dict = self._get_shared_move_line_vals(debit, credit, amount_currency, move.id, False)
    #         counterpart_aml_dict.update(self._get_counterpart_move_line_vals(self.invoice_ids))
    #         counterpart_aml_dict.update({'currency_id': currency_id})
    #         counterpart_aml = aml_obj.create(counterpart_aml_dict)
    #
    #     #Reconcile with the invoices
    #     if self.payment_difference_handling == 'reconcile' and self.payment_difference and not self.payment_invoice_ids:
    #         writeoff_line = self._get_shared_move_line_vals(0, 0, 0, move.id, False)
    #         debit_wo, credit_wo, amount_currency_wo, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(self.payment_difference, self.currency_id, self.company_id.currency_id)
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
    #     if self.payment_invoice_ids and self.payment_type in ['inbound', 'outbound']:
    #         invoice_ids = []
    #         for counterpart_aml_list_itr in counterpart_aml_list.keys():
    #             invoice_obj = self.env['account.invoice'].browse([counterpart_aml_list_itr])
    #             invoice_ids.append(counterpart_aml_list_itr)
    #             invoice_obj.register_payment(counterpart_aml_list[counterpart_aml_list_itr])
    #         self.invoice_ids = [(6, 0, invoice_ids)]
    #     else:
    #         self.invoice_ids.register_payment(counterpart_aml)
    #
    #     return move

    def _create_payment_entry(self, amount):
        """ Create a journal entry corresponding to a payment, if the payment references invoice(s) they are reconciled.
                    Return the journal entry.
                """
        aml_obj = self.env['account.move.line'].with_context(
            check_move_validity=False)
        # debit, credit, amount_currency, currency_id = aml_obj.with_context(
        #     date=self.payment_date)._compute_amount_fields(amount, self.currency_id, self.company_id.currency_id)
        # custom code by sitaram solutions start
        debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date,
                                                                           manual_rate=self.manual_currency_exchange_rate,
                                                                           active_manual_currency=self.apply_manual_currency_exchange, )._compute_amount_fields(
            amount, self.currency_id, self.company_id.currency_id)
        # custom code by sitaram solutions end
        move = self.env['account.move'].create(self._get_move_vals())
        counterpart_aml_list = {}
        # Write line corresponding to invoice payment
        if self.payment_invoice_ids and self.payment_type == 'inbound':
            total_reconcile_amount = 0.00
            total_separate_amount_currency = 0.00
            for payment_invoice_id in self.payment_invoice_ids:
                if payment_invoice_id.reconcile_amount > 0:
                    separate_amount_currency = amount_currency
                    reconcile_amount = payment_invoice_id.reconcile_amount
                    if amount_currency and credit:
                        reconcile_amount = (
                            payment_invoice_id.reconcile_amount * credit) / amount_currency
                        separate_amount_currency = -payment_invoice_id.reconcile_amount
                        reconcile_amount = -reconcile_amount
                    total_reconcile_amount += reconcile_amount
                    total_separate_amount_currency += separate_amount_currency
                    counterpart_aml_dict = self._get_shared_move_line_vals(debit, reconcile_amount,
                                                                           separate_amount_currency, move.id, False)
                    counterpart_aml_dict.update(
                        self._get_counterpart_move_line_vals([payment_invoice_id.invoice_id]))
                    counterpart_aml_dict.update({'currency_id': currency_id})
                    counterpart_aml = aml_obj.create(counterpart_aml_dict)
                    counterpart_aml_list[payment_invoice_id.invoice_id.id] = counterpart_aml
            if credit > round(total_reconcile_amount, 5):
                remaining_reconcile_amount = credit - total_reconcile_amount
                separate_amount_currency = amount_currency
                if amount_currency and credit:
                    separate_amount_currency = amount_currency - total_separate_amount_currency
                counterpart_aml_dict = self._get_shared_move_line_vals(debit, remaining_reconcile_amount,
                                                                       separate_amount_currency, move.id, False)
                counterpart_aml_dict.update(
                    self._get_counterpart_move_line_vals(self.invoice_ids))
                counterpart_aml_dict.update({'currency_id': currency_id})
                counterpart_aml = aml_obj.create(counterpart_aml_dict)
        elif self.payment_invoice_ids and self.payment_type == 'outbound':
            total_reconcile_amount = 0.00
            total_separate_amount_currency = 0.00
            for payment_invoice_id in self.payment_invoice_ids:
                if payment_invoice_id.reconcile_amount > 0:
                    separate_amount_currency = amount_currency
                    reconcile_amount = payment_invoice_id.reconcile_amount
                    if amount_currency and debit:
                        reconcile_amount = (
                            payment_invoice_id.reconcile_amount * debit) / amount_currency
                        separate_amount_currency = payment_invoice_id.reconcile_amount
                    total_reconcile_amount += reconcile_amount
                    total_separate_amount_currency += separate_amount_currency
                    counterpart_aml_dict = self._get_shared_move_line_vals(reconcile_amount, credit,
                                                                           separate_amount_currency, move.id, False)
                    counterpart_aml_dict.update(
                        self._get_counterpart_move_line_vals([payment_invoice_id.invoice_id]))
                    counterpart_aml_dict.update({'currency_id': currency_id})
                    counterpart_aml = aml_obj.create(counterpart_aml_dict)
                    counterpart_aml_list[payment_invoice_id.invoice_id.id] = counterpart_aml
            if debit > round(total_reconcile_amount, 5):
                remaining_reconcile_amount = debit - total_reconcile_amount
                separate_amount_currency = amount_currency
                if amount_currency and debit:
                    separate_amount_currency = amount_currency - total_separate_amount_currency
                counterpart_aml_dict = self._get_shared_move_line_vals(remaining_reconcile_amount, credit,
                                                                       separate_amount_currency, move.id, False)
                counterpart_aml_dict.update(
                    self._get_counterpart_move_line_vals(self.invoice_ids))
                counterpart_aml_dict.update({'currency_id': currency_id})
                counterpart_aml = aml_obj.create(counterpart_aml_dict)
        else:
            counterpart_aml_dict = self._get_shared_move_line_vals(
                debit, credit, amount_currency, move.id, False)
            counterpart_aml_dict.update(
                self._get_counterpart_move_line_vals(self.invoice_ids))
            counterpart_aml_dict.update({'currency_id': currency_id})
            counterpart_aml = aml_obj.create(counterpart_aml_dict)

        # Reconcile with the invoices
        if self.payment_difference_handling == 'reconcile' and self.payment_difference and not self.payment_invoice_ids:
            writeoff_line = self._get_shared_move_line_vals(
                0, 0, 0, move.id, False)
            debit_wo, credit_wo, amount_currency_wo, currency_id = aml_obj.with_context(
                date=self.payment_date)._compute_amount_fields(self.payment_difference, self.currency_id,
                                                               self.company_id.currency_id)
            writeoff_line['name'] = self.writeoff_label
            writeoff_line['account_id'] = self.writeoff_account_id.id
            writeoff_line['debit'] = debit_wo
            writeoff_line['credit'] = credit_wo
            writeoff_line['amount_currency'] = amount_currency_wo
            writeoff_line['currency_id'] = currency_id
            writeoff_line = aml_obj.create(writeoff_line)
            if counterpart_aml['debit'] or (writeoff_line['credit'] and not counterpart_aml['credit']):
                counterpart_aml['debit'] += credit_wo - debit_wo
            if counterpart_aml['credit'] or (writeoff_line['debit'] and not counterpart_aml['debit']):
                counterpart_aml['credit'] += debit_wo - credit_wo
            counterpart_aml['amount_currency'] -= amount_currency_wo

        # Write counterpart lines
        if not self.currency_id.is_zero(self.amount):
            if not self.currency_id != self.company_id.currency_id:
                amount_currency = 0

            if self.bank_charge_amount and self.bank_charge_account_id:
                debit_bc, credit_bc, amount_currency_bc, currency_id_bc = aml_obj.with_context(
                    date=self.payment_date, manual_rate=self.manual_currency_exchange_rate, active_manual_currency=self.apply_manual_currency_exchange)._compute_amount_fields(self.bank_charge_amount, self.currency_id, self.company_id.currency_id)
                if credit:
                    if debit_bc:
                        credit -= debit_bc or credit_bc
                    if credit_bc:
                        credit += credit_bc or debit_bc
                if debit:
                    if debit_bc:
                        debit += debit_bc or credit_bc
                    if credit_bc:
                        debit -= credit_bc or debit_bc
                if amount_currency:
                    amount_currency += amount_currency_bc or 0.0
            liquidity_aml_dict = self._get_shared_move_line_vals(
                credit, debit, -amount_currency, move.id, False)
            if amount:
                amount -= self.bank_charge_amount
            liquidity_aml_dict.update(
                self._get_liquidity_move_line_vals(-amount))
            aml_obj.create(liquidity_aml_dict)

        if self.bank_charge_amount:
            if not self.bank_charge_account_id:
                raise UserError(_('Please select bank charge account!'))
            self._prepare_bank_charge_gain_loss_entry(
                move, debit_bc, credit_bc, amount_currency_bc, currency_id_bc)

        # validate the payment
        if not self.journal_id.post_at_bank_rec:
            m_credit = round(
                sum(m_line.credit for m_line in move.line_ids.filtered(lambda x: x.credit)), 5)
            m_debit = round(
                sum(m_line.debit for m_line in move.line_ids.filtered(lambda x: x.debit)), 5)
            line_credit = move.line_ids.filtered(lambda x: x.credit)
            line_debit = move.line_ids.filtered(lambda x: x.debit)
            if self.payment_type == 'inbound' and line_credit:
                if m_credit > m_debit:
                    line_credit[0].credit -= m_credit - m_debit
                elif m_debit > m_credit:
                    line_credit[0].credit += m_debit - m_credit
            if self.payment_type == 'outbound' and line_debit:
                if m_credit > m_debit:
                    line_debit[0].debit += m_credit - m_debit
                elif m_debit > m_credit:
                    line_debit[0].debit -= m_debit - m_credit
            move.post()

        # reconcile the invoice receivable/payable line(s) with the payment
        if self.payment_invoice_ids and self.payment_type in ['inbound', 'outbound']:
            invoice_ids = []
            for counterpart_aml_list_itr in counterpart_aml_list.keys():
                invoice_obj = self.env['account.invoice'].browse(
                    [counterpart_aml_list_itr])
                invoice_ids.append(counterpart_aml_list_itr)
                invoice_obj.register_payment(
                    counterpart_aml_list[counterpart_aml_list_itr])
            self.invoice_ids = [(6, 0, invoice_ids)]
        else:
            self.invoice_ids.register_payment(counterpart_aml)

        return move

    def _prepare_bank_charge_gain_loss_entry(self, move, debit_bc, credit_bc, amount_currency_bc, currency_id_bc):
        aml_obj = self.env['account.move.line'].with_context(
            check_move_validity=False)
        partner_id = False
        if self.payment_type in ('inbound', 'outbound'):
            partner_id = self.env['res.partner']._find_accounting_partner(
                self.partner_id).id
        account_id = self.bank_charge_account_id.id
        bank_entry_dict = {
            'account_id': account_id,
            'partner_id': partner_id or False,
            'company_id': self.company_id.id,
            'amount_currency': amount_currency_bc or False,
            'currency_id': currency_id_bc,
            'name': self._get_counterpart_move_line_vals(self.invoice_ids).get('name'),
            'payment_id': self.id,
            'move_id': move.id
        }
        if debit_bc:
            bank_entry_dict['debit'] = debit_bc
        if credit_bc:
            bank_entry_dict['credit'] = credit_bc
        aml_obj.create(bank_entry_dict)
        # move.line_ids = [(0, 0, bank_entry_dict)]


# ADD by kinjal - V1.0.2.3 - V1.0.2.4
class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.multi
    def _update_check(self):
        """ Raise Warning to cause rollback if the move is posted, some entries are reconciled or the move is older than the lock date"""
        move_ids = set()
        for line in self:
            err_msg = _('Move name (id): %s (%s)') % (
                line.move_id.name, str(line.move_id.id))
            if line.move_id.state != 'draft':
                raise UserError(
                    _('You cannot do this modification on a posted journal entry, you can just change some non legal fields. You must revert the journal entry to cancel it.\n%s.') % err_msg)
            if line.reconciled and not (line.debit == 0 and line.credit == 0):
                if line.invoice_id:
                    raise UserError(
                        _('You cannot do this modification on a reconciled entry. You can just change some non legal fields or you must unreconcile first.\n%s.') % err_msg)
                else:
                    line.remove_move_reconcile()
            if line.move_id.id not in move_ids:
                move_ids.add(line.move_id.id)
        self.env['account.move'].browse(list(move_ids))._check_lock_date()
        return True

    @api.multi
    def unlink(self):
        self._update_check()
        move_ids = set()
        for line in self:
            if line.move_id.id not in move_ids:
                move_ids.add(line.move_id.id)
        recon = self.env['account.partial.reconcile'].search(['|', ('debit_move_id', 'in', self.ids), ('credit_move_id', 'in', self.ids)])
        if recon:
            recon.unlink()
        result = super(AccountMoveLine, self).unlink()
        if self._context.get('check_move_validity', True) and move_ids:
            self.env['account.move'].browse(list(move_ids))._post_validate()
        return result
