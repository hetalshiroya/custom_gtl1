from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)

class DispatchJob(models.Model):

    _name = 'freight.dispatch.job'
    _description = 'Dispatch Job'
    _order = 'create_date desc, write_date desc'

    _inherit = ['mail.thread', 'mail.activity.mixin']

    dispatch_job_status = fields.Selection([('01', 'New'), ('02', 'Done'), ('04', 'Posted'), ('03', 'Cancelled'),], string="Dispatch Job Status", default="01",
                                      copy=False, track_visibility='onchange', store=True)
    dispatch_job_no = fields.Char(string='Dispatch Job No', copy=False, readonly=True, index=True)
    booking_ref = fields.Many2one('freight.booking', string='Booking Job Ref', track_visibility='onchange',
                                        copy=False, index=True)
    type = fields.Selection([('job', 'Job'), ('non', 'Non-Job')], string="Job Type", default="job",
                                           copy=False, track_visibility='onchange', store=True)
    task = fields.Selection([('01', 'Collect Document'), ('02', 'Deliver Document'), ('03', 'Others')], string="Task Type", default="01",
                                           copy=False, track_visibility='onchange', store=True)
    others = fields.Char(string='Others - Description', copy=False, track_visibility='onchange')
    deadline = fields.Date(string='Completion Deadline', copy=False, default=datetime.now().date(), track_visibility='onchange')
    received_date = fields.Date(string='Received Date', copy=False, default=datetime.now().date(), track_visibility='onchange')
    completion_date = fields.Date(string='Completion Date', copy=False, default=datetime.now().date(), track_visibility='onchange')
    customer_received_date = fields.Date(string='Customer Received Date', copy=False, track_visibility='onchange')
    customer_id = fields.Many2one('res.partner', string='Customer/Carrier', track_visibility='onchange')
    address = fields.Text(string='Address', track_visibility='onchange')
    dispatcher_id = fields.Many2one('res.partner', string='Dispatcher', track_visibility='onchange')
    verify_by = fields.Many2one('res.users', string='Verified By', track_visibility='onchange')
    post_journal = fields.Boolean(string='Post to Journal', track_visibility='onchange', default=False, copy=False)
    amount = fields.Monetary(string='Amount to Post', default=1)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True, store=True,
                                  default=lambda self: self._get_currency())
    request_by = fields.Many2one('res.users', string='Requested By', track_visibility='onchange',
                                 default=lambda self: self.env.user)
    note = fields.Text(string='Remark', track_visibility='onchange')
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, readonly=1,
                                 default=lambda self: self.env.user.company_id.id)
    move_id = fields.Many2one('account.move', 'Journal Entry', copy=False)
    account_date = fields.Date("Accounting Date", help="Effective date for accounting entries", copy=False,
                               default=fields.Date.context_today)
    property_account_expense_id = fields.Many2one('account.account', string="COG Account (DR)", domain=[('deprecated', '=', False)],
                                                  help="COG Account")
    account_id = fields.Many2one('account.account', string='Accrual Account (CR)', domain=[('deprecated', '=', False)],
                                 help="The Accrual Current Liabilities account")

    @api.model
    def _get_currency(self):
        return self.env.user.company_id.currency_id.id

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



    @api.model
    def create(self, vals):
        vals['dispatch_job_no'] = self.env['ir.sequence'].next_by_code('dj')
        res = super(DispatchJob, self).create(vals)
        return res


    @api.onchange('customer_id')
    def onchange_customer_id(self):
        adr = ''
        if self.customer_id.street:
            adr += self.customer_id.street
        if self.customer_id.street2:
            adr += ' ' + self.customer_id.street2
        if self.customer_id.zip:
            adr += ' ' + self.customer_id.zip
        if self.customer_id.city:
            adr += ' ' + self.customer_id.city
        if self.customer_id.state_id:
            adr += ', ' + self.customer_id.state_id.name + "\n"
        if self.customer_id.phone:
            adr += 'Phone: ' + self.customer_id.phone
        elif self.customer_id.mobile:
            adr += '. Mobile: ' + self.customer_id.mobile
        self.address = adr


    @api.multi
    def name_get(self):
        result = []
        for dj in self:
            name = str(dj.dispatch_job_no)
        result.append((dj.id, name))
        return result


    @api.onchange('customer_received_date')
    def _onchange_customer_received_date(self):
        print('_onchange_customer_received_date')
        if self.customer_received_date:
            self.dispatch_job_status = '02'


    @api.multi
    def action_cancel_dispatch_job(self):
        for dj in self:
            dj.move_id.unlink()
            dj.dispatch_job_status = '03'


    @api.multi
    def action_post_journal(self):
        #refer to action_move_line_create (account_voucher.py)
        #create the journal entries for each of them
        print('action_post_journal')
        for dispatch_job in self:
            local_context = dict(self._context, force_company=dispatch_job.company_id.id)
            if dispatch_job.move_id:
                continue
            company_currency = dispatch_job.company_id.currency_id.id
            current_currency = dispatch_job.currency_id.id or company_currency
            # we select the context to use accordingly if it's a multicurrency case or not
            # But for the operations made by _convert, we always need to give the date in the context
            ctx = local_context.copy()
            ctx['date'] = dispatch_job.account_date
            ctx['check_move_validity'] = False
            # Create the account move record.
            move = self.env['account.move'].create(dispatch_job.account_move_get())
            # Get the name of the account_move just created
            # Create the first line of the dispatch_job
            move_line = self.env['account.move.line'].with_context(ctx).create(
                dispatch_job.with_context(ctx).first_move_line_get(move.id, company_currency, current_currency))
            line_total = move_line.debit - move_line.credit
            #line_total = line_total + dispatch_job._convert(dispatch_job.tax_amount)
            # Create one move line per dispatch_job line where amount is not 0.0
            line_total = dispatch_job.with_context(ctx).dispatch_job_move_line_create(line_total, move.id, company_currency,
                                                                           current_currency)
            #Do not create payment
            #payment_id = self.env['account.payment'].create(dispatch_job.pay_now_payment_create())
            #payment_id.post()

            # Reconcile the receipt with the payment
            # lines_to_reconcile = (payment_id.move_line_ids + move.line_ids).filtered(
            #     lambda l: l.account_id == dispatch_job.account_id)
            # lines_to_reconcile.reconcile()
            # We post the voucher.
            dispatch_job.write({
                'move_id': move.id,
                'dispatch_job_status': '04',
            })
            move.post()

        return True


    @api.multi
    def account_move_get(self):
        print('account_move_get')
        ref = ''
        if self.dispatch_job_no:
            name = self.dispatch_job_no
        elif self.payment_journal_id.sequence_id:
            if not self.payment_journal_id.sequence_id.active:
                raise UserError(_('Please activate the sequence of selected journal !'))
            name = self.payment_journal_id.sequence_id.with_context(ir_sequence_date=self.date).next_by_id()
        else:
            raise UserError(_('Please define a sequence on the journal.'))
        if self.booking_ref:
            ref = self.booking_ref.booking_no
        else:
            ref = self.dispatch_job_no
        move = {
            'name': name,
            'journal_id': self.payment_journal_id.id,
            #'narration': self.narration,
            'date': self.account_date,
            'ref': ref,
        }
        return move


    # @api.model
    # def _default_journal(self):
    #     company_id = self._context.get('company_id', self.env.user.company_id.id)
    #     domain = [
    #         ('type', '=', 'purchase'),
    #         ('company_id', '=', company_id),
    #     ]
    #     return self.env['account.journal'].search(domain, limit=1)

    # @api.model
    # def _default_journal(self):
    #     print('payment_journal_id.id=' + str(self.payment_journal_id.id))
    #     return self.payment_journal_id


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
            'name': self.dispatch_job_no or '/',
            'debit': debit,
            'credit': credit,
            'account_id': self.account_id.id,
           # 'account_id': self.property_account_expense_id.id,
            'move_id': move_id,
            'journal_id': self.payment_journal_id.id,
            'partner_id': self.dispatcher_id.commercial_partner_id.id,
            #'currency_id': company_currency != current_currency and current_currency or False,
            #'amount_currency': (sign * abs(self.amount)  # amount < 0 for refunds
            #        if company_currency != current_currency else 0.0),
            'date': self.account_date,
            'date_maturity': self.account_date,
        }
        return move_line

    @api.multi
    def dispatch_job_move_line_create(self, line_total, move_id, company_currency, current_currency):
        print('dispatch_job_move_line_create')
        #Important
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
        #tax_calculation_rounding_method = self.env.user.company_id.tax_calculation_rounding_method
        #tax_lines_vals = []
        for line in self:
            # create one move line per voucher line where amount is not 0.0
            #line_subtotal = line.price_subtotal
            # convert the amount set on the voucher line into the currency of the voucher's company
            amount = self.amount
            move_line = {
                'journal_id': self.payment_journal_id.id,
                'name': line.dispatch_job_no or '/',
                #'account_id': line.account_id.id,
                'account_id': self.property_account_expense_id.id,
                'move_id': move_id,
                'quantity': 1,
                #'product_id': line.product_id.id,
                'partner_id': self.dispatcher_id.commercial_partner_id.id,
                #'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
                #'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
                'credit': 0.0,
                'debit': abs(amount),
                'date': self.account_date,
                #'tax_ids': [(4, t.id) for t in line.tax_ids],
                #'amount_currency': amount,
                'currency_id': company_currency,
                'payment_id': self._context.get('payment_id'),
            }
            self.env['account.move.line'].create(move_line)
        return amount


    # @api.multi
    # def post(self):
    #     """ Create the journal items for the payment and update the payment's state to 'posted'.
    #         A journal entry is created containing an item in the source liquidity account (selected journal's default_debit or default_credit)
    #         and another in the destination reconcilable account (see _compute_destination_account_id).
    #         If invoice_ids is not empty, there will be one reconcilable move line per invoice to reconcile with.
    #         If the payment is a transfer, a second journal entry is created in the destination journal to receive money from the transfer account.
    #     """
    #     for rec in self:
    #
    #         if rec.state != 'draft':
    #             raise UserError(_("Only a draft payment can be posted."))
    #
    #         if any(inv.state != 'open' for inv in rec.invoice_ids):
    #             raise ValidationError(_("The payment cannot be processed because the invoice is not open!"))
    #
    #         # keep the name in case of a payment reset to draft
    #         if not rec.name:
    #             # Use the right sequence to set the name
    #             if rec.payment_type == 'transfer':
    #                 sequence_code = 'account.payment.transfer'
    #             else:
    #                 if rec.partner_type == 'customer':
    #                     if rec.payment_type == 'inbound':
    #                         sequence_code = 'account.payment.customer.invoice'
    #                     if rec.payment_type == 'outbound':
    #                         sequence_code = 'account.payment.customer.refund'
    #                 if rec.partner_type == 'supplier':
    #                     if rec.payment_type == 'inbound':
    #                         sequence_code = 'account.payment.supplier.refund'
    #                     if rec.payment_type == 'outbound':
    #                         sequence_code = 'account.payment.supplier.invoice'
    #             rec.name = self.env['ir.sequence'].with_context(ir_sequence_date=rec.payment_date).next_by_code(
    #                 sequence_code)
    #             if not rec.name and rec.payment_type != 'transfer':
    #                 raise UserError(_("You have to define a sequence for %s in your company.") % (sequence_code,))
    #
    #         # Create the journal entry
    #         amount = rec.amount * (rec.payment_type in ('outbound', 'transfer') and 1 or -1)
    #         move = rec._create_payment_entry(amount)
    #
    #         # In case of a transfer, the first journal entry created debited the source liquidity account and credited
    #         # the transfer account. Now we debit the transfer account and credit the destination liquidity account.
    #         if rec.payment_type == 'transfer':
    #             transfer_credit_aml = move.line_ids.filtered(
    #                 lambda r: r.account_id == rec.company_id.transfer_account_id)
    #             transfer_debit_aml = rec._create_transfer_entry(amount)
    #             (transfer_credit_aml + transfer_debit_aml).reconcile()
    #
    #         rec.write({'state': 'posted', 'move_name': move.name})
    #     return True

    @api.multi
    def pay_now_payment_create(self):
        print('pay_now_payment_create')
        payment_methods = self.payment_journal_id.outbound_payment_method_ids
        payment_type = 'outbound'
        partner_type = 'supplier'
        sequence_code = 'account.payment.supplier.invoice'
        company_currency = self.payment_journal_id.company_id.currency_id.id
        return {
            'payment_type': payment_type,
            'payment_method_id': payment_methods and payment_methods[0].id or False,
            'partner_type': partner_type,
            'partner_id': self.dispatcher_id.commercial_partner_id.id,
            'amount': self.amount,
            'currency_id': company_currency,
            'payment_date': self.account_date,
            #'journal_id': self.journal_id.id,
            'journal_id': self.payment_journal_id.id,
            'company_id': self.company_id.id,
            'communication': self.dispatch_job_no,
        }