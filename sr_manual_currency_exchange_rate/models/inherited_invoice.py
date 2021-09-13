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
from datetime import datetime
from odoo.exceptions import UserError, RedirectWarning


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    apply_manual_currency_exchange = fields.Boolean(
        string='Apply Manual Currency Exchange')
    manual_currency_exchange_rate = fields.Float(
        string='Manual Currency Exchange Rate', digits=(8, 6))
    # TS
    exchange_rate_inverse = fields.Float(
        string='Exchange Rate', help='Eg, USD to MYR (eg 4.21)', copy=False, digits=(5, 6))
    active_manual_currency_rate = fields.Boolean(
        'active Manual Currency', default=False)

    @api.onchange('currency_id')
    def onchange_currency_id(self):
        # Custom Module by Sitaram Solutions
        if self.company_id or self.currency_id:
            if self.company_id.currency_id != self.currency_id:
                self.active_manual_currency_rate = True
            else:
                self.active_manual_currency_rate = False
        else:
            self.active_manual_currency_rate = False

    @api.onchange('company_id', 'currency_id')
    def _get_current_rate(self):
        # print('_get_current_rate')
        if self.company_id or self.currency_id:
            if self.company_id.currency_id != self.currency_id:
                self.apply_manual_currency_exchange = True
                self.active_manual_currency_rate = True
                # fc = self.env['res.currency'].search([('name', '=', self.currency_id.name)], limit=1)
                # for rate_id in fc.rate_ids:
                # print('apply_manual_currency_exchange=' + str(self.apply_manual_currency_exchange))
                rate_rec = self.env['res.currency.rate'].search([('currency_id', '=', self.currency_id.id),
                                                                 ('company_id', '=',
                                                                  self.company_id.id),
                                                                 ('name', '<=', datetime.now(
                                                                 ).date()),
                                                                 ('date_to', '>=', datetime.now().date())], limit=1)
                if rate_rec:
                    # print('rate=' + str(rate_rec.rate))
                    self.exchange_rate_inverse = rate_rec.rate
                    self.manual_currency_exchange_rate = float(
                        round(1/self.exchange_rate_inverse, 6))

                    # print('rate=' + str(self.manual_currency_exchange_rate))
                    # print('self.apply_manual_currency_exchange=' + str(
                    #     self.apply_manual_currency_exchange))
            else:
                self.exchange_rate_inverse = 1
                self.manual_currency_exchange_rate = 1
                self.apply_manual_currency_exchange = False
                self.active_manual_currency_rate = False

    @api.onchange('exchange_rate_inverse')
    def _update_exchange_rate(self):
        if self.exchange_rate_inverse:
            self.manual_currency_exchange_rate = float(
                round(1/self.exchange_rate_inverse, 6))
            # self.apply_manual_currency_exchange = self.active_manual_currency_rate
            # print('_update_exchange_rate manual rate=' + str(self.manual_currency_exchange_rate))
            # print('self.apply_manual_currency_exchange=' + str(
            #   self.apply_manual_currency_exchange))

    # Load all unsold PO lines

    @api.onchange('purchase_id')
    def purchase_order_change(self):
        if not self.purchase_id:
            return {}
        if not self.partner_id:
            self.partner_id = self.purchase_id.partner_id.id

        new_lines = self.env['account.invoice.line']
        for line in self.purchase_id.order_line - self.invoice_line_ids.mapped('purchase_line_id'):
            data = self._prepare_invoice_line_from_po_line(line)
            if data.get('product_id'):
                new_line = new_lines.new(data)
                new_line._set_additional_fields(self)
                new_lines += new_line
        # Custom Code by Sitaram Solutions Start
        self.currency_id = self.purchase_id.currency_id.id
        self.active_manual_currency_rate = self.purchase_id.active_manual_currency_rate
        self.apply_manual_currency_exchange = self.purchase_id.apply_manual_currency_exchange
        self.manual_currency_exchange_rate = self.purchase_id.manual_currency_exchange_rate
        # Custom Code by Sitaram Solutions End
        self.invoice_line_ids += new_lines
        self.payment_term_id = self.purchase_id.payment_term_id
        self.env.context = dict(
            self.env.context, from_purchase_order_change=True)
        self.purchase_id = False
        return {}

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        account_id = False
        payment_term_id = False
        fiscal_position = False
        bank_id = False
        warning = {}
        domain = {}
        company_id = self.company_id.id
        p = self.partner_id if not company_id else self.partner_id.with_context(
            force_company=company_id)
        type = self.type
        if p:
            rec_account = p.property_account_receivable_id
            pay_account = p.property_account_payable_id
            if not rec_account and not pay_account:
                action = self.env.ref('account.action_account_config')
                msg = _(
                    'Cannot find a chart of accounts for this company, You should configure it. \nPlease go to Account Configuration.')
                raise RedirectWarning(msg, action.id, _(
                    'Go to the configuration panel'))

            if type in ('in_invoice', 'in_refund'):
                account_id = pay_account.id
                payment_term_id = p.property_supplier_payment_term_id.id
            else:
                account_id = rec_account.id
                payment_term_id = p.property_payment_term_id.id

            delivery_partner_id = self.get_delivery_partner_id()
            fiscal_position = self.env['account.fiscal.position'].get_fiscal_position(
                self.partner_id.id, delivery_id=delivery_partner_id)

            # If partner has no warning, check its company
            if p.invoice_warn == 'no-message' and p.parent_id:
                p = p.parent_id
            if p.invoice_warn != 'no-message':
                # Block if partner only has warning but parent company is blocked
                if p.invoice_warn != 'block' and p.parent_id and p.parent_id.invoice_warn == 'block':
                    p = p.parent_id
                warning = {
                    'title': _("Warning for %s") % p.name,
                    'message': p.invoice_warn_msg
                }
                if p.invoice_warn == 'block':
                    self.partner_id = False

        self.account_id = account_id
        self.payment_term_id = payment_term_id
        self.date_due = False
        self.fiscal_position_id = fiscal_position

        if type in ('in_invoice', 'out_refund'):
            bank_ids = p.commercial_partner_id.bank_ids
            bank_id = bank_ids[0].id if bank_ids else False
            self.partner_bank_id = bank_id
            domain = {'partner_bank_id': [('id', 'in', bank_ids.ids)]}

        res = {}
        if warning:
            res['warning'] = warning
        if domain:
            res['domain'] = domain
        # Custom Code by Sitaram Solutions Start
        if self.invoice_line_ids:
            if self.invoice_line_ids[0].purchase_id:
                self.currency_id = self.invoice_line_ids[0].purchase_id.currency_id.id
        # Custom Code by Sitaram Solutions End
        return res

    @api.multi
    def action_move_create(self):
        """ Creates invoice related analytics and financial move lines """
        account_move = self.env['account.move']

        for inv in self:
            if not inv.journal_id.sequence_id:
                raise UserError(
                    _('Please define sequence on the journal related to this invoice.'))
            if not inv.invoice_line_ids.filtered(lambda line: line.account_id):
                raise UserError(_('Please add at least one invoice line.'))
            if inv.move_id:
                continue

            if not inv.date_invoice:
                inv.write({'date_invoice': fields.Date.context_today(self)})
            if not inv.date_due:
                inv.write({'date_due': inv.date_invoice})
            company_currency = inv.company_id.currency_id

            # create move lines (one per invoice line + eventual taxes and analytic lines)
            iml = inv.invoice_line_move_line_get()
            # print('iml', iml)
            iml += inv.tax_line_move_line_get()
            # print('iml with tax line', iml)
            diff_currency = inv.currency_id != company_currency
            # create one move line for the total and possibly adjust the other lines amount
            total, total_currency, iml = inv.compute_invoice_totals(
                company_currency, iml)
            # print('iml after compute invoice total', iml)
            # print('action_move_create manual rate=' + str(self.manual_currency_exchange_rate))
            # print('action_move_create self.apply_manual_currency_exchange=' + str(
            #    self.apply_manual_currency_exchange))
            # print('action_move_create total=' + str(total))

            name = inv.name or ''
            # if inv.payment_term_id:
            #     totlines = inv.payment_term_id.with_context(currency_id=company_currency.id).compute(total, inv.date_invoice)[0]
            #     print('tot lines=',totlines)
            #     res_amount_currency = total_currency
            #     for i, t in enumerate(totlines):
            #         if inv.currency_id != company_currency:
            #             amount_currency = company_currency._convert(t[1], inv.currency_id, inv.company_id, inv._get_currency_rate_date() or fields.Date.today())
            #         else:
            #             amount_currency = False
            #         print('amount_currency=', amount_currency)
            #         # last line: add the diff
            #         res_amount_currency -= amount_currency or 0
            #         # print('res_amount_currency=' + str(res_amount_currency))
            #         if i + 1 == len(totlines):
            #             amount_currency += res_amount_currency
            #             # print('amount_currency=' + str(amount_currency))
            #         # Modified code by Sitaram SOlutions start
            #         iml.append({
            #             'type': 'dest',
            #             'name': name,
            #             'price': float(round(total_currency / self.manual_currency_exchange_rate, 3)) if self.active_manual_currency_rate and self.apply_manual_currency_exchange else t[1],
            #             'account_id': inv.account_id.id,
            #             'date_maturity': t[0],
            #             'amount_currency': diff_currency and float(round(amount_currency, 3)),
            #             'currency_id': diff_currency and inv.currency_id.id,
            #             'invoice_id': inv.id
            #         })
            # else:
            # print('without payterm')
            # print('exch rate', self.manual_currency_exchange_rate)
            # print('after exch rate', float(round(total_currency / self.manual_currency_exchange_rate, 2)))
            # Modified Code by Sitaram Solutions Start
            iml.append({
                'type': 'dest',
                'name': name,
                # 'price': float(round(total_currency / self.manual_currency_exchange_rate, 3)) if self.active_manual_currency_rate and self.apply_manual_currency_exchange else total,
                'price': float(round(total_currency * self.exchange_rate_inverse, 4)) if self.active_manual_currency_rate and self.apply_manual_currency_exchange else total,
                'account_id': inv.account_id.id,
                'date_maturity': inv.date_due,
                'amount_currency': diff_currency and total_currency,
                'currency_id': diff_currency and inv.currency_id.id,
                'invoice_id': inv.id
            })
            # print('action_move_create self.apply_manual_currency_exchange=' + str(
            #    self.apply_manual_currency_exchange))
            # print('iml after append >> ', iml)
            part = self.env['res.partner']._find_accounting_partner(
                inv.partner_id)
            line = [(0, 0, self.line_get_convert(l, part.id)) for l in iml]
            # code vy Shivam/#TS for add diff value in first line
            # debit = credit = 0.000
            # for l in line:
            #     # print (">>>>line original", l[2])
            #     #debit += l[2].get('debit')
            #     #credit += l[2].get('credit')
            #     debit += round(l[2].get('debit'), self.currency_id.decimal_places)
            #     credit += round(l[2].get('credit'), self.currency_id.decimal_places)
            #     # if inv.type in ['in_invoice'] or inv.type in ['out_refund']:
            #     #     if credit > 0:
            #     #         break
            #     # if inv.type in ['out_invoice'] or inv.type in ['in_refund']:
            #     #     if debit > 0:
            #     #         break
            # # print('debit=', debit, ' credit=', credit)
            # diff = round(debit - credit, 2)
            # # print("diff", diff)
            # # positive >> == debit bigger
            # # negetive >> == credit bigger

            # # print ("diff", diff)
            # if inv.type in ['out_invoice']:
            #     # print ("Invoice")
            #     if diff < 0:
            #         # print ("negative")
            #         cnt = 1
            #         for c in line:
            #             if c[2].get('credit') and cnt == 1 and c[2].get('account_id'):
            #                 dp = len(str(c[2].get('credit')).split(".")[1])
            #                 # print('credit=', c[2].get('credit'))
            #                 # print('dp=', dp)
            #                 if dp >= 2:
            #                     # it is minus minus
            #                     c[2]['credit'] += diff
            #                     cnt += 1
            #     if diff > 0:
            #         # print("positive")
            #         cnt = 1
            #         for c in line:
            #             if c[2].get('credit') and cnt == 1 and c[2].get('account_id'):
            #                 dp = len(str(c[2].get('credit')).split(".")[1])
            #                 # print('credit=', c[2].get('credit'))
            #                 # print('dp=', dp)
            #                 if dp >= 2:
            #                     c[2]['credit'] += diff
            #                     cnt += 1
            # if inv.type in ['in_invoice']:
            #     # print ("BILL")
            #     if diff < 0:
            #         # print ("negative")
            #         cnt = 1
            #         for c in line:
            #             if c[2].get('debit') and cnt == 1 and c[2].get('account_id'):
            #                 dp = len(str(c[2].get('debit')).split(".")[1])
            #                 # print('debit=', c[2].get('debit'))
            #                 # print('dp=', dp)
            #                 if dp >= 2:
            #                     # it is minus minus
            #                     c[2]['debit'] -= diff
            #                     cnt += 1
            #     if diff > 0:
            #         # print("positive")
            #         cnt = 1
            #         for c in line:
            #             if c[2].get('debit') and cnt == 1 and c[2].get('account_id'):
            #                 dp = len(str(c[2].get('debit')).split(".")[1])
            #                 # print('debit=', c[2].get('debit'))
            #                 # print('dp=', dp)
            #                 if dp >= 2:
            #                     c[2]['debit'] -= diff
            #                     cnt += 1
            # # Credit note for customer
            # if inv.type in ['out_refund']:
            #     # print ("invoice refund")
            #     if diff < 0:
            #         # print("negative")
            #         cnt = 1
            #         for c in line:
            #             if c[2].get('debit') and cnt == 1 and c[2].get('account_id'):
            #                 dp = len(str(c[2].get('debit')).split(".")[1])
            #                 # print('debit=', c[2].get('debit'))
            #                 # print('dp=', dp)
            #                 if dp >= 2:
            #                     # it is minus minus
            #                     c[2]['debit'] -= diff
            #                     cnt += 1
            #     if diff > 0:
            #         # print("positive")
            #         cnt = 1
            #         for c in line:
            #             if c[2].get('debit') and cnt == 1 and c[2].get('account_id'):
            #                 dp = len(str(c[2].get('debit')).split(".")[1])
            #                 # print('debit=', c[2].get('debit'))
            #                 # print('dp=', dp)
            #                 if dp >= 2:
            #                     c[2]['debit'] -= diff
            #                     cnt += 1
            #     # if diff > 0:
            #     #     print ("positive")
            #     #     cnt = 1
            #     #     for c in line:
            #     #         if c[2].get('debit') and cnt == 1 and c[2].get('account_id'):
            #     #             c[2]['debit'] -= diff
            #     #             cnt += 1
            # if inv.type in ['in_refund']:
            #     # print ("PO vendor Bill refund")
            #     if diff < 0:
            #         # print("negative")
            #         cnt = 1
            #         for c in line:
            #             if c[2].get('credit') and cnt == 1 and c[2].get('account_id'):
            #                 dp = len(str(c[2].get('credit')).split(".")[1])
            #                 # print('credit=', c[2].get('credit'))
            #                 # print('dp=', dp)
            #                 if dp >= 2:
            #                     # it is minus minus
            #                     c[2]['credit'] += diff
            #                     cnt += 1
            #     if diff > 0:
            #         # print("positive")
            #         cnt = 1
            #         for c in line:
            #             if c[2].get('credit') and cnt == 1 and c[2].get('account_id'):
            #                 dp = len(str(c[2].get('credit')).split(".")[1])
            #                 # print('credit=', c[2].get('credit'))
            #                 # print('dp=', dp)
            #                 if dp >= 2:
            #                     c[2]['credit'] += diff
            #                     cnt += 1
            # code change done by shivam

            line = inv.group_lines(iml, line)
            line = inv.finalize_invoice_move_lines(line)
            date = inv.date or inv.date_invoice
            move_vals = {
                'ref': inv.reference,
                'line_ids': line,
                'journal_id': inv.journal_id.id,
                'date': date,
                'narration': inv.comment,
            }
            m_debit = m_credit = 0.000
            for m in move_vals.get('line_ids'):
                # print (">>>>line updated", m[2])
                # m_debit += round(m[2].get('debit'), 2)
                # m_credit += round(m[2].get('credit'), 2)
                m_debit += m[2].get('debit')
                m_credit += m[2].get('credit')
            print(">m_debit", m_debit)
            print(">m_credit", m_credit)
            move = account_move.create(move_vals)
            # Pass invoice in method post: used if you want to get the same
            # account move reference when creating the same invoice after a cancelled one:
            move.post(invoice=inv)

            # make the invoice point to that move
            vals = {
                'move_id': move.id,
                'date': date,
                'move_name': move.name,
            }
            inv.write(vals)
        return True

    @api.multi
    def compute_invoice_totals(self, company_currency, invoice_move_lines):
        total = 0
        total_currency = 0
        # print('compute_invoice_totals manual rate=' + str(self.manual_currency_exchange_rate))
        # print('compute_invoice_totals self.apply_manual_currency_exchange=' + str(self.apply_manual_currency_exchange))
        for line in invoice_move_lines:
            if self.currency_id != company_currency:
                currency = self.currency_id
                date = self._get_currency_rate_date() or fields.Date.context_today(self)
                if not (line.get('currency_id') and line.get('amount_currency')):
                    line['currency_id'] = currency.id
                    line['amount_currency'] = currency.round(line['price'])
                    # Modified Code by Sitaram Solutions Start
                    if self.active_manual_currency_rate and self.apply_manual_currency_exchange:
                        # TS - fix bug 20/2/2021 (Difference debit - credit: 0.01)
                        # line['price'] = float(round(line['price'] / self.manual_currency_exchange_rate, 4))
                        line['price'] = float(
                            round(line['price'] * self.exchange_rate_inverse, 4))
                    else:
                        line['price'] = currency._convert(
                            line['price'], company_currency, self.company_id, date)
                    # Modified Code by Sitaram Solutions End
            else:
                line['currency_id'] = False
                line['amount_currency'] = False
                line['price'] = self.currency_id.round(line['price'])
            if self.type in ('out_invoice', 'in_refund'):
                total += line['price']
                total_currency += line['amount_currency'] or line['price']
                line['price'] = - line['price']
            else:
                total -= line['price']
                total_currency -= line['amount_currency'] or line['price']
        # print('compute_invoice_totals Total=' + str(total))
        # print('compute_invoice_totals Total_currency=' + str(total_currency))
        # TS - fix bug 20/2/2021 (Difference debit - credit: 0.01)
        return float(round(total, 3)), total_currency, invoice_move_lines


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    def _set_currency(self):
        company = self.invoice_id.company_id
        currency = self.invoice_id.currency_id
        if company and currency:
            if company.currency_id != currency:
                # Modified Code by Sitaram Solutions Start
                if self.invoice_id.active_manual_currency_rate and self.invoice_id.apply_manual_currency_exchange:
                    # self.price_unit = float(round(self.price_unit * self.invoice_id.manual_currency_exchange_rate, 4))
                    self.price_unit = float(
                        round(self.price_unit * self.invoice_id.exchange_rate_inverse, 4))

                else:
                    self.price_unit = self.price_unit * \
                        currency.with_context(
                            dict(self._context or {}, date=self.invoice_id.date_invoice)).rate
                # Modified Code by Sitaram Solutions End

    # def _set_currency(self):
    #     company = self.invoice_id.company_id
    #     currency = self.invoice_id.currency_id
    #     if company and currency:
    #         if company.currency_id != currency:
    #             # Modified Code by Sitaram Solutions Start
    #             if self.invoice_id.active_manual_currency_rate and self.invoice_id.apply_manual_currency_exchange:
    #                 self.price_unit = float(round(self.price_unit * self.invoice_id.manual_currency_exchange_rate, 2))
    #             else:
    #                 self.price_unit = self.price_unit * currency.with_context(dict(self._context or {}, date=self.invoice_id.date_invoice)).rate
