from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    iso_image = fields.Binary("ISO")
