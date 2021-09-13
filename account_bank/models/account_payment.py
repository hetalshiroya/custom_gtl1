# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
import pytz


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    bank_date = fields.Date(string='Bank Date')

    @api.multi
    def cancel(self):
        line_to_del = []
        for rec in self:
            for mv_line in rec.move_line_ids:
                line_to_del.append(mv_line.statement_line_id) if mv_line.statement_line_id else ''
        res = super(AccountPayment, self).cancel()
        for line in line_to_del:
            stmt_id = line.statement_id
            line.unlink()
            stmt_id.balance_end_real = stmt_id.balance_end
        return res

    # Bulk Reconciliation Process
    @api.multi
    def action_reconcile(self, starting_bal, payment_ids):
        jr_id = pay_type = stmt_id = stmt_trans_id = company_id = mv_line = dest_mv_line = False
        ABS = self.env['account.bank.statement']
        for pay_id in payment_ids:
            pay_br = self.browse(pay_id)
            pay_type = pay_br.payment_type if not pay_type else pay_type
            if (pay_type != pay_br.payment_type):
                raise ValidationError(_('Warning! \n You are not allowed to reconcile Internal transfer with other payment types'))
            if pay_br.state != 'posted':
                raise ValidationError(_('Warning! \n You are not allowed to reconcile already reconciled entries'))
            company_id = pay_br.company_id.id if not company_id else company_id
            jr_id = pay_br.journal_id.id if not jr_id else jr_id
            if (jr_id != pay_br.journal_id.id) or (company_id != pay_br.company_id.id):
                raise ValidationError(_('Warning! \n Payment Journal, Company should be same for the selected payments'))
            if not pay_br.bank_date:
                raise UserError(_('Warning! \n Kindly Provide Bank Date To Reconcile'))
        for payment_id in payment_ids:
            payment_br = self.browse(payment_id)
            curr_time = fields.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if self.env.user.tz:
                tz = pytz.timezone(self.env.user.tz)
                curr_time = pytz.utc.localize(fields.datetime.now()).astimezone(tz).strftime('%Y-%m-%d %H:%M:%S')
            for line in payment_br.move_line_ids:
                if (line.account_id.user_type_id.name == 'Bank and Cash') and (line.journal_id.id == payment_br.journal_id.id):
                    mv_line = line
            if not mv_line:
                raise ValidationError(_('Warning! \n Bank and Cash account is missing in Move lines'))
            ref_val = str(payment_br.journal_id.name) + ' : ' + curr_time
            amount = -(payment_br.amount) if (payment_br.partner_type == 'supplier') or (payment_br.payment_type == 'transfer') else payment_br.amount
            if not stmt_id:
                st_values = {
                    'is_from_payment': True,
                    'journal_id': payment_br.journal_id.id,
                    'user_id': self.env.user.id or False,
                    'name': ref_val or '',
                    'balance_start': starting_bal
                }
                stmt_id = ABS.create(st_values)
            payment_br.action_reconcile_line(mv_line, stmt_id.id, amount)
            stmt_id.balance_end_real = stmt_id.balance_end
            stmt_id.check_confirm_bank()
            if payment_br.destination_journal_id:
                for dest_line in payment_br.move_line_ids:
                    if (dest_line.account_id.user_type_id.name == 'Bank and Cash') and (dest_line.journal_id.id == payment_br.destination_journal_id.id):
                        dest_mv_line = dest_line
                if not dest_mv_line:
                    raise ValidationError(_('Warning! \n Bank and Cash account is missing in Move lines'))
                dest_starting_bal = ABS._get_opening_balance(payment_br.destination_journal_id.id)
                amount = payment_br.amount
                dest_ref_val = str(payment_br.destination_journal_id.name) + ' : ' + curr_time
                if not stmt_trans_id:
                    dest_st_values = {
                        'is_from_payment': True,
                        'journal_id': payment_br.destination_journal_id.id,
                        'user_id': self.env.user.id or False,
                        'name': dest_ref_val or '',
                        'balance_start': dest_starting_bal
                    }
                    stmt_trans_id = ABS.create(dest_st_values)
                payment_br.action_reconcile_line(dest_mv_line, stmt_trans_id.id, amount)
                stmt_trans_id.balance_end_real = stmt_trans_id.balance_end
                stmt_trans_id.check_confirm_bank()
        return True

    @api.one
    def action_reconcile_line(self, mv_line, statement_id, amount):
        ABSL = self.env['account.bank.statement.line']
        st_line_values = {
            'statement_id': statement_id,
            'payment_id': self.id,
            'date': self.bank_date or False,
            'name': self.communication or self.name,
            'partner_id': self.partner_id.id,
            'ref': self.name or False,
            'amount': amount
        }
        stmt_line_id = ABSL.create(st_line_values)
        mv_line.update({
            'statement_id': statement_id,
            'statement_line_id': stmt_line_id.id,
        })
        self.state = 'reconciled'
        return True
