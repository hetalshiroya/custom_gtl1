from odoo import models, api
from datetime import datetime
import dateutil.relativedelta
from datetime import timedelta, date
import calendar
from odoo.tools.misc import formatLang
import math
import logging
_logger = logging.getLogger(__name__)


class print_customer_statement(models.AbstractModel):
    _name = 'report.goexcel_customer_statement.cust_statement_template'

    @api.multi
    def get_company_info(self, o):
        if self.env.user.company_id:
            company_info = {
                    'image': self.env.user.company_id,
                    'name': self.env.user.company_id.name,
                    'street': self.env.user.company_id.street,
                    'city': str(self.env.user.company_id.city) + ' ' + str(self.env.user.company_id.zip),
                    'state': self.env.user.company_id.state_id and self.env.user.company_id.state_id.name,
                    'country': self.env.user.company_id.country_id and self.env.user.company_id.country_id.name,
            }
        return company_info

    @api.multi
    def set_amount(self, amount):
        amount = formatLang(self.env, amount)
        return amount

    def get_month_name(self, day, mon, year):
        year = str(year)
        day = str(day)
        if mon == 1:
            return day + ' - ' + 'JAN' + ' - ' + year
        elif mon == 2:
            return day + ' - ' + 'FEB' + ' - ' + year
        elif mon == 3:
            return day + ' - ' + 'MAR' + ' - ' + year
        elif mon == 4:
            return day + ' - ' + 'APR' + ' - ' + year
        elif mon == 5:
            return day + ' - ' + 'MAY' + ' - ' + year
        elif mon == 6:
            return day + ' - ' + 'JUN' + ' - ' + year
        elif mon == 7:
            return day + ' - ' + 'JUL' + ' - ' + year
        elif mon == 8:
            return day + ' - ' + 'AUG' + ' - ' + year
        elif mon == 9:
            return day + ' - ' + 'SEP' + ' - ' + year
        elif mon == 10:
            return day + ' - ' + 'OCT' + ' - ' + year
        elif mon == 11:
            return day + ' - ' + 'NOV' + ' - ' + year
        elif mon == 12:
            return day + ' - ' + 'DEC' + ' - ' + year

    def set_ageing(self, obj):
        over_date = obj.overdue_date
        d5 = con5 = False
        if obj.aging_group == 'by_month':
            d1 = over_date - dateutil.relativedelta.relativedelta(months=1)
            d1 = datetime(d1.year, d1.month, 1) + timedelta(days=calendar.monthrange(d1.year, d1.month)[1] - 1)
            d1 = d1.date()
            d2 = over_date - dateutil.relativedelta.relativedelta(months=2)
            d2 = datetime(d2.year, d2.month, 1) + timedelta(days=calendar.monthrange(d2.year, d2.month)[1] - 1)
            d2 = d2.date()
            d3 = over_date - dateutil.relativedelta.relativedelta(months=3)
            d3 = datetime(d3.year, d3.month, 1) + timedelta(days=calendar.monthrange(d3.year, d3.month)[1] - 1)
            d3 = d3.date()
            d4 = over_date - dateutil.relativedelta.relativedelta(months=4)
            d4 = datetime(d4.year, d4.month, 1) + timedelta(days=calendar.monthrange(d4.year, d4.month)[1] - 1)
            d4 = d4.date()
            d5 = over_date - dateutil.relativedelta.relativedelta(months=5)
            d5 = datetime(d5.year, d5.month, 1) + timedelta(days=calendar.monthrange(d5.year, d5.month)[1] - 1)
            d5 = d5.date()
        else:
            d1 = over_date - timedelta(days=30)
            d2 = over_date - timedelta(days=60)
            d3 = over_date - timedelta(days=90)
            d4 = over_date - timedelta(days=120)

        con1 = int(str(over_date - d1).split(' ')[0])
        con2 = int(str(over_date - d2).split(' ')[0])
        con3 = int(str(over_date - d3).split(' ')[0])
        con4 = int(str(over_date - d4).split(' ')[0])

        f1 = self.get_month_name(over_date.day, over_date.month, over_date.year)
        d1 = self.get_month_name(d1.day, d1.month, d1.year)
        d2 = self.get_month_name(d2.day, d2.month, d2.year)
        d3 = self.get_month_name(d3.day, d3.month, d3.year)
        d4 = self.get_month_name(d4.day, d4.month, d4.year) + ' (UPTO)'
        if d5:
            con5 = int(str(over_date - d5).split(' ')[0])
            d5 = self.get_month_name(d5.day, d5.month, d5.year)

        not_due = 0.0
        f_pe = 0.0  # 0 -30
        s_pe = 0.0  # 31-60
        t_pe = 0.0  # 61-90
        fo_pe = 0.0  # 91-120
        fi_pe = 0.0  # 120 - 150
        l_pe = 0.0  # +150
        total = 0.0  # Total
        move_lines = self.get_lines_aging(obj)
        for line in move_lines:
            ag_date = False
            if obj.aging_by == 'due_date':
                ag_date = line.get('date_maturity')
            else:
                ag_date = line.get('date')
            if ag_date and obj.overdue_date:
                due_date = ag_date
                over_date = obj.overdue_date
                if over_date != due_date:
                    if not ag_date > obj.overdue_date:
                        days = over_date - due_date
                        days = int(str(days).split(' ')[0])
                    else:
                        days = -1
                else:
                    days = 0
                if line.get('total') > 0:
                    if days < 0:
                        not_due += line.get('total')
                    elif days < con1:
                        f_pe += line.get('total')
                    elif days < con2:
                        s_pe += line.get('total')
                    elif days < con3:
                        t_pe += line.get('total')
                    elif days < con4:
                        fo_pe += line.get('total')
                    elif days < con5 and d5:
                        fi_pe += line.get('total')
                    else:
                        l_pe += line.get('total')

        bf_balance_lines = self.get_balance_bf(obj)
        for balance_line in bf_balance_lines:
            total += balance_line.get('total')
            ag_date = False
            if obj.aging_by == 'due_date':
                ag_date = balance_line.get('date_maturity')
            else:
                ag_date = balance_line.get('invoice_date')
            if ag_date and obj.overdue_date:
                due_date = ag_date
                over_date = obj.overdue_date
                if over_date != due_date:
                    if not ag_date > obj.overdue_date:
                        bf_balance_days = obj.overdue_date - due_date
                        bf_balance_days = int(str(bf_balance_days).split(' ')[0])
                    else:
                        bf_balance_days = -1
                else:
                    bf_balance_days = 0
                balance_bf = balance_line.get('total')
                if bf_balance_days < con1:
                    f_pe += balance_bf
                elif bf_balance_days < con2:
                    s_pe += balance_bf
                elif bf_balance_days < con3:
                    t_pe += balance_bf
                elif bf_balance_days < con4:
                    fo_pe += balance_bf
                elif bf_balance_days < con5 and d5:
                    fi_pe += balance_bf
                else:
                    l_pe += balance_bf

        if d5:
            return [{
                'not_due': not_due,
                f1: f_pe,
                d1: s_pe,
                d2: t_pe,
                d3: fo_pe,
                d4: fi_pe,
                d5: l_pe,
                total: total,
            }, [f1, d1, d2, d3, d4, d5, total]]
        return [{
            'not_due': not_due,
            f1: f_pe,
            d1: s_pe,
            d2: t_pe,
            d3: fo_pe,
            d4: fi_pe,
            total: total
        }, [f1, d1, d2, d3, d4, total]]

    def _lines_get(self, partner):
        domain = []
        if partner.aging_by == 'inv_date':
            domain.append(('date_invoice', '<=', partner.overdue_date))
            domain.append(('date_invoice', '>=', partner.invoice_start_date))
            # if partner.soa_type == 'unpaid_invoices':
            domain.append(('state', 'not in', ('paid', 'cancel')))
        elif partner.aging_by == 'due_date':
            domain.append(('date_due', '<=', partner.overdue_date))
            domain.append(('date_due', '>=', partner.invoice_start_date))
            # if partner.soa_type == 'unpaid_invoices':
            domain.append(('state', 'not in', ('paid', 'cancel')))
        move_ids = self.env['account.invoice'].search([('partner_id', '=', partner.id)] + domain).mapped('move_id').ids
        movelines = self.env['account.move.line'].search([('partner_id', '=', partner.id),
                                                          # ('date', '<=', partner.overdue_date),
                                                          # ('date', '>=', partner.invoice_start_date),
                                                          ('account_id.user_type_id.type', 'in', ['receivable', 'payable']),
                                                          ('move_id.state', '<>', 'draft'),
                                                          ('move_id', 'in', move_ids)])
        return movelines

    # get only the account move lines for the selected date
    def _lines_get_receivable(self, partner):
        domain = []
        if partner.aging_by == 'inv_date':
            domain.append(('date_invoice', '<=', partner.overdue_date))
            domain.append(('date_invoice', '>=', partner.invoice_start_date))
            # if partner.soa_type == 'unpaid_invoices':
            domain.append(('state', 'not in', ('paid', 'cancel')))
        elif partner.aging_by == 'due_date':
            domain.append(('date_due', '<=', partner.overdue_date))
            domain.append(('date_due', '>=', partner.invoice_start_date))
            # if partner.soa_type == 'unpaid_invoices':
            domain.append(('state', 'not in', ('paid', 'cancel')))
        move_ids = self.env['account.invoice'].search([('partner_id', '=', partner.id)] + domain).mapped('move_id').ids
        movelines = self.env['account.move.line'].search([('partner_id', '=', partner.id),
                                                          # ('date', '<=', partner.overdue_date),
                                                          # ('date', '>=', partner.invoice_start_date),
                                                          ('account_id.user_type_id.type', '=', 'receivable'),
                                                          ('move_id.state', '<>', 'draft'),
                                                          ('move_id', 'in', move_ids)
                                                          ])
        return movelines

    def _lines_get_payable(self, partner):
        domain = []
        if partner.aging_by == 'inv_date':
            domain.append(('date_invoice', '<=', partner.overdue_date))
            domain.append(('date_invoice', '>=', partner.invoice_start_date))
            # if partner.soa_type == 'unpaid_invoices':
            domain.append(('state', 'not in', ('paid', 'cancel')))
        elif partner.aging_by == 'due_date':
            domain.append(('date_due', '<=', partner.overdue_date))
            domain.append(('date_due', '>=', partner.invoice_start_date))
            # if partner.soa_type == 'unpaid_invoices':
            domain.append(('state', 'not in', ('paid', 'cancel')))
        move_ids = self.env['account.invoice'].search([('partner_id', '=', partner.id)] + domain).mapped('move_id').ids
        movelines = self.env['account.move.line'].search([('partner_id', '=', partner.id),
                                                          # ('date', '<=', partner.overdue_date),
                                                          # ('date', '>=', partner.invoice_start_date),
                                                          ('account_id.user_type_id.type', '=', 'payable'),
                                                          ('move_id.state', '<>', 'draft'),
                                                          ('move_id', 'in', move_ids)
                                                          ])
        return movelines

    # get the bring forward balance
    def _lines_get_all(self, partner):
        domain = []
        if partner.aging_by == 'inv_date':
            domain.append(('date_invoice', '<', partner.invoice_start_date))
            # if partner.soa_type == 'unpaid_invoices':
            domain.append(('state', 'not in', ('paid', 'cancel')))
        elif partner.aging_by == 'due_date':
            domain.append(('date_due', '<', partner.invoice_start_date))
            # if partner.soa_type == 'unpaid_invoices':
            domain.append(('state', 'not in', ('paid', 'cancel')))
        move_ids = self.env['account.invoice'].search([('partner_id', '=', partner.id)] + domain).mapped('move_id').ids
        movelines = self.env['account.move.line'].search([('partner_id', '=', partner.id),
                                                          # ('date', '<', partner.invoice_start_date),
                                                          ('account_id.user_type_id.type', 'in', ['receivable', 'payable']),
                                                          ('move_id.state', '<>', 'draft'),
                                                          ('move_id', 'in', move_ids)
                                                          ])
        return movelines

    # get the bring forward balance
    def _lines_get_all_receivable(self, partner):
        domain = []
        if partner.aging_by == 'inv_date':
            domain.append(('date_invoice', '<', partner.invoice_start_date))
            # if partner.soa_type == 'unpaid_invoices':
            domain.append(('state', 'not in', ('paid', 'cancel')))
        elif partner.aging_by == 'due_date':
            domain.append(('date_due', '<', partner.invoice_start_date))
            # if partner.soa_type == 'unpaid_invoices':
            domain.append(('state', 'not in', ('paid', 'cancel')))
        move_ids = self.env['account.invoice'].search([('partner_id', '=', partner.id)] + domain).mapped('move_id').ids
        movelines = self.env['account.move.line'].search([('partner_id', '=', partner.id),
                                                          # ('date', '<', partner.invoice_start_date),
                                                          ('move_id', 'in', move_ids),
                                                          ('account_id.user_type_id.type', '=', 'receivable'),
                                                          ('move_id.state', '<>', 'draft')])
        return movelines

    # get the bring forward balance
    def _lines_get_all_payable(self, partner):
        domain = []
        if partner.aging_by == 'inv_date':
            domain.append(('date_invoice', '<', partner.invoice_start_date))
            # if partner.soa_type == 'unpaid_invoices':
            domain.append(('state', 'not in', ('paid', 'cancel')))
        elif partner.aging_by == 'due_date':
            domain.append(('date_due', '<', partner.invoice_start_date))
            # if partner.soa_type == 'unpaid_invoices':
            domain.append(('state', 'not in', ('paid', 'cancel')))
        move_ids = self.env['account.invoice'].search([('partner_id', '=', partner.id)] + domain).mapped('move_id').ids
        movelines = self.env['account.move.line'].search([('partner_id', '=', partner.id),
                                                          # ('date', '<', partner.invoice_start_date),
                                                          ('move_id', 'in', move_ids),
                                                          ('account_id.user_type_id.type', '=', 'payable'),
                                                          ('move_id.state', '<>', 'draft')])
        return movelines

    def _lines_get_receivable_end_date(self, partner):
        domain = []
        if partner.aging_by == 'inv_date':
            domain.append(('date_invoice', '<=', partner.overdue_date))
            # if partner.soa_type == 'unpaid_invoices':
            domain.append(('state', 'not in', ('paid', 'cancel')))
        elif partner.aging_by == 'due_date':
            domain.append(('date_due', '<=', partner.overdue_date))
            # if partner.soa_type == 'unpaid_invoices':
            domain.append(('state', 'not in', ('paid', 'cancel')))
        move_ids = self.env['account.invoice'].search([('partner_id', '=', partner.id)] + domain).mapped('move_id').ids
        movelines = self.env['account.move.line'].search([('partner_id', '=', partner.id),
                                                          # ('date', '<', partner.overdue_date),
                                                          ('move_id', 'in', move_ids),
                                                          ('account_id.user_type_id.type', '=', 'receivable'),
                                                          ('move_id.state', '<>', 'draft')])
        return movelines

    def _lines_get_payable_end_date(self, partner):
        domain = []
        if partner.aging_by == 'inv_date':
            domain.append(('date_invoice', '<', partner.overdue_date))
            # if partner.soa_type == 'unpaid_invoices':
            domain.append(('state', 'not in', ('paid', 'cancel')))
        elif partner.aging_by == 'due_date':
            domain.append(('date_due', '<', partner.overdue_date))
            # if partner.soa_type == 'unpaid_invoices':
            domain.append(('state', 'not in', ('paid', 'cancel')))
        move_ids = self.env['account.invoice'].search([('partner_id', '=', partner.id)] + domain).mapped('move_id').ids
        movelines = self.env['account.move.line'].search([('partner_id', '=', partner.id),
                                                          ('move_id', 'in', move_ids),
                                                          # ('date', '<', partner.overdue_date),
                                                          ('account_id.user_type_id.type', '=', 'payable'),
                                                          ('move_id.state', '<>', 'draft')])
        return movelines

    def _lines_get_all_end_date(self, partner):
        domain = []
        if partner.aging_by == 'inv_date':
            domain.append(('date_invoice', '<', partner.overdue_date))
            # if partner.soa_type == 'unpaid_invoices':
            domain.append(('state', 'not in', ('paid', 'cancel')))
        elif partner.aging_by == 'due_date':
            domain.append(('date_due', '<', partner.overdue_date))
            # if partner.soa_type == 'unpaid_invoices':
            domain.append(('state', 'not in', ('paid', 'cancel')))
        move_ids = self.env['account.invoice'].search([('partner_id', '=', partner.id) + domain]).mapped('move_id').ids
        movelines = self.env['account.move.line'].search([('partner_id', '=', partner.id),
                                                          ('move_id', 'in', move_ids),
                                                          # ('date', '<', partner.overdue_date),
                                                          ('account_id.user_type_id.type', 'in', ['receivable', 'payable']),
                                                          ('move_id.state', '<>', 'draft')])
        return movelines

    # get the bring forward balance
    def get_balance_bf(self, partner):
        if partner.account_type == 'ar':
            move_lines = self._lines_get_receivable_end_date(partner)
        if partner.account_type == 'ap':
            move_lines = self._lines_get_payable_end_date(partner)
        elif partner.account_type == 'both':
            move_lines = self._lines_get_all_end_date(partner)
        res = []
        total_inv_amt = 0.0
        total_paid_amt = 0.0
        total = 0.0
        if move_lines:
            reversed_move_lines = move_lines.sorted(key=lambda x: x.date)
            for line in reversed_move_lines:
                # invoice_paid = False
                inv_amt = 0.0
                paid_amt = 0.0
                if line.debit:
                    inv_amt = line.debit
                if line.credit:
                    paid_amt = line.credit
                invoices = self.env['account.invoice'].search([
                    ('move_id', '=', line.move_id.id)])
                for invoice in invoices:
                    if invoice.residual == 0 and invoice.type not in ['out_refund', 'in_invoice']:
                        invoice_paid = True
                # if inv_amt < 0:   # for credit note
                #     invoice_paid = False
                # if not invoice_paid:
                if invoice.type in ['out_refund', 'in_invoice']:
                    total = -(paid_amt)
                else:
                    total = float(inv_amt)
                if total != 0:
                    res.append({
                        'ref': 'Balance b/f',
                        'invoice_date': invoice.date_invoice,
                        'date_maturity': invoice.date_due,
                        'debit': float(total_inv_amt),
                        'credit': float(total_paid_amt),
                        'total': float(total),
                    })

        return res

    def get_lines_aging(self, partner):
        if partner.account_type == 'ar':
            balance_move_lines = self._lines_get_receivable_end_date(partner)
        if partner.account_type == 'ap':
            balance_move_lines = self._lines_get_payable_end_date(partner)
        elif partner.account_type == 'both':
            balance_move_lines = self._lines_get_all_end_date(partner)
        res = []
        total_inv_amt = 0.0
        total_paid_amt = 0.0
        balance_total = 0.0
        if balance_move_lines:
            reversed_balance_move_lines = balance_move_lines.sorted(key=lambda x: x.date)
            for line in reversed_balance_move_lines:
                invoice_paid = False
                balance_inv_amt = 0.0
                balance_paid_amt = 0.0
                if line.debit:
                    balance_inv_amt = line.debit
                if line.credit:
                    balance_paid_amt = line.credit

                total_inv_amt += round(balance_inv_amt, 2)
                if balance_inv_amt < 0:  # for credit note
                    balance_paid_amt = math.fabs(balance_paid_amt)
                    balance_paid_amt = round(balance_paid_amt, 2)
                    balance_inv_amt = 0
                total_paid_amt += round(balance_paid_amt, 2)
                invoices = self.env['account.invoice'].search([
                    ('move_id', '=', line.move_id.id), ])
                for invoice in invoices:
                    if invoice.residual == 0:
                        invoice_paid = True
                if not invoice_paid:
                    balance_total += float(balance_inv_amt)

            if balance_total > 0 or balance_total < 0:
                res.append({
                    'date': False,
                    'desc': '',
                    'inv_ref': '',
                    'inv_original': '',
                    'nett_weight': '',
                    'unit_price': '',
                    'payment_ref': '',
                    'invoice_prod_cat': '',
                    'ref': 'Balance b/f',
                    'date_maturity': False,
                    'over_due': False,
                    'debit': 0.0,
                    'credit': 0.0,
                    'total': float(balance_total),
                })

        if partner.account_type == 'ar':
            move_lines = self._lines_get_receivable(partner)
        if partner.account_type == 'ap':
            move_lines = self._lines_get_payable(partner)
        elif partner.account_type == 'both':
            move_lines = self._lines_get(partner)
        if move_lines:
            reversed_move_lines = move_lines.sorted(key=lambda x: x.date)
            for line in reversed_move_lines:
                inv_amt = 0.0
                paid_amt = 0.0
                over_due = False
                if line.debit:
                    inv_amt = line.debit
                if line.credit:
                    paid_amt = line.credit
                    if inv_amt > 0:
                        if date.today() > line.date_maturity:
                            over_due = True
                total = 0.0

                inv_amt = round(inv_amt, 2)
                if inv_amt < 0:  # for credit note
                    paid_amt = math.fabs(paid_amt)
                    paid_amt = round(paid_amt, 2)
                    inv_amt = 0
                total = float(inv_amt - paid_amt)
                invoices = self.env['account.invoice'].search([
                    ('move_id', '=', line.move_id.id), ])
                invoice_ref = ''
                invoice_prod_cat = ''
                invoice_original = ''
                nett_weight = 0
                unit_price = 0
                payment_ref = ''
                invoice_paid = False
                for invoice in invoices:
                    invoice_ref = invoice.number
                    if invoice.residual == 0:
                        invoice_paid = True
                    invoice_original = invoice.origin
                    if invoice.type == ['out_invoice', 'in_invoice']:
                        payment_ref = invoice.origin
                    else:
                        payment_ref = invoice.reference
                    inv_lines = invoice.invoice_line_ids.filtered((lambda i: i.sequence == 1))
                    for inv_line in inv_lines:
                        nett_weight = inv_line.quantity
                        unit_price = inv_line.price_unit
                if paid_amt > 0:
                    payments = self.env['account.payment'].search([('id', '=', line.payment_id.id), ])
                    if payments:
                        for payment in payments:
                            invoice_ref = payment.name
                            if payment.communication:
                                payment_ref = payment.communication
                    if not invoice_paid:
                        res.append({
                            'date': line.date,
                            'desc': line.ref or '/',
                            'inv_ref': invoice_ref or '',
                            'inv_original': invoice_original or '',
                            'nett_weight': nett_weight or '',
                            'unit_price': unit_price or '',
                            'payment_ref': payment_ref or '',
                            'invoice_prod_cat': invoice_prod_cat or '',
                            'ref': line.move_id.name or '',
                            'date_maturity': line.date_maturity,
                            'over_due': over_due,
                            'debit': float(inv_amt),
                            'credit': float(paid_amt),
                            'total': float(total),
                        })

        return res

    # get only the statements for the selected date
    def get_lines(self, partner):
        if partner.account_type == 'ar':
            balance_move_lines = self._lines_get_all_receivable(partner)
        if partner.account_type == 'ap':
            balance_move_lines = self._lines_get_all_payable(partner)
        elif partner.account_type == 'both':
            balance_move_lines = self._lines_get_all(partner)
        res = []
        total_inv_amt = 0.0
        total_paid_amt = 0.0
        balance_total = 0.0
        if balance_move_lines:
            reversed_balance_move_lines = balance_move_lines.sorted(key=lambda x: x.date)
            for line in reversed_balance_move_lines:
                balance_inv_amt = 0.0
                balance_paid_amt = 0.0
                if line.debit:
                    balance_inv_amt = line.debit
                if line.credit:
                    balance_paid_amt = line.credit
                total_inv_amt += round(balance_inv_amt, 2)
                if balance_inv_amt < 0:  # for credit note
                    balance_paid_amt = math.fabs(balance_paid_amt)
                    balance_paid_amt = round(balance_paid_amt, 2)
                    balance_inv_amt = 0
                total_paid_amt += round(balance_paid_amt, 2)
                balance_total += float(balance_inv_amt - balance_paid_amt)
            if balance_total > 0 or balance_total < 0:
                res.append({
                    'date': False,
                    'desc': '',
                    'inv_ref': '',
                    'inv_original': '',
                    'nett_weight': '',
                    'unit_price': '',
                    'payment_ref': '',
                    'invoice_prod_cat': '',
                    'ref': 'Balance b/f',
                    'date_maturity': False,
                    'over_due': False,
                    'debit': 0.0,
                    'credit': 0.0,
                    'total': float(balance_total),
                })

        # get the selected date
        if partner.account_type == 'ar':
            move_lines = self._lines_get_receivable(partner)
        if partner.account_type == 'ap':
            move_lines = self._lines_get_payable(partner)
        elif partner.account_type == 'both':
            move_lines = self._lines_get(partner)
        if move_lines:
            reversed_move_lines = move_lines.sorted(key=lambda x: x.date)
            for line in reversed_move_lines:
                inv_amt = 0.0
                paid_amt = 0.0
                over_due = False
                if line.debit:
                    inv_amt = line.debit
                if line.credit:
                    paid_amt = line.credit
                    if inv_amt > 0:
                        if date.today() > line.date_maturity:
                            over_due = True
                total = 0.0
                inv_amt = round(inv_amt, 2)
                if inv_amt < 0:    # for credit note
                    paid_amt = math.fabs(paid_amt)
                    paid_amt = round(paid_amt, 2)
                    inv_amt = 0
                total = float(inv_amt - paid_amt)
                invoices = self.env['account.invoice'].search([('move_id', '=', line.move_id.id)])
                invoice_ref = ''
                invoice_prod_cat = ''
                invoice_original = ''
                nett_weight = 0
                unit_price = 0
                payment_ref = ''
                for invoice in invoices:
                    invoice_ref = invoice.number
                    invoice_original = invoice.origin
                    if invoice.type in ['out_invoice', 'in_invoice']:
                        payment_ref = invoice.origin

                    else:
                        payment_ref = invoice.reference
                    inv_lines = invoice.invoice_line_ids.filtered((lambda i: i.sequence == 1))
                    for inv_line in inv_lines:
                        nett_weight = inv_line.quantity
                        unit_price = inv_line.price_unit

                if paid_amt > 0:
                    payments = self.env['account.payment'].search([('id', '=', line.payment_id.id), ])
                    for payment in payments:
                        invoice_ref = payment.name
                        if payment.communication:
                            payment_ref = payment.communication

                res.append({
                            'date': line.date,
                            'desc': line.ref or '/',
                            'inv_ref': invoice_ref or '',
                            'inv_original': invoice_original or '',
                            'nett_weight': nett_weight or '',
                            'unit_price': unit_price or '',
                            'payment_ref': payment_ref or '',
                            'invoice_prod_cat': invoice_prod_cat or '',
                            'ref': line.move_id.name or '',
                            'date_maturity': line.date_maturity,
                            'over_due': over_due,
                            'debit': float(inv_amt),
                            'credit': float(paid_amt),
                            'total': float(total),
                        })

        return res

    @api.multi
    def _get_report_values(self, docids, data=None):
        partner_id = self._context.get('default_res_id')
        if partner_id:
            partner_ids = self.env['res.partner'].browse(self._context.get('default_res_id'))
            return {
                'doc_ids': partner_id,
                'doc_model': 'res.partner',
                'docs': partner_ids,
                'get_lines': self.get_lines,
                'set_ageing': self.set_ageing,
                'set_amount': self.set_amount,
                'get_company_info': self.get_company_info,
            }

        else:
            docs = self.env['res.partner'].browse(data['form'])
            return {
                'doc_ids': data['ids'],
                'doc_model': 'res.partner',
                'docs': docs,
                'get_lines': self.get_lines,
                'set_ageing': self.set_ageing,
                'set_amount': self.set_amount,
                'get_company_info': self.get_company_info,
            }
