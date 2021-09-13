# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    bl_term = fields.Char(string='BL Term')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        param = self.env['ir.config_parameter'].sudo()
        bl_term = param.get_param('custom_gtl.bl_term')
        res.update(bl_term=bl_term)
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        param = self.env['ir.config_parameter'].sudo()
        bl_term = self.bl_term or False
        param.set_param('custom_gtl.bl_term', bl_term)

