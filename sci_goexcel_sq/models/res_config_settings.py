# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    air_freight_note = fields.Text(related="company_id.air_freight_note", string="Air Freight Terms & Conditions", readonly=False)
    land_freight_note = fields.Text(related="company_id.land_freight_note", string="Land Freight Terms & Conditions", readonly=False)
    is_installed_sale = fields.Boolean(string="Is the Sale Module Installed")
    module_stock_dropshipping = fields.Boolean("Dropshipping")
