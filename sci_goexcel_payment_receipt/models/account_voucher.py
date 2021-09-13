from odoo import api, models, _
import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import UserError, ValidationError


class AccountVoucher(models.Model):

    _inherit = 'account.voucher'

    @api.model
    def create(self, vals):
        # print('create')
        # print('name=' + str(vals.get('name')))
        # print('number=' + str(vals.get('number')))
        # print('voucher_type=' + str(vals.get('voucher_type')))
        # #if vals.get('name', 'New') == 'New':
        # if vals.get('voucher_type') == 'purchase':
        #     seq = self.env['ir.sequence']
        #     number = seq.next_by_code('pv')
        #     vals['number'] = number
        # elif vals.get('voucher_type') == 'sale':
        #     seq = self.env['ir.sequence']
        #     number = seq.next_by_code('pr')
        #     vals['number'] = number
        # print('number=' + number)

        # done by Laxicon Solution - Shivam
        if not vals.get('number') and vals.get('voucher_type') == 'sale':
            if 'company_id' in vals:
                vals['number'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('so.payment.receipts') or _('New')
            else:
                vals['number'] = self.env['ir.sequence'].next_by_code('so.payment.receipts') or _('New')
        if not vals.get('number') and vals.get('voucher_type') == 'purchase':
            if 'company_id' in vals:
                vals['number'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('po.payment.receipts') or _('New')
            else:
                vals['number'] = self.env['ir.sequence'].next_by_code('po.payment.receipts') or _('New')
        return super(AccountVoucher, self).create(vals)

    @api.multi
    def action_print_payment_voucher(self):

        data = {
            'model': self._name,
            'ids': self.ids,
            'form': self.ids,
        }
        if self.voucher_type == 'sale':
            return self.env.ref('sci_goexcel_payment_receipt.report_sr_action').report_action(self, data=data)
        else:
            print("Print AV PR Action")
            return self.env.ref('sci_goexcel_payment_receipt.report_av_pr_action').report_action(self, data=data)

    @api.multi
    def action_post_journal_entries(self):
        print('action_post_journal')
        for voucher in self:
            local_context = dict(self._context, force_company=voucher.journal_id.company_id.id)
            if voucher.move_id:
                continue
            company_currency = voucher.company_id.currency_id.id
            current_currency = voucher.currency_id.id or company_currency
            # we select the context to use accordingly if it's a multicurrency case or not
            # But for the operations made by _convert, we always need to give the date in the context
            ctx = local_context.copy()
            ctx['date'] = voucher.account_date
            ctx['check_move_validity'] = False
            # Create the account move record.
            move = self.env['account.move'].create(voucher.account_move_get())
            # Get the name of the account_move just created
            # Create the first line of the dispatch_job
            move_line = self.env['account.move.line'].with_context(ctx).create(
                voucher.with_context(ctx).first_move_line_get(move.id, company_currency, current_currency))
            line_total = move_line.debit - move_line.credit
            if voucher.voucher_type == 'sale':
                line_total = line_total - voucher._convert(voucher.tax_amount)
            elif voucher.voucher_type == 'purchase':
                line_total = line_total + voucher._convert(voucher.tax_amount)
            # line_total = line_total + dispatch_job._convert(dispatch_job.tax_amount)
            # Create one move line per dispatch_job line where amount is not 0.0
            line_total = voucher.with_context(ctx).voucher_move_line_create(line_total, move.id,
                                                                                      company_currency,
                                                                                      current_currency)
            # Do not create payment
            # payment_id = self.env['account.payment'].create(dispatch_job.pay_now_payment_create())
            # payment_id.post()

            # Reconcile the receipt with the payment
            # lines_to_reconcile = (payment_id.move_line_ids + move.line_ids).filtered(
            #     lambda l: l.account_id == dispatch_job.account_id)
            # lines_to_reconcile.reconcile()
            # We post the voucher.
            voucher.write({
                'move_id': move.id,
                'state': 'posted',
                'number': move.name
            })
            move.post()

        return True

    @api.multi
    def account_move_get(self):
        print('account_move_get')
        if self.number:
            name = self.number
        elif self.journal_id.sequence_id:
            if not self.journal_id.sequence_id.active:
                raise UserError(_('Please activate the sequence of selected journal !'))
            name = self.journal_id.sequence_id.with_context(ir_sequence_date=self.date).next_by_id()
        else:
            raise UserError(_('Please define a sequence on the journal.'))

        move = {
            'name': name,
            'journal_id': self.journal_id.id,
            'narration': self.narration,
            'date': self.account_date,
            # change by kinjal V2.0.4 - 2.0.5
            'ref': self.name,
            # 'ref': self.reference,
        }
        return move

    @api.multi
    def first_move_line_get(self, move_id, company_currency, current_currency):

        print('first_move_line_get')
        debit = credit = 0.0
        # Credit Account to the Bank Journal for purchase
        if self.voucher_type == 'purchase':
            credit = self._convert(self.amount)
            account_id = self.journal_id.default_credit_account_id.id
        # Debit to Bank Journal for sale
        elif self.voucher_type == 'sale':
            debit = self._convert(self.amount)
            account_id = self.journal_id.default_debit_account_id.id
            #account_id = self.account_id.id
            #account_id = self.journal_id.default_debit_account_id.id
        if debit < 0.0: debit = 0.0
        if credit < 0.0: credit = 0.0
        sign = debit - credit < 0 and -1 or 1
        # if self.voucher_type == 'sale':
        #     sign = -1
        print('amount=' + str(sign * abs(self.amount)))
        # set the first line of the voucher
        move_line = {
            # change by kinjal V2.0.4 - 2.0.5
            'name': self.number or '/',
            # 'name': self.name or '/',
            'debit': debit,
            'credit': credit,
            'account_id': account_id,
            'move_id': move_id,
            'journal_id': self.journal_id.id,
            'partner_id': self.partner_id.commercial_partner_id.id,
            'currency_id': company_currency != current_currency and current_currency or False,
            'amount_currency': (sign * abs(self.amount)  # amount < 0 for refunds
                                if company_currency != current_currency else 0.0),
            'date': self.account_date,
            'date_maturity': self.date_due,
        }
        return move_line


    @api.multi
    def voucher_move_line_create(self, line_total, move_id, company_currency, current_currency):
        print('voucher_move_line_create')
        # Important
        '''
        Create one account move line, on the given account move, per voucher line where amount is not 0.0.
        It returns Tuple with tot_line what is total of difference between debit and credit and
        a list of lists with ids to be reconciled with this format (total_deb_cred,list_of_lists).

        :param voucher_id: Voucher id what we are working with
        :param line_total: Amount of the first line, which correspond to the amount we should totally split among all voucher lines.
        :param move_id: Account move wher those lines will be joined.
        :param company_currency: id of currency of the company to which the voucher belong
        :param current_currency: id of currency of the voucher
        :return: Tuple build as (remaining amount not allocated on voucher lines, list of account_move_line created in this method)
        :rtype: tuple(float, list of int)
        '''
        # tax_calculation_rounding_method = self.env.user.company_id.tax_calculation_rounding_method
        # tax_lines_vals = []
        debit = credit = 0.0
        for line in self.line_ids:
            # create one move line per voucher line where amount is not 0.0
            # line_subtotal = line.price_subtotal
            # convert the amount set on the voucher line into the currency of the voucher's company
            if not line.price_subtotal:
                continue
            line_subtotal = line.price_subtotal
            # Credit to Account for sale
            if self.voucher_type == 'sale':
                line_subtotal = 1 * line.price_subtotal
                account_id = line.account_id.id
                #account_id = self.journal_id.default_debit_account_id.id
                amount = self._convert(line.price_unit * line.quantity)
                credit = abs(amount)
                #account_id = self.journal_id.default_debit_account_id.id
            # Debit to the Account for purchase
            if self.voucher_type == 'purchase':
                account_id = line.account_id.id
                amount = self._convert(line.price_unit * line.quantity)
                debit = abs(amount)

            print('credit=' + str(credit))
            print('debit=' + str(debit))
            # convert the amount set on the voucher line into the currency of the voucher's company

            move_line = {
                'journal_id': self.journal_id.id,
                'name': line.name or '/',
                'account_id': account_id,
                #'account_id': self.property_account_expense_id.id,
                'move_id': move_id,
                'quantity': 1,
                'product_id': line.product_id.id,
                'partner_id': self.partner_id.commercial_partner_id.id,
                'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
                'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
                'credit': credit,
                'debit': debit,
                'date': self.account_date,
                # 'tax_ids': [(4, t.id) for t in line.tax_ids],
                # 'amount_currency': amount,
                'amount_currency': line_subtotal if current_currency != company_currency else 0.0,
                'currency_id': company_currency != current_currency and current_currency or False,
                'payment_id': self._context.get('payment_id'),
            }
            self.env['account.move.line'].create(move_line)
        return amount


    @api.multi
    def _convert(self, amount):
        '''
        This function convert the amount given in company currency. It takes either the rate in the voucher (if the
        payment_rate_currency_id is relevant) either the rate encoded in the system.
        :param amount: float. The amount to convert
        :param voucher: id of the voucher on which we want the conversion
        :param context: to context to use for the conversion. It may contain the key 'date' set to the voucher date
            field in order to select the good rate to use.
        :return: the amount in the currency of the voucher's company
        :rtype: float
        '''
        for voucher in self:
            return voucher.currency_id._convert(amount, voucher.company_id.currency_id, voucher.company_id,
                                                voucher.account_date)
