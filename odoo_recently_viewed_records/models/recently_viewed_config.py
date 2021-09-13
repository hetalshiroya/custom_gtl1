# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    recently_viewed_limit = fields.Integer(related="company_id.recently_viewed_limit", string="Recently Viewed Records Limit", help="Limit the Number of Recently Viewed Records.", readonly=False)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ir_default = self.env['ir.default'].sudo()
        recently_viewed_limit = ir_default.get('res.config.settings', 'recently_viewed_limit')
        res.update({'recently_viewed_limit': recently_viewed_limit})
        return res


class ResCompany(models.Model):

    _inherit = 'res.company'

    recently_viewed_limit = fields.Integer("Recently Viewed Records Limit", help="Limit the Number of Recently Viewed Records.")
