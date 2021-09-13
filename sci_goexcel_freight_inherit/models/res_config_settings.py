# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    use_freight_note = fields.Boolean(related="company_id.use_freight_note", string='Use Freight Note', readonly=False)
    freight_note = fields.Text(related="company_id.freight_note", string="Remark", readonly=False)
