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
from odoo.exceptions import ValidationError


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.model
    def _compute_amount_fields(self, amount, src_currency, company_currency):
        """ Helper function to compute value for fields debit/credit/amount_currency based on an amount and the currencies given in parameter"""
        amount_currency = False
        currency_id = False
        date = self.env.context.get('date') or fields.Date.today()
        company = self.env.context.get('company_id')
        company = self.env['res.company'].browse(
            company) if company else self.env.user.company_id
        if src_currency and src_currency != company_currency:
            amount_currency = amount
            if self._context.get('active_manual_currency'):
                # TS - bug 18/2/2021(TMI)
                if self._context.get('manual_rate') != 0:
                    # print(' _compute_amount_fields manual_rate=', self._context.get('manual_rate'))
                    # print(' _compute_amount_fields amount=', amount)
                    # TS - bug # USD3097 * 4.118 (GTL)
                    amount = round(
                        amount / self._context.get('manual_rate'), 5)
                    # print(' _compute_amount_fields converted amount=', amount)
                else:
                    raise ValidationError(_('Exchange Rate Cannot Be Zero!!'))
                # END
            else:
                amount = src_currency._convert(
                    amount, company_currency, company, date)
            currency_id = src_currency.id
        debit = amount > 0 and amount or 0.0
        credit = amount < 0 and -amount or 0.0
        return debit, credit, amount_currency, currency_id
