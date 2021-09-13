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
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    apply_manual_currency_exchange = fields.Boolean(
        string='Apply Manual Currency Exchange')
    manual_currency_exchange_rate = fields.Float(
        string='Manual Currency Exchange Rate', digits=(8, 6), copy=False)
    # TS
    exchange_rate_inverse = fields.Float(
        string='Exchange Rate', help='Eg, USD to MYR (eg 4.21)')
    active_manual_currency_rate = fields.Boolean(
        'active Manual Currency', default=False)

    @api.onchange('company_id', 'currency_id')
    def onchange_currency_id(self):
        # Custom Method by Sitaram Solutions
        if self.company_id or self.currency_id:
            if self.company_id.currency_id != self.currency_id:
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
                    self.manual_currency_exchange_rate = float(
                        round(1/self.exchange_rate_inverse, 4))

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


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.onchange('product_qty', 'product_uom')
    def _onchange_quantity(self):
        if not self.product_id:
            return
        params = {'order_id': self.order_id}
        seller = self.product_id._select_seller(
            partner_id=self.partner_id,
            quantity=self.product_qty,
            date=self.order_id.date_order and self.order_id.date_order.date(),
            uom_id=self.product_uom,
            params=params)

        if seller or not self.date_planned:
            self.date_planned = self._get_date_planned(
                seller).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        if not seller:
            if self.product_id.seller_ids.filtered(lambda s: s.name.id == self.partner_id.id):
                self.price_unit = 0.0
            return
        # Custom Code by Sitaram Solutions Start
        if self.order_id.active_manual_currency_rate and self.order_id.apply_manual_currency_exchange:
            self.price_unit = seller.price * self.order_id.manual_currency_exchange_rate
            return
        # Custom Code by Sitaram Solutions End

        price_unit = self.env['account.tax']._fix_tax_included_price_company(
            seller.price, self.product_id.supplier_taxes_id, self.taxes_id, self.company_id) if seller else 0.0
        if price_unit and seller and self.order_id.currency_id and seller.currency_id != self.order_id.currency_id:
            price_unit = seller.currency_id._convert(
                price_unit, self.order_id.currency_id, self.order_id.company_id, self.date_order or fields.Date.today())

        if seller and self.product_uom and seller.product_uom != self.product_uom:
            price_unit = seller.product_uom._compute_price(
                price_unit, self.product_uom)

        self.price_unit = price_unit
