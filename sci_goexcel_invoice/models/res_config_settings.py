# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    invoice_note = fields.Text(related="company_id.invoice_note", string="Additional Notes for Invoice", readonly=False)
    invoice_note_foreign_currency = fields.Text(related="company_id.invoice_note_foreign_currency",
                                                string="Additional Notes for Invoice (Foreign Currency)", readonly=False)

    is_installed_sale = fields.Boolean(string="Is the Sale Module Installed")
    module_stock_dropshipping = fields.Boolean("Dropshipping")

