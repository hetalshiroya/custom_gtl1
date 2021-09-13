# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    soa_note = fields.Text(related="company_id.soa_note", string="Additional Notes for Customer SOA", readonly=False)
