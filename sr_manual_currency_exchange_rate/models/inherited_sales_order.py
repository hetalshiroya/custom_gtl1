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

from odoo import models, fields, api
from datetime import datetime


class SalesOrder(models.Model):
    _inherit = 'sale.order'

    apply_manual_currency_exchange = fields.Boolean(
        string='Apply Manual Currency Exchange')
    manual_currency_exchange_rate = fields.Float(
        string='Manual Currency Exchange Rate', digits=(8, 6), copy=False)
    # TS
    exchange_rate_inverse = fields.Float(
        string='Exchange Rate', help='Eg, USD to MYR (eg 4.21)')
    company_currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id')
    active_manual_currency_rate = fields.Boolean(
        'active Manual Currency', default=False)

    def _prepare_invoice(self):
        result = super(SalesOrder, self)._prepare_invoice()
        # Custom Code by Sitaram Solutions Start
        result.update({
            'apply_manual_currency_exchange': self.apply_manual_currency_exchange,
            'manual_currency_exchange_rate': self.manual_currency_exchange_rate,
            'active_manual_currency_rate': self.active_manual_currency_rate
        })
        # Custom Code by Sitaram Solutions End
        return result

    @api.onchange('company_currency_id', 'currency_id')
    def onchange_currency_id(self):
        # Custom Method by Sitaram Solutions
        if self.company_currency_id or self.currency_id:
            if self.company_currency_id != self.currency_id:
                self.active_manual_currency_rate = True
            else:
                self.active_manual_currency_rate = False
        else:
            self.active_manual_currency_rate = False

    @api.onchange('company_id', 'currency_id')
    def _get_current_rate(self):
        if self.company_id or self.currency_id:
            if self.company_id.currency_id != self.currency_id:
                self.apply_manual_currency_exchange = self.active_manual_currency_rate
                # fc = self.env['res.currency'].search([('name', '=', self.currency_id.name)], limit=1)
                # for rate_id in fc.rate_ids:
                rate_rec = self.env['res.currency.rate'].search([('currency_id', '=', self.currency_id.id),
                                                                 ('company_id', '=',
                                                                  self.company_id.id),
                                                                 ('name', '<=', datetime.now(
                                                                 ).date()),
                                                                 ('date_to', '>=', datetime.now().date())], limit=1)
                if rate_rec:
                    print('rate=' + str(rate_rec.rate))
                    self.exchange_rate_inverse = rate_rec.rate
                    self.manual_currency_exchange_rate = 1/self.exchange_rate_inverse

                    print('rate=' + str(self.manual_currency_exchange_rate))
                    print('self.apply_manual_currency_exchange=' + str(
                        self.apply_manual_currency_exchange))
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
            self.apply_manual_currency_exchange = self.active_manual_currency_rate
            print('_update_exchange_rate manual rate=' +
                  str(self.manual_currency_exchange_rate))
            print('self.apply_manual_currency_exchange=' + str(
                self.apply_manual_currency_exchange))


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        # Custom Code by Sitaram Solutions Start
        if self.order_id.active_manual_currency_rate and self.order_id.apply_manual_currency_exchange:
            self = self.with_context(
                manual_rate=self.order_id.manual_currency_exchange_rate,
                active_manutal_currency=self.order_id.apply_manual_currency_exchange,
            )
            # Custom Code by Sitaram Solutions End
        return super(SaleOrderLine, self).product_uom_change()
