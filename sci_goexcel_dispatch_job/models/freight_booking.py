from odoo import api, fields, models,exceptions, _
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)


class FreightBooking(models.Model):
    _inherit = "freight.booking"

    booking_dispatch_job_count = fields.Integer(string='Dispatch Job Count', compute='_get_dispatch_job_count', readonly=True)
    #sq_description = fields.Char(string='SQ Description', track_visibility='onchange')
    post_journal = fields.Boolean(string='Post to Journal', track_visibility='onchange', default=False, copy=False)
    amount = fields.Monetary(string='Amount to Post', default=5)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True, store=True,
                                  default=lambda self: self._get_currency())
    move_id = fields.Many2one('account.move', 'Journal Entry', copy=False)
    account_date = fields.Date("Accounting Date", help="Effective date for accounting entries", copy=False,
                               default=fields.Date.context_today)
    property_account_expense_id = fields.Many2one('account.account', string="COG Account (DR)",
                                                  domain=[('deprecated', '=', False)],
                                                  help="COG Account")
    account_id = fields.Many2one('account.account', string='Accrual Account (CR)', domain=[('deprecated', '=', False)],
                                 help="The Accrual Current Liabilities account")

    @api.model
    def _get_currency(self):
        return self.env.user.company_id.currency_id.id

    def _get_dispatch_job_count(self):
        for operation in self:
            djs = self.env['freight.dispatch.job'].search([
                ('booking_ref', '=', operation.id),
            ])

        self.update({
            'booking_dispatch_job_count': len(djs),
        })


    @api.multi
    def action_copy_to_dispatch_job(self):
        dj_obj = self.env['freight.dispatch.job']

        dj_val = {
            'dispatch_job_status': '01',
            'booking_ref': self.id,
            'customer_id': self.customer_name.id or False,
            'type': 'job',
        }

        dj = dj_obj.create(dj_val)

    @api.model
    def _default_payment_journal(self):
        company_id = self._context.get('company_id', self.env.user.company_id.id)
        domain = [
            ('type', 'in', ('bank', 'cash')),
            ('company_id', '=', company_id),
        ]
        return self.env['account.journal'].search(domain, limit=1)

    payment_journal_id = fields.Many2one('account.journal', string='Bank Journal',
                                         domain="[('type', 'in', ['cash', 'bank'])]", default=_default_payment_journal)

    @api.multi
    def action_post_journal(self):
        # refer to action_move_line_create (account_voucher.py)
        # create the journal entries for each of them
        print('action_post_journal')
        for freight_job in self:
            local_context = dict(self._context, force_company=freight_job.company_id.id)
            if freight_job.move_id:
                continue
            company_currency = freight_job.company_id.currency_id.id
            current_currency = freight_job.currency_id.id or company_currency
            # we select the context to use accordingly if it's a multicurrency case or not
            # But for the operations made by _convert, we always need to give the date in the context
            ctx = local_context.copy()
            ctx['date'] = freight_job.account_date
            ctx['check_move_validity'] = False
            # Create the account move record.
            move = self.env['account.move'].create(freight_job.account_move_get())
            # Get the name of the account_move just created
            # Create the first line of the freight_job
            move_line = self.env['account.move.line'].with_context(ctx).create(
                freight_job.with_context(ctx).first_move_line_get(move.id, company_currency, current_currency))
            line_total = move_line.debit - move_line.credit
            # line_total = line_total + freight_job._convert(freight_job.tax_amount)
            # Create one move line per freight_job line where amount is not 0.0
            line_total = freight_job.with_context(ctx).freight_job_move_line_create(line_total, move.id,
                                                                                      company_currency,
                                                                                      current_currency)
            freight_job.write({
                'move_id': move.id,
            })
            move.post()

        return True


    @api.multi
    def account_move_get(self):
        print('account_move_get')
        ref = ''
        if self.booking_no:
            name = self.booking_no
        elif self.payment_journal_id.sequence_id:
            if not self.payment_journal_id.sequence_id.active:
                raise UserError(_('Please activate the sequence of selected journal !'))
            name = self.payment_journal_id.sequence_id.with_context(ir_sequence_date=self.date).next_by_id()
        else:
            raise UserError(_('Please define a sequence on the journal.'))
        if self.booking_no:
            ref = self.booking_no
        move = {
            'name': name,
            'journal_id': self.payment_journal_id.id,
            # 'narration': self.narration,
            'date': self.account_date,
            'ref': ref,
        }
        return move

    journal_id = fields.Many2one('account.journal', 'Journal', readonly=True, states={'draft': [('readonly', False)]})

    @api.multi
    def first_move_line_get(self, move_id, company_currency, current_currency):
        print('first_move_line_get')
        debit = credit = 0.0
        credit = self.amount
        if debit < 0.0: debit = 0.0
        if credit < 0.0: credit = 0.0
        sign = debit - credit < 0 and -1 or 1
        # set the first line of the voucher
        move_line = {
            'name': self.booking_no or '/',
            'debit': debit,
            'credit': credit,
            'account_id': self.account_id.id,
            # 'account_id': self.property_account_expense_id.id,
            'move_id': move_id,
            'journal_id': self.payment_journal_id.id,
            'partner_id': self.owner.commercial_partner_id.id,
            # 'currency_id': company_currency != current_currency and current_currency or False,
            # 'amount_currency': (sign * abs(self.amount)  # amount < 0 for refunds
            #        if company_currency != current_currency else 0.0),
            'date': self.account_date,
            'date_maturity': self.account_date,
        }
        return move_line

    @api.multi
    def freight_job_move_line_create(self, line_total, move_id, company_currency, current_currency):
        print('freight_job_move_line_create')
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
        for line in self:
            # create one move line per voucher line where amount is not 0.0
            # line_subtotal = line.price_subtotal
            # convert the amount set on the voucher line into the currency of the voucher's company
            amount = self.amount
            move_line = {
                'journal_id': self.payment_journal_id.id,
                'name': line.booking_no or '/',
                # 'account_id': line.account_id.id,
                'account_id': self.property_account_expense_id.id,
                'move_id': move_id,
                'quantity': 1,
                # 'product_id': line.product_id.id,
                'partner_id': self.owner.commercial_partner_id.id,
                # 'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
                # 'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
                'credit': 0.0,
                'debit': abs(amount),
                'date': self.account_date,
                # 'tax_ids': [(4, t.id) for t in line.tax_ids],
                # 'amount_currency': amount,
                'currency_id': company_currency,
                'payment_id': self._context.get('payment_id'),
            }
            self.env['account.move.line'].create(move_line)
        return amount
