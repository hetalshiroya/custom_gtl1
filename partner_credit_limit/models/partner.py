# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    over_credit = fields.Boolean('Allow Over Credit?', track_visibility='always', default=True)
    # credit_used = fields.Float(string='Credit Used', digits=(8,0))
